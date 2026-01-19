"""Monitoring infrastructure - CloudWatch logs, alarms, and backups"""
from aws_cdk import (
    Stack,
    aws_cloudwatch as cloudwatch,
    aws_logs as logs,
    aws_backup as backup,
    aws_events as events,
    Tags,
    Duration,
    RemovalPolicy,
)
from constructs import Construct
from typing import Dict


class MonitoringStack(Stack):
    """
    Creates CloudWatch monitoring, logging, and backup resources

    Resources:
    - CloudWatch log groups for system, docker, and each developer
    - CloudWatch alarms for CPU, disk, and other metrics
    - AWS Backup plan for EBS volume (daily backups, 30-day retention)
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        compute_stack,
        config: Dict,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create log groups
        log_groups_config = [
            (f"/aws/ec2/{config['PROJECT_NAME']}/system", "System logs"),
            (f"/aws/ec2/{config['PROJECT_NAME']}/docker", "Docker daemon logs"),
        ]

        # Add log group for each developer container
        for i in range(1, config['NUM_DEVELOPERS'] + 1):
            log_groups_config.append(
                (
                    f"/aws/ec2/{config['PROJECT_NAME']}/containers/dev{i}",
                    f"Container logs for developer {i}"
                )
            )

        # Create all log groups
        for log_group_name, description in log_groups_config:
            logs.LogGroup(
                self,
                log_group_name.replace("/", "-").replace(".", "-"),
                log_group_name=log_group_name,
                retention=logs.RetentionDays.ONE_MONTH,
                removal_policy=RemovalPolicy.DESTROY,
            )

        # Create CloudWatch alarms

        # 1. CPU Utilization Alarm
        cpu_alarm = cloudwatch.Alarm(
            self,
            "HighCPUAlarm",
            alarm_name=f"{config['PROJECT_NAME']}-high-cpu",
            alarm_description="Alert when CPU exceeds 80%",
            metric=cloudwatch.Metric(
                namespace="AWS/EC2",
                metric_name="CPUUtilization",
                dimensions_map={
                    "InstanceId": compute_stack.instance.instance_id
                },
                statistic="Average",
                period=Duration.minutes(5),
            ),
            threshold=80,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        )

        # 2. Status Check Failed Alarm
        status_alarm = cloudwatch.Alarm(
            self,
            "StatusCheckFailedAlarm",
            alarm_name=f"{config['PROJECT_NAME']}-status-check-failed",
            alarm_description="Alert when instance status check fails",
            metric=cloudwatch.Metric(
                namespace="AWS/EC2",
                metric_name="StatusCheckFailed",
                dimensions_map={
                    "InstanceId": compute_stack.instance.instance_id
                },
                statistic="Maximum",
                period=Duration.minutes(1),
            ),
            threshold=1,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
        )

        # Create backup plan if enabled
        if config.get('ENABLE_BACKUP', True):
            # Create backup vault
            backup_vault = backup.BackupVault(
                self,
                "BackupVault",
                backup_vault_name=f"{config['PROJECT_NAME']}-vault",
                removal_policy=RemovalPolicy.DESTROY,
            )

            # Create backup plan
            backup_plan = backup.BackupPlan(
                self,
                "BackupPlan",
                backup_plan_name=f"{config['PROJECT_NAME']}-daily-backup",
                backup_vault=backup_vault,
            )

            # Add backup rule (daily at 2 AM UTC)
            backup_plan.add_rule(
                backup.BackupPlanRule(
                    rule_name="DailyBackup",
                    schedule_expression=events.Schedule.cron(
                        hour="2",
                        minute="0",
                    ),
                    delete_after=Duration.days(
                        config.get('BACKUP_RETENTION_DAYS', 30)
                    ),
                    start_window=Duration.hours(1),
                    completion_window=Duration.hours(2),
                )
            )

            # Add EBS volume to backup selection
            backup_plan.add_selection(
                "BackupSelection",
                resources=[
                    backup.BackupResource.from_arn(
                        compute_stack.data_volume.volume_arn
                    )
                ],
            )

        # Apply tags
        for key, value in config['TAGS'].items():
            Tags.of(cpu_alarm).add(key, value)
            Tags.of(status_alarm).add(key, value)
