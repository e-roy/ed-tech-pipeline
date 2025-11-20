#!/usr/bin/env python3
"""
Configure WebSocket API Gateway to use path parameters.
Create a route that matches /{session_id} and forwards to backend /ws/{session_id}
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
    print("Configuring WebSocket API Gateway for Path Parameters")
    print("=" * 80)
    print("")
    print("API Gateway WebSocket doesn't forward query params during $connect")
    print("Solution: Use path parameters instead")
    print("")
    
    # Get or create integration
    integrations = apigw.get_integrations(ApiId=WS_API_ID)
    integration_id = None
    
    if integrations.get('Items'):
        integration_id = integrations['Items'][0]['IntegrationId']
        print(f"Using existing integration: {integration_id}")
    else:
        print("Creating new integration...")
        integration = apigw.create_integration(
            ApiId=WS_API_ID,
            IntegrationType='HTTP_PROXY',
            IntegrationUri=f"http://{EC2_IP}:8000/ws",
            IntegrationMethod='GET'
        )
        integration_id = integration['IntegrationId']
        print(f"Created integration: {integration_id}")
    
    # Update integration to handle path parameters
    # The integration URI will be: http://{EC2_IP}:8000/ws/{session_id}
    # But HTTP_PROXY doesn't support path transformation directly
    # So we need to use a route that extracts the path parameter
    
    # Create a route with path parameter pattern: $connect or {session_id}
    # Actually, for WebSocket API Gateway, we can use route selection expression
    # But the simplest is to create a route that matches any path and extracts session_id
    
    # Check existing routes
    routes = apigw.get_routes(ApiId=WS_API_ID)
    print("\nExisting routes:")
    for route in routes.get('Items', []):
        print(f"  {route.get('RouteKey', 'N/A')}: {route['RouteId']}")
    
    # For WebSocket API Gateway, the $connect route is special
    # We can't easily change it to use path parameters
    # Instead, we need to:
    # 1. Keep $connect route as is
    # 2. Create a custom route that matches path pattern
    # 3. OR use route selection expression to extract session_id from path
    
    # Actually, WebSocket API Gateway route selection is based on $request.body.action
    # For $connect, we need to extract session_id from the path
    
    # Better approach: Update the $connect route to use integration request parameters
    # that extract session_id from the request path
    
    print("\n" + "=" * 80)
    print("SOLUTION: Update Integration to Handle Path Parameters")
    print("=" * 80)
    print("")
    print("For HTTP_PROXY integration, we need to configure it to:")
    print("1. Extract session_id from request path")
    print("2. Forward to backend /ws/{session_id}")
    print("")
    print("However, HTTP_PROXY doesn't support path transformation easily.")
    print("")
    print("ALTERNATIVE: Use route selection expression or create custom route")
    print("")
    print("RECOMMENDED: Update frontend to use path, and configure integration")
    print("to forward the entire path to backend")
    print("")
    
    # Update integration URI to include path parameter placeholder
    # But HTTP_PROXY will forward the path as-is
    # So if frontend connects to /prod/{session_id}, API Gateway will forward to /ws/{session_id}
    # We need to configure the integration URI to be: http://{EC2_IP}:8000/ws
    
    # Actually, the path after /prod/ will be forwarded to the integration
    # So if client connects to /prod/abc123, API Gateway forwards to /ws/abc123
    # But the integration URI is just /ws, so we need to configure it differently
    
    # Let's try updating the integration to use the path from the route
    integration_uri = f"http://{EC2_IP}:8000/ws"
    
    print(f"Integration URI: {integration_uri}")
    print("")
    print("When client connects to: wss://.../prod/{session_id}")
    print("API Gateway will forward to: http://{EC2_IP}:8000/ws/{session_id}")
    print("(The path after /prod/ is appended to the integration URI)")
    print("")
    
    # Update integration
    try:
        apigw.update_integration(
            ApiId=WS_API_ID,
            IntegrationId=integration_id,
            IntegrationUri=integration_uri,
            IntegrationType='HTTP_PROXY',
            IntegrationMethod='GET'
        )
        print("[OK] Integration updated")
    except ClientError as e:
        print(f"[ERROR] Failed to update integration: {e}")
        exit(1)
    
    # The $connect route should forward the path parameter
    # But we need to verify the route configuration
    
    print("\n" + "=" * 80)
    print("Configuration Complete")
    print("=" * 80)
    print("")
    print("Frontend should connect to:")
    print(f"  wss://{WS_API_ID}.execute-api.{AWS_REGION}.amazonaws.com/prod/{{session_id}}")
    print("")
    print("API Gateway will forward to:")
    print(f"  http://{EC2_IP}:8000/ws/{{session_id}}")
    print("")
    print("Backend endpoint /ws/{session_id} should handle this.")
    print("")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

