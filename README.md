# haws
HPCC on AWS cluster management



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
haas stack create mycluster1 mycluster1
```

