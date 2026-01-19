#!/usr/bin/env python3
"""
Claude API Proxy with Usage Tracking
Logs all API calls to CloudWatch for monitoring and cost tracking
"""

from flask import Flask, request, Response
import requests
import json
import time
from datetime import datetime
import boto3
import os

app = Flask(__name__)

# CloudWatch client
cloudwatch = boto3.client('cloudwatch', region_name='ap-southeast-7')
logs_client = boto3.client('logs', region_name='ap-southeast-7')

LOG_GROUP = '/aws/ec2/code-server-multi-dev/claude-api'
PROJECT_NAME = 'code-server-multi-dev'

# Claude API endpoint
CLAUDE_API_URL = "https://api.anthropic.com/v1"

# Cost per token (as of 2024)
COSTS = {
    'claude-3-sonnet': {'input': 3.0 / 1_000_000, 'output': 15.0 / 1_000_000},
    'claude-3-haiku': {'input': 0.25 / 1_000_000, 'output': 1.25 / 1_000_000},
    'claude-3-opus': {'input': 15.0 / 1_000_000, 'output': 75.0 / 1_000_000},
}


def get_developer_from_key(api_key):
    """Extract developer ID from API key (stored in env)"""
    for i in range(1, 9):
        dev_key = os.environ.get(f'DEV{i}_CLAUDE_KEY', '')
        if api_key == dev_key:
            return f'dev{i}'
    return 'unknown'


def calculate_cost(model, input_tokens, output_tokens):
    """Calculate cost based on token usage"""
    model_key = model.split('-')[0:3]  # Extract base model name
    model_key = '-'.join(model_key)

    if model_key not in COSTS:
        model_key = 'claude-3-sonnet'  # Default

    input_cost = input_tokens * COSTS[model_key]['input']
    output_cost = output_tokens * COSTS[model_key]['output']

    return input_cost + output_cost


def log_to_cloudwatch(log_data):
    """Send logs to CloudWatch"""
    try:
        # Create log stream if not exists
        stream_name = f"{log_data['developer']}/{datetime.now().strftime('%Y/%m/%d')}"

        try:
            logs_client.create_log_stream(
                logGroupName=LOG_GROUP,
                logStreamName=stream_name
            )
        except logs_client.exceptions.ResourceAlreadyExistsException:
            pass

        # Put log event
        logs_client.put_log_events(
            logGroupName=LOG_GROUP,
            logStreamName=stream_name,
            logEvents=[{
                'timestamp': int(time.time() * 1000),
                'message': json.dumps(log_data)
            }]
        )
    except Exception as e:
        print(f"Error logging to CloudWatch: {e}")


def send_metrics_to_cloudwatch(developer, model, input_tokens, output_tokens, cost):
    """Send custom metrics to CloudWatch"""
    try:
        cloudwatch.put_metric_data(
            Namespace='CodeServer/ClaudeAPI',
            MetricData=[
                {
                    'MetricName': 'InputTokens',
                    'Value': input_tokens,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': [
                        {'Name': 'Developer', 'Value': developer},
                        {'Name': 'Model', 'Value': model},
                        {'Name': 'Project', 'Value': PROJECT_NAME},
                    ]
                },
                {
                    'MetricName': 'OutputTokens',
                    'Value': output_tokens,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': [
                        {'Name': 'Developer', 'Value': developer},
                        {'Name': 'Model', 'Value': model},
                        {'Name': 'Project', 'Value': PROJECT_NAME},
                    ]
                },
                {
                    'MetricName': 'TotalCost',
                    'Value': cost,
                    'Unit': 'None',
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': [
                        {'Name': 'Developer', 'Value': developer},
                        {'Name': 'Model', 'Value': model},
                        {'Name': 'Project', 'Value': PROJECT_NAME},
                    ]
                },
                {
                    'MetricName': 'APICall',
                    'Value': 1,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': [
                        {'Name': 'Developer', 'Value': developer},
                        {'Name': 'Project', 'Value': PROJECT_NAME},
                    ]
                }
            ]
        )
    except Exception as e:
        print(f"Error sending metrics: {e}")


@app.route('/v1/messages', methods=['POST'])
def proxy_messages():
    """Proxy Claude API messages endpoint with tracking"""

    # Get API key from header
    api_key = request.headers.get('x-api-key')
    if not api_key:
        return {'error': 'Missing API key'}, 401

    # Get developer ID
    developer = get_developer_from_key(api_key)

    # Forward request to Claude API
    headers = {
        'x-api-key': api_key,
        'anthropic-version': request.headers.get('anthropic-version', '2023-06-01'),
        'content-type': 'application/json',
    }

    start_time = time.time()

    try:
        response = requests.post(
            f"{CLAUDE_API_URL}/messages",
            headers=headers,
            json=request.json,
            timeout=300
        )

        elapsed_time = time.time() - start_time

        # Parse response for usage data
        if response.status_code == 200:
            response_data = response.json()
            usage = response_data.get('usage', {})

            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            model = response_data.get('model', 'unknown')

            # Calculate cost
            cost = calculate_cost(model, input_tokens, output_tokens)

            # Log to CloudWatch
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'developer': developer,
                'model': model,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'cost_usd': round(cost, 6),
                'response_time_seconds': round(elapsed_time, 2),
                'status': 'success'
            }

            log_to_cloudwatch(log_data)
            send_metrics_to_cloudwatch(developer, model, input_tokens, output_tokens, cost)

        return Response(
            response.content,
            status=response.status_code,
            headers=dict(response.headers)
        )

    except Exception as e:
        # Log error
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'developer': developer,
            'status': 'error',
            'error': str(e)
        }
        log_to_cloudwatch(log_data)

        return {'error': str(e)}, 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return {'status': 'healthy', 'service': 'claude-proxy'}


if __name__ == '__main__':
    # Run on all interfaces, port 8080
    app.run(host='0.0.0.0', port=8000, debug=False)
