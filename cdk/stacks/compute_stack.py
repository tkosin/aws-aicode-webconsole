"""Compute infrastructure - EC2 instance and EBS volume"""
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    CfnOutput,
    RemovalPolicy,
)
from constructs import Construct
from typing import Dict


class ComputeStack(Stack):
    """
    Creates EC2 instance and EBS volume for code-server

    Resources:
    - EC2 t3.2xlarge instance with Ubuntu 22.04
    - EBS gp3 root volume (50 GB)
    - EBS gp3 data volume (500 GB) for developer workspaces
    - User data script for Docker and initial setup
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        network_stack,
        security_stack,
        config: Dict,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get latest Ubuntu 22.04 LTS AMI
        ubuntu_ami = ec2.MachineImage.lookup(
            name="ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*",
            owners=["099720109477"],  # Canonical
        )

        # Create user data script
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "#!/bin/bash",
            "set -e",
            "exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1",
            "",
            "# Update system",
            "apt-get update",
            "DEBIAN_FRONTEND=noninteractive apt-get upgrade -y",
            "",
            "# Install Docker",
            "curl -fsSL https://get.docker.com -o get-docker.sh",
            "sh get-docker.sh",
            "usermod -aG docker ubuntu",
            "",
            "# Install Docker Compose",
            "COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\\\" -f4)",
            'curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose',
            "chmod +x /usr/local/bin/docker-compose",
            "",
            "# Install AWS CLI v2",
            'curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"',
            "apt-get install -y unzip",
            "unzip awscliv2.zip",
            "./aws/install",
            "",
            "# Install CloudWatch agent",
            "wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb",
            "dpkg -i -E ./amazon-cloudwatch-agent.deb",
            "",
            "# Wait for EBS volume to attach",
            "echo 'Waiting for EBS volume...'",
            "while [ ! -e /dev/nvme1n1 ]; do",
            "    sleep 5",
            "done",
            "",
            "# Format and mount EBS volume if needed",
            "if ! file -s /dev/nvme1n1 | grep -q ext4; then",
            "    echo 'Creating ext4 filesystem...'",
            "    mkfs.ext4 /dev/nvme1n1",
            "fi",
            "",
            "# Create mount point",
            "mkdir -p /mnt/ebs-data",
            "",
            "# Mount volume",
            "mount /dev/nvme1n1 /mnt/ebs-data",
            "",
            "# Add to fstab for auto-mount on reboot",
            "UUID=$(blkid -s UUID -o value /dev/nvme1n1)",
            'echo "UUID=$UUID /mnt/ebs-data ext4 defaults,nofail 0 2" >> /etc/fstab',
            "",
            "# Create directory structure for developers",
            "for i in {1..8}; do",
            "    mkdir -p /mnt/ebs-data/dev${i}/{workspace,config}",
            "    chown -R ubuntu:ubuntu /mnt/ebs-data/dev${i}",
            "done",
            "",
            "# Create resource monitoring script",
            "cat > /home/ubuntu/monitor-resources.sh << 'EOFSCRIPT'",
            "#!/bin/bash",
            "# Monitor all developer container resources",
            "",
            'echo "======================================"',
            'echo "Developer Container Resource Usage"',
            'echo "Date: $(date)"',
            'echo "======================================"',
            'echo ""',
            "",
            "# Docker stats (CPU, Memory per container)",
            'docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"',
            "",
            'echo ""',
            'echo "======================================"',
            'echo "Disk Usage"',
            'echo "======================================"',
            "df -h /mnt/ebs-data | tail -1",
            "",
            'echo ""',
            'echo "======================================"',
            'echo "Port Usage"',
            'echo "======================================"',
            'netstat -tulpn | grep LISTEN | grep -E ":(3000|4000|5000|5432|6379|8000|8443|8444|8445|8446|8447|8448|8449|8450)" || echo "No dev servers running"',
            "",
            'echo ""',
            'echo "======================================"',
            'echo "Top Processes by Memory"',
            'echo "======================================"',
            "ps aux --sort=-%mem | head -10",
            "EOFSCRIPT",
            "",
            "chmod +x /home/ubuntu/monitor-resources.sh",
            "chown ubuntu:ubuntu /home/ubuntu/monitor-resources.sh",
            "",
            "# Create helper scripts directory",
            "mkdir -p /home/ubuntu/dev-tools",
            "",
            "# Create port checking script",
            "cat > /home/ubuntu/dev-tools/check-ports.sh << 'EOFSCRIPT'",
            "#!/bin/bash",
            'echo "=== Open Ports ==="',
            'netstat -tulpn | grep LISTEN | grep -E ":(3000|3001|3002|4000|4001|8000|8001|5432|6379)"',
            "EOFSCRIPT",
            "",
            "# Create stop all servers script",
            "cat > /home/ubuntu/dev-tools/stop-all-servers.sh << 'EOFSCRIPT'",
            "#!/bin/bash",
            'echo "Stopping all Node.js servers..."',
            'pkill -f "node.*dev" || echo "No Node.js dev servers running"',
            'echo "Stopping all Python servers..."',
            'pkill -f "python.*uvicorn" || echo "No Python servers running"',
            'echo "Stopping all npm processes..."',
            'pkill -f "npm.*run" || echo "No npm processes running"',
            'echo "Done!"',
            "EOFSCRIPT",
            "",
            "chmod +x /home/ubuntu/dev-tools/*.sh",
            "chown -R ubuntu:ubuntu /home/ubuntu/dev-tools",
            "",
            "echo 'User data script completed successfully'",
        )

        # Create EC2 instance
        self.instance = ec2.Instance(
            self,
            "CodeServerInstance",
            instance_name=f"{config['PROJECT_NAME']}-ec2",
            instance_type=ec2.InstanceType(config['EC2_INSTANCE_TYPE']),
            machine_image=ubuntu_ami,
            vpc=network_stack.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC,
                availability_zones=[config['AVAILABILITY_ZONES'][0]],
            ),
            security_group=network_stack.ec2_security_group,
            role=security_stack.ec2_role,
            user_data=user_data,
            key_name=config['EC2_KEY_NAME'],
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/sda1",
                    volume=ec2.BlockDeviceVolume.ebs(
                        volume_size=config['EBS_ROOT_SIZE'],
                        volume_type=ec2.EbsDeviceVolumeType.GP3,
                        delete_on_termination=True,
                    ),
                )
            ],
        )

        # Create EBS data volume
        self.data_volume = ec2.Volume(
            self,
            "DataVolume",
            volume_name=f"{config['PROJECT_NAME']}-data-volume",
            availability_zone=self.instance.instance_availability_zone,
            size=ec2.Size.gibibytes(config['EBS_DATA_SIZE']),
            volume_type=ec2.EbsDeviceVolumeType.GP3,
            removal_policy=RemovalPolicy.SNAPSHOT,
        )

        # Attach EBS volume to instance
        ec2.CfnVolumeAttachment(
            self,
            "VolumeAttachment",
            instance_id=self.instance.instance_id,
            volume_id=self.data_volume.volume_id,
            device="/dev/sdf",
        )

        # Outputs
        CfnOutput(
            self,
            "InstanceId",
            value=self.instance.instance_id,
            description="EC2 Instance ID",
            export_name=f"{config['PROJECT_NAME']}-instance-id",
        )

        CfnOutput(
            self,
            "InstancePublicIP",
            value=self.instance.instance_public_ip,
            description="EC2 Instance Public IP",
            export_name=f"{config['PROJECT_NAME']}-instance-ip",
        )

        CfnOutput(
            self,
            "VolumeId",
            value=self.data_volume.volume_id,
            description="EBS Data Volume ID",
            export_name=f"{config['PROJECT_NAME']}-volume-id",
        )
