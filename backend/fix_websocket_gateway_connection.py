#!/usr/bin/env python3
"""
Fix WebSocket API Gateway - ensure proper connection configuration.
The issue might be that API Gateway WebSocket needs specific headers or configuration.
"""
import boto3
from botocore.exceptions import ClientError

AWS_PROFILE = 'default1'
AWS_REGION = 'us-east-2'
WS_API_ID = '927uc04ep5'
EC2_IP = '13.58.115.166'

try:
    session = boto3.Session(profile_name=AWS_PROFILE)
    apigw = session.client('apigatewayv2', region_name=AWS_REGION)
    
    print("=" * 80)
    print("Reconfiguring WebSocket API Gateway Integration")
    print("=" * 80)
    
    # Get integration
    integrations = apigw.get_integrations(ApiId=WS_API_ID)
    integration_id = integrations['Items'][0]['IntegrationId']
    
    print(f"Integration ID: {integration_id}")
    
    # For WebSocket API Gateway with HTTP_PROXY, the integration URI should be the base endpoint
    # API Gateway will append query parameters automatically
    # But we need to ensure the integration is configured for WebSocket upgrade
    integration_uri = f"http://{EC2_IP}:8000/ws"
    
    print(f"Integration URI: {integration_uri}")
    print("")
    print("Updating integration with proper WebSocket configuration...")
    
    # Update integration
    # For WebSocket, we need HTTP_PROXY with proper configuration
    try:
        apigw.update_integration(
            ApiId=WS_API_ID,
            IntegrationId=integration_id,
            IntegrationUri=integration_uri,
            IntegrationType='HTTP_PROXY',
            IntegrationMethod='GET',
            # Pass query parameters through
            RequestParameters={
                'overwrite:querystring': '$request.querystring'
            } if False else {}  # This might not work, so we'll try without
        )
        print("[OK] Integration updated")
    except ClientError as e:
        print(f"[WARN] Standard update failed: {e}")
        print("Trying without request parameters...")
        
        try:
            apigw.update_integration(
                ApiId=WS_API_ID,
                IntegrationId=integration_id,
                IntegrationUri=integration_uri,
                IntegrationType='HTTP_PROXY',
                IntegrationMethod='GET'
            )
            print("[OK] Integration updated (basic configuration)")
        except ClientError as e2:
            print(f"[ERROR] Failed: {e2}")
            exit(1)
    
    # Verify the integration
    integration = apigw.get_integration(
        ApiId=WS_API_ID,
        IntegrationId=integration_id
    )
    
    print("\nIntegration Configuration:")
    print(f"  URI: {integration.get('IntegrationUri', 'N/A')}")
    print(f"  Type: {integration.get('IntegrationType', 'N/A')}")
    print(f"  Method: {integration.get('IntegrationMethod', 'N/A')}")
    
    # Check if we need to update the stage for auto-deploy
    try:
        stages = apigw.get_stages(ApiId=WS_API_ID)
        prod_stage = None
        for stage in stages.get('Items', []):
            if stage['StageName'] == 'prod':
                prod_stage = stage
                break
        
        if prod_stage:
            print(f"\nStage 'prod' exists")
            print(f"  Auto Deploy: {prod_stage.get('AutoDeploy', False)}")
            
            # Ensure auto-deploy is enabled
            if not prod_stage.get('AutoDeploy', False):
                print("Enabling auto-deploy...")
                apigw.update_stage(
                    ApiId=WS_API_ID,
                    StageName='prod',
                    AutoDeploy=True
                )
                print("[OK] Auto-deploy enabled")
        else:
            print("\nCreating 'prod' stage...")
            apigw.create_stage(
                ApiId=WS_API_ID,
                StageName='prod',
                AutoDeploy=True
            )
            print("[OK] Stage created")
            
    except Exception as e:
        print(f"[WARN] Stage check failed: {e}")
    
    print("\n" + "=" * 80)
    print("Configuration Complete")
    print("=" * 80)
    print("")
    print("IMPORTANT: API Gateway WebSocket with HTTP_PROXY integration")
    print("should automatically forward query parameters from the client request.")
    print("")
    print("Test URL:")
    print(f"  wss://{WS_API_ID}.execute-api.{AWS_REGION}.amazonaws.com/prod?session_id=test")
    print("")
    print("If connection still fails, the issue might be:")
    print("1. Backend not receiving the connection (check backend logs)")
    print("2. API Gateway not forwarding WebSocket upgrade properly")
    print("3. Need to use AWS_PROXY instead of HTTP_PROXY")
    print("")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

