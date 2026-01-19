"""Network infrastructure stack - VPC, Subnets, IGW, Security Groups"""
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    Tags,
)
from constructs import Construct
from typing import Dict


class NetworkStack(Stack):
    """
    Creates VPC, Subnets, Internet Gateway, and Security Groups

    Resources:
    - VPC with public subnets in 2 AZs
    - Internet Gateway
    - Security Group for ALB (allows HTTPS from internet)
    - Security Group for EC2 (allows ports 8443-8450 from ALB, SSH from admin)
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Dict,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC
        self.vpc = ec2.Vpc(
            self,
            "CodeServerVPC",
            vpc_name=f"{config['PROJECT_NAME']}-vpc",
            ip_addresses=ec2.IpAddresses.cidr(config['VPC_CIDR']),
            max_azs=2,
            nat_gateways=0,  # No NAT gateway to save cost
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                )
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True,
        )

        # Create Security Group for ALB
        self.alb_security_group = ec2.SecurityGroup(
            self,
            "ALBSecurityGroup",
            security_group_name=f"{config['PROJECT_NAME']}-alb-sg",
            vpc=self.vpc,
            description="Security group for Application Load Balancer",
            allow_all_outbound=True,
        )

        # Allow HTTPS from internet
        self.alb_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="Allow HTTPS from internet",
        )

        # Allow HTTP (for redirect to HTTPS)
        self.alb_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="Allow HTTP for redirect to HTTPS",
        )

        # Create Security Group for EC2
        self.ec2_security_group = ec2.SecurityGroup(
            self,
            "EC2SecurityGroup",
            security_group_name=f"{config['PROJECT_NAME']}-ec2-sg",
            vpc=self.vpc,
            description="Security group for EC2 code-server instance",
            allow_all_outbound=True,
        )

        # Allow ports 8443-8450 from ALB (for code-server containers)
        for port in range(
            config['CONTAINER_BASE_PORT'],
            config['CONTAINER_BASE_PORT'] + config['NUM_DEVELOPERS']
        ):
            self.ec2_security_group.add_ingress_rule(
                peer=ec2.Peer.security_group_id(
                    self.alb_security_group.security_group_id
                ),
                connection=ec2.Port.tcp(port),
                description=f"Allow port {port} from ALB",
            )

        # Allow SSH from admin IP (if configured)
        if 'ADMIN_SSH_CIDR' in config:
            self.ec2_security_group.add_ingress_rule(
                peer=ec2.Peer.ipv4(config['ADMIN_SSH_CIDR']),
                connection=ec2.Port.tcp(22),
                description="Allow SSH from admin",
            )

        # Apply tags
        for key, value in config['TAGS'].items():
            Tags.of(self.vpc).add(key, value)
            Tags.of(self.alb_security_group).add(key, value)
            Tags.of(self.ec2_security_group).add(key, value)

        # Store public subnets for other stacks
        self.public_subnets = self.vpc.public_subnets
