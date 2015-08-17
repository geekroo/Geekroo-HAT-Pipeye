#!/bin/bash
echo "Step 1: Update software package lists"
sudo apt-get update
echo "Step 2: Install PiGPIO"
cd ~
wget abyz.co.uk/rpi/pigpio/pigpio.zip
unzip pigpio.zip
cd PIGPIO
make
sudo make install
cd ..
rm ./pigpio.zip
rm -rf PIGPIO
echo "Step 3: Install Python Packages"
sudo apt-get -y install python-netifaces python-psutil
echo "Step 4:Install pipeye software"
git clone https://github.com/geekroo/Geekroo-HAT-Pipeye.git
cd Geekroo-HAT-Pipeye
sudo cp pipeye.py /usr/bin/
sudo cp pipeyecon.py /usr/bin/
cd ..
echo "Step 4: Install Services"
c3=$(grep -n '/var/pipeyelog' /etc/fstab)
c2=$(grep -n '^sudo python /usr/bin/pipeye.py' /etc/rc.local)
c1=$(grep -n '^sudo pigpiod' /etc/rc.local)
if [ -z "$c3" ]; then
  su -c "echo 'tmpfs   /var/pipeyelog    tmpfs    defaults,noatime,nosuid,mode=0755,size=1m    0 0' >> /etc/fstab"
fi
num=$(grep -n '^exit 0' /etc/rc.local | awk -F ":" '{print $1}')
numfinal=$[$num-1]
numfinala=$numfinal"a"
if [ -z "$c2" ]; then
  sed -i "$numfinala sudo python /usr/bin/pipeye.py &" /etc/rc.local
fi
if [ -z "$c1" ]; then
  sed -i "$numfinala sudo pigpiod" /etc/rc.local
fi
echo "Please Run sudo reboot to restart your Raspberry Pi!"
echo "After reboot, please run sudo python /usr/bin/pipeyecon.py to have fun :)"
