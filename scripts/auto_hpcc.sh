#!/bin/bash

# grab parameters
thor_nodes=$1
roxie_nodes=$2
support_nodes=$3
slaves_per_node=$4

# Get required metadata
instance_type=`curl -s http://169.254.169.254/latest/meta-data/instance-type`
instance_id=`curl -s http://169.254.169.254/latest/meta-data/instance-id`

# determine region
region=`curl --silent http://169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region`

# determine stack name
stack_name=`aws ec2 describe-tags --region ${region} --filters "Name=resource-id,Values=${instance_id}" | jq -r '.Tags[] | select(.Key=="aws:cloudformation:stack-name") | .Value'`

# create hosts file
host_file=/tmp/ip.list

aws ec2 describe-instances --region ${region} \
    --filters "Name=tag:aws:cloudformation:stack-name,Values=${stack_name}" "Name=tag:aws:cloudformation:logical-id,Values=MasterASG" |\
    jq -r '.Reservations[].Instances[] | select(.State.Name=="running") | .PrivateIpAddress' > ${host_file}.masters

aws ec2 describe-instances --region ${region}\
    --filters "Name=tag:aws:cloudformation:stack-name,Values=${stack_name}" "Name=tag:aws:cloudformation:logical-id,Values=SlaveASG" |\
    jq -r '.Reservations[].Instances[] | select(.State.Name=="running") | .PrivateIpAddress' > ${host_file}.slaves

cat ${host_file}.masters ${host_file}.slaves > ${host_file}
rm -f ${host_file}.masters ${host_file}.slaves

# output to log
echo Instance Id: ${instance_id}
echo Instance Type: ${instance_type}
echo Stack Name: ${stack_name}
echo Region: ${region}
echo Thor nodes: ${thor_nodes}
echo Roxie nodes: ${roxie_nodes}
echo Support nodes: ${support_nodes}
echo Slaves Per Node: ${slaves_per_node}
echo Host Lists
cat ${host_file}

# generate the configuration file for HPCC
tmp_config=/tmp/environment.xml
/opt/HPCCSystems/sbin/envgen -env ${tmp_config} -ipfile ${host_file} \
			     -thornodes ${thor_nodes}\
			     -roxienodes ${roxie_nodes}\
			     -supportnodes ${support_nodes}\
			     -slavesPerNode ${slaves_per_node}
sudo cp ${tmp_config} /etc/HPCCSystems/environment.xml
