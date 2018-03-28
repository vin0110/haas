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

[Read](https://github.com/vin0110/haas/blob/master/docs/configuration.md) how to configure your environment.



## Steps to create a stack

```shell
# create the stack
haas --debug stack create mycluster1 -p template_url=templates/haas_cft.json -p KeyName=osr -p MasterInstanceType=c4.large -p SlaveInstanceType=c4.large
```



## Steps to save/restore a cluster

```shell
# save a cluster to S3
haas data [--resource dropzone|workunit|dfs] save mycluster mycheckpoint
# restore a cluster from S3
haas data [--resource dropzone|workunit|dfs] restore mycheckpoint mycluster
# check progress
haas data progress mycluster
```

