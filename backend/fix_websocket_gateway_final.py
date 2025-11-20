#!/usr/bin/env python3
"""
Fix WebSocket API Gateway integration - configure to properly pass query parameters.
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
    print("Fixing WebSocket API Gateway Integration")
    print("=" * 80)
    
    # Get integration
    integrations = apigw.get_integrations(ApiId=WS_API_ID)
    integration_id = None
    for integration in integrations.get('Items', []):
        integration_id = integration['IntegrationId']
        break
    
    if not integration_id:
        print("ERROR: No integration found")
        exit(1)
    
    print(f"Integration ID: {integration_id}")
    
    # For WebSocket API Gateway with HTTP_PROXY, the integration URI should include
    # the query parameter template. API Gateway will substitute $request.querystring.session_id
    # with the actual value from the incoming request.
    integration_uri = f"http://{EC2_IP}:8000/ws?session_id=$request.querystring.session_id"
    
    print(f"Setting integration URI to: {integration_uri}")
    print("(API Gateway will substitute $request.querystring.session_id with actual value)")
    
    try:
        # Update integration
        apigw.update_integration(
            ApiId=WS_API_ID,
            IntegrationId=integration_id,
            IntegrationUri=integration_uri,
            IntegrationMethod='GET'
        )
        print("[OK] Integration updated successfully")
        
    except ClientError as e:
        print(f"[ERROR] Failed to update integration: {e}")
        print("\nTrying alternative: Using base URI without query params...")
        
        # Alternative: Use base URI and let API Gateway append query string
        base_uri = f"http://{EC2_IP}:8000/ws"
        try:
            apigw.update_integration(
                ApiId=WS_API_ID,
                IntegrationId=integration_id,
                IntegrationUri=base_uri,
                IntegrationMethod='GET'
            )
            print(f"[OK] Integration updated to base URI: {base_uri}")
            print("[WARNING] Query parameters may need to be handled via route configuration")
        except ClientError as e2:
            print(f"[ERROR] Alternative also failed: {e2}")
            exit(1)
    
    # Verify routes
    routes = apigw.get_routes(ApiId=WS_API_ID)
    print("\nRoutes:")
    for route in routes.get('Items', []):
        route_key = route.get('RouteKey', 'N/A')
        target = route.get('Target', 'N/A')
        print(f"  {route_key}: {target}")
    
    print("\n" + "=" * 80)
    print("Configuration Updated")
    print("=" * 80)
    print("")
    print("Test WebSocket connection:")
    print(f"  wss://{WS_API_ID}.execute-api.{AWS_REGION}.amazonaws.com/prod?session_id=test")
    print("")
    print("Note: Changes may take a few seconds to propagate.")
    print("")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

