"""Certificate infrastructure - ACM certificate with manual DNS validation"""
from aws_cdk import (
    Stack,
    aws_certificatemanager as acm,
    Tags,
    CfnOutput,
)
from constructs import Construct
from typing import Dict


class CertificateStack(Stack):
    """
    Creates ACM SSL certificate with manual DNS validation

    Resources:
    - ACM wildcard certificate for *.domain.com
    - Manual DNS validation (user must add CNAME records at their DNS provider)

    NOTE: This does NOT use Route53. After deployment, you will see DNS validation
    records in the CDK output. You must manually create these CNAME records at
    your DNS provider (Cloudflare, GoDaddy, etc.) for the certificate to be issued.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Dict,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Request wildcard certificate with DNS validation
        # This will output validation records that must be manually added
        self.certificate = acm.Certificate(
            self,
            "Certificate",
            domain_name=f"*.{config['BASE_DOMAIN']}",
            subject_alternative_names=[config['BASE_DOMAIN']],
            validation=acm.CertificateValidation.from_dns(),
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

        CfnOutput(
            self,
            "CertificateDomainName",
            value=f"*.{config['BASE_DOMAIN']}",
            description="Certificate domain name",
        )

        # Output URLs for each developer (for reference)
        for i in range(1, config['NUM_DEVELOPERS'] + 1):
            CfnOutput(
                self,
                f"Dev{i}URL",
                value=f"https://dev{i}.{config['BASE_DOMAIN']}",
                description=f"Developer {i} Code-Server URL (after CNAME setup)",
            )

        # Important note in outputs
        CfnOutput(
            self,
            "DNSValidationNote",
            value="Check AWS Console for DNS validation CNAME records. Add them to your DNS provider.",
            description="⚠️ IMPORTANT: Manual DNS validation required",
        )
