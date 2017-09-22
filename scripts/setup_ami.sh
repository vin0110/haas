#!/bin/bash

echo Setup AMI ${thor_nodes} ${roxie_nodes} ${support_nodes} ${slaves_per_node}


# update system
sudo apt-get update
sudo apt-get -y install python-pip awscli jq

# install pip3
wget https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py
sudo python3 /tmp/get-pip.py

# install the helper script for cfn-signal
sudo pip2 install https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz

# get hpcc platform 
curl -s http://cdn.hpccsystems.com/releases/CE-Candidate-6.4.0/bin/platform/hpccsystems-platform-community_6.4.0-1xenial_amd64.deb -O hpccsystems-platform-community_6.4.0-1xenial_amd64.deb

# install hpcc -- fails to install because of dependencies
sudo dpkg -i *.deb

# install all dependencies and complete hpcc install
sudo apt-get -y -f install

# clean up
rm -f *.deb

# get haas code
GIT_DIR=https://raw.githubusercontent.com/vin0110/haas/master/scripts
HAAS_DIR=/opt/haas
sudo mkdir $HAAS_DIR
sudo chmod a+rwx $HAAS_DIR
cd $HAAS_DIR
for file in auto_hpcc.sh checkpoint.py resize.py /utils.py requirements.txt
do
    curl -s ${GIT_DIR}/${file} -O ${file}
done

# install python libraries needed for checkpoint
sudo pip3 install -r requirements.txt
rm -f requirements.txt
