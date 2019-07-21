#!/bin/bash

# verify custom swap file size
SWAP=7G
if [ $# -gt 0 ];then
    SWAP=$1
fi

# update apt source
apt-get -y update
apt-get -y install python3-pip

# headless X-11
apt-get -y install xvfb

# install firefox of specific version 66.0
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

# install chrome of specific version 75.0
if test ! -f ./google-chrome-stable_75.0.3770.100-1_amd64.deb; then
    wget http://dl.google.com/linux/deb/pool/main/g/google-chrome-stable/google-chrome-stable_75.0.3770.100-1_amd64.deb
    sudo dpkg -i google-chrome-stable_75.0.3770.100-1_amd64.deb
fi

# copy firefox & chrome drivers
cp firefox/geckodriver.ubuntu /usr/local/bin/geckodriver
cp chrome/chromedriver.linux64 /usr/local/bin/chromedriver

# install InstaGrow dependencies
pip3 install -r requirements.txt

# allocate swap file
fallocate -l ${SWAP} /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
Xvfb :99 &
#export DISPLAY=:99

# create boot list
if test ! -f /etc/rc.local; then
    # echo "rc.local1 does not exists"
    echo -e '#!/bin/bash\n\nexit 0' >> /etc/rc.local
fi

chown root:root /etc/rc.local
chmod 755 /etc/rc.local
systemctl enable rc-local.service

# update boot list (part 1, for droplet.py service)
if ! grep -q "droplet.py" /etc/rc.local; then
    dir=$(echo $PWD | sed 's/\//\\\//g')
    #sed -i "s/^exit 0/swapon \/swapfile\ncd $dir\npython3 droplet.py\nexit 0/" /etc/rc.local
    sed -i "s/^exit 0/swapon \/swapfile\nexit 0/" /etc/rc.local
    sed -i "s/^exit 0/Xvfb :99 \&\nexit 0/" /etc/rc.local
    #sed -i "s/^exit 0/export DISPLAY=:99\nexit 0/" /etc/rc.local
    sed -i "s/^exit 0/cd $dir\nexit 0/" /etc/rc.local
    sed -i "s/^exit 0/screen -d -m python3 droplet.py\nexit 0/" /etc/rc.local
fi

# update boot list (part 2, for Xvfb service)
if ! grep -q "Xvfb" /etc/rc.local; then
    sed -i "s/^exit 0/Xvfb :99 \&\nexit 0/" /etc/rc.local
    #sed -i "s/^exit 0/export DISPLAY=:99\nexit 0/" /etc/rc.local
fi

# update bash environment profile
if ! grep -q "DISPLAY" /etc/profile; then
    sed -i '$s/$/\nexport DISPLAY=:99/' /etc/profile
fi

# fix broken install, if any
apt-get -y install -f
# apt --fix-broken install