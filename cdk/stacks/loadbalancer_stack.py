"""Load balancer infrastructure - ALB, Target Groups, Listeners"""
from aws_cdk import (
    Stack,
    aws_elasticloadbalancingv2 as elbv2,
    aws_elasticloadbalancingv2_targets as targets,
    aws_ec2 as ec2,
    Tags,
    CfnOutput,
    Duration,
)
from constructs import Construct
from typing import Dict, Optional


class LoadBalancerStack(Stack):
    """
    Creates Application Load Balancer with target groups for each developer

    Resources:
    - Application Load Balancer (internet-facing)
    - 8 Target Groups (one per developer, ports 8443-8450)
    - HTTPS Listener with host-based routing rules
    - HTTP Listener (redirects to HTTPS)

    NOTE: This uses host-based routing (dev1.domain.com, dev2.domain.com, etc.)
    You MUST manually create CNAME records at your DNS provider pointing to
    the ALB DNS name (available in CDK outputs after deployment).
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        network_stack,
        compute_stack,
        config: Dict,
        certificate_arn: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Application Load Balancer
        self.alb = elbv2.ApplicationLoadBalancer(
            self,
            "ALB",
            load_balancer_name=f"{config['PROJECT_NAME']}-alb",
            vpc=network_stack.vpc,
            internet_facing=True,
            security_group=network_stack.alb_security_group,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
        )

        # Create target groups for each developer
        self.target_groups = []

        for i in range(1, config['NUM_DEVELOPERS'] + 1):
            port = config['CONTAINER_BASE_PORT'] + i - 1
            subdomain = f"dev{i}.{config['BASE_DOMAIN']}"

            target_group = elbv2.ApplicationTargetGroup(
                self,
                f"TargetGroupDev{i}",
                target_group_name=f"{config['PROJECT_NAME']}-dev{i}-tg",
                vpc=network_stack.vpc,
                port=port,
                protocol=elbv2.ApplicationProtocol.HTTP,
                targets=[
                    targets.InstanceTarget(
                        instance=compute_stack.instance,
                        port=port,
                    )
                ],
                health_check=elbv2.HealthCheck(
                    path="/healthz",
                    protocol=elbv2.Protocol.HTTP,
                    port=str(port),
                    interval=Duration.seconds(30),
                    timeout=Duration.seconds(5),
                    healthy_threshold_count=2,
                    unhealthy_threshold_count=3,
                ),
                deregistration_delay=Duration.seconds(30),
                stickiness_cookie_duration=Duration.hours(1),
            )

            self.target_groups.append({
                'id': i,
                'port': port,
                'target_group': target_group,
                'subdomain': subdomain,
            })

            Tags.of(target_group).add("Developer", f"dev{i}")

        # Create HTTPS listener if certificate is provided
        if certificate_arn:
            from aws_cdk import aws_certificatemanager as acm

            certificate = acm.Certificate.from_certificate_arn(
                self,
                "Certificate",
                certificate_arn
            )

            https_listener = self.alb.add_listener(
                "HTTPSListener",
                port=443,
                protocol=elbv2.ApplicationProtocol.HTTPS,
                certificates=[certificate],
                default_action=elbv2.ListenerAction.fixed_response(
                    status_code=404,
                    content_type="text/plain",
                    message_body="Not Found - Invalid subdomain",
                ),
            )

            # Add host-based routing rules for each developer
            for tg_config in self.target_groups:
                https_listener.add_action(
                    f"Dev{tg_config['id']}Rule",
                    priority=tg_config['id'],
                    conditions=[
                        elbv2.ListenerCondition.host_headers(
                            [tg_config['subdomain']]
                        )
                    ],
                    action=elbv2.ListenerAction.forward(
                        target_groups=[tg_config['target_group']]
                    ),
                )

        # Create HTTP listener (redirect to HTTPS)
        http_listener = self.alb.add_listener(
            "HTTPListener",
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            default_action=elbv2.ListenerAction.redirect(
                protocol="HTTPS",
                port="443",
                permanent=True,
            ),
        )

        # Apply tags
        for key, value in config['TAGS'].items():
            Tags.of(self.alb).add(key, value)

        # Outputs
        CfnOutput(
            self,
            "ALBDNSName",
            value=self.alb.load_balancer_dns_name,
            description="ALB DNS Name",
            export_name=f"{config['PROJECT_NAME']}-alb-dns",
        )

        CfnOutput(
            self,
            "ALBArn",
            value=self.alb.load_balancer_arn,
            description="ALB ARN",
            export_name=f"{config['PROJECT_NAME']}-alb-arn",
        )

        # Output target group ARNs
        for tg_config in self.target_groups:
            CfnOutput(
                self,
                f"TargetGroupDev{tg_config['id']}Arn",
                value=tg_config['target_group'].target_group_arn,
                description=f"Target Group ARN for Developer {tg_config['id']}",
            )

        # Output CNAME setup instructions
        CfnOutput(
            self,
            "CNAMESetupInstructions",
            value=f"Create CNAME records at your DNS provider: dev1-dev8.{config['BASE_DOMAIN']} -> {self.alb.load_balancer_dns_name}",
            description="⚠️ IMPORTANT: Manual CNAME setup required",
        )
