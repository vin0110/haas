#!/bin/bash

# extract configuration parameters
thor_nodes=$1
roxie_nodes=$2
support_nodes=$3
slaves_per_node=$4

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
GIT_DIR=https://raw.githubusercontent.com/vin0110/haas/issue_54/scripts
HAAS_DIR=/opt/haas
sudo mkdir $HAAS_DIR
sudo chmod a+rwx $HAAS_DIR
cd $HAAS_DIR
wget ${GIT_DIR}/auto_hpcc.sh
wget ${GIT_DIR}/checkpoint.py
wget ${GIT_DIR}/utils.py
wget ${GIT_DIR}/requirements.txt

# create environment.xml file
sudo bash ./auto_hpcc.sh ${thor_nodes} ${roxie_nodes} ${support_nodes}\
     ${slaves_per_node} 

# install python libraries needed for checkpoint
sudo pip install -r requirements.txt
rm -f requirements.txt

