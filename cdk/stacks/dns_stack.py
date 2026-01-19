"""DNS infrastructure - Route53 records and ACM certificate"""
from aws_cdk import (
    Stack,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_certificatemanager as acm,
    Tags,
    CfnOutput,
)
from constructs import Construct
from typing import Dict, Optional


class DNSStack(Stack):
    """
    Creates Route53 DNS records and ACM SSL certificate

    Resources:
    - ACM wildcard certificate for *.domain.com
    - Route53 A records for each developer subdomain (dev1-dev8)
    - Automatic DNS validation for certificate
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Dict,
        loadbalancer_stack=None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get hosted zone
        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self,
            "HostedZone",
            hosted_zone_id=config['ROUTE53_HOSTED_ZONE_ID'],
            zone_name=config['BASE_DOMAIN'],
        )

        # Request wildcard certificate
        self.certificate = acm.Certificate(
            self,
            "Certificate",
            domain_name=f"*.{config['BASE_DOMAIN']}",
            subject_alternative_names=[config['BASE_DOMAIN']],
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        # Create A records for each developer subdomain (if ALB is provided)
        if loadbalancer_stack:
            for i in range(1, config['NUM_DEVELOPERS'] + 1):
                subdomain = f"dev{i}"

                route53.ARecord(
                    self,
                    f"ARecordDev{i}",
                    record_name=subdomain,
                    zone=hosted_zone,
                    target=route53.RecordTarget.from_alias(
                        targets.LoadBalancerTarget(loadbalancer_stack.alb)
                    ),
                    comment=f"A record for developer {i} code-server",
                )

        # Apply tags
        for key, value in config['TAGS'].items():
            Tags.of(self.certificate).add(key, value)

        # Outputs
        CfnOutput(
            self,
            "CertificateArn",
            value=self.certificate.certificate_arn,
            description="ACM Certificate ARN",
            export_name=f"{config['PROJECT_NAME']}-cert-arn",
        )

        # Output URLs for each developer
        for i in range(1, config['NUM_DEVELOPERS'] + 1):
            CfnOutput(
                self,
                f"Dev{i}URL",
                value=f"https://dev{i}.{config['BASE_DOMAIN']}",
                description=f"Developer {i} Code-Server URL",
            )
