import troposphere
import troposphere.ec2
import troposphere.iam
import troposphere.ecs
import troposphere.autoscaling

import awacs.aws
import awacs.sts


def generate_cft():
    VPC_NETWORK = "10.0.0.0/16"
    VPC_PRIVATE = "10.0.0.0/24"

    t = troposphere.Template()
    t.add_description("HaaS Stack")

    key_name = t.add_parameter(troposphere.Parameter(
        "KeyName",
        Type="AWS::EC2::KeyPair::KeyName",
        ConstraintDescription="must be a valid keypair Id",
        )
    )

    username_and_password = t.add_parameter(troposphere.Parameter(
        "UserNameAndPassword",
        Type="String",
        Default="",
        Description="(Optional) Enter like: username/password Used to log into ECL Watch and ECL IDE."
        )
    )

    cluster_size = t.add_parameter(troposphere.Parameter(
        "ClusterSize",
        Type="Number",
        Default="1",
        Description="Number of slave instances to be launched"
        )
    )

    num_slaves = t.add_parameter(troposphere.Parameter(
        "NumberOfSlavesPerNode",
        Type="Number",
        Default="1",
        Description="Number of THOR slave nodes per slave instance"
        )
    )

    master_instance_type = t.add_parameter(troposphere.Parameter(
        "MasterInstanceType",
        Type="String",
        AllowedValues=[
            't2.micro',
            'c4.large', 'c4.xlarge', 'c4.2xlarge',
            'm4.large', 'm4.xlarge', 'm4.2xlarge',
            'r4.large', 'r4.xlarge', 'r4.2xlarge'
        ],
        Default="c4.large",
        Description="HPCC Thor Master EC2 instance type"
        )
    )

    slave_instance_type = t.add_parameter(troposphere.Parameter(
        "SlaveInstanceType",
        Type="String",
        AllowedValues=[
            't2.micro',
            'c4.large', 'c4.xlarge', 'c4.2xlarge',
            'm4.large', 'm4.xlarge', 'm4.2xlarge',
            'r4.large', 'r4.xlarge', 'r4.2xlarge'
        ],
        Default="c4.large",
        Description="HPCC Thor Slave EC2 instance type"
        )
    )

    vpc_availability_zone = t.add_parameter(troposphere.Parameter(
        "AvailabilityZone",
        Type="String",
        AllowedValues=[
            'us-east-1d'
        ],
        Default="us-east-1d",
        Description="Availability zone",
    ))

    t.add_mapping('RegionMap', {
        'us-east-1': {'64': 'ami-24c2ee32'}
    })

    instance_role = t.add_resource(troposphere.iam.Role(
        "HPCCInstanceRoles",
        AssumeRolePolicyDocument=awacs.aws.Policy(
            Statement=[
                awacs.aws.Statement(
                    Effect=awacs.aws.Allow,
                    Action=[awacs.sts.AssumeRole],
                    Principal=awacs.aws.Principal(
                        "Service", ["ec2.amazonaws.com"]
                    )
                )
            ]
        ),
        Policies=[
            troposphere.iam.Policy(
                PolicyName="root",
                PolicyDocument=awacs.aws.Policy(
                    Statement=[
                        awacs.aws.Statement(
                            Effect=awacs.aws.Allow,
                            Action=[awacs.aws.Action("*")],
                            Resource=["*"]
                        )
                    ]
                )
            )
        ],
        Path="/"
    ))
    instance_profile = t.add_resource(troposphere.iam.InstanceProfile(
        "HPCCInstanceProfile",
        Path="/",
        Roles=[troposphere.Ref(instance_role)]

    ))

    vpc = t.add_resource(troposphere.ec2.VPC(
        "HPCCVpc",
        CidrBlock=VPC_NETWORK,
        InstanceTenancy="default",
        EnableDnsSupport=True,
        EnableDnsHostnames=False,
        Tags=troposphere.Tags(
            Name=troposphere.Ref("AWS::StackName")
        )
    ))

    internetGateway = t.add_resource(
        troposphere.ec2.InternetGateway(
            "InternetGateway",
            Tags=troposphere.Tags(
                Name=troposphere.Join("-", [troposphere.Ref("AWS::StackName"), "gateway"]),
            ),
    ))

    gatewayAttachment = t.add_resource(troposphere.ec2.VPCGatewayAttachment(
        "InternetGatewayAttachment",
        InternetGatewayId=troposphere.Ref(internetGateway),
        VpcId=troposphere.Ref(vpc)
    ))

    # public routing table
    publicRouteTable = t.add_resource(troposphere.ec2.RouteTable(
        "PublicRouteTable",
        VpcId=troposphere.Ref(vpc),
        Tags=troposphere.Tags(
            Name=troposphere.Join("-", [troposphere.Ref("AWS::StackName"), "public-rt"]),
        ),
    ))

    internetRoute = t.add_resource(troposphere.ec2.Route(
        "RouteToInternet",
        DestinationCidrBlock="0.0.0.0/0",
        GatewayId=troposphere.Ref(internetGateway),
        RouteTableId=troposphere.Ref(publicRouteTable),
        DependsOn=gatewayAttachment.title
    ))
    subnet = t.add_resource(troposphere.ec2.Subnet(
        "Subnet",
        CidrBlock=VPC_PRIVATE,
        Tags=troposphere.Tags(
            Name=troposphere.Join("-", [troposphere.Ref("AWS::StackName"), "subnet"]),
        ),
        VpcId=troposphere.Ref(vpc)
    ))

    t.add_resource(troposphere.ec2.SubnetRouteTableAssociation(
        "SubnetRouteTableAssociation",
        RouteTableId=troposphere.Ref(publicRouteTable),
        SubnetId=troposphere.Ref(subnet)
    ))

    placement_group = t.add_resource(troposphere.ec2.PlacementGroup(
        "HPCCPlacementGroup",
        Strategy="cluster"
    ))

    security_groups = t.add_resource(
        troposphere.ec2.SecurityGroup(
            "HPCCSecurityGroups",
            GroupDescription="Enable SSH and HTTP access on the inbound port",
            SecurityGroupEgress=[
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="-1",
                    CidrIp="0.0.0.0/0",
                ),
            ],
            SecurityGroupIngress=[
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=8888,
                    ToPort=8888,
                    CidrIp="0.0.0.0/0",
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=9042,
                    ToPort=9042,
                    CidrIp="0.0.0.0/0",
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=7000,
                    ToPort=7000,
                    CidrIp="0.0.0.0/0",
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=7001,
                    ToPort=7001,
                    CidrIp="0.0.0.0/0",
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=7199,
                    ToPort=7199,
                    CidrIp="0.0.0.0/0",
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=9160,
                    ToPort=9160,
                    CidrIp="0.0.0.0/0",
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=61620,
                    ToPort=61620,
                    CidrIp="0.0.0.0/0",
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=61621,
                    ToPort=61621,
                    CidrIp="0.0.0.0/0",
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=8002,
                    ToPort=8002,
                    CidrIp="0.0.0.0/0",
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=8010,
                    ToPort=8010,
                    CidrIp="0.0.0.0/0",
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=8015,
                    ToPort=8015,
                    CidrIp="0.0.0.0/0",
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=8145,
                    ToPort=8145,
                    CidrIp="0.0.0.0/0",
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=22,
                    ToPort=22,
                    CidrIp="0.0.0.0/0",
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=0,
                    ToPort=65535,
                    CidrIp="0.0.0.0/0",
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="udp",
                    FromPort=0,
                    ToPort=65535,
                    CidrIp="0.0.0.0/0",
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=8050,
                    ToPort=8050,
                    CidrIp="0.0.0.0/0",
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=8008,
                    ToPort=8008,
                    CidrIp="0.0.0.0/0",
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=9876,
                    ToPort=9876,
                    CidrIp="0.0.0.0/0",
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="icmp",
                    FromPort=-1,
                    ToPort=-1,
                    CidrIp="0.0.0.0/0",
                ),
            ],
            VpcId=troposphere.Ref(vpc)
        )
    )

    # AutoScaling
    slave_launch_config = t.add_resource(troposphere.autoscaling.LaunchConfiguration(
        "SlaveLaunchCfg",
        ImageId=troposphere.FindInMap(
            "RegionMap",
            troposphere.Ref("AWS::Region"), "64"),
        InstanceType=troposphere.Ref(slave_instance_type),
        AssociatePublicIpAddress="True",
        KeyName=troposphere.Ref(key_name),
        SecurityGroups=[troposphere.Ref(security_groups)],
        IamInstanceProfile=troposphere.Ref(instance_profile),
        UserData=troposphere.Base64(
            troposphere.Join(
                '\n', [
                    "#!/bin/bash",
                    "exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1",
                    "echo [Initialization] starting the slave node",
                    troposphere.Join(
                        " ", [
                            "su - osr /bin/bash -c 'cd /home/osr/project-aws; git pull; /bin/bash scripts/auto_hpcc.sh",
                            troposphere.Ref("AWS::StackName"),
                            troposphere.Ref("AWS::Region"),
                            "'",
                        ]
                    ),
                    "echo [Initialization] completed the slave node",
                    "echo SCRIPT: 'Signal stack that setup of HPCC System is complete.'",
                    troposphere.Join(
                        " ", [
                            "/usr/local/bin/cfn-signal -e 0 --stack ",
                            troposphere.Ref("AWS::StackName"),
                            "--resource SlaveASG ",
                            "--region ",
                            troposphere.Ref("AWS::Region")
                        ]
                    ),
                    "echo SCRIPT: 'Done signaling stack that setup of HPCC System has completed.'"
                ]
            )
        ),
    ))
    slave_autoscaling_group = t.add_resource(troposphere.autoscaling.AutoScalingGroup(
        "SlaveASG",
        DesiredCapacity=troposphere.Ref(cluster_size),
        # @TODO: disable here to support t2.micro for cheap testing
        #PlacementGroup=troposphere.Ref(placement_group),
        LaunchConfigurationName=troposphere.Ref(slave_launch_config),
        MinSize=troposphere.Ref(cluster_size),
        MaxSize=troposphere.Ref(cluster_size),
        HealthCheckType="EC2",
        HealthCheckGracePeriod="300",
        VPCZoneIdentifier=[troposphere.Ref(subnet)],
        #AvailabilityZones=[troposphere.Ref(vpc_availability_zone)],
        Tags=[
            troposphere.autoscaling.Tag("StackName", troposphere.Ref("AWS::StackName"), True),
            troposphere.autoscaling.Tag("slavesPerNode", troposphere.Ref(num_slaves), True),
            troposphere.autoscaling.Tag("UserNameAndPassword", troposphere.Ref(username_and_password), True),
            troposphere.autoscaling.Tag("Name", troposphere.Join("-", [troposphere.Ref("AWS::StackName"), "Slave"]), True),
        ],
    ))

    master_launch_config = t.add_resource(troposphere.autoscaling.LaunchConfiguration(
        "MasterLaunchCfg",
        ImageId=troposphere.FindInMap(
            "RegionMap",
            troposphere.Ref("AWS::Region"), "64"),
        InstanceType=troposphere.Ref(master_instance_type),
        AssociatePublicIpAddress="True",
        KeyName=troposphere.Ref(key_name),
        SecurityGroups=[troposphere.Ref(security_groups)],
        IamInstanceProfile=troposphere.Ref(instance_profile),
        UserData=troposphere.Base64(
            troposphere.Join(
                '\n', [
                    "#!/bin/bash",
                    "exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1",
                    "echo [Initialization] starting the master node",
                    troposphere.Join(
                        " ", [
                            "su - osr /bin/bash -c 'cd /home/osr/project-aws; git pull; /bin/bash scripts/auto_hpcc.sh",
                            troposphere.Ref("AWS::StackName"),
                            troposphere.Ref("AWS::Region"),
                            "'",
                        ]
                    ),
                    "echo [Initialization] completed the master node",
                    "echo SCRIPT: 'Signal stack that setup of HPCC System is complete.'",
                    troposphere.Join(
                        " ", [
                            "/usr/local/bin/cfn-signal -e 0 --stack ",
                            troposphere.Ref("AWS::StackName"),
                            "--resource MasterASG ",
                            "--region ",
                            troposphere.Ref("AWS::Region")
                        ]
                    ),
                    "echo SCRIPT: 'Done signaling stack that setup of HPCC System has completed.'"
                ]
            )
        ),
    ))
    master_autoscaling_group = t.add_resource(troposphere.autoscaling.AutoScalingGroup(
        "MasterASG",
        DesiredCapacity="1",  # need to update x -> N+x
        # @TODO: disable here to support t2.micro for cheap testing
        #PlacementGroup=troposphere.Ref(placement_group),
        LaunchConfigurationName=troposphere.Ref(master_launch_config),
        MinSize="1",
        MaxSize="1",
        HealthCheckType="EC2",
        HealthCheckGracePeriod="300",
        VPCZoneIdentifier=[troposphere.Ref(subnet)],
        #AvailabilityZones=[troposphere.Ref(vpc_availability_zone)],
        Tags=[
            troposphere.autoscaling.Tag("StackName", troposphere.Ref("AWS::StackName"), True),
            troposphere.autoscaling.Tag("slavesPerNode", troposphere.Ref(num_slaves), True),
            troposphere.autoscaling.Tag("UserNameAndPassword", troposphere.Ref(username_and_password), True),
            troposphere.autoscaling.Tag("Name", troposphere.Join("-", [troposphere.Ref("AWS::StackName"), "Master"]), True),
        ],
    ))

    print(t.to_json())

    return t.to_dict()

if __name__ == '__main__':
    generate_cft()