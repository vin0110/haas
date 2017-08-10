# HaaS
HPCC as a service: HPCC cluster management in clouds.



## Prepare your environment

```shell
# install required 3rd-party libraries
source scripts/install.sh
# start the virtualenv
source scripts/init.sh
# initialize the AWS credentials
aws configure
# initialize haas directory
mkdir ~/.haas
```



## Steps to create a stack

```shell
# generate haas configuration
haas config new mycluster1
# create the stack
haas --debug stack create mycluster1 -p template_url=templates/haas_cft.json -p KeyName=osr -p MasterInstanceType=c4.large -p SlaveInstanceType=c4.large
```



## Steps to save/restore a cluster

```shell
# save a cluster to S3
haas data save mycluster1
# restore a cluster from S3
haas data restore mycluster1 mycluster2
```

