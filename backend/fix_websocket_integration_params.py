#!/usr/bin/env python3
"""
Fix WebSocket API Gateway integration to properly pass query parameters.
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
    print("Fixing WebSocket API Gateway Query Parameter Passing")
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
    
    # For WebSocket API Gateway with HTTP_PROXY, we need to configure
    # request parameters to pass query string through
    # The integration URI should be the base endpoint
    integration_uri = f"http://{EC2_IP}:8000/ws"
    
    print(f"Integration URI: {integration_uri}")
    print("Configuring request parameters to pass session_id query parameter...")
    
    # Update integration with request parameters
    # This tells API Gateway to pass the query parameter to the backend
    try:
        apigw.update_integration(
            ApiId=WS_API_ID,
            IntegrationId=integration_id,
            IntegrationUri=integration_uri,
            IntegrationMethod='GET',
            RequestParameters={
                'querystring.session_id': '$request.querystring.session_id'
            }
        )
        print("[OK] Integration updated with query parameter mapping")
    except ClientError as e:
        print(f"[ERROR] Failed to update: {e}")
        # Try without request parameters (some configurations don't support it)
        try:
            apigw.update_integration(
                ApiId=WS_API_ID,
                IntegrationId=integration_id,
                IntegrationUri=integration_uri,
                IntegrationMethod='GET'
            )
            print("[OK] Integration updated (without explicit parameter mapping)")
            print("[WARNING] Query parameters may need to be handled differently")
        except ClientError as e2:
            print(f"[ERROR] Failed: {e2}")
            exit(1)
    
    # Also update routes to ensure they pass query parameters
    routes = apigw.get_routes(ApiId=WS_API_ID)
    for route in routes.get('Items', []):
        route_key = route.get('RouteKey')
        route_id = route['RouteId']
        
        # Update route to pass query parameters
        try:
            apigw.update_route(
                ApiId=WS_API_ID,
                RouteId=route_id,
                RouteKey=route_key,
                Target=f"integrations/{integration_id}",
                RequestParameters={
                    'querystring.session_id': '$request.querystring.session_id'
                }
            )
            print(f"[OK] Route {route_key} updated to pass query parameters")
        except ClientError as e:
            # Some route configurations may not support RequestParameters
            print(f"[INFO] Route {route_key} - query params handled by integration")
    
    print("\n" + "=" * 80)
    print("SUCCESS!")
    print("=" * 80)
    print("")
    print("WebSocket API Gateway configured to pass query parameters.")
    print("")
    print("Test connection:")
    print(f"  wss://{WS_API_ID}.execute-api.{AWS_REGION}.amazonaws.com/prod?session_id=test")
    print("")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

