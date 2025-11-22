#!/usr/bin/env python3
"""
Fix ACL on existing S3 objects to make them publicly readable.
Run this to update objects uploaded before ACL='public-read' was added.
"""

import boto3
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
    exit(1)

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

def list_all_objects():
    """List all objects in the bucket"""
    objects = []
    paginator = s3_client.get_paginator('list_objects_v2')

    for page in paginator.paginate(Bucket=S3_BUCKET_NAME):
        if 'Contents' in page:
            objects.extend(page['Contents'])

    return objects

def set_public_acl(key):
    """Set public-read ACL on an object"""
    try:
        s3_client.put_object_acl(
            Bucket=S3_BUCKET_NAME,
            Key=key,
            ACL='public-read'
        )
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

# Main execution
print(f"🔍 Scanning bucket: {S3_BUCKET_NAME}\n")

objects = list_all_objects()

if not objects:
    print("📭 No objects found in bucket")
    exit(0)

print(f"Found {len(objects)} objects\n")
print("🔧 Setting public-read ACL on all objects...\n")

success_count = 0
fail_count = 0

for obj in objects:
    key = obj['Key']
    size_mb = obj['Size'] / (1024 * 1024)

    print(f"Processing: {key} ({size_mb:.2f} MB)")

    if set_public_acl(key):
        success_count += 1
        print(f"   ✅ Now public")
    else:
        fail_count += 1

print(f"\n{'='*60}")
print(f"✅ Success: {success_count}/{len(objects)}")

if fail_count > 0:
    print(f"❌ Failed: {fail_count}/{len(objects)}")

print(f"\n📝 All objects should now be accessible via direct URLs:")
print(f"   https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/<object-key>")
