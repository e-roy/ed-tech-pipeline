#!/usr/bin/env python3
"""
Add /scaffoldtest resource to API Gateway.
"""
import boto3
from botocore.exceptions import ClientError

AWS_PROFILE = 'default1'
AWS_REGION = 'us-east-2'
REST_API_ID = 'w8d3k51hg6'
EC2_IP = '13.58.115.166'

try:
    session = boto3.Session(profile_name=AWS_PROFILE)
    apigw = session.client('apigateway', region_name=AWS_REGION)
    
    print("=" * 80)
    print("Adding /scaffoldtest resource to API Gateway")
    print("=" * 80)
    
    # Get root resource
    resources = apigw.get_resources(restApiId=REST_API_ID)
    root_id = None
    for resource in resources['items']:
        if resource['path'] == '/':
            root_id = resource['id']
            break
    
    if not root_id:
        print("ERROR: Could not find root resource")
        exit(1)
    
    print(f"[OK] Found root resource: {root_id}")
    
    # Check if /scaffoldtest already exists
    scaffoldtest_id = None
    for resource in resources['items']:
        if resource['path'] == '/scaffoldtest':
            scaffoldtest_id = resource['id']
            print(f"[OK] /scaffoldtest resource already exists: {scaffoldtest_id}")
            break
    
    # Create /scaffoldtest resource if it doesn't exist
    if not scaffoldtest_id:
        print("[*] Creating /scaffoldtest resource...")
        scaffoldtest_resource = apigw.create_resource(
            restApiId=REST_API_ID,
            parentId=root_id,
            pathPart='scaffoldtest'
        )
        scaffoldtest_id = scaffoldtest_resource['id']
        print(f"[OK] /scaffoldtest resource created: {scaffoldtest_id}")
    
    # Check if GET method exists
    try:
        apigw.get_method(
            restApiId=REST_API_ID,
            resourceId=scaffoldtest_id,
            httpMethod='GET'
        )
        print("[OK] GET method already exists")
    except ClientError as e:
        if e.response['Error']['Code'] == 'NotFoundException':
            # Create GET method
            print("[*] Creating GET method...")
            apigw.put_method(
                restApiId=REST_API_ID,
                resourceId=scaffoldtest_id,
                httpMethod='GET',
                authorizationType='NONE'
            )
            print("[OK] GET method created")
            
            # Create integration
            print("[*] Creating HTTP integration...")
            integration_uri = f"http://{EC2_IP}:8000/scaffoldtest"
            apigw.put_integration(
                restApiId=REST_API_ID,
                resourceId=scaffoldtest_id,
                httpMethod='GET',
                type='HTTP_PROXY',
                integrationHttpMethod='GET',
                uri=integration_uri,
                connectionType='INTERNET'
            )
            print(f"[OK] Integration created: {integration_uri}")
            
            # Create method response
            apigw.put_method_response(
                restApiId=REST_API_ID,
                resourceId=scaffoldtest_id,
                httpMethod='GET',
                statusCode='200',
                responseParameters={
                    'method.response.header.Content-Type': True
                }
            )
            
            # Create integration response
            apigw.put_integration_response(
                restApiId=REST_API_ID,
                resourceId=scaffoldtest_id,
                httpMethod='GET',
                statusCode='200',
                responseParameters={
                    'method.response.header.Content-Type': "'text/html'"
                }
            )
        else:
            raise
    
    # Also add /health and / (root) for completeness
    for path_part in ['health', '']:
        if path_part == '':
            path_to_check = '/'
        else:
            path_to_check = f'/{path_part}'
        
        resource_id = None
        for resource in resources['items']:
            if resource['path'] == path_to_check:
                resource_id = resource['id']
                break
        
        if not resource_id and path_part != '':  # Don't recreate root
            print(f"[*] Creating {path_to_check} resource...")
            new_resource = apigw.create_resource(
                restApiId=REST_API_ID,
                parentId=root_id,
                pathPart=path_part
            )
            resource_id = new_resource['id']
            
            # Create GET method
            apigw.put_method(
                restApiId=REST_API_ID,
                resourceId=resource_id,
                httpMethod='GET',
                authorizationType='NONE'
            )
            
            # Create integration
            integration_uri = f"http://{EC2_IP}:8000{path_to_check}"
            apigw.put_integration(
                restApiId=REST_API_ID,
                resourceId=resource_id,
                httpMethod='GET',
                type='HTTP_PROXY',
                integrationHttpMethod='GET',
                uri=integration_uri,
                connectionType='INTERNET'
            )
            
            apigw.put_method_response(
                restApiId=REST_API_ID,
                resourceId=resource_id,
                httpMethod='GET',
                statusCode='200'
            )
            
            apigw.put_integration_response(
                restApiId=REST_API_ID,
                resourceId=resource_id,
                httpMethod='GET',
                statusCode='200'
            )
            print(f"[OK] {path_to_check} resource configured")
    
    # Redeploy API
    print("[*] Redeploying API to 'prod' stage...")
    apigw.create_deployment(
        restApiId=REST_API_ID,
        stageName='prod',
        description='Added /scaffoldtest endpoint'
    )
    print("[OK] API redeployed")
    
    print("")
    print("=" * 80)
    print("SUCCESS!")
    print("=" * 80)
    print("")
    print("You can now access:")
    print(f"  https://{REST_API_ID}.execute-api.us-east-2.amazonaws.com/prod/scaffoldtest")
    print("")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

