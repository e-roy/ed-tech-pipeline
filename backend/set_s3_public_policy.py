#!/usr/bin/env python3
"""
Set S3 bucket policy to allow public read access.
Run this once to configure your bucket for public access.
"""

import boto3
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from environment
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-2')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME]):
    print("❌ Missing AWS credentials in .env file")
    print("Required: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME")
    exit(1)

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# Define bucket policy for public read access
bucket_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{S3_BUCKET_NAME}/*"
        }
    ]
}

try:
    # Set the bucket policy
    print(f"🔧 Setting public read policy on bucket: {S3_BUCKET_NAME}")

    s3_client.put_bucket_policy(
        Bucket=S3_BUCKET_NAME,
        Policy=json.dumps(bucket_policy)
    )

    print(f"✅ Bucket policy successfully set!")
    print(f"   All objects in {S3_BUCKET_NAME} are now publicly readable")
    print(f"   Direct URLs will work: https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/path/to/file")

    # Verify the policy was set
    print("\n📋 Current bucket policy:")
    response = s3_client.get_bucket_policy(Bucket=S3_BUCKET_NAME)
    policy = json.loads(response['Policy'])
    print(json.dumps(policy, indent=2))

except Exception as e:
    print(f"❌ Failed to set bucket policy: {e}")
    print("\nMake sure:")
    print("1. You disabled 'Block all public access' in S3 console")
    print("2. Your IAM user has s3:PutBucketPolicy permission")
    print("3. The bucket name is correct")
    exit(1)
