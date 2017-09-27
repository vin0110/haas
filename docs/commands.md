# Commands

Commands are invoked from the commandline as such:
```
haas [global-options] <command class> <sub command> [options] [parameters]
```

Use `haas --help`, `haas class --help`, or `haas class command --help` to
get help.

There are three classes of commands:

  * Cloud formation stack,
  * HPCC cluster, and
  * Data management.

Syntax:
  * Braces "[]" denote optional parameters
  * Angle brackets "<>" denote parameters by name

Many command operate on a specific stack by name.
If the stack name is not provided and environ variable "HAAS_STACK" is
set then its value is used for the stack name.

## Configuration

HaaS is configured using the _rc_ file `~/.haasrc` and
command-ine parameters.
Command-line parameters overwrite those in the rc file.
The following configuration parameters can be specified in the rcfile.

  * haas_dir -- defaults to `~/.haas`
  * username
  * log_file
  * identity -- location of pem file
  * key -- AWS access key
  * secret -- AWS secret key
  * region -- AWS region
  * bucket -- S3 bucket used for checkpoints (default: 'hpcc_checkpoint')
  * debug -- print debug messages (default; false)
  * test -- do not execute (default: false)

## Cloud formation stack

Currently, only AWS configuration is supported.
AWS provisioning is managed using CloudFormation, which is via a template
file (CFT).
See AWS publications for creating a template file.
A CFT may have parameters (such as number of nodes).
HaaS supports passing parameters to the CFT.
The CFT defines the parameters.
HaaS will read parameters from either a configuration file
stored in a YAML format or the command line.
It passes these parameters to AWS in the `haas stack create` command.

All stack commands accept parameters that specify the AWS
credientals (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY).
Either is not specified, haas will use credentials stored according to
AWS toolset.

  * `haas stack create` creates a cloud
  formation stack.
  If a configuration file has been defined for this stack-name, than
  it uses that.
  If there is a named configuration file **and** there the stack-name
  has not been defined, it first defines the stack-name and then
  creates the stack.
  Error if a cluster of same name is active.
  One can create several clusters from the same configuration file.

  * `haas stack list` shows the active stacks.

  * `haas stack delete [<stack-name>]` destroys the named stack.

  * `haas stack template` lists (and configure) the parameters in 
named template file.
  * `haas stack ip` shows the public ips of the cluster nodes
  * `haas stack events` lists the events during provisioning.

## HPCC cluster

HPCC configuration is defined by the HPCC command line tools.
It not strictly used by HaaS.
The default initialization file for these tools is `~/ecl.ini`.

  * `haas cluster [<stack-name>] start [stack-name]` starts the cluster.
  The configuration for the cluster was defined when the stack was
  created.

  * `haas cluster [<stack-name>] stop [stack-name]` stops the cluster.

  * `haas cluster [<stack-name>] restart [stack-name]` restarts the cluster.

  * `haas cluster [<stack-name>] status` gives status of the HPCC cluster --
  whether components work normally on cluster nodes.

## Data management

When necessary, these commands get AWS credentials as described above.

  * `haas data save stack-name resource cluster-file` saves all
  parts of the named cluster file to the given s3 bucket.

  * `haas data restore stack-name resource cluster-file`
  restores all parts of the named cluster file from the given s3
  bucket.

  * `haas data resize stack-name`
  Re-distributes files from previous layout to current layout.
  This is particularly useful when restore from a cluster with different
  number of slave nodes with the current cluster.





