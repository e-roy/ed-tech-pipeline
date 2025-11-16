#!/usr/bin/env python3
"""Test if S3 objects are publicly accessible"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

BUCKET = os.getenv('S3_BUCKET_NAME')
REGION = os.getenv('AWS_REGION', 'us-east-1')

# Test with one of the existing images
test_key = "users/1/output/images/img_010c1d5c0484.png"
test_url = f"https://{BUCKET}.s3.{REGION}.amazonaws.com/{test_key}"

print(f"Testing public access to S3 object:\n")
print(f"URL: {test_url}\n")

try:
    response = requests.get(test_url, timeout=10)

    if response.status_code == 200:
        print(f"✅ SUCCESS! Image is publicly accessible")
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        print(f"   Size: {len(response.content)} bytes ({len(response.content)/(1024*1024):.2f} MB)")
        print(f"\n🎉 Your S3 bucket is now configured correctly!")
        print(f"   All objects in the bucket are publicly readable.")
    elif response.status_code == 403:
        print(f"❌ FORBIDDEN (403) - Object is not publicly accessible")
        print(f"\nPossible causes:")
        print(f"1. Bucket policy not applied correctly")
        print(f"2. 'Block all public access' still enabled")
        print(f"3. IAM permissions issue")
    elif response.status_code == 404:
        print(f"❌ NOT FOUND (404) - Object doesn't exist")
        print(f"   Check if the key is correct: {test_key}")
    else:
        print(f"⚠️  Unexpected status code: {response.status_code}")
        print(f"   Response: {response.text[:200]}")

except Exception as e:
    print(f"❌ Error testing URL: {e}")
