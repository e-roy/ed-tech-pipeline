#!/usr/bin/env python3
"""Associate Elastic IP with instance - try different approaches."""
import boto3
from botocore.exceptions import ClientError

REGION = 'us-east-2'
PROFILE = 'default1'
INSTANCE_ID = 'i-051a27d0f69e98ca2'

try:
    session = boto3.Session(profile_name=PROFILE)
    ec2_client = session.client('ec2', region_name=REGION)
    
    # Get instance details
    instance = ec2_client.describe_instances(InstanceIds=[INSTANCE_ID])
    instance_data = instance['Reservations'][0]['Instances'][0]
    private_ip = instance_data['PrivateIpAddress']
    current_public_ip = instance_data.get('PublicIpAddress')
    
    print(f"Instance: {INSTANCE_ID}")
    print(f"Current Public IP: {current_public_ip}")
    print(f"Private IP: {private_ip}")
    
    # Get unassociated Elastic IPs in us-east-2
    all_addresses = ec2_client.describe_addresses()
    unassociated = []
    for addr in all_addresses['Addresses']:
        if 'InstanceId' not in addr:
            # Check if it's in us-east-2 (check by availability zone or just try)
            unassociated.append(addr)
    
    if not unassociated:
        print("\nNo unassociated Elastic IPs found in us-east-2")
        print("Proceeding with API Gateway setup using current dynamic IP")
        print("WARNING: IP will change on instance restart")
        return current_public_ip
    
    # Try to associate first available
    elastic_ip_obj = unassociated[0]
    allocation_id = elastic_ip_obj['AllocationId']
    elastic_ip = elastic_ip_obj['PublicIp']
    
    print(f"\nAttempting to associate Elastic IP: {elastic_ip}")
    print(f"Allocation ID: {allocation_id}")
    
    # Try without specifying private IP
    try:
        ec2_client.associate_address(
            InstanceId=INSTANCE_ID,
            AllocationId=allocation_id
        )
        print(f"[OK] Elastic IP {elastic_ip} associated successfully")
        return elastic_ip
    except ClientError as e:
        print(f"[ERROR] Failed to associate: {e}")
        print("\nProceeding with current dynamic IP for API Gateway setup")
        print("NOTE: You may need to manually associate Elastic IP via AWS Console")
        return current_public_ip
        
except Exception as e:
    print(f"Error: {e}")
    return None

if __name__ == '__main__':
    associate_elastic_ip()

