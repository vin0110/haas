#!/bin/bash

# Get required metadata
instance_type=`curl -s http://169.254.169.254/latest/meta-data/instance-type`
instance_id=`curl -s http://169.254.169.254/latest/meta-data/instance-id`

region=`curl --silent http://169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region`
availability_zone=`curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone`
stack_name=`aws ec2 describe-tags --region ${region} --filters "Name=resource-id,Values=${instance_id}" | jq -r '.Tags[] | select(.Key=="aws:cloudformation:stack-name") | .Value'`
# tid=`aws ec2 describe-tags --region ${region} --filters "Name=resource-id,Values=${instance_id}" | jq -r '.Tags[] | select(.Key=="tid") | .Value'`
slaves_per_node=`aws ec2 describe-tags --region ${region} --filters "Name=resource-id,Values=${instance_id}" | jq -r '.Tags[] | select(.Key=="slavesPerNode") | .Value'`
[[ -z "${slaves_per_node}" ]] && slaves_per_node=`getconf _NPROCESSORS_ONLN`

# instance_id private_ip
#master_ip_list=`aws ec2 describe-instances --region ${region} --filters "Name=tag:tid,Values=${tid},Name=tag:aws:cloudformation:logical-id,Values=MasterASG" | jq -r '.Reservations[].Instances[] | .InstanceId + " " + .PrivateIpAddress'`
#slave_ip_list=`aws ec2 describe-instances --region ${region} --filters "Name=tag:tid,Values=${tid},Name=tag:aws:cloudformation:logical-id,Values=SlaveASG" | jq -r '.Reservations[].Instances[] | .InstanceId + " " + .PrivateIpAddress'`
#cluster_size=`echo ${slave_ip_list} | wc -l`

host_file=/tmp/ip.list
rm -rf ${host_file}; touch ${host_file}
aws ec2 describe-instances --region ${region} --filters "Name=tag:aws:cloudformation:stack-name,Values=${stack_name}" "Name=tag:aws:cloudformation:logical-id,Values=MasterASG" | jq -r '.Reservations[].Instances[] | .PrivateIpAddress' >> ${host_file}
aws ec2 describe-instances --region ${region} --filters "Name=tag:aws:cloudformation:stack-name,Values=${stack_name}" "Name=tag:aws:cloudformation:logical-id,Values=SlaveASG" | jq -r '.Reservations[].Instances[] | .PrivateIpAddress' >> ${host_file}
cluster_size=`tail -n +2 ${host_file} | wc -l`

# output to log
echo Instance Id: ${instance_id}
echo Instance Type: ${instance_type}
echo Stack Name: ${stack_name}
echo Region: ${region}
# echo Tid: ${tid}
echo Slaves Per Node: ${slaves_per_node}
echo Host Lists
cat ${host_file}

# generate the configuration file for HPCC
tmp_config=/tmp/environment.xml
/opt/HPCCSystems/sbin/envgen -env ${tmp_config} -ipfile ${host_file} -thornodes ${cluster_size} -roxienodes ${cluster_size} -slavesPerNode ${slaves_per_node}
sudo cp ${tmp_config} /etc/HPCCSystems/environment.xml

# TODO: event driven?
sleep 60
sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a dafilesrv start"
sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a hpcc-init start"
