#!/usr/bin/env python3
"""Check Elastic IP status and find available ones."""
import boto3
from botocore.exceptions import ClientError, ProfileNotFound

REGION = 'us-east-2'
PROFILE = 'default1'
INSTANCE_ID = 'i-051a27d0f69e98ca2'

try:
    session = boto3.Session(profile_name=PROFILE)
    ec2_client = session.client('ec2', region_name=REGION)
    
    # Check instance current IP
    instance = ec2_client.describe_instances(InstanceIds=[INSTANCE_ID])
    current_ip = instance['Reservations'][0]['Instances'][0].get('PublicIpAddress')
    print(f"Current instance IP: {current_ip}")
    
    # Check if instance has Elastic IP
    addresses = ec2_client.describe_addresses(
        Filters=[{'Name': 'instance-id', 'Values': [INSTANCE_ID]}]
    )
    
    if addresses['Addresses']:
        elastic_ip = addresses['Addresses'][0]['PublicIp']
        print(f"Instance already has Elastic IP: {elastic_ip}")
    else:
        print("Instance does NOT have Elastic IP")
        
        # Check for unassociated Elastic IPs
        all_addresses = ec2_client.describe_addresses()
        unassociated = [addr for addr in all_addresses['Addresses'] if 'InstanceId' not in addr]
        
        if unassociated:
            print(f"\nFound {len(unassociated)} unassociated Elastic IP(s):")
            for addr in unassociated:
                print(f"  - {addr['PublicIp']} (Allocation ID: {addr['AllocationId']})")
            print("\nYou can associate one of these with the instance.")
        else:
            print("\nNo unassociated Elastic IPs found.")
            print("Options:")
            print("1. Release an unused Elastic IP from another region")
            print("2. Request limit increase from AWS")
            print("3. Use current dynamic IP (will change on restart)")
            
except Exception as e:
    print(f"Error: {e}")

