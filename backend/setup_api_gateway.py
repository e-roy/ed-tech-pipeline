#!/usr/bin/env python3
"""
Automated API Gateway Setup Script
Uses AWS profile 'default1' to set up REST and WebSocket API Gateways.
"""
import boto3
import sys
import json
import time
from botocore.exceptions import ClientError, ProfileNotFound

REGION = 'us-east-2'
PROFILE = 'default1'
INSTANCE_ID = 'i-051a27d0f69e98ca2'
REST_API_NAME = 'pipeline-backend-api'
WS_API_NAME = 'pipeline-backend-websocket'

def get_elastic_ip():
    """Get or allocate Elastic IP for EC2 instance."""
    print("=" * 80)
    print("STEP 1: Elastic IP Allocation")
    print("=" * 80)
    
    try:
        session = boto3.Session(profile_name=PROFILE)
        ec2_client = session.client('ec2', region_name=REGION)
        
        # Check if instance already has Elastic IP
        response = ec2_client.describe_addresses(
            Filters=[{'Name': 'instance-id', 'Values': [INSTANCE_ID]}]
        )
        
        if response['Addresses']:
            elastic_ip = response['Addresses'][0]['PublicIp']
            allocation_id = response['Addresses'][0]['AllocationId']
            print(f"[OK] Instance already has Elastic IP: {elastic_ip}")
            print(f"     Allocation ID: {allocation_id}")
            return elastic_ip
        
        # Get instance details
        instance = ec2_client.describe_instances(InstanceIds=[INSTANCE_ID])
        instance_data = instance['Reservations'][0]['Instances'][0]
        private_ip = instance_data['PrivateIpAddress']
        current_ip = instance_data.get('PublicIpAddress', '13.58.115.166')
        
        # Check for unassociated Elastic IPs first
        all_addresses = ec2_client.describe_addresses()
        unassociated = [addr for addr in all_addresses['Addresses'] if 'InstanceId' not in addr]
        
        if unassociated:
            # Use first unassociated Elastic IP
            allocation_id = unassociated[0]['AllocationId']
            elastic_ip = unassociated[0]['PublicIp']
            print(f"[OK] Found unassociated Elastic IP: {elastic_ip}")
            print(f"     Allocation ID: {allocation_id}")
            
            # Try to associate
            print(f"[*] Associating Elastic IP with instance...")
            try:
                ec2_client.associate_address(
                    InstanceId=INSTANCE_ID,
                    AllocationId=allocation_id
                )
                print(f"[OK] Elastic IP {elastic_ip} associated with instance {INSTANCE_ID}")
                return elastic_ip
            except ClientError as e:
                print(f"[WARNING] Could not associate Elastic IP: {e}")
                print(f"         This may require manual association via AWS Console")
                print(f"         Proceeding with current IP for API Gateway setup")
        else:
            print(f"[WARNING] No unassociated Elastic IPs found")
            print(f"         Elastic IP limit reached - cannot allocate new one")
        
        # Use current IP (will work but may change on restart)
        print(f"[*] Using current instance IP: {current_ip}")
        print(f"[WARNING] This IP may change on instance restart")
        print(f"         API Gateway integration will need to be updated if IP changes")
        return current_ip
        
    except ProfileNotFound:
        print(f"[ERROR] AWS profile '{PROFILE}' not found.")
        sys.exit(1)
    except ClientError as e:
        print(f"[ERROR] AWS Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        sys.exit(1)

def create_rest_api(elastic_ip):
    """Create REST API Gateway."""
    print("\n" + "=" * 80)
    print("STEP 2: Create REST API Gateway")
    print("=" * 80)
    
    try:
        session = boto3.Session(profile_name=PROFILE)
        apigw_client = session.client('apigateway', region_name=REGION)
        
        # Check if API already exists
        apis = apigw_client.get_rest_apis()
        for api in apis.get('items', []):
            if api['name'] == REST_API_NAME:
                api_id = api['id']
                print(f"[OK] REST API already exists: {api_id}")
                print(f"     Name: {REST_API_NAME}")
                return api_id
        
        # Create REST API
        print(f"[*] Creating REST API: {REST_API_NAME}...")
        api = apigw_client.create_rest_api(
            name=REST_API_NAME,
            description='Pipeline Backend REST API for HTTPS access',
            endpointConfiguration={'types': ['REGIONAL']}
        )
        api_id = api['id']
        print(f"[OK] REST API created: {api_id}")
        
        # Get root resource
        resources = apigw_client.get_resources(restApiId=api_id)
        root_id = resources['items'][0]['id']
        
        # Create /api resource
        print(f"[*] Creating /api resource...")
        api_resource = apigw_client.create_resource(
            restApiId=api_id,
            parentId=root_id,
            pathPart='api'
        )
        api_resource_id = api_resource['id']
        print(f"[OK] /api resource created: {api_resource_id}")
        
        # Create {proxy+} resource
        print(f"[*] Creating /api/{{proxy+}} resource...")
        proxy_resource = apigw_client.create_resource(
            restApiId=api_id,
            parentId=api_resource_id,
            pathPart='{proxy+}'
        )
        proxy_resource_id = proxy_resource['id']
        print(f"[OK] /api/{{proxy+}} resource created: {proxy_resource_id}")
        
        # Create ANY method
        print(f"[*] Creating ANY method...")
        integration_url = f"http://{elastic_ip}:8000/{{proxy}}"
        apigw_client.put_method(
            restApiId=api_id,
            resourceId=proxy_resource_id,
            httpMethod='ANY',
            authorizationType='NONE'
        )
        
        # Create integration
        print(f"[*] Creating HTTP integration...")
        apigw_client.put_integration(
            restApiId=api_id,
            resourceId=proxy_resource_id,
            httpMethod='ANY',
            type='HTTP_PROXY',
            integrationHttpMethod='ANY',
            uri=integration_url,
            connectionType='INTERNET'
        )
        
        # Create method response
        apigw_client.put_method_response(
            restApiId=api_id,
            resourceId=proxy_resource_id,
            httpMethod='ANY',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Origin': True
            }
        )
        
        # Create integration response
        apigw_client.put_integration_response(
            restApiId=api_id,
            resourceId=proxy_resource_id,
            httpMethod='ANY',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Origin': "'*'"
            }
        )
        
        print(f"[OK] Method and integration configured")
        
        # Deploy API
        print(f"[*] Deploying API to 'prod' stage...")
        deployment = apigw_client.create_deployment(
            restApiId=api_id,
            stageName='prod',
            description='Production deployment'
        )
        print(f"[OK] API deployed to 'prod' stage")
        
        rest_url = f"https://{api_id}.execute-api.{REGION}.amazonaws.com/prod"
        print(f"\n[SUCCESS] REST API Gateway URL: {rest_url}")
        
        return api_id
        
    except ClientError as e:
        print(f"[ERROR] AWS Error: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return None

def create_websocket_api(elastic_ip):
    """Create WebSocket API Gateway."""
    print("\n" + "=" * 80)
    print("STEP 3: Create WebSocket API Gateway")
    print("=" * 80)
    
    try:
        session = boto3.Session(profile_name=PROFILE)
        # WebSocket APIs use v2 API
        apigwv2_client = session.client('apigatewayv2', region_name=REGION)
        
        # Check if API already exists
        apis = apigwv2_client.get_apis()
        for api in apis.get('Items', []):
            if api['Name'] == WS_API_NAME:
                api_id = api['ApiId']
                print(f"[OK] WebSocket API already exists: {api_id}")
                print(f"     Name: {WS_API_NAME}")
                return api_id
        
        # Create WebSocket API
        print(f"[*] Creating WebSocket API: {WS_API_NAME}...")
        api = apigwv2_client.create_api(
            Name=WS_API_NAME,
            ProtocolType='WEBSOCKET',
            RouteSelectionExpression='$request.body.action',
            Description='Pipeline Backend WebSocket API for real-time updates'
        )
        api_id = api['ApiId']
        print(f"[OK] WebSocket API created: {api_id}")
        
        # Create integration
        integration_uri = f"http://{elastic_ip}:8000/ws?session_id=$request.querystring.session_id"
        print(f"[*] Creating HTTP integration...")
        integration = apigwv2_client.create_integration(
            ApiId=api_id,
            IntegrationType='HTTP_PROXY',
            IntegrationUri=integration_uri,
            IntegrationMethod='GET'
        )
        integration_id = integration['IntegrationId']
        print(f"[OK] Integration created: {integration_id}")
        
        # Create $connect route
        print(f"[*] Creating $connect route...")
        connect_route = apigwv2_client.create_route(
            ApiId=api_id,
            RouteKey='$connect',
            Target=f"integrations/{integration_id}"
        )
        print(f"[OK] $connect route created")
        
        # Create $disconnect route
        print(f"[*] Creating $disconnect route...")
        disconnect_route = apigwv2_client.create_route(
            ApiId=api_id,
            RouteKey='$disconnect',
            Target=f"integrations/{integration_id}"
        )
        print(f"[OK] $disconnect route created")
        
        # Create $default route
        print(f"[*] Creating $default route...")
        default_route = apigwv2_client.create_route(
            ApiId=api_id,
            RouteKey='$default',
            Target=f"integrations/{integration_id}"
        )
        print(f"[OK] $default route created")
        
        # Create stage
        print(f"[*] Creating 'prod' stage...")
        stage = apigwv2_client.create_stage(
            ApiId=api_id,
            StageName='prod',
            Description='Production stage',
            AutoDeploy=True
        )
        print(f"[OK] Stage 'prod' created")
        
        ws_url = f"wss://{api_id}.execute-api.{REGION}.amazonaws.com/prod"
        print(f"\n[SUCCESS] WebSocket API Gateway URL: {ws_url}")
        
        return api_id
        
    except ClientError as e:
        print(f"[ERROR] AWS Error: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return None

def main():
    """Main execution."""
    print("\n" + "=" * 80)
    print("API GATEWAY SETUP - AUTOMATED IMPLEMENTATION")
    print(f"Using AWS Profile: {PROFILE}")
    print(f"Region: {REGION}")
    print("=" * 80)
    
    # Step 1: Elastic IP
    elastic_ip = get_elastic_ip()
    if not elastic_ip:
        print("[ERROR] Failed to get Elastic IP. Exiting.")
        sys.exit(1)
    
    # Step 2: REST API Gateway
    rest_api_id = create_rest_api(elastic_ip)
    
    # Step 3: WebSocket API Gateway
    ws_api_id = create_websocket_api(elastic_ip)
    
    # Summary
    print("\n" + "=" * 80)
    print("SETUP SUMMARY")
    print("=" * 80)
    print(f"\nElastic IP: {elastic_ip}")
    if rest_api_id:
        rest_url = f"https://{rest_api_id}.execute-api.{REGION}.amazonaws.com/prod"
        print(f"REST API URL: {rest_url}")
    if ws_api_id:
        ws_url = f"wss://{ws_api_id}.execute-api.{REGION}.amazonaws.com/prod"
        print(f"WebSocket API URL: {ws_url}")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("\n1. Update Vercel environment variables:")
    if rest_api_id:
        print(f"   NEXT_PUBLIC_API_URL={rest_url}")
    if ws_api_id:
        print(f"   NEXT_PUBLIC_WS_URL={ws_url}")
    print("\n2. Update backend .env on EC2:")
    print(f"   FRONTEND_URL=https://pipeline-q3b1.vercel.app")
    print("\n3. Deploy backend code changes (WebSocket query param support)")
    print("\n4. Test endpoints through API Gateway")
    print("\n5. Document URLs in backend/API_GATEWAY_URLS.md")
    print("\n")

if __name__ == '__main__':
    main()

