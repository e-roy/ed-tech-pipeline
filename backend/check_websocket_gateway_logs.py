#!/usr/bin/env python3
"""
Check CloudWatch logs for WebSocket API Gateway to see connection attempts.
"""
import os
from datetime import datetime, timedelta

import boto3

AWS_PROFILE = os.environ.get("AWS_PROFILE", "default1")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-2")
WS_API_ID = os.environ.get("WS_API_ID", "927uc04ep5")

try:
    session = boto3.Session(profile_name=AWS_PROFILE)
    logs = session.client('logs', region_name=AWS_REGION)
    
    print("=" * 80)
    print("Checking CloudWatch Logs for WebSocket API Gateway")
    print("=" * 80)
    
    # Check for log groups
    log_group_name = f"/aws/apigateway/{WS_API_ID}"
    
    try:
        # Try to get log streams
        streams = logs.describe_log_streams(
            logGroupName=log_group_name,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        if streams.get('logStreams'):
            print(f"Found {len(streams['logStreams'])} log streams")
            
            # Get recent events
            for stream in streams['logStreams'][:3]:
                stream_name = stream['logStreamName']
                print(f"\nLog Stream: {stream_name}")
                
                events = logs.get_log_events(
                    logGroupName=log_group_name,
                    logStreamName=stream_name,
                    limit=20
                )
                
                for event in events.get('events', []):
                    timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                    message = event['message']
                    print(f"  [{timestamp}] {message[:200]}")
        else:
            print("No log streams found")
            print("Logging might not be enabled for this API Gateway")
            
    except logs.exceptions.ResourceNotFoundException:
        print(f"Log group not found: {log_group_name}")
        print("CloudWatch logging might not be enabled for WebSocket API Gateway")
        print("\nTo enable logging:")
        print("1. Go to API Gateway Console")
        print("2. Select WebSocket API")
        print("3. Go to Logging & Tracing")
        print("4. Enable CloudWatch Logs")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

