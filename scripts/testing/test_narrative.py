#!/usr/bin/env python3
"""Test script for the Narrative Builder endpoint."""

import requests
import json

url = "http://YOUR_SERVER_IP:8000/api/build-narrative"  # Replace with your EC2 IP or API Gateway URL
headers = {
    "Content-Type": "application/json",
    "X-User-Email": "demo@example.com"
}
data = {
    "topic": "Machine Learning Basics",
    "learning_objective": "Understand what machine learning is and how it works",
    "key_points": [
        "Computers learn from data",
        "Patterns are identified automatically",
        "Predictions improve over time"
    ]
}

print("🧪 Testing Narrative Builder endpoint...")
print(f"URL: {url}")
print(f"Data: {json.dumps(data, indent=2)}\n")

try:
    response = requests.post(url, headers=headers, json=data)

    print(f"Status Code: {response.status_code}")
    print(f"\nResponse:")

    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2))
        print(f"\n✅ SUCCESS!")
        print(f"Session ID: {result.get('session_id')}")
        print(f"Cost: ${result.get('cost')}")
        print(f"Duration: {result.get('duration')}s")
    else:
        print(response.text)
        print(f"\n❌ FAILED!")

except Exception as e:
    print(f"❌ ERROR: {e}")
