# HaaS
HPCC as a service: HPCC cluster management in clouds.

## Installation

First download the source.
Either clone the repository
```shell
$ git clone git@github.com:vin0110/haas.git
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
$ python setup.py install
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

## Create an Amazon Machine Image

When EC2 instances are created they are overlaid with an image.
This project uses a vanilla Ubuntu AMI.
However, it is expected that most users will create their own AMI because
you should not trust someone else.
Additionally, the user will want to install a specific the HPCC version and
desired plugins.
Moreover, a custom AMI boots faster than the solution provided.

To work with HaaS, EC2 instances must have an HPCC installation and
support files from HaaS.
The AMI must have HPCC preloaded or it must be installed on startup.
[Installing HPCC](http://cdn.hpccsystems.com/releases/CE-Candidate-%7Bcurrent_version%7D/docs/Installing_and_RunningTheHPCCPlatform-%7Bcurrent_version_full%7D.pdf)
can be done in two steps:
```
$ curl http://cdn.hpccsystems.com/releases/CE-Candidate-X.Y.Z/bin/platform/hpccsystems-platform-community_X.Y.Z-disto_amd64.deb -o hpcc-systems.deb
$ sudo apt-get install hpcc-systems.deb
```

Some files from this repository must be copied onto the EC2
instance.
Again, these can be preloaded in the AMI or copied in the
installation.
The following snippet of code from
[setup_ami.sh](https://github.com/vin0110/haas/blob/master/scripts/setup_ami.sh)
copies the necessary files to the proper directory.
```
GIT_DIR=https://raw.githubusercontent.com/vin0110/haas/master/scripts
HAAS_DIR=/opt/haas
sudo mkdir $HAAS_DIR
sudo chmod a+rwx $HAAS_DIR
cd $HAAS_DIR
for file in auto_hpcc.sh checkpoint.py resize.py utils.py requirements.txt
do
    curl -s ${GIT_DIR}/${file} -O ${file}
done
```

These requirements are formalized in the
[setup_ami.sh](https://github.com/vin0110/haas/blob/master/scripts/setup_ami.sh)
file.
It shows all the steps necessary to configure a vanilla AMI for
use with the default CloudFormation Template (CFT).
Some of the steps are specific to this CFT and may not be
necessary for each custom solution.

## Create a CloudFormationtemplate

The project comes with a default
[CFT](https://github.com/vin0110/haas/blob/master/templates/haas_cft.json).
It creates a stack with a configurable number of nodes and
instances types.
The parameters of a template can be discovered with the _stack template_
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
Not all parameters are required.

The size of the cluster is determined by several parameters.
The cluster size is the number of Thor and Roxie slave nodes.
The cluster size must be greater than both the Thor and Roxie nodes and
no larger than their sum.
If Thor is non-zero than the number of support nodes will be at least 1.

The CFT uses the AWS
[userdata](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html)
to initialize the EC2 instances.

## Creating and using a stack

A stack is created using the _stack create_ command.
For example: the following command
```
$ haas stack create -f config.yaml 2nodes
```
creates a stack named _2nodes_ using the configuration in config.yaml,
which may be something like:
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
This assumes that the AWS key and region were provide via a configruation
file.

Stack creation takes several minutes.
It can be tracked with `haas stack events 2nodes`.
After the stack has been created, start HPCC by
```
$ haas cluster start 2nodes
```
if the identity file is defined in `~/.haasrc` or
```
$ haas -i ~/.haas/mykey.pem cluster start 2nodes
```
if it has not.
Now the HPCC cluster is running and you can start executing on the
cluster.
Execute `haas stack ip 2nodes` to get the public IP of the root nodes and
logon to ECL Watch.
The default install does not have user/password.

If you need to restore a previously saved checkpoint
```
$ haas data restore 2nodes resource checkpoint-name
```
where resource is one of _dfs_, _wu_, or _dz_.

When finished, you can save the state with the _cluster save_ command.
Then delete the cluster:
```
haas stack delete 2nodes
```
