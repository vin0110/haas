# Create an Amazon Machine Image

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

