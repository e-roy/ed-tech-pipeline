#!/usr/bin/env python3
"""
Check and fix WebSocket API Gateway configuration.
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
    print("Checking WebSocket API Gateway Configuration")
    print("=" * 80)
    
    # Get API details
    api = apigw.get_api(ApiId=WS_API_ID)
    print(f"API Name: {api['Name']}")
    print(f"API ID: {WS_API_ID}")
    print(f"API Endpoint: {api['ApiEndpoint']}")
    print("")
    
    # Get integrations
    integrations = apigw.get_integrations(ApiId=WS_API_ID)
    print("Integrations:")
    for integration in integrations.get('Items', []):
        print(f"  Integration ID: {integration['IntegrationId']}")
        print(f"  Integration URI: {integration.get('IntegrationUri', 'N/A')}")
        print(f"  Integration Type: {integration.get('IntegrationType', 'N/A')}")
        print(f"  Connection Type: {integration.get('ConnectionType', 'N/A')}")
        print("")
    
    # Get routes
    routes = apigw.get_routes(ApiId=WS_API_ID)
    print("Routes:")
    for route in routes.get('Items', []):
        print(f"  Route Key: {route.get('RouteKey', 'N/A')}")
        print(f"  Route ID: {route['RouteId']}")
        target = route.get('Target', 'N/A')
        print(f"  Target: {target}")
        print("")
    
    # Check $connect route
    connect_route = None
    for route in routes.get('Items', []):
        if route.get('RouteKey') == '$connect':
            connect_route = route
            break
    
    if connect_route:
        print("$connect Route Configuration:")
        print(f"  Route ID: {connect_route['RouteId']}")
        print(f"  Target: {connect_route.get('Target', 'N/A')}")
        
        # Get integration details
        if 'Target' in connect_route:
            integration_id = connect_route['Target'].split('/')[-1]
            try:
                integration = apigw.get_integration(
                    ApiId=WS_API_ID,
                    IntegrationId=integration_id
                )
                print(f"  Integration URI: {integration.get('IntegrationUri', 'N/A')}")
                print(f"  Integration Type: {integration.get('IntegrationType', 'N/A')}")
                
                # Check if URI is correct
                expected_uri = f"http://{EC2_IP}:8000/ws"
                current_uri = integration.get('IntegrationUri', '')
                
                if current_uri != expected_uri:
                    print(f"  WARNING: Integration URI mismatch!")
                    print(f"    Current: {current_uri}")
                    print(f"    Expected: {expected_uri}")
                    print("  Need to update integration URI")
                else:
                    print(f"  Integration URI is correct: {current_uri}")
                    
            except ClientError as e:
                print(f"  Error getting integration: {e}")
    
    # Check $default route
    default_route = None
    for route in routes.get('Items', []):
        if route.get('RouteKey') == '$default':
            default_route = route
            break
    
    if default_route:
        print("\n$default Route Configuration:")
        print(f"  Route ID: {default_route['RouteId']}")
        print(f"  Target: {default_route.get('Target', 'N/A')}")
    
    print("")
    print("=" * 80)
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

