# HAAS

The tool _haas_ (HPCC as a service)
creates and manages HPCC clusters on clouds.
It leverages cloud and HPCC tools as much as possible.

Initial design is for AWS.
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
The network is setup using Amazon Virtual Private Cloud (VPC).

Initially, data is loaded from S3.
Before the cluster is torn down, S3 can be updated with the latest
data.






