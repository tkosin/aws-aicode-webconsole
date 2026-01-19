#!/usr/bin/env python3
"""CDK application entry point"""
import os
from aws_cdk import App, Environment, Tags
from config import prod as config
from stacks import (
    NetworkStack,
    SecurityStack,
    ComputeStack,
    LoadBalancerStack,
    CertificateStack,
    MonitoringStack,
)


app = App()

# Define environment
env = Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=config.AWS_REGION,
)

# Convert config module to dict
config_dict = {
    key: getattr(config, key)
    for key in dir(config)
    if not key.startswith('__') and not callable(getattr(config, key))
}

# Stack naming
stack_prefix = config.PROJECT_NAME

# Create Network Stack
network_stack = NetworkStack(
    app,
    f"{stack_prefix}-network",
    config=config_dict,
    env=env,
    description="Network infrastructure: VPC, Subnets, Security Groups",
)

# Create Security Stack
security_stack = SecurityStack(
    app,
    f"{stack_prefix}-security",
    config=config_dict,
    env=env,
    description="Security infrastructure: IAM Roles, Secrets Manager",
)

# Create Compute Stack
compute_stack = ComputeStack(
    app,
    f"{stack_prefix}-compute",
    network_stack=network_stack,
    security_stack=security_stack,
    config=config_dict,
    env=env,
    description="Compute infrastructure: EC2 Instance, EBS Volume",
)

# Create Certificate Stack (must be before LoadBalancer)
certificate_stack = CertificateStack(
    app,
    f"{stack_prefix}-certificate",
    config=config_dict,
    env=env,
    description="Certificate infrastructure: ACM Certificate with manual DNS validation",
)

# Create Load Balancer Stack
loadbalancer_stack = LoadBalancerStack(
    app,
    f"{stack_prefix}-loadbalancer",
    network_stack=network_stack,
    compute_stack=compute_stack,
    config=config_dict,
    certificate_arn=certificate_stack.certificate.certificate_arn,
    env=env,
    description="Load Balancer infrastructure: ALB, Target Groups, Listeners",
)

# Create Monitoring Stack
monitoring_stack = MonitoringStack(
    app,
    f"{stack_prefix}-monitoring",
    compute_stack=compute_stack,
    config=config_dict,
    env=env,
    description="Monitoring infrastructure: CloudWatch Logs, Alarms, Backups",
)

# Set stack dependencies
compute_stack.add_dependency(network_stack)
compute_stack.add_dependency(security_stack)
loadbalancer_stack.add_dependency(compute_stack)
loadbalancer_stack.add_dependency(certificate_stack)
monitoring_stack.add_dependency(compute_stack)

# Apply global tags to all resources
for key, value in config.TAGS.items():
    Tags.of(app).add(key, value)

# Synthesize CloudFormation templates
app.synth()
