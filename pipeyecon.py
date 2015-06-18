#!/usr/bin/env python
# coding=utf-8
import os
import sys
import time
from time import sleep

tmpFolder = "/var/pipeyelog/"
tmpFile = tmpFolder + "pipeyelog.txt"

def drawMenu():
    print "-------------------------"
    print "Operation Selection:"
    print "[b]:get battery info"
    print "[e]:exit program"
    print "[Enter]:display this menu"
    print "other string:send to pipeye"
    print "-------------------------"
    
while True:
    drawMenu()
    op = str(raw_input("Operation Selection:"))
    if op == "b":
        if os.path.isdir(tmpFolder) is not True:
            os.mkdir(tmpFolder)
        if os.path.isfile(tmpFolder + "givemeinfo.txt") is not True:
            os.mknod(tmpFolder + "givemeinfo.txt")
        fp = open(tmpFolder + "givemeinfo.txt","w")
        fp.write("givemeinfo")
        fp.close()
        sleep(1)
        if os.path.isfile(tmpFolder + "pipeyelog.txt") is True:
            fp = open(tmpFolder + "pipeyelog.txt","r")
            info = fp.readline()
            print info
            fp.close()
    elif op == "e":
        sleep(0.5)
        sys.exit()
    else:
        if (op != "") and (os.path.isdir(tmpFolder + str(op)[0:84]) is not True):
            os.mkdir(tmpFolder + str(op)[0:84])
