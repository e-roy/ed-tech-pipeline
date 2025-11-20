#!/usr/bin/env python3
"""
Check AWS resources to answer clarifying questions for API Gateway plan.
Uses AWS profile 'default1' to query resources.
"""
import boto3
import sys
from botocore.exceptions import ClientError, ProfileNotFound
from datetime import datetime

def check_ec2_instance(profile_name: str = 'default1'):
    """Check EC2 instance details, including Elastic IP."""
    print("=" * 80)
    print("1. EC2 INSTANCE DETAILS")
    print("=" * 80)
    
    try:
        session = boto3.Session(profile_name=profile_name)
        ec2_client = session.client('ec2', region_name='us-east-1')
        
        # Find instance by IP
        target_ip = "13.58.115.166"
        
        # Get all instances
        response = ec2_client.describe_instances()
        
        found_instance = None
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if instance.get('State', {}).get('Name') == 'running':
                    public_ip = instance.get('PublicIpAddress')
                    if public_ip == target_ip:
                        found_instance = instance
                        break
                if found_instance:
                    break
        
        if not found_instance:
            print(f"[!] Instance with IP {target_ip} not found in us-east-1")
            print("   Checking other regions...")
            
            # Check us-east-2
            ec2_client_2 = session.client('ec2', region_name='us-east-2')
            response = ec2_client_2.describe_instances()
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    if instance.get('State', {}).get('Name') == 'running':
                        public_ip = instance.get('PublicIpAddress')
                        if public_ip == target_ip:
                            found_instance = instance
                            print(f"   [OK] Found in us-east-2")
                            break
                    if found_instance:
                        break
        
        if found_instance:
            instance_id = found_instance['InstanceId']
            print(f"\n[OK] Found EC2 Instance:")
            print(f"   Instance ID: {instance_id}")
            print(f"   Public IP: {found_instance.get('PublicIpAddress', 'N/A')}")
            print(f"   Private IP: {found_instance.get('PrivateIpAddress', 'N/A')}")
            print(f"   State: {found_instance.get('State', {}).get('Name', 'N/A')}")
            print(f"   Instance Type: {found_instance.get('InstanceType', 'N/A')}")
            print(f"   Region: {found_instance.get('Placement', {}).get('AvailabilityZone', 'N/A')[:-1]}")
            
            # Check for Elastic IP
            region = found_instance.get('Placement', {}).get('AvailabilityZone', 'us-east-1a')[:-1]
            ec2_client_region = session.client('ec2', region_name=region)
            
            addresses = ec2_client_region.describe_addresses()
            elastic_ip_found = False
            for address in addresses.get('Addresses', []):
                if address.get('InstanceId') == instance_id:
                    print(f"\n   [OK] ELASTIC IP ASSOCIATED:")
                    print(f"      Elastic IP: {address.get('PublicIp')}")
                    print(f"      Allocation ID: {address.get('AllocationId')}")
                    elastic_ip_found = True
                    break
            
            if not elastic_ip_found:
                print(f"\n   [!] NO ELASTIC IP FOUND")
                print(f"      IP address may change on instance restart")
                print(f"      Recommendation: Allocate and associate Elastic IP")
            
            # Check security groups
            print(f"\n   Security Groups:")
            for sg in found_instance.get('SecurityGroups', []):
                sg_id = sg['GroupId']
                sg_name = sg['GroupName']
                print(f"      - {sg_name} ({sg_id})")
                
                # Get security group rules
                sg_details = ec2_client_region.describe_security_groups(GroupIds=[sg_id])
                if sg_details['SecurityGroups']:
                    sg_rules = sg_details['SecurityGroups'][0]
                    print(f"        Inbound Rules:")
                    for rule in sg_rules.get('IpPermissions', []):
                        from_port = rule.get('FromPort', 'N/A')
                        to_port = rule.get('ToPort', 'N/A')
                        protocol = rule.get('IpProtocol', 'N/A')
                        for ip_range in rule.get('IpRanges', []):
                            cidr = ip_range.get('CidrIp', 'N/A')
                            print(f"          {protocol} {from_port}-{to_port} from {cidr}")
        else:
            print(f"[ERROR] Could not find instance with IP {target_ip}")
            print("   Please verify the IP address is correct")
            
    except ProfileNotFound:
        print(f"[ERROR] Error: AWS profile '{profile_name}' not found.")
        sys.exit(1)
    except ClientError as e:
        print(f"[ERROR] AWS Error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

def check_s3_bucket(profile_name: str = 'default1'):
    """Check S3 bucket details and data."""
    print("\n" + "=" * 80)
    print("2. S3 BUCKET DETAILS")
    print("=" * 80)
    
    bucket_name = "pipeline-backend-assets"
    
    try:
        session = boto3.Session(profile_name=profile_name)
        
        # Check both regions
        for region in ['us-east-1', 'us-east-2']:
            try:
                s3_client = session.client('s3', region_name=region)
                
                # Get bucket location
                try:
                    location = s3_client.get_bucket_location(Bucket=bucket_name)
                    bucket_region = location.get('LocationConstraint') or 'us-east-1'
                    
                    if bucket_region == region or (bucket_region == '' and region == 'us-east-1'):
                        print(f"\n[OK] Bucket found in region: {bucket_region or 'us-east-1'}")
                        
                        # Get bucket size and object count
                        paginator = s3_client.get_paginator('list_objects_v2')
                        total_size = 0
                        total_objects = 0
                        
                        for page in paginator.paginate(Bucket=bucket_name):
                            if 'Contents' in page:
                                for obj in page['Contents']:
                                    total_size += obj['Size']
                                    total_objects += 1
                        
                        size_mb = total_size / (1024 * 1024)
                        size_gb = total_size / (1024 * 1024 * 1024)
                        
                        print(f"   Total Objects: {total_objects:,}")
                        if size_gb >= 1:
                            print(f"   Total Size: {size_gb:.2f} GB ({size_mb:.2f} MB)")
                        else:
                            print(f"   Total Size: {size_mb:.2f} MB")
                        
                        # Check if migration is needed
                        if bucket_region != 'us-east-2':
                            print(f"\n   [!] MIGRATION NEEDED:")
                            print(f"      Current region: {bucket_region or 'us-east-1'}")
                            print(f"      Target region: us-east-2")
                            print(f"      Data size: {size_mb:.2f} MB")
                            if size_mb < 100:
                                print(f"      Priority: LOW (small amount of data)")
                            elif size_mb < 1000:
                                print(f"      Priority: MEDIUM")
                            else:
                                print(f"      Priority: HIGH (large amount of data)")
                        else:
                            print(f"\n   [OK] Already in us-east-2")
                        
                        break
                except ClientError as e:
                    if e.response['Error']['Code'] != 'NoSuchBucket':
                        raise
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchBucket':
                    continue
                else:
                    raise
        else:
            print(f"[ERROR] Bucket '{bucket_name}' not found in us-east-1 or us-east-2")
            
    except ProfileNotFound:
        print(f"[ERROR] Error: AWS profile '{profile_name}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error: {e}")

def check_api_gateways(profile_name: str = 'default1'):
    """Check existing API Gateway resources in us-east-2."""
    print("\n" + "=" * 80)
    print("3. API GATEWAY RESOURCES (us-east-2)")
    print("=" * 80)
    
    try:
        session = boto3.Session(profile_name=profile_name)
        apigw_client = session.client('apigateway', region_name='us-east-2')
        
        # Check REST APIs
        rest_apis = apigw_client.get_rest_apis()
        rest_count = len(rest_apis.get('items', []))
        print(f"\n[REST APIs] Count: {rest_count}")
        
        if rest_count > 0:
            print("   Existing REST APIs:")
            for api in rest_apis.get('items', [])[:10]:  # Show first 10
                print(f"      - {api['name']} (ID: {api['id']})")
            if rest_count > 10:
                print(f"      ... and {rest_count - 10} more")
        
        # Check WebSocket APIs (different API for WebSocket)
        # Note: WebSocket APIs use v2 API which requires different SDK calls
        # For now, we'll note that they need to be checked manually
        ws_count = 0  # Placeholder - WebSocket APIs need different API call
        print(f"\n[WebSocket APIs] Count: {ws_count} (check AWS Console manually)")
        print(f"   Note: WebSocket APIs use v2 API and require different SDK calls")
        
        if rest_count > 0 or ws_count > 0:
            print(f"\n   [!] Found {rest_count + ws_count} existing API Gateway(s)")
            print(f"      These may need to be cleaned up or reused")
        else:
            print(f"\n   [OK] No existing API Gateways in us-east-2")
            print(f"      Clean slate for new deployment")
            
    except ProfileNotFound:
        print(f"[ERROR] Error: AWS profile '{profile_name}' not found.")
        sys.exit(1)
    except ClientError as e:
        if e.response['Error']['Code'] == 'AccessDenied':
            print(f"[!] Access denied to API Gateway. May need additional permissions.")
        else:
            print(f"[ERROR] AWS Error: {e}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")

def check_vpc_endpoints(profile_name: str = 'default1'):
    """Check VPC endpoints for API Gateway (for private integration option)."""
    print("\n" + "=" * 80)
    print("4. VPC ENDPOINTS (for API Gateway private integration)")
    print("=" * 80)
    
    try:
        session = boto3.Session(profile_name=profile_name)
        ec2_client = session.client('ec2', region_name='us-east-2')
        
        endpoints = ec2_client.describe_vpc_endpoints()
        api_gateway_endpoints = [
            ep for ep in endpoints.get('VpcEndpoints', [])
            if 'execute-api' in ep.get('ServiceName', '')
        ]
        
        if api_gateway_endpoints:
            print(f"\n[OK] Found {len(api_gateway_endpoints)} API Gateway VPC endpoint(s):")
            for ep in api_gateway_endpoints:
                print(f"   - {ep['VpcEndpointId']} ({ep.get('State', 'N/A')})")
            print(f"\n   💡 Can use private integration (more secure)")
        else:
            print(f"\n   [!] No API Gateway VPC endpoints found")
            print(f"      Will need to use public integration (0.0.0.0/0)")
            
    except ProfileNotFound:
        print(f"[ERROR] Error: AWS profile '{profile_name}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error: {e}")

def main():
    """Run all checks."""
    profile_name = 'default1'
    
    print("\n" + "=" * 80)
    print("AWS RESOURCE CHECK FOR API GATEWAY PLAN")
    print(f"Using AWS Profile: {profile_name}")
    print("=" * 80)
    
    check_ec2_instance(profile_name)
    check_s3_bucket(profile_name)
    check_api_gateways(profile_name)
    check_vpc_endpoints(profile_name)
    
    print("\n" + "=" * 80)
    print("SUMMARY & RECOMMENDATIONS")
    print("=" * 80)
    print("\nBased on the checks above:")
    print("1. Review EC2 Elastic IP status - allocate if needed")
    print("2. Review S3 migration priority based on data size")
    print("3. Decide on security group approach (public vs private)")
    print("4. Check if existing API Gateways should be reused or cleaned up")
    print("\n")

if __name__ == '__main__':
    main()

