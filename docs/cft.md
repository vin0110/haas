# Using CloudFormation Template

Configuring resources in AWS is complex, tedious, and error pone.
Therefore, AWS developed
[CloudFormation](https://aws.amazon.com/cloudformation/?nc2=h_m1),
which provisions and manages a collection of AWS resources.
The _receipe_ for provisioning is defined in a JSON file called
a _template_ or a CFT (CloudFormation Template).

## Example CFT: haas_cft.json

This project provides a CFT.
It has a handful of parameters that can be listed with the **stack template**
command.
```
$ haas stack template https://raw.githubusercontent.com/vin0110/haas/master/templates/haas_cft.json
```
(See the project
[readme](https://github.com/vin0110/haas/blob/master/README.md)
for an explanation of the parameters.

The CFT uses the AWS
[userdata](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html)
to initialize the EC2 instances.
But it does not start HPCC services in the initialization code becuase
we have to wait until all instances have been created.
Therefore, HPCC initialization is performed after stack creation using
the **cluster start** command.

