#!/usr/bin/env python3
"""
Find the longest (largest) video file in S3 bucket.
"""
import boto3
import sys
from botocore.exceptions import ClientError, ProfileNotFound

# Video file extensions to look for
VIDEO_EXTENSIONS = ['.mp4', '.webm', '.mov', '.avi', '.mkv', '.flv', '.wmv']

def find_longest_video(bucket_name: str, profile_name: str = 'default1', region: str = 'us-east-1'):
    """
    Find the longest (largest) video file in the S3 bucket.
    
    Args:
        bucket_name: Name of the S3 bucket
        profile_name: AWS profile name to use
        region: AWS region
    """
    try:
        # Create a session with the specified profile
        session = boto3.Session(profile_name=profile_name)
        s3_client = session.client('s3', region_name=region)
        
        print(f"Searching for the longest video file in bucket: {bucket_name}")
        print(f"   Using AWS profile: {profile_name}")
        print(f"   Region: {region}\n")
        
        # List all objects in the bucket
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket_name)
        
        largest_video = None
        largest_size = 0
        
        for page in page_iterator:
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                key = obj['Key']
                
                # Check if it's a video file
                if any(key.lower().endswith(ext) for ext in VIDEO_EXTENSIONS):
                    size = obj['Size']
                    if size > largest_size:
                        largest_size = size
                        largest_video = {
                            'key': key,
                            'size': size,
                            'last_modified': obj['LastModified'],
                            'size_mb': size / (1024 * 1024),
                            'size_gb': size / (1024 * 1024 * 1024)
                        }
        
        if not largest_video:
            print("No video files found in the bucket.")
            return
        
        print("=" * 80)
        print("LONGEST VIDEO FILE FOUND:")
        print("=" * 80)
        print(f"\nPath: {largest_video['key']}")
        print(f"Size: {largest_video['size_mb']:.2f} MB ({largest_video['size']:,} bytes)")
        if largest_video['size_gb'] >= 1.0:
            print(f"      {largest_video['size_gb']:.2f} GB")
        print(f"Last Modified: {largest_video['last_modified'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Generate public URL
        url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{largest_video['key']}"
        print(f"\nURL: {url}")
        print("\n" + "=" * 80)
        
    except ProfileNotFound:
        print(f"Error: AWS profile '{profile_name}' not found.")
        print(f"   Make sure you have configured the profile with: aws configure --profile {profile_name}")
        sys.exit(1)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"Error: Bucket '{bucket_name}' does not exist.")
        elif error_code == 'AccessDenied':
            print(f"Error: Access denied to bucket '{bucket_name}'.")
            print(f"   Check your AWS credentials and permissions.")
        else:
            print(f"AWS Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    # Try to get bucket name from environment or use default
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    bucket_name = os.getenv('S3_BUCKET_NAME', 'pipeline-backend-assets')
    profile_name = 'default1'
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    # Allow bucket name to be passed as command line argument
    if len(sys.argv) > 1:
        bucket_name = sys.argv[1]
    
    find_longest_video(bucket_name, profile_name, region)

