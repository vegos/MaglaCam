#!/usr/bin/python

# This is my attempt to learn python on a Raspberry Pi
# Creating a camera application for stills or timelapse
# using a Raspberry Pi Model B, a Camera Board v1.3
# and a LCD-PI32 3.2" TFT LCD with Touchscreen
# 
# (c)2014, Antonis Maglaras
# Version: Unknown

import pygame
import picamera
import sys
import time
from time import strftime
import datetime
import os
import getopt
import array, fcntl
from cStringIO import StringIO


# Set up some colors
BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
RED   = (255,   0,   0)
GREEN = (  0, 255,   0)
BLUE  = (  0,   0, 255)

Exit = False

_IOC_NRBITS   =  8
_IOC_TYPEBITS =  8
_IOC_SIZEBITS = 14
_IOC_DIRBITS  =  2

_IOC_DIRMASK    = (1 << _IOC_DIRBITS) - 1
_IOC_NRMASK     = (1 << _IOC_NRBITS) - 1
_IOC_TYPEMASK   = (1 << _IOC_TYPEBITS ) - 1

_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT+_IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT+_IOC_TYPEBITS
_IOC_DIRSHIFT  = _IOC_SIZESHIFT+_IOC_SIZEBITS

_IOC_NONE = 0
_IOC_WRITE = 1

_IOC_READ = 2

def _IOC(dir, type, nr, size):
#  print 'dirshift {}, typeshift {}, nrshift {}, sizeshift {}'.format(_IOC_DIRSHIFT, _IOC_TYPESHIFT, _IOC_NRSHIFT, _IOC_SIZESHIFT)
  ioc = (dir << _IOC_DIRSHIFT ) | (type << _IOC_TYPESHIFT ) | (nr << _IOC_NRSHIFT ) | (size << _IOC_SIZESHIFT)
  if ioc > 2147483647: ioc -= 4294967296
  return ioc
     
#def _IO(type, nr):
#  return _IOC(_IOC_NONE,  type, nr, 0)

def _IOR(type,nr,size):
   return _IOC(_IOC_READ,  type, nr, size)

#def _IOW(type,nr,size):
#  return _IOC(_IOC_WRITE, type, nr, sizeof(size))
        
SSD1289_GET_KEYS = _IOR(ord('K'), 1, 4)
#print 'ssd {} {:12} {:0>8x} {:0>32b}'.format(ssd1289, hex(ssd1289), ssd1289, ssd1289)
buf = array.array('h',[0])
        
 
# Set the framebuffer device to be the TFT & set the touchscreen dev
os.environ["SDL_FBDEV"] = "/dev/fb1"
os.environ["SDL_MOUSEDRV"] = "TSLIB"
os.environ["SDL_MOUSEDEV"] = "/dev/input/event0"


# Define some values
ISO = 0
SS = 0
WB = 1
METERING = 0
tmpISO = "auto"
tmpSS = 0
tmpSSstring = "auto"
tmpWB = "auto"
tmpMETERING = "auto"
ShutterSpeed = 0



def buttonCheck(sec):
    rightnow = datetime.datetime.now().second+sec
    #    for x in range(0,sec):
    while datetime.datetime.now().second<rightnow:
       with open('/dev/fb1', 'rw') as fd:
         fcntl.ioctl(fd, SSD1289_GET_KEYS, buf, 1) # read the key register
         keybits = 0b11111-buf[0] # invert so bits show key pressed
         
         if keybits:
#             print 'buf {:0>8b}'.format(keybits)
             buttons = (keybits & 0b10000 > 0, keybits & 0b01000 > 0, keybits & 0b00100 > 0, keybits & 0b00010 > 0, keybits & 0b00001 > 0)
             if buttons == (1,0,0,0,0):
                 return 1
                 break
             if buttons == (0,0,0,1,0):
                 return 3
                 break
             if buttons == (0,0,0,0,1):
                 return 2                 
                 break
         for event in pygame.event.get():
             if event.type == pygame.MOUSEMOTION:
                 mouseX,mouseY = pygame.mouse.get_pos()
                 if mouseX>=240 and mouseX<=320 and mouseY >=150 and mouseY <= 175:
                     return 3
                     break
                 if mouseX>=240 and mouseX<=320 and mouseY >=190 and mouseY <= 215:
                     return 2
                     breaek
                 if mouseX>=240 and mouseX<=320 and mouseY >=0 and mouseY <= 30:
                     return 1
                     break
#                 print ("%s x %s" % pygame.mouse.get_pos())
         pygame.display.update()

    return 0


def delayFor(sec):
    global ISO
    global SS
    global WB
    global METERING
    global Exit   
    rightnow = datetime.datetime.now().second+sec
    #    for x in range(0,sec):
    while datetime.datetime.now().second<rightnow:
       with open('/dev/fb1', 'rw') as fd:
         fcntl.ioctl(fd, SSD1289_GET_KEYS, buf, 1) # read the key register
         keybits = 0b11111-buf[0] # invert so bits show key pressed
         
         if keybits:
#             print 'buf {:0>8b}'.format(keybits)
             # there's probably a better way to do this ...
             buttons = (keybits & 0b10000 > 0, keybits & 0b01000 > 0, keybits & 0b00100 > 0, keybits & 0b00010 > 0, keybits & 0b00001 > 0)
             if buttons == (0,1,0,0,0):
                 ISO+=1
                 break
             if buttons == (0,0,0,0,1):
                 WB+=1
                 break
             if buttons == (0,0,1,0,0):
                 SS+=1
                 break
             if buttons == (0,0,0,1,0):
                 METERING+=1
                 break
             if buttons == (1,0,0,0,0):
                 Exit = True
         for event in pygame.event.get():
             if event.type == pygame.MOUSEMOTION:
                 mouseX,mouseY = pygame.mouse.get_pos()
                 if mouseX>=190 and mouseX<=240 and mouseY >=65 and mouseY <= 95:
                     ISO+=1
                 if mouseX>=190 and mouseX<=240 and mouseY >=110 and mouseY <= 135:
                     SS+=1
                 if mouseX>=190 and mouseX<=240 and mouseY >=150 and mouseY <= 175:
                     METERING+=1
                 if mouseX>=190 and mouseX<=240 and mouseY >=190 and mouseY <= 215:
                     WB+=1
                 if mouseX>=240 and mouseX<=320 and mouseY >=0 and mouseY <= 30:
                     Exit = True
#                 print ("%s x %s" % pygame.mouse.get_pos())
         pygame.display.update()
         


def drawMainMenu():
   screen.fill((0,0,0))
   showText("Shoot",25,250,5,(255,255,255),False,False)
   showText("ISO",25,20,70,(200,200,100),False,False)
   showText("Shutter Speed",25,20,110,(200,200,1),False,False)
   showText("Metering",25,20,150,(200,200,1),False,False)
   showText("White Balance",25,20,190,(200,200,1),False,False)

   
def drawOptions():
   global ISO
   global SS
   global WB
   global METERING
   global tmpISO
   global tmpSS
   global tmpWB
   global tmpMETERING
   global ShutterSpeed
   global tmpSSstring
   oldISO = tmpISO
   oldSS = tmpSSstring
   oldWB = tmpWB
   oldMETERING = tmpMETERING
   oldSSstring = tmpSSstring
   
   if ISO == 1:
      tmpISO = "100"
   elif ISO == 2:
      tmpISO = "200"
   elif ISO == 3:
      tmpISO = "400"
   elif ISO == 4:
      tmpISO = "800"
   elif ISO == 5:
      tmpISO = "auto"
   else:
      tmpISO = "auto"
      ISO = 0
      
   if WB == 1:
      tmpWB = "auto"
   elif WB == 2:
      tmpWB = "sun"
   elif WB == 3:
      tmpWB = "cloud"
   elif WB == 4:
      tmpWB = "shade"
   elif WB == 5:
      tmpWB = "tungsten"
   elif WB == 6:
      tmpWB = "fluorescent"
   elif WB == 7:
      tmpWB = "incandescent"
   elif WB == 8:
      tmpWB = "flash"
   elif WB == 9:
      tmpWB = "horizon"
   elif WB == 10:
      tmpWB = "off"
   else:
      tmpWB = "auto"
      WB = 1

   if METERING == 1:
      tmpMETERING = "average"
   elif METERING == 2:
      tmpMETERING = "spot"
   elif METERING == 3:
      tmpMETERING = "backlit"
   elif METERING == 4:
      tmpMETERING = "matrix"
   elif METERING == 5:
      tmpMETERING = "auto"
      METERING = 0
   else:
      tmpMETERING = "auto"
      METERING = 0
      
   if SS == 1:
      tmpSS = 1000
      ShutterSpeed = 1
      tmpSSstring = "1/1000"   
   elif SS == 2:
      tmpSS = 500
      ShutterSpeed = 2
      tmpSSstring = "1/500"
   elif SS == 3:
      tmpSS = 250
      ShutterSpeed = 4
      tmpSSstring = "1/250"   
   elif SS == 4:
      tmpSS = 125
      ShutterSpeed = 8
      tmpSSstring = "1/125"
   elif SS == 5:
      tmpSS = 60
      ShutterSpeed = 17
      tmpSSstring = "1/60"
   elif SS == 6:
      tmpSS = 30
      ShutterSpeed = 33
      tmpSSstring = "1/30"
   elif SS == 7:
      tmpSS = 15
      ShutterSpeed = 67
      tmpSSstring = "1/15"
   elif SS == 8:
      tmpSS = 8
      ShutterSpeed = 125
      tmpSSstring = "1/8"
   elif SS == 9:
      tmpSS = 4
      ShutterSpeed = 250
      tmpSSstring = "1/4"
   elif SS == 10:
      tmpSS = 2
      ShutterSpeed = 500
      tmpSSstring = "1/2"   
   elif SS == 11:
      tmpSS = 1
      ShutterSpeed = 1000
      tmpSSstring = "1"
   else: #if SS == 12:
      tmpSSstring = "auto"
      tmpSS = 0
      SS = 0
      ShutterSpeed = 0
         
   if oldISO != tmpISO:
      showText(oldISO,25,200,70,(0,0,0),False,False)
   if oldSSstring != tmpSSstring:
      showText(oldSSstring,25,200,110,(0,0,0),False,False)
   if oldMETERING != tmpMETERING:
      showText(oldMETERING,25,200,150,(0,0,0),False,False)
   if oldWB != tmpWB:
      showText(oldWB,25,200,190,(0,0,0),False,False)
   showText(tmpISO,25,200,70,(255,255,1),False,False)
   showText(tmpSSstring,25,200,110,(255,255,1),False,False)
   showText(tmpMETERING,25,200,150,(255,255,1),False,False)
   showText(tmpWB,25,200,190,(255,255,1),False,False)



def showText(text, size, xx, yy, color, centered, clearScreen):
    if clearScreen:
        screen.fill((0, 0, 0)) 

    myfont = pygame.font.Font(None, size)
    mytext = myfont.render(text, 0, color)
    if centered:
        mytextrect = mytext.get_rect()
        mytextrect.centerx = xx
        mytextrect.centery = yy
        screen.blit(mytext,mytextrect)
    else:
        screen.blit(mytext, (xx, yy))

    pygame.display.flip()
                                                                                                    
def captureImage():
    global tmpISO
    global tmpWB
    global tmpMETERING
    global ImgNumber
    global ShutterSpeed
    if (os.path.isdir("/mnt/usb/DCIM")):
       pathname = "/mnt/usb/DCIM"
    else:
       pathname = "/mnt/cray_root/timelapse/"
    filename = pathname+"IMG"+str(ImgNumber).zfill(5)+"_"+datetime.datetime.fromtimestamp(time.time()).strftime('%d%m%y%H%M%S')+".JPG"
    options = "-n"
    if ShutterSpeed != 0:
       options += " -ss "+str(ShutterSpeed)
    if tmpISO != "auto":
       options += " -ISO "+tmpISO
    if tmpMETERING != "auto":
       options += " -mm "+tmpMETERING
    options += " -awb "+tmpWB
#    print "Options: "+options
    options += " -o "+filename
    x="raspistill "+options
#    print "Filename: "+filename
    os.system(x)
    pic = pygame.image.load(filename)
    pic = pygame.transform.scale(pic, (320, 240))
    picrect = pic.get_rect()
#    screen.fill((0,0,0))
    screen.blit(pic, picrect)
    pygame.display.flip()

 
def displayText(text, size, line, color, clearScreen):
    if clearScreen:
        screen.fill((0, 0, 0)) 
    font = pygame.font.Font(None, size)
    text = font.render(text, 0, color)
    textRotated = pygame.transform.rotate(text, -90)
    textpos = textRotated.get_rect()
    textpos.centery = 80  
    if line == 1:
        textpos.centerx = 90
        screen.blit(textRotated,textpos)
    elif line == 2:
        textpos.centerx = 40
        screen.blit(textRotated,textpos)
    pygame.display.flip()
 
 
def main():
    global screen
    global ImgNumber
    global Exit
    global tmpISO
    global tmpSS
    global tmpWB
    global tmpMETERING
    pygame.init()
    size = width, height = 320, 240
    black = 0, 0, 0 
    pygame.mouse.set_visible(0)
    screen = pygame.display.set_mode(size)
    
    drawMainMenu()
    while Exit == False:       
       drawOptions()
       delayFor(1)
    ImgNumber = 0
    screen.fill((0,0,0))
    
    exitOrNo = True
    while exitOrNo:
        ImgNumber+=1
        showText("Shooting...",20,10,10,(255,255,255),False,True)
        captureImage()
        showText("Shot "+str(ImgNumber),20,10,10,(255,255,255),False,False)
        showText("ISO",18,10,150,(255,255,255),False,False)
        showText("Shutter Speed",18,10,170,(255,255,255),False,False)
        showText("Metering",18,10,190,(255,255,255),False,False)
        showText("White Balance",18,10,210,(255,255,255),False,False)
        showText(tmpISO,18,105,150,(255,255,255),False,False)
        showText(tmpSSstring,18,105,170,(255,255,255),False,False)
        showText(tmpMETERING,18,105,190,(255,255,255),False,False)
        showText(tmpWB,18,105,210,(255,255,255),False,False)
        showText("Shoot",25,255,10,(255,255,1),False,False)
        showText("Menu",25,260,150,(255,255,1),False,False)
        showText("Exit",25,275,190,(255,255,1),False,False)        
        ret = buttonCheck(10)
        if ret == 2:
           sys.exit()
           exitOrNo = True
        elif ret == 1:
           exitOrNo = True
        elif ret == 3:
           screen.fill((0,0,0))
           drawMainMenu()
           Exit = False
           while Exit == False:
              drawOptions()
              delayFor(1)
           exitOrNo = True
        else:
           while ret == 0:
              ret = buttonCheck(1)              
#           time.sleep(10)
#        time.sleep(10) 

#        graph = pygame.image.load("satellite.gif")
#        graph = pygame.transform.rotate(graph, 0)
#        graphrect = graph.get_rect()
#        screen.fill(black)
#        screen.blit(graph, graphrect)
#        pygame.display.flip()
#        time.sleep(10)
 
if __name__ == '__main__':
    while True:
       main()
