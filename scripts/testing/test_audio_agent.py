"""
Test script for Audio Pipeline Agent (OpenAI TTS).

This tests the agent in isolation without requiring the full orchestrator.
Useful for development and debugging.

Usage:
    python test_audio_agent.py
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agents.audio_pipeline import AudioPipelineAgent
from app.agents.base import AgentInput


async def test_audio_generation():
    """Test basic TTS audio generation."""
    print("=" * 60)
    print("Testing Audio Pipeline Agent")
    print("=" * 60)

    # Create agent instance
    agent = AudioPipelineAgent()

    # Sample script (4-part educational format)
    test_script = {
        "hook": {
            "text": "Have you ever wondered how plants make their own food?",
            "duration": "10",
            "key_concepts": ["photosynthesis", "plants"],
            "visual_guidance": "Show a vibrant green plant in sunlight"
        },
        "concept": {
            "text": "Plants use a process called photosynthesis to convert sunlight, water, and carbon dioxide into glucose and oxygen.",
            "duration": "15",
            "key_concepts": ["photosynthesis", "glucose", "oxygen", "carbon dioxide"],
            "visual_guidance": "Diagram showing the photosynthesis equation"
        },
        "process": {
            "text": "Inside plant cells are tiny structures called chloroplasts. They contain a green pigment called chlorophyll that captures energy from sunlight. This energy powers a chemical reaction that transforms water from the roots and carbon dioxide from the air into glucose sugar.",
            "duration": "20",
            "key_concepts": ["chloroplasts", "chlorophyll", "chemical reaction"],
            "visual_guidance": "Animated diagram of chloroplast and the chemical process"
        },
        "conclusion": {
            "text": "So plants are basically solar-powered food factories! They create their own energy while also producing the oxygen we breathe. Pretty amazing, right?",
            "duration": "15",
            "key_concepts": ["solar energy", "oxygen production"],
            "visual_guidance": "Happy plant with sun and oxygen bubbles"
        }
    }

    # Create agent input
    agent_input = AgentInput(
        session_id="test_session_001",
        data={
            "script": test_script,
            "voice": "alloy",  # OpenAI default voice
            "audio_option": "tts"
        }
    )

    print("\n📝 Input Script:")
    print(f"  - Hook: {len(test_script['hook']['text'])} chars")
    print(f"  - Concept: {len(test_script['concept']['text'])} chars")
    print(f"  - Process: {len(test_script['process']['text'])} chars")
    print(f"  - Conclusion: {len(test_script['conclusion']['text'])} chars")
    print(f"  - Voice: {agent_input.data['voice']}")

    print("\n🔊 Generating audio...")

    # Process the request
    result = await agent.process(agent_input)

    # Display results
    print("\n" + "=" * 60)
    if result.success:
        print("✅ SUCCESS!")
        print("=" * 60)

        audio_files = result.data.get("audio_files", [])
        total_duration = result.data.get("total_duration", 0)
        total_cost = result.data.get("total_cost", 0)

        print(f"\n📊 Summary:")
        print(f"  - Audio files generated: {len(audio_files)}")
        print(f"  - Total duration: {total_duration:.1f} seconds")
        print(f"  - Total cost: ${total_cost:.4f}")
        print(f"  - Processing time: {result.duration:.2f}s")

        print(f"\n📁 Audio Files:")
        for audio in audio_files:
            print(f"\n  Part: {audio['part']}")
            print(f"    - File: {audio['filepath']}")
            print(f"    - Duration: {audio['duration']:.1f}s")
            print(f"    - Cost: ${audio['cost']:.4f}")
            print(f"    - Characters: {audio.get('character_count', 0)}")

            # Check if file exists
            if os.path.exists(audio['filepath']):
                file_size = os.path.getsize(audio['filepath'])
                print(f"    - File size: {file_size / 1024:.1f} KB")
                print(f"    - Status: ✓ File created successfully")
            else:
                print(f"    - Status: ✗ File not found")

    else:
        print("❌ FAILED!")
        print("=" * 60)
        print(f"\nError: {result.error}")
        print(f"Processing time: {result.duration:.2f}s")

    print("\n" + "=" * 60)
    return result


async def test_non_tts_option():
    """Test non-TTS audio option (e.g., 'none')."""
    print("\n\n" + "=" * 60)
    print("Testing Non-TTS Option (audio_option='none')")
    print("=" * 60)

    agent = AudioPipelineAgent()

    agent_input = AgentInput(
        session_id="test_session_002",
        data={
            "script": {
                "hook": {"text": "Test", "duration": "5"},
                "concept": {"text": "Test", "duration": "5"},
                "process": {"text": "Test", "duration": "5"},
                "conclusion": {"text": "Test", "duration": "5"}
            },
            "audio_option": "none"
        }
    )

    result = await agent.process(agent_input)

    if result.success:
        print("\n✅ Non-TTS option handled correctly")
        print(f"   Message: {result.data.get('message', 'N/A')}")
        print(f"   Cost: ${result.cost:.4f}")
    else:
        print(f"\n❌ Failed: {result.error}")

    return result


async def test_get_voices():
    """Test fetching available voices from OpenAI."""
    print("\n\n" + "=" * 60)
    print("Testing Get Available Voices")
    print("=" * 60)

    agent = AudioPipelineAgent()
    voices = await agent.get_available_voices()

    if voices:
        print(f"\n✅ Found {len(voices)} available voices:")
        for voice in voices:
            print(f"   - {voice['name']} (ID: {voice['voice_id']})")
            print(f"     {voice['description']}")
    else:
        print("\n⚠️  No voices found")

    return voices


async def main():
    """Run all tests."""
    print("\n🧪 Audio Pipeline Agent Test Suite")
    print("=" * 60)

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n⚠️  WARNING: OPENAI_API_KEY not set!")
        print("   Set it in .env file or export it:")
        print("   export OPENAI_API_KEY='your-key-here'")
        print("\n   Tests will run but audio generation will fail.\n")
    else:
        print(f"\n✓ OPENAI_API_KEY found (length: {len(api_key)})")

    # Run tests
    try:
        # Test 1: Basic TTS generation
        result1 = await test_audio_generation()

        # Test 2: Non-TTS option
        result2 = await test_non_tts_option()

        # Test 3: Get voices (always available, doesn't require API)
        voices = await test_get_voices()

        print("\n\n" + "=" * 60)
        print("🎉 All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Run tests
    asyncio.run(main())
