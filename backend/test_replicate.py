"""
Test script to verify Replicate API connection.
Person B - Hour 0-1: Environment Setup
"""
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_replicate_connection():
    """Test basic Replicate API call"""
    import replicate

    api_key = os.getenv("REPLICATE_API_KEY")
    if not api_key or api_key == "your-replicate-api-key-here":
        print("❌ REPLICATE_API_KEY not set in .env file")
        print("   Please add your API key to backend/.env")
        return False

    print("✅ REPLICATE_API_KEY found in environment")
    print(f"   Key prefix: {api_key[:8]}...")

    try:
        print("\n🔄 Testing Replicate API with Llama 3.1...")
        # Create client with API token
        client = replicate.Client(api_token=api_key)

        # Try with a known working model
        output = await client.async_run(
            "meta/meta-llama-3-70b-instruct",
            input={
                "prompt": "Say hello in exactly 3 words",
                "max_tokens": 10,
                "temperature": 0.7
            }
        )

        # Concatenate streaming output
        full_response = "".join([chunk for chunk in output])
        print(f"✅ Replicate API works!")
        print(f"   Response: {full_response.strip()}")
        return True

    except Exception as e:
        print(f"❌ Replicate API test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_replicate_connection())
    if success:
        print("\n✅ All tests passed! Ready to build agents.")
    else:
        print("\n❌ Setup incomplete. Fix errors above before continuing.")
