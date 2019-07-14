#!/bin/bash

SWAP=7G
if [ $# -gt 0 ];then
    SWAP=$1
fi

apt-get -y update
apt-get -y install python3-pip

# headless X-11
apt-get -y install xvfb

#apt-get -y install firefox
apt-get -y install firefox
apt-get -y remove firefox
if test ! -f ./firefox-66.0b9.tar.bz2; then
    wget https://ftp.mozilla.org/pub/firefox/releases/66.0b9/linux-x86_64/en-US/firefox-66.0b9.tar.bz2
    tar xvf firefox-66.0b9.tar.bz2 -C ./firefox
fi

rm -rf /usr/lib/firefox
rm /usr/bin/firefox
cp -r ./firefox/firefox /usr/lib/firefox
ln -s /usr/lib/firefox/firefox /usr/bin/firefox
apt-mark hold firefox

cp firefox/geckodriver.ubuntu /usr/local/bin/geckodriver

pip3 install -r requirements.txt

fallocate -l ${SWAP} /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
Xvfb :99 &
#export DISPLAY=:99

if test ! -f /etc/rc.local; then
    # echo "rc.local1 does not exists"
    echo -e '#!/bin/bash\n\nexit 0' >> /etc/rc.local
fi

chown root:root /etc/rc.local
chmod 755 /etc/rc.local
systemctl enable rc-local.service

if ! grep -q "droplet.py" /etc/rc.local; then
    dir=$(echo $PWD | sed 's/\//\\\//g')
    #sed -i "s/^exit 0/swapon \/swapfile\ncd $dir\npython3 droplet.py\nexit 0/" /etc/rc.local
    sed -i "s/^exit 0/swapon \/swapfile\nexit 0/" /etc/rc.local
    sed -i "s/^exit 0/Xvfb :99 \&\nexit 0/" /etc/rc.local
    #sed -i "s/^exit 0/export DISPLAY=:99\nexit 0/" /etc/rc.local
    sed -i "s/^exit 0/cd $dir\nexit 0/" /etc/rc.local
    sed -i "s/^exit 0/screen -d -m python3 droplet.py\nexit 0/" /etc/rc.local
fi

if ! grep -q "Xvfb" /etc/rc.local; then
    sed -i "s/^exit 0/Xvfb :99 \&\nexit 0/" /etc/rc.local
    #sed -i "s/^exit 0/export DISPLAY=:99\nexit 0/" /etc/rc.local
fi

if ! grep -q "DISPLAY" /etc/profile; then
    sed -i '$s/$/\nexport DISPLAY=:99/' /etc/profile
fi