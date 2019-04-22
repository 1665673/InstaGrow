#!/bin/bash

SWAP=7G
if [ $# -gt 0 ];then
    SWAP=$1
fi

apt-get -y update
apt-get -y install python3-pip
apt-get -y install firefox

cp firefox/geckodriver.ubuntu /usr/local/bin/geckodriver

pip3 install -r requirements.txt

fallocate -l ${SWAP} /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

chown root:root /etc/rc.local
chmod 755 /etc/rc.local
systemctl enable rc-local.service

sed -i 's/^exit 0/swapon \/swapfile\ncd $PWD\npython3 droplet.py\nexit 0/' /etc/rc.local
