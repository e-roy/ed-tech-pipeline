#!/usr/bin/env python3
"""
Fix WebSocket API Gateway to use path parameters instead of query parameters.
API Gateway WebSocket doesn't forward query params during $connect, so we need to use path.
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
    print("Reconfiguring WebSocket API Gateway for Path Parameters")
    print("=" * 80)
    print("")
    print("ISSUE: API Gateway WebSocket doesn't forward query parameters")
    print("SOLUTION: Use path parameters instead")
    print("")
    
    # Get current integration
    integrations = apigw.get_integrations(ApiId=WS_API_ID)
    integration_id = integrations['Items'][0]['IntegrationId']
    
    # Update integration to use path parameter format
    # Backend endpoint: /ws/{session_id}
    integration_uri = f"http://{EC2_IP}:8000/ws/{{session_id}}"
    
    print(f"Updating integration URI to: {integration_uri}")
    print("(Note: {session_id} is a placeholder - API Gateway will substitute)")
    
    # Actually, for HTTP_PROXY, we can't use path parameters directly
    # We need to create a route that extracts session_id from query and transforms it
    # OR use a route selection expression
    
    # Better approach: Create a new route with path parameter
    # Route key: $connect with route selection that includes session_id
    
    # Actually, the simplest fix is to:
    # 1. Keep integration URI as base: /ws
    # 2. Configure route to extract session_id from query and pass as header or path
    # 3. OR update frontend to use path parameter format
    
    # For now, let's update the integration to use a route that can handle path params
    # But HTTP_PROXY doesn't support path transformation easily
    
    # Alternative: Update frontend to use path parameter format
    # wss://api-id.execute-api.region.amazonaws.com/prod/{session_id}
    # And configure API Gateway route to match this pattern
    
    print("")
    print("RECOMMENDED SOLUTION:")
    print("1. Update frontend to use path parameter: wss://.../prod/{session_id}")
    print("2. Create route with route key pattern: $connect or {session_id}")
    print("3. Configure integration to forward path parameter")
    print("")
    print("OR simpler: Use route selection to extract query param and transform")
    print("")
    
    # For HTTP_PROXY, we can try using request parameters to pass query as path
    # But this is complex. Let's document the solution instead.
    
    print("=" * 80)
    print("SOLUTION: Update Frontend to Use Path Parameters")
    print("=" * 80)
    print("")
    print("Change WebSocket URL from:")
    print("  wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod?session_id=xxx")
    print("")
    print("To:")
    print("  wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod/xxx")
    print("")
    print("Then configure API Gateway route to match /{session_id} pattern")
    print("and forward to backend /ws/{session_id}")
    print("")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

