#!/usr/bin/env python3
"""
Try simpler WebSocket API Gateway configuration - base URI only.
"""
import boto3

AWS_PROFILE = 'default1'
AWS_REGION = 'us-east-2'
WS_API_ID = '927uc04ep5'
EC2_IP = '13.58.115.166'

try:
    session = boto3.Session(profile_name=AWS_PROFILE)
    apigw = session.client('apigatewayv2', region_name=AWS_REGION)
    
    print("=" * 80)
    print("Updating WebSocket Integration - Simple Base URI")
    print("=" * 80)
    
    # Get integration
    integrations = apigw.get_integrations(ApiId=WS_API_ID)
    integration_id = integrations['Items'][0]['IntegrationId']
    
    # Use base URI - API Gateway should append query parameters automatically
    base_uri = f"http://{EC2_IP}:8000/ws"
    
    print(f"Setting integration URI to: {base_uri}")
    print("API Gateway should automatically append query parameters from client request")
    
    apigw.update_integration(
        ApiId=WS_API_ID,
        IntegrationId=integration_id,
        IntegrationUri=base_uri,
        IntegrationMethod='GET'
    )
    
    print("[OK] Integration updated")
    print("")
    print("Test: wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod?session_id=test")
    print("")
    print("If this doesn't work, the backend /ws endpoint should accept connections")
    print("without query parameters and extract session_id from headers or connection metadata.")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

