#!/usr/bin/env python
# coding=utf-8
import os
import sys
import time
import pigpio  #pigpio库
import netifaces
import thread
import psutil
import threading
from time import sleep

# software serial para
TX =13
RX =16
baud = 9600
bits = 8
ten_char_time = 100.0 / float(baud)
exitThread = False
op = ""
firstStart = False
busy = False
debugmode = 0
logFolder = "/home/pi/"
logfile = ""
tmpFolder = "/var/pipeyelog/"
tmpFile = tmpFolder + "pipeyelog.txt"
mutex = threading.Lock()

# convert battery voltage to real value
def convertBatVoltage(v):
    return str('%0.2f' % (long(v,10) * 78.125 / 1000000)) + "V"
    
# convert input current reg to value
def convertInputCurrent(v):
    tempCurrent = int(v,10) & 7
    if tempCurrent == 0:
        return "0.1"
    elif tempCurrent == 1:
        return "0.15"
    elif tempCurrent == 2:
        return "0.5"
    elif tempCurrent == 3:
        return "0.9"
    elif tempCurrent == 4:
        return "1.2"
    elif tempCurrent == 5:
        return "1.5"
    elif tempCurrent == 6:
        return "2.0"
    elif tempCurrent == 7:
        return "3.0"

# convert charge current reg to value
def convertChargeCurrent(v):
    offsetCurrent = 0.512
    if int(v,10) & 128 == 128:
        offsetCurrent = offsetCurrent + 2.048
    if int(v,10) & 64 == 64:
        offsetCurrent = offsetCurrent + 1.024
    if int(v,10) & 32 == 32:
        offsetCurrent = offsetCurrent + 0.512
    if int(v,10) & 16 == 16:
        offsetCurrent = offsetCurrent + 0.256
    if int(v,10) & 8  == 8:
        offsetCurrent = offsetCurrent + 0.128
    if int(v,10) & 4  == 4:
        offsetCurrent = offsetCurrent + 0.64
    return str(offsetCurrent)
    
# convert charge Voltage reg to value
def convertChargeVoltage(v):
    offsetVoltage = 3.504
    if int(v,10) & 128 == 128:
        offsetVoltage = offsetVoltage + 0.512
    if int(v,10) & 64 == 64:
        offsetVoltage = offsetVoltage + 0.256
    if int(v,10) & 32 == 32:
        offsetVoltage = offsetVoltage + 0.128
    if int(v,10) & 16 == 16:
        offsetVoltage = offsetVoltage + 0.64
    if int(v,10) & 8  == 8:
        offsetVoltage = offsetVoltage + 0.32
    if int(v,10) & 4  == 4:
        offsetVoltage = offsetVoltage + 0.16
    return str(offsetVoltage)
    
# save pmu info to file
def savePmuInfo(s):
    strPmuInfo = s.split("|")
    strPmuInfoItem = ""
    strPmuInfoItem = strPmuInfoItem + "ID:"
    strPmuInfoItem = strPmuInfoItem + strPmuInfo[0]
    strPmuInfoItem = strPmuInfoItem + ","
    strPmuInfoItem = strPmuInfoItem + "DumpEnergy:"
    strPmuInfoItem = strPmuInfoItem + strPmuInfo[1]
    strPmuInfoItem = strPmuInfoItem + ","
    strPmuInfoItem = strPmuInfoItem + "BatVoltage:"
    strPmuInfoItem = strPmuInfoItem + convertBatVoltage(strPmuInfo[2])
    strPmuInfoItem = strPmuInfoItem + ","
    strPmuInfoItem = strPmuInfoItem + "InputCurrent:"
    strPmuInfoItem = strPmuInfoItem + convertInputCurrent(strPmuInfo[3])
    strPmuInfoItem = strPmuInfoItem + ","
    strPmuInfoItem = strPmuInfoItem + "ChargeCurrent:"
    strPmuInfoItem = strPmuInfoItem + convertChargeCurrent(strPmuInfo[4])
    strPmuInfoItem = strPmuInfoItem + ","
    strPmuInfoItem = strPmuInfoItem + "ChargeVoltage:"
    strPmuInfoItem = strPmuInfoItem + convertChargeVoltage(strPmuInfo[5])
    strPmuInfoItem = strPmuInfoItem + ","
    strPmuInfoItem = strPmuInfoItem + "LogTime:"
    strPmuInfoItem = strPmuInfoItem + time.strftime('[%Y-%m-%d]-%H:%M:%S',time.localtime(time.time()))
    strPmuInfoItem = strPmuInfoItem + "\n"
    if os.path.isfile("/home/pi/pipeyelog.txt") is not True:
        os.mknod("/home/pi/pipeyelog.txt")
    fp = open("/home/pi/pipeyelog.txt","a")
    fp.write(strPmuInfoItem)
    fp.close()
    #ID|DumpEnergy|BatVoltage|InputCurrent|ChargeCurrent|ChargeVoltage|DateTime
    #if int(strPmuinfo[1]) < 1:
    #    os.system("sudo halt -h")
    
# init software serial
def initMySerial():
    global baud,bits,RX,TX,status
    # default band set
    if len(sys.argv) > 1:
        baud = int(sys.argv[1])
    # set data bit default 8
    if len(sys.argv) > 2:
        bits = int(sys.argv[2])
    # set gpio pin (BCM GPIO)
    pi.set_mode(RX, pigpio.INPUT)
    pi.set_mode(TX, pigpio.OUTPUT)
    # fatal exceptions off (so that closing an unopened gpio doesn't error)
    pigpio.exceptions = False
    # close rx reading
    pi.bb_serial_read_close(RX)
    # fatal exceptions on
    pigpio.exceptions = True
    # open gpio for reading
    status = pi.bb_serial_read_open(RX, baud, bits)
    # create a wave
    pi.wave_clear()
    
# pigpio init
pi = pigpio.pi()

# software serial init
initMySerial()
startTime = time.time()

def getAdpaterAddress(adp):
    try:
        ip = netifaces.ifaddresses(adp)[netifaces.AF_INET][0]['addr']
    except:
        ip = ''
    return ip

def getCPUuse2():
    try:
        cu = psutil.cpu_percent(1)
    except:
        cu = '0'
    return cu
    
def getCPUuse():
    try:
        cu = str(os.popen("top -bn1 | awk '/Cpu\(s\):/ {print $2}'").readline().strip())
    except:
        cu = '0'
    return cu
    
def getCPUtemperature():
    res = os.popen('vcgencmd measure_temp').readline()
    return(res.replace("temp=","").replace("'C\n",""))
 
def getRAMinfo():
    p = os.popen('free')
    i = 0
    while 1:
        i = i + 1
        line = p.readline()
        if i==2:
            return(line.split()[1:4])
            
def getDiskSpace():
    p = os.popen("df -h /")
    i = 0
    while 1:
        i = i +1
        line = p.readline()
        if i==2:
            return(line.split()[1:5])
            
def tellPMUInfo():
    
    sleep(0.1)
    sendMessageToPMU(str(getCPUuse()) + "!0")
    
    sendMessageToPMU(str(getCPUtemperature()) + "!1")
    # ram info
    RAM_stats = getRAMinfo()
    
    sendMessageToPMU(str(round(int(RAM_stats[0]) / 1000,1)) + "!2")
    
    sendMessageToPMU(str(round(int(RAM_stats[1]) / 1000,1)) + "!3")
    
    sendMessageToPMU(str(round((int(RAM_stats[0]) - int(RAM_stats[1])) / 1000,1)) + "!4")
    # disk info
    DISK_stats = getDiskSpace()
    
    diskTotal = float(DISK_stats[0].replace("G",""))
    
    diskUsed  = float(DISK_stats[1].replace("G",""))
    
    diskFree = diskTotal - diskUsed
    
    sendMessageToPMU(str(diskTotal) + "!5")
    
    sendMessageToPMU(str(diskUsed) + "!6")
    
    sendMessageToPMU(str(diskFree) + "!7")
    
    # network info
    eth0ip = getAdpaterAddress('eth0')
    if eth0ip == "":
        eth0ip = "none"
    
    sendMessageToPMU(eth0ip + "!8")
    wlan0ip = getAdpaterAddress('wlan0')
    
    sendMessageToPMU(wlan0ip + "!9")
# parse command recevied from serial
def parseCommand(s):
    if s == "shutdown":
        print "shutdown"
        
        sendMessageToPMU("[RPI]:I'm halting...");
        os.system("sudo halt -h")
    elif s == "reboot":
        print "reboot"
        
        sendMessageToPMU("[RPI]:I'm rebooting...");
        os.system("sudo reboot")
    elif s == "Hello Raspberry PI!":
        
        sendMessageToPMU("Hello PMU!")
    elif s == "givemeinfo":
        # empty info info
        # sendMessageToPMU("empty!9")
        # cpu info
        
        tellPMUInfo()
    elif s.find("rualive") > -1:
        
        sendMessageToPMU(s.replace("rualive!","") + "!:")
        tellPMUInfo()

# Send message to PMU
def sendMessageToPMU(msg):
    if mutex.acquire(1): 
        print msg
        msg = msg[0:84]
        msg = "~" + msg + "~"
        #pi.wave_clear()
        pi.wave_add_serial(TX, baud, bytearray(msg))
        while pi.wave_tx_busy(): # wait until all data sent
            pass
        #wid=
        wid = pi.wave_create()
        pi.wave_send_once(wid)   # transmit serial data
        #pi.wave_clear()
        pi.wave_delete(wid)
        mutex.release()

   # sleep(0.1)
    
def tmpFolderMonitor(no,interval):
    global exitThread,tmpFolder,tmpFile
    while True:
        if exitThread == True:
            thread.exit_thread()
        checkTmpFolder()
        l = os.listdir(tmpFolder)
        if len(l) > 0:
            for i in l:
                if os.path.isdir(tmpFolder + str(i)) is True:
                    
                    sendMessageToPMU(str(i))
                    if str(i) != "":
                        os.rmdir(tmpFolder + str(i))
                    sleep(1)
        if os.path.isfile(tmpFolder + "givemeinfo.txt") is True:
            os.remove(tmpFolder + "givemeinfo.txt")
            
            sendMessageToPMU("givemeinfo")
        sleep(interval)
            
# software serial monitor
def softSerialMonitor(no,interval):
    global exitThread
    while True:
        if exitThread == True:
            pi.bb_serial_read_close(RX)
            pi.stop()
            print "[sSerial Monitor]:exit"
            thread.exit_thread()
        count = 1
        strTemp = ""
        while count: # read echoed serial data
            (count, result) = pi.bb_serial_read(RX)
            if count:
                strTemp = strTemp + result
            time.sleep(ten_char_time) 
        if ((strTemp.find("~") == 0) and (strTemp.rfind("~") == len(strTemp) - 1)):
            if len(strTemp) > 2:
                strTemp = strTemp[1:len(strTemp)-1]
            if strTemp is not "":
                if strTemp[len(strTemp)-2:len(strTemp)] == "!0":
                    savePmuInfo(str(strTemp))
                else:
                    parseCommand(strTemp)
        #else:
        #    print "bad message"
                
# convert input current reg to value
def convertInputCurrent(v):
    tempCurrent = int(v,10) & 7
    r = 0
    if tempCurrent == 0:
        r = "0.1"
    elif tempCurrent == 1:
        r = "0.15"
    elif tempCurrent == 2:
        r = "0.5"
    elif tempCurrent == 3:
        r = "0.9"
    elif tempCurrent == 4:
        r = "1.2"
    elif tempCurrent == 5:
        r = "1.5"
    elif tempCurrent == 6:
        r = "2.0"
    elif tempCurrent == 7:
        r = "3.0"
    return r + "A"
        
# convert input current reg to value
def convertInputVoltage(v):
    offsetVoltage = 3.88
    if int(v,10) & 64 == 64:
        offsetVoltage = offsetVoltage + 0.64
    if int(v,10) & 32 == 32:
        offsetVoltage = offsetVoltage + 0.32
    if int(v,10) & 16 == 16:
        offsetVoltage = offsetVoltage + 0.16
    if int(v,10) & 8  == 8:
        offsetVoltage = offsetVoltage + 0.08
    return str(offsetVoltage) + "V"
        
# convert charge current reg to value
def convertChargeCurrent(v):
    offsetCurrent = 0.512
    if int(v,10) & 128 == 128:
        offsetCurrent = offsetCurrent + 2.048
    if int(v,10) & 64 == 64:
        offsetCurrent = offsetCurrent + 1.024
    if int(v,10) & 32 == 32:
        offsetCurrent = offsetCurrent + 0.512
    if int(v,10) & 16 == 16:
        offsetCurrent = offsetCurrent + 0.256
    if int(v,10) & 8  == 8:
        offsetCurrent = offsetCurrent + 0.128
    if int(v,10) & 4  == 4:
        offsetCurrent = offsetCurrent + 0.64
    return str(offsetCurrent) + "A"
    
# convert charge Voltage reg to value
def convertChargeVoltage(v):
    offsetVoltage = 3.504
    if int(v,10) & 128 == 128:
        offsetVoltage = offsetVoltage + 0.512
    if int(v,10) & 64 == 64:
        offsetVoltage = offsetVoltage + 0.256
    if int(v,10) & 32 == 32:
        offsetVoltage = offsetVoltage + 0.128
    if int(v,10) & 16 == 16:
        offsetVoltage = offsetVoltage + 0.064
    if int(v,10) & 8  == 8:
        offsetVoltage = offsetVoltage + 0.032
    if int(v,10) & 4  == 4:
        offsetVoltage = offsetVoltage + 0.016
    return str(offsetVoltage) + "V"

def createFolder(f):
    if os.path.isdir(f) is not True:
        os.mkdir(f) 
    
def createFile(f):
    if os.path.isfile(f) is not True:
        os.mknod(f)


# save pmu info to file
def savePmuInfo(s):
    global logFolder,logFile,tmpFolder,tmpFile
    strPmuInfo = s.split("|")
    strPmuInfoItem = ""
    strPmuInfoItem = strPmuInfoItem + "ID:"
    strPmuInfoItem = strPmuInfoItem + strPmuInfo[0]
    strPmuInfoItem = strPmuInfoItem + ","
    strPmuInfoItem = strPmuInfoItem + "DumpEnergy:"
    strPmuInfoItem = strPmuInfoItem + strPmuInfo[1]
    strPmuInfoItem = strPmuInfoItem + "%,"
    strPmuInfoItem = strPmuInfoItem + "BatVoltage:"
    strPmuInfoItem = strPmuInfoItem + convertBatVoltage(strPmuInfo[2])
    strPmuInfoItem = strPmuInfoItem + ","
    strPmuInfoItem = strPmuInfoItem + "InputC:"
    strPmuInfoItem = strPmuInfoItem + convertInputCurrent(strPmuInfo[3])
    strPmuInfoItem = strPmuInfoItem + ","
    strPmuInfoItem = strPmuInfoItem + "InputV:"
    strPmuInfoItem = strPmuInfoItem + convertInputVoltage(strPmuInfo[4])
    strPmuInfoItem = strPmuInfoItem + ","
    strPmuInfoItem = strPmuInfoItem + "ChargeC:"
    strPmuInfoItem = strPmuInfoItem + convertChargeCurrent(strPmuInfo[5])
    strPmuInfoItem = strPmuInfoItem + ","
    strPmuInfoItem = strPmuInfoItem + "ChargeV:"
    strPmuInfoItem = strPmuInfoItem + convertChargeVoltage(strPmuInfo[6])
    strPmuInfoItem = strPmuInfoItem + ","
    strPmuInfoItem = strPmuInfoItem + "LogTime:"
    strPmuInfoItem = strPmuInfoItem + time.strftime('[%Y-%m-%d]-%H:%M:%S',time.localtime(time.time()))
    strPmuInfoItem = strPmuInfoItem + "\n"
    createFolder(logFolder)
    logFile = logFolder + "pipeye_" + time.strftime('[%Y-%m-%d]' + ".txt")
    createFile(logFile)
    #if os.path.isfile("/home/pi/pipeyelog.txt") is not True:
    #    os.mknod("/home/pi/pipeyelog.txt")
    fp = open(logFile,"a")
    fp.write(strPmuInfoItem)
    fp.close()
    createFolder(tmpFolder)
    createFile(tmpFile)
    checkTmpFolder()
    fp = open(tmpFile,"w")
    fp.write(strPmuInfoItem)
    fp.close()
    
    
def checkPmuInfo(no,interval):
    global exitThread
    while True:
        if exitThread == True:
            print "[pipeye Monitor]:exit"
            thread.exit_thread()
        sleep(interval)
        
        sendMessageToPMU("givemeinfo")
        
def checkTmpFolder():
    global tmpFolder
    if firstStart is not True:
        if os.path.isdir(tmpFolder) is not True:
            os.mkdir(tmpFolder)

def createThread():
    tMon = thread.start_new_thread(softSerialMonitor,(1,0))  
    tPmuMon = thread.start_new_thread(checkPmuInfo,(1,60))  
    tTmpFolder = thread.start_new_thread(tmpFolderMonitor,(1,0.5))  

#print "pipeye V1.0"
#print ""
#print "please run me in background like 'sudo python pipeye.py &'"
#print "or add me to /etc/rc.local"

while True:
    if firstStart is not True:
        checkTmpFolder()
        createThread()
        
        sendMessageToPMU("I've started!")
        firstStart = True
        
        sendMessageToPMU("givemeinfo")
    #softSerialMonitor()
    
    if debugmode == 1:
        print "-------------------------"
        print "Operation Selection:"
        print "[b]:get battery info"
        print "[e]:exit program"
        print "[Enter]:display this menu"
        print "-------------------------"
        op = str(raw_input("Operation Selection:"))
        if op == "b":
            
            sendMessageToPMU("givemeinfo")
        elif op == "e":
            exitThread = True
            sleep(0.5)
            sys.exit()
        else:
            sendMessageToPMU(op)
    sleep(2)