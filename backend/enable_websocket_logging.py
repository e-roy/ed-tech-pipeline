#!/usr/bin/env python3
"""
Enable CloudWatch logging for the WebSocket API Gateway.
"""
import json
import os
import time

import boto3
from botocore.exceptions import ClientError


AWS_PROFILE = os.environ.get("AWS_PROFILE", "default1")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-2")
WS_API_ID = os.environ.get("WS_API_ID", "927uc04ep5")
STAGE_NAME = os.environ.get("STAGE_NAME", "prod")


def ensure_log_group(logs_client, log_group_name: str):
    """Create the CloudWatch log group if it does not exist."""
    try:
        logs_client.create_log_group(logGroupName=log_group_name)
        print(f"[OK] Created log group: {log_group_name}")
    except logs_client.exceptions.ResourceAlreadyExistsException:
        print(f"[-] Log group already exists: {log_group_name}")

    # Optional: keep logs for 7 days to avoid costs
    logs_client.put_retention_policy(logGroupName=log_group_name, retentionInDays=7)


def ensure_resource_policy(logs_client, account_id: str, policy_name: str):
    """Ensure CloudWatch Logs resource policy allows API Gateway to publish logs."""
    statement = {
        "Sid": "APIGatewayAccess",
        "Effect": "Allow",
        "Principal": {"Service": "apigateway.amazonaws.com"},
        "Action": [
            "logs:CreateLogStream",
            "logs:PutLogEvents"
        ],
        "Resource": [
            f"arn:aws:logs:{AWS_REGION}:{account_id}:log-group:/aws/apigateway/*"
        ]
    }

    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [statement],
    }

    existing = logs_client.describe_resource_policies().get("resourcePolicies", [])
    for policy in existing:
        if policy["policyName"] == policy_name:
            print(f"[-] Resource policy already exists: {policy_name}")
            return

    logs_client.put_resource_policy(
        policyName=policy_name,
        policyDocument=json.dumps(policy_doc)
    )
    print(f"[OK] Created resource policy: {policy_name}")


def enable_stage_logging(apigw_client, log_group_arn: str):
    """Enable access logging and route logging for the stage."""
    route_settings = {
        "$connect": {
            "DataTraceEnabled": True,
            "LoggingLevel": "INFO",
        },
        "$default": {
            "DataTraceEnabled": True,
            "LoggingLevel": "INFO",
        },
        "$disconnect": {
            "DataTraceEnabled": True,
            "LoggingLevel": "INFO",
        },
    }

    log_format = (
        '{ "requestId":"$context.requestId", '
        '"ip":"$context.identity.sourceIp", '
        '"routeKey":"$context.routeKey", '
        '"status":"$context.status", '
        '"connectionId":"$context.connectionId", '
        '"protocol":"$context.protocol" }'
    )

    apigw_client.update_stage(
        ApiId=WS_API_ID,
        StageName=STAGE_NAME,
        AccessLogSettings={
            "DestinationArn": log_group_arn,
            "Format": log_format,
        },
        RouteSettings=route_settings,
        DefaultRouteSettings={
            "DataTraceEnabled": True,
            "LoggingLevel": "INFO",
        },
        AutoDeploy=True,
    )
    print(f"[OK] Enabled logging for stage '{STAGE_NAME}'")


def main():
    session = boto3.Session(profile_name=AWS_PROFILE)
    logs_client = session.client("logs", region_name=AWS_REGION)
    apigw_client = session.client("apigatewayv2", region_name=AWS_REGION)
    sts_client = session.client("sts")

    account_id = sts_client.get_caller_identity()["Account"]
    log_group_name = f"/aws/apigateway/{WS_API_ID}"
    log_group_arn = f"arn:aws:logs:{AWS_REGION}:{account_id}:log-group:{log_group_name}"

    print("=" * 80)
    print("Enabling CloudWatch logging for WebSocket API Gateway")
    print("=" * 80)

    ensure_log_group(logs_client, log_group_name)
    ensure_resource_policy(logs_client, account_id, "APIGatewayWebSocketLogs")
    enable_stage_logging(apigw_client, log_group_arn)

    print("\n[INFO] Waiting a few seconds for settings to propagate...")
    time.sleep(5)
    print("[DONE] Logging enabled. Reproduce the issue and fetch logs.")


if __name__ == "__main__":
    try:
        main()
    except ClientError as exc:
        print(f"[ERROR] AWS ClientError: {exc}")
        raise

