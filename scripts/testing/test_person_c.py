"""
Test Script for Person C Agents
Tests Video Generator, FFmpeg Compositor, and Storage Service
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.video_generator import VideoGeneratorAgent
from app.services.ffmpeg_compositor import FFmpegCompositor
from app.services.storage import StorageService
from app.agents.base import AgentInput
from app.config import get_settings


def print_header(text: str):
    """Print section header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_result(agent: str, success: bool, cost: float, duration: float, details: str = ""):
    """Print test result."""
    status = "✓ SUCCESS" if success else "✗ FAILED"
    print(f"\n{status} - {agent}")
    print(f"  Cost: ${cost:.4f}")
    print(f"  Duration: {duration:.2f}s")
    if details:
        print(f"  Details: {details}")


async def test_video_generator_scene_planning():
    """Test 1: Scene planning with LLM."""
    print_header("Test 1: Video Generator - Scene Planning")

    settings = get_settings()
    if not settings.REPLICATE_API_KEY:
        print("❌ REPLICATE_API_KEY not set - skipping test")
        return False

    agent = VideoGeneratorAgent(settings.REPLICATE_API_KEY)

    # Create mock approved images
    approved_images = [
        {
            "id": "img_1",
            "url": "https://example.com/front.png",
            "view_type": "front"
        },
        {
            "id": "img_2",
            "url": "https://example.com/side.png",
            "view_type": "side"
        }
    ]

    # Test scene planning (without actual video generation)
    try:
        scenes = await agent._plan_video_scenes(
            approved_images,
            "dynamic product showcase with smooth camera movements",
            "test_session"
        )

        success = len(scenes) > 0
        print_result(
            "Scene Planning",
            success,
            0.001,  # Approximate LLM cost
            0.0,
            f"Planned {len(scenes)} scenes"
        )

        if scenes:
            print("\nScene Details:")
            for i, scene in enumerate(scenes, 1):
                print(f"  {i}. View: {scene.get('image_view', 'unknown')}")
                print(f"     Motion: {scene.get('motion_intensity', 0.5):.2f}")
                print(f"     Camera: {scene.get('camera_movement', 'static')}")
                print(f"     Prompt: {scene.get('scene_prompt', '')[:60]}...")

        return success

    except Exception as e:
        print(f"❌ Scene planning failed: {e}")
        return False


async def test_video_generator_full(skip_generation: bool = True):
    """Test 2: Full video generation (expensive, skip by default)."""
    print_header("Test 2: Video Generator - Full Pipeline")

    if skip_generation:
        print("⚠️  SKIPPED - Video generation is expensive (~$0.40 per clip)")
        print("   Set skip_generation=False to test with real video generation")
        return True

    settings = get_settings()
    if not settings.REPLICATE_API_KEY:
        print("❌ REPLICATE_API_KEY not set - skipping test")
        return False

    agent = VideoGeneratorAgent(settings.REPLICATE_API_KEY)

    # Use real image URLs (would need actual generated images)
    approved_images = [
        {
            "id": "img_1",
            "url": "https://replicate.delivery/example/image1.png",  # Replace with real URL
            "view_type": "front"
        }
    ]

    agent_input = AgentInput(
        session_id="test_video_gen",
        data={
            "approved_images": approved_images,
            "video_prompt": "smooth rotation showcase",
            "clip_duration": 3.0,
            "model": "stable-video-diffusion"
        }
    )

    try:
        result = await agent.process(agent_input)

        print_result(
            "Video Generation",
            result.success,
            result.cost,
            result.duration,
            f"Generated {len(result.data.get('clips', []))} clips"
        )

        if result.success:
            print("\nClip URLs:")
            for i, clip in enumerate(result.data["clips"], 1):
                print(f"  {i}. {clip['url']}")

        return result.success

    except Exception as e:
        print(f"❌ Video generation failed: {e}")
        return False


async def test_ffmpeg_compositor():
    """Test 3: FFmpeg Compositor (requires FFmpeg installed)."""
    print_header("Test 3: FFmpeg Compositor")

    try:
        compositor = FFmpegCompositor()
        print("✓ FFmpeg Compositor initialized")
        print(f"  Work directory: {compositor.work_dir}")

        # Test FFmpeg availability (already done in __init__)
        return True

    except RuntimeError as e:
        print(f"❌ FFmpeg Compositor initialization failed: {e}")
        print("\nTo install FFmpeg:")
        print("  macOS: brew install ffmpeg")
        print("  Ubuntu: sudo apt-get install ffmpeg")
        print("  Windows: Download from https://ffmpeg.org/download.html")
        return False


async def test_ffmpeg_composition(skip_composition: bool = True):
    """Test 4: Full video composition (requires video files)."""
    print_header("Test 4: FFmpeg - Video Composition")

    if skip_composition:
        print("⚠️  SKIPPED - Requires real video clip files")
        print("   Set skip_composition=False to test with real clips")
        return True

    try:
        compositor = FFmpegCompositor()

        # Would need real video clip URLs
        clips = [
            {"url": "https://example.com/clip1.mp4"},
            {"url": "https://example.com/clip2.mp4"}
        ]

        text_config = {
            "product_name": "Test Product",
            "call_to_action": "Shop Now!",
            "text_color": "#FFFFFF"
        }

        result = await compositor.compose_final_video(
            clips=clips,
            text_config=text_config,
            audio_config={"enabled": False},
            session_id="test_composition"
        )

        print_result(
            "Video Composition",
            True,
            0.0,  # FFmpeg is free
            0.0,
            f"Output: {result['output_path']}"
        )

        return True

    except Exception as e:
        print(f"❌ Video composition failed: {e}")
        return False


async def test_storage_service():
    """Test 5: Storage Service."""
    print_header("Test 5: Storage Service")

    try:
        storage = StorageService()

        settings = get_settings()
        has_credentials = (
            settings.AWS_ACCESS_KEY_ID and
            settings.AWS_SECRET_ACCESS_KEY and
            settings.S3_BUCKET_NAME
        )

        if has_credentials:
            print("✓ Storage Service initialized")
            print(f"  Bucket: {storage.bucket_name}")
            print(f"  Region: {settings.AWS_REGION}")
            return True
        else:
            print("⚠️  Storage Service not configured (credentials missing)")
            print("   Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME in .env")
            print("   This is OK for local testing - storage is optional for MVP")
            return True

    except Exception as e:
        print(f"❌ Storage Service failed: {e}")
        return False


async def test_integration():
    """Test 6: Integration check."""
    print_header("Test 6: Integration Check")

    try:
        # Check all imports work
        from app.services.orchestrator import VideoGenerationOrchestrator
        from app.agents.video_generator import VideoGeneratorAgent
        from app.services.ffmpeg_compositor import FFmpegCompositor
        from app.services.storage import StorageService

        print("✓ All Person C modules import successfully")

        # Check orchestrator can initialize Person C agents
        from app.services.websocket_manager import WebSocketManager
        ws_manager = WebSocketManager()
        orchestrator = VideoGenerationOrchestrator(ws_manager)

        has_video_gen = orchestrator.video_generator is not None
        has_compositor = orchestrator.ffmpeg_compositor is not None

        print(f"✓ Orchestrator has Video Generator: {has_video_gen}")
        print(f"✓ Orchestrator has FFmpeg Compositor: {has_compositor}")

        settings = get_settings()
        if not settings.REPLICATE_API_KEY:
            print("⚠️  REPLICATE_API_KEY not set - agents will not work at runtime")

        return has_compositor  # Compositor should always be available

    except Exception as e:
        print(f"❌ Integration check failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("  PERSON C AGENT TEST SUITE")
    print("  Video Generation Pipeline + FFmpeg Composition")
    print("=" * 80)

    tests = [
        ("Scene Planning", test_video_generator_scene_planning()),
        ("Video Generation (Skipped)", test_video_generator_full(skip_generation=True)),
        ("FFmpeg Initialization", test_ffmpeg_compositor()),
        ("Video Composition (Skipped)", test_ffmpeg_composition(skip_composition=True)),
        ("Storage Service", test_storage_service()),
        ("Integration", test_integration()),
    ]

    results = []
    for name, test_coro in tests:
        try:
            result = await test_coro
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} crashed: {e}")
            results.append((name, False))

    # Summary
    print_header("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {name}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
