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
    sed -i "s/^exit 0/cd $dir\nexit 0/" /etc/rc.local
    sed -i "s/^exit 0/screen -d -m python3 droplet.py\nexit 0/" /etc/rc.local
fi