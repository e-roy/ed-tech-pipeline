"""
Test Script for Person B Agents
Image Pipeline: Prompt Parser + Batch Image Generator

This script tests the complete image generation pipeline independently
of the full application stack.
"""

import os
import asyncio
import json
from dotenv import load_dotenv

from app.agents.base import AgentInput
from app.agents.prompt_parser import PromptParserAgent
from app.agents.batch_image_generator import BatchImageGeneratorAgent

# Load environment variables
load_dotenv()


async def test_prompt_parser():
    """Test the Prompt Parser Agent"""
    print("\n" + "=" * 60)
    print("TEST 1: Prompt Parser Agent")
    print("=" * 60)

    api_key = os.getenv("REPLICATE_API_KEY")
    if not api_key or api_key == "your-replicate-api-key-here":
        print("❌ REPLICATE_API_KEY not set in .env file")
        return None

    try:
        agent = PromptParserAgent(api_key)

        # Test input
        test_input = AgentInput(
            session_id="test-session-001",
            data={
                "user_prompt": "pink tennis shoes with white laces",
                "options": {
                    "num_images": 4,  # Reduced for testing
                    "style_keywords": ["professional", "studio"]
                }
            }
        )

        print(f"\n📝 Input Prompt: '{test_input.data['user_prompt']}'")
        print(f"📊 Requested Images: {test_input.data['options']['num_images']}")
        print(f"\n⏳ Calling Prompt Parser Agent...")

        result = await agent.process(test_input)

        if result.success:
            print(f"\n✅ Prompt Parser Success!")
            print(f"   Duration: {result.duration:.2f}s")
            print(f"   Cost: ${result.cost:.4f}")
            print(f"   Consistency Seed: {result.data['consistency_seed']}")
            print(f"   Product Category: {result.data['product_category']}")
            print(f"   Style Keywords: {', '.join(result.data['style_keywords'])}")
            print(f"   Generated Prompts: {len(result.data['image_prompts'])}")

            print("\n📋 Prompt Details:")
            for i, prompt in enumerate(result.data['image_prompts'][:2], 1):  # Show first 2
                print(f"\n   Prompt {i} ({prompt['view_type']}):")
                print(f"   {prompt['prompt'][:100]}...")
                print(f"   Negative: {prompt['negative_prompt'][:50]}...")

            return result.data
        else:
            print(f"\n❌ Prompt Parser Failed: {result.error}")
            return None

    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_batch_image_generator(prompt_parser_output=None):
    """Test the Batch Image Generator Agent"""
    print("\n" + "=" * 60)
    print("TEST 2: Batch Image Generator Agent")
    print("=" * 60)

    api_key = os.getenv("REPLICATE_API_KEY")
    if not api_key:
        print("❌ REPLICATE_API_KEY not set")
        return False

    try:
        agent = BatchImageGeneratorAgent(api_key)

        # Use output from prompt parser or create test data
        if prompt_parser_output:
            image_prompts = prompt_parser_output["image_prompts"]
        else:
            # Fallback test data
            print("⚠️  Using fallback test data (Prompt Parser output not available)")
            image_prompts = [
                {
                    "prompt": "Professional product photography of pink athletic tennis shoes, front view, white background",
                    "negative_prompt": "blurry, distorted, low quality",
                    "view_type": "front",
                    "seed": 123456,
                    "guidance_scale": 7.5
                }
            ]

        # Test with flux-schnell (fastest/cheapest for testing)
        test_input = AgentInput(
            session_id="test-session-002",
            data={
                "image_prompts": image_prompts,
                "model": "flux-schnell"  # Fast model for testing
            }
        )

        print(f"\n🎨 Generating {len(image_prompts)} images with Flux-Schnell")
        print(f"⏳ This may take 30-60 seconds...")

        result = await agent.process(test_input)

        if result.success:
            print(f"\n✅ Image Generation Success!")
            print(f"   Duration: {result.duration:.2f}s")
            print(f"   Total Cost: ${result.cost:.4f}")
            print(f"   Images Generated: {len(result.data['images'])}")

            print("\n🖼️  Generated Images:")
            for i, img in enumerate(result.data['images'], 1):
                print(f"\n   Image {i} ({img['view_type']}):")
                print(f"   URL: {img['url']}")
                print(f"   Cost: ${img['cost']:.4f}")
                print(f"   Duration: {img['duration']:.2f}s")

            if result.data.get('errors'):
                print(f"\n⚠️  Some generations failed:")
                for error in result.data['errors']:
                    print(f"   - {error}")

            return True
        else:
            print(f"\n❌ Image Generation Failed: {result.error}")
            return False

    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_pipeline():
    """Test the complete pipeline: Prompt Parser → Image Generator"""
    print("\n" + "=" * 60)
    print("TEST 3: Full Image Generation Pipeline")
    print("=" * 60)

    # Test Prompt Parser
    prompt_result = await test_prompt_parser()

    if not prompt_result:
        print("\n❌ Pipeline test aborted - Prompt Parser failed")
        return False

    # Test Image Generator with Prompt Parser output
    image_result = await test_batch_image_generator(prompt_result)

    if image_result:
        print("\n" + "=" * 60)
        print("✅ FULL PIPELINE TEST PASSED!")
        print("=" * 60)
        print("\nPerson B Image Pipeline is ready for integration!")
        print("Next steps:")
        print("  1. Test with orchestrator via API endpoints")
        print("  2. Integrate with frontend")
        print("  3. Test end-to-end user flow")
        return True
    else:
        print("\n❌ Pipeline test failed at Image Generation stage")
        return False


async def quick_test():
    """Quick test - just verify agents can be imported and initialized"""
    print("\n" + "=" * 60)
    print("QUICK TEST: Agent Initialization")
    print("=" * 60)

    api_key = os.getenv("REPLICATE_API_KEY")
    if not api_key or api_key == "your-replicate-api-key-here":
        print("❌ REPLICATE_API_KEY not set in .env file")
        return False

    try:
        print("\n✅ Initializing Prompt Parser Agent...")
        parser = PromptParserAgent(api_key)
        print(f"   Model: {parser.model}")

        print("\n✅ Initializing Batch Image Generator Agent...")
        generator = BatchImageGeneratorAgent(api_key)
        print(f"   Available models: {list(generator.models.keys())}")

        print("\n✅ Quick test passed - agents initialized successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Quick test failed: {e}")
        return False


if __name__ == "__main__":
    import sys

    print("\n🎯 Person B Agent Testing Suite")
    print("Testing Image Pipeline: Prompt Parser + Batch Image Generator\n")

    # Check command line arguments
    if len(sys.argv) > 1:
        test_mode = sys.argv[1]
    else:
        test_mode = "quick"

    if test_mode == "quick":
        print("Mode: Quick test (initialization only)")
        success = asyncio.run(quick_test())

    elif test_mode == "parser":
        print("Mode: Prompt Parser only")
        result = asyncio.run(test_prompt_parser())
        success = result is not None

    elif test_mode == "generator":
        print("Mode: Image Generator only")
        success = asyncio.run(test_batch_image_generator())

    elif test_mode == "full":
        print("Mode: Full pipeline test (WILL COST MONEY - uses real API)")
        print("This will generate real images via Replicate API")
        confirm = input("\nAre you sure? (yes/no): ")
        if confirm.lower() == "yes":
            success = asyncio.run(test_full_pipeline())
        else:
            print("Test cancelled")
            success = False

    else:
        print(f"Unknown test mode: {test_mode}")
        print("Available modes: quick, parser, generator, full")
        success = False

    # Exit with appropriate code
    sys.exit(0 if success else 1)
