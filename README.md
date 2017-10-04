# HaaS
HPCC as a service: HPCC cluster management in clouds.

## Requirements
* python 3+
* pip

```
sudo apt-get install -y python3-setuptools python3-dev
wget https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py
sudo python3 /tmp/get-pip.py
pip install ruamel.yaml
```


## Installation

First download the source.
Either clone the repository
```shell
$ git clone https://github.com/vin0110/haas.git
```
or download zip file
```shell
$ curl https://github.com/vin0110/haas/archive/master.zip -o haas-master.zip
$ unzip haas-master.zip
$ mv haas-master haas
```
Install HaaS
```shell
$ cd haas
$ sudo python3 setup.py install
````

## Configure AWS

To configure AWS you first need an account.
From your AWS account get [credentials](http://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html#Using_CreateAccessKey),
which consists of a _access key_ and a _secret key_.
HaaS uses **boto3** -- the AWS SDK of Python.
There are several ways to pass the credentials to boto3 described in the
[manual](https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration).
The most convenient might be to put your credentials into a file named
`~/.aws/credentials` (Unix).
For example
```
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```
You may set the region as well in the `~/.aws/config` file
```
[default]
region=us-east-1
```

Many of the HaaS commands use _ssh_ or _scp_; therefore, you will need to
create
[EC2 Key Pairs](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html) on AWS.
The key pair will have a name (_i.e._, "mykey") that is used when creating EC2
instances and to log into these instances.
Download the file to a known location, such as `~/.haas/mykey.pem`.
This file location must be passed to any cluster or data comamand that
uses _ssh_.
Or it can be set in the `~/.haasrc` file, as
```
identity=~/.haas/mykey.pem
```

## Configure the stack

The project comes with a default
[CFT](https://github.com/vin0110/haas/blob/master/templates/haas_cft.json).
It creates a stack with a configurable number of nodes and
instances types.
The parameters of a template can be discovered with the **stack template**
command.
```
$ haas stack template https://raw.githubusercontent.com/vin0110/haas/master/templates/haas_cft.json
Name                           Type                           Default
----                           ----                           -------
AMIId                          String                         ami-cd0f5cb6
KeyName                        AWS::EC2::KeyPair::KeyName
ThorNodes                      Number                         1
ClusterSize                    Number                         1
SupportNodes                   Number                         0
AvailabilityZone               String                         us-east-1d
SlaveInstanceType              String                         c4.large
UserNameAndPassword            String
MasterInstanceType             String                         c4.large
RoxieNodes                     Number                         0
SlavesPerNode                  Number                         1
```

The size of the cluster is determined by several parameters.
A total of `ClusterSize` + `SupportNodes` nodes are created, the former
is the number of _slave_ nodes and the latter the number of _master_
nodes.
`ThorNodes` and `RoxieNodes` define the number of slaves nodes in each
cluster.
The `ClusterSize` should be greater than both `ThorNodes` and
`RoxieNodes` and not greater than their sum.

The easiest way to configure a template is with the **stack template**
command and the `--configure` option:
```
$ haas stack template --configure https://raw.githubusercontent.com/vin0110/haas/master/templates/haas_cft.json
```
This will prompt you for values for the parameters and will output a
configuration in YAML syntax.
For example:
```
AMIId: ami-cd0f5cb6
KeyName: osr
ThorNodes: '1'
ClusterSize: '1'
SupportNodes: '0'
AvailabilityZone: us-east-1d
SlaveInstanceType: t2.micro
UserNameAndPassword: ''
MasterInstanceType: t2.micro
RoxieNodes: '0'
SlavesPerNode: '2'
```
Save this to a file such as `~/.haas/config.yaml`.

## Creating and using a stack

A stack is created using the **stack create** command.
For example: the following command
```
$ haas stack create -f config.yaml twonodes
```
creates a stack named _twonodes_ using the configuration in config.yaml.
This assumes that the AWS key and region were provide via a configruation
file.

Stack creation takes several minutes.
It can be tracked with `haas stack events twonodes`.
After the stack has been created, start HPCC by
```
$ haas cluster start twonodes
```
if the identity file is defined in `~/.haasrc` or
```
$ haas -i ~/.haas/mykey.pem cluster start twonodes
```
if it has not.
Now the HPCC cluster is running and you can start executing on the
cluster.
Execute `haas stack ip twonodes` to get the public IP of the root nodes and
logon to ECL Watch.
The default install does not have user/password.

If you need to restore a previously saved checkpoint
```
$ haas data restore twonodes resource checkpoint-name
```
where resource is one of _dfs_, _wu_, or _dz_.

When finished, you can save the state with the _cluster save_ command.
Then delete the cluster:
```
haas stack delete twonodes
```
