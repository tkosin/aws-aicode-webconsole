"""Security infrastructure - IAM roles and Secrets Manager"""
from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    Tags,
    RemovalPolicy,
    SecretValue,
)
from constructs import Construct
import secrets
import string
from typing import Dict


class SecurityStack(Stack):
    """
    Creates IAM roles and Secrets Manager secrets

    Resources:
    - IAM role for EC2 with permissions for Secrets Manager, CloudWatch, Bedrock
    - Secrets Manager secrets for code-server passwords (8 developers)
    - No Claude API keys needed (using AWS Bedrock with IAM authentication)
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Dict,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create IAM role for EC2
        self.ec2_role = iam.Role(
            self,
            "EC2Role",
            role_name=f"{config['PROJECT_NAME']}-ec2-role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            description="IAM role for code-server EC2 instance",
        )

        # Add policy for Secrets Manager access
        self.ec2_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["secretsmanager:GetSecretValue"],
                resources=[
                    f"arn:aws:secretsmanager:{config['AWS_REGION']}:{self.account}:secret:{config['PROJECT_NAME']}/*"
                ],
            )
        )

        # Add policy for CloudWatch Logs
        self.ec2_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[
                    f"arn:aws:logs:{config['AWS_REGION']}:{self.account}:log-group:/aws/ec2/{config['PROJECT_NAME']}/*"
                ],
            )
        )

        # Add policy for CloudWatch Metrics
        self.ec2_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
            )
        )

        # Add policy for AWS Bedrock access
        # Developers will use Claude Code extension via Bedrock
        bedrock_region = config.get('BEDROCK_REGION', 'ap-southeast-1')
        self.ec2_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:ListFoundationModels",
                    "bedrock:GetFoundationModel",
                ],
                resources=[
                    f"arn:aws:bedrock:{bedrock_region}::foundation-model/*"
                ],
            )
        )

        # Create Secrets Manager secrets for each developer
        self.secrets = {}

        for i in range(1, config['NUM_DEVELOPERS'] + 1):
            # Generate random password
            password = self._generate_password()

            # Create secret for code-server password
            secret = secretsmanager.Secret(
                self,
                f"Dev{i}Password",
                secret_name=f"{config['PROJECT_NAME']}/dev{i}/password",
                description=f"Code-server password for developer {i}",
                secret_string_value=SecretValue.unsafe_plain_text(password),
                removal_policy=RemovalPolicy.DESTROY,
            )

            self.secrets[f"dev{i}_password"] = secret

            # Apply tags
            Tags.of(secret).add("Developer", f"dev{i}")

        # Apply global tags
        for key, value in config['TAGS'].items():
            Tags.of(self.ec2_role).add(key, value)

    def _generate_password(self, length: int = 20) -> str:
        """Generate a secure random password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
