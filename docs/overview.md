# HAWS

The tool _haws_ creates and manages HPCC clusters on AWS.
It leverages AWS and HPCC tools as much as possible.
It uses [Cloud Formation](https://aws.amazon.com/cloudformation/) to
create a _stack_ in AWS.
In our case the stack is the cluster.
It loads an
[AMI](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html)
into each of the allocated EC2 instances.

The tool also leverages HPCC
[client tools](http://cdn.hpccsystems.com/releases/CE-Candidate-6.2.18/docs/HPCCClientTools-6.2.18-1.pdf).

## Cluster architecture

The cluster is an _N+1_ architecture: there are N worker nodes and an
additional node for cluster-wide services, such as the name server.
As N gets large it user can instantiate more than one extra
node for cluster-wide services.
(Simplicity we call both instances N+1.)

The cluster can be configure to run Thor and/or Roxie nodes.
The cluster can be _dual_ or _separate_.
In joint, all N workers run both Thor and Roxie servers.
In separate, T workers run Thor processes and R workers run Roxie.
T + R must equal N.
Either T or R can be zero--which is how to create a single-purpose
cluster.

Each type of worker (Thor, Roxie, or dual)
mounts the same number and size of EBS volumes.
The network is setup _how is it setup?_

Initially, data is loaded from S3.
Before the cluster is torn down, S3 can be updated with the latest
data.

## Configuration parameter overview

| Parameter | Description | Values | Comment |
|-----------|-------------|--------|---------|
| nodes | number of nodes | integer > 0 | |
| service | number of cluster-wide service nodes| integer > 0 | |
| separate | sets nodes to separate | boolean | if not separate, then dual |
| thor nodes | number of thor nodes |  non-negative integer | ignored if separate is false |
| roxie nodes | number of roxie nodes |  non-negative integer | ignored if separate is false |
| volumes | list of EBS volumes to attach to dual or thor nodes | | |
| roxie volumes | list of EBS volumes to attach to roxie nodes | ignored if not separate | |

**Nodes**
If separate then number of nodes equals thor nodes plus roxies nodes.
If two of the node parameters are set, the third is calculated.
If all three are specified, number of nodes is ignored.

**Volumes**
The volume parameters contains a list volume descriptors.
Each descriptor has a name (ie, mount point), type, and size.
The base volume parameter is used for all nodes in dual or Thor nodes
in separate.






