#!/bin/bash

# update system
sudo apt-get update
sudo apt-get -y install awscli

# install pip for haas modules
sudo apt-get -y install python-pip

# get hpcc platform 
wget http://cdn.hpccsystems.com/releases/CE-Candidate-6.4.0/bin/platform/hpccsystems-platform-community_6.4.0-1xenial_amd64.deb

# install hpcc -- fails to install because of dependencies
sudo dpkg -i *.deb

# install all dependencies and complete hpcc install
sudo apt-get -y -f install

# clean up
rm -f *.deb

# get haas code
HAAS_DIR=/opt/haas
sudo mkdir $HAAS_DIR
sudo chmod a+rwx $HAAS_DIR
cd $HAAS_DIR
wget https://raw.githubusercontent.com/vin0110/haas/master/scripts/checkpoint.py
wget https://raw.githubusercontent.com/vin0110/haas/master/scripts/utils.py
wget https://raw.githubusercontent.com/vin0110/haas/master/scripts/auto_hpcc.sh
wget https://raw.githubusercontent.com/vin0110/haas/master/scripts/requirements.txt

sudo pip install -r requirements.txt
rm -f requirements.txt
