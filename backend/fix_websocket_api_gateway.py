#!/usr/bin/env python3
"""
Fix WebSocket API Gateway integration for proper WebSocket support.
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
    
    # Get current integration
    integrations = apigw.get_integrations(ApiId=WS_API_ID)
    integration_id = None
    for integration in integrations.get('Items', []):
        integration_id = integration['IntegrationId']
        break
    
    if not integration_id:
        print("ERROR: No integration found")
        exit(1)
    
    print(f"Found integration: {integration_id}")
    
    # Get current integration details
    current_integration = apigw.get_integration(
        ApiId=WS_API_ID,
        IntegrationId=integration_id
    )
    
    print(f"Current URI: {current_integration.get('IntegrationUri', 'N/A')}")
    
    # For WebSocket API Gateway, the integration URI should be the base endpoint
    # Query parameters are passed through automatically
    # The backend endpoint /ws accepts query parameters
    new_uri = f"http://{EC2_IP}:8000/ws"
    
    print(f"Updating integration URI to: {new_uri}")
    
    # Update integration
    # For WebSocket, we need to use the correct integration type
    # HTTP_PROXY should work, but we need to ensure it's configured correctly
    try:
        apigw.update_integration(
            ApiId=WS_API_ID,
            IntegrationId=integration_id,
            IntegrationUri=new_uri,
            IntegrationMethod='GET'  # WebSocket upgrade starts as GET
        )
        print("[OK] Integration updated")
    except ClientError as e:
        print(f"[ERROR] Failed to update integration: {e}")
        print("Trying alternative approach...")
        
        # Try updating with request parameters to pass query string
        try:
            apigw.update_integration(
                ApiId=WS_API_ID,
                IntegrationId=integration_id,
                IntegrationUri=new_uri,
                IntegrationMethod='GET',
                RequestParameters={
                    'querystring.session_id': '$request.querystring.session_id'
                }
            )
            print("[OK] Integration updated with request parameters")
        except ClientError as e2:
            print(f"[ERROR] Alternative approach also failed: {e2}")
            exit(1)
    
    # Get routes and verify they're pointing to the integration
    routes = apigw.get_routes(ApiId=WS_API_ID)
    print("\nRoutes configuration:")
    for route in routes.get('Items', []):
        route_key = route.get('RouteKey', 'N/A')
        route_id = route['RouteId']
        target = route.get('Target', 'N/A')
        print(f"  {route_key}: {target}")
        
        # Verify target points to our integration
        if target != f"integrations/{integration_id}":
            print(f"    WARNING: Route target doesn't match integration")
    
    print("\n" + "=" * 80)
    print("SUCCESS!")
    print("=" * 80)
    print("")
    print("WebSocket API Gateway integration updated.")
    print("The integration now points to: http://13.58.115.166:8000/ws")
    print("Query parameters (session_id) will be passed through automatically.")
    print("")
    print("Note: WebSocket connections may take a moment to propagate.")
    print("")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

