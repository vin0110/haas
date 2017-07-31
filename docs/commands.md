# Commands

Commands are invoked from the commandline as such:
```
haas [global-options] <command class> <sub command> [options] [parameters]
```

Use `haas help`, `haas <class> help`, or `haas class command help` to
get help.

There are four classes of commands:

  * Configuration,
  * Cloud formation stack,
  * HPCC cluster, and
  * Data management.

## Configuration

The configuration is stored in a YAML file.
Each configuration has a name.
More than one configuration can be stored in a configuration file.

The default configuration file is `~/.haas`, which can be overridden
with a commandline option.
Every command supports the global option `[-f configuration-file]`.
The `~/.haas` file also contains per-user settings (don't know what
yet).
These settings are loaded whether or not configuration file is
specified with `-f`.

  * `haas config list [-l] [config-name]` list the configurations
available in the configuration file.
The long option gives additional information.
The name parameter limits output to the named configuration.

  * `haas config refresh` interactively updates local information from AWS.
For convenience haas maintains a local database for each user.
This DB may get out of sync if haas is executed on different computers
or if the AWS console is used.

  * `haas config status stack-name [-l]` gives the status of each node
in the named stack.


## Cloud formation stack

All stack commands accept a parameter that specifies the AWS
credientals, `[-a awsfile]`.
Uses `~/.aws` if awsfile not specified.

  * `haas stack create [-n stack-name] [config-name]` creates a cloud
formation stack using the named configuration.
The cluster name is an integer if not given a name.
Error if a cluster of same name exists.

  * `haas stack list` shows the active stacks.

  * `haas stack destroy [stack-name]` destroys the named stack.

  * `haas stack update [stack-name]` don't know what this does.
But boto can update a stack.

## HPCC cluster

Some command use HPCC client tools commands.
The default initialization file for these tools is `~/ecl.ini`.
Each command in this section has the option `[-e ecl-file]` to use a
different ECL initialization file.

  * `haas cluster start [stack-name]` starts the cluster.
The configuration for the cluster was defined when the stack was
created.

  *  `haas cluster stop [stack-name]` stops the cluster.

  * `haas cluster restart [stack-name]` restarts the cluster.

`haas cluster status [stack-name]` gives status of the HPCC cluster.
What is this?

## Data management

  * `haas data save cluster-file s3-bucket` saves all parts of the
named cluster file to the given s3 bucket.

  * `haas data restore [-f] s3-bucket cluster-file` restores all parts
of the named cluster file from the given s3 bucket.
If cluster file exist, use `[-f]` (force) to overwrite.

  * `haas data resize cluster-file [target-parts]` re-distributes a cluster
file from the number of existing parts to target number of parts.
If target parts is not given, redistribute to number of nodes or
number of Thor nodes.





