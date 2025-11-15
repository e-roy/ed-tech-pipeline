"""
Direct Video Generation Test
Generates fresh images, then immediately creates videos from them.
Cost: ~$0.81 total
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.agents.prompt_parser import PromptParserAgent
from app.agents.batch_image_generator import BatchImageGeneratorAgent
from app.agents.video_generator import VideoGeneratorAgent
from app.agents.base import AgentInput
from app.config import get_settings


async def main():
    print("=" * 80)
    print("  DIRECT VIDEO PIPELINE TEST")
    print("  Fresh Images → Video Clips")
    print("=" * 80)

    settings = get_settings()
    if not settings.REPLICATE_API_KEY:
        print("\n❌ REPLICATE_API_KEY not set!")
        return

    # Step 1: Generate Images
    print("\n🎨 Step 1: Generating fresh images...")
    print("   Prompt: red sneakers")
    print("   Model: flux-schnell")
    print("   Estimated cost: $0.006")

    prompt_agent = PromptParserAgent(settings.REPLICATE_API_KEY)
    image_agent = BatchImageGeneratorAgent(settings.REPLICATE_API_KEY)

    # Parse prompt
    prompt_input = AgentInput(
        session_id="video_test",
        data={
            "user_prompt": "red sneakers",
            "options": {}
        }
    )

    prompt_result = await prompt_agent.process(prompt_input)

    if not prompt_result.success:
        print(f"❌ Prompt parsing failed: {prompt_result.error}")
        return

    print(f"   ✓ Parsed prompt: {len(prompt_result.data['image_prompts'])} views")

    # Generate images
    image_input = AgentInput(
        session_id="video_test",
        data={
            "image_prompts": prompt_result.data["image_prompts"][:2],  # Only 2 images
            "model": "flux-schnell"
        }
    )

    image_result = await image_agent.process(image_input)

    if not image_result.success:
        print(f"❌ Image generation failed: {image_result.error}")
        return

    images = image_result.data["images"]
    print(f"   ✓ Generated {len(images)} images (${image_result.cost:.3f})")
    for i, img in enumerate(images, 1):
        print(f"     {i}. {img['view_type']}: {img['url'][:60]}...")

    # Step 2: Generate Videos
    print("\n🎬 Step 2: Generating video clips...")
    print("   Prompt: dynamic sneaker showcase")
    print("   Duration: 3.0s per clip")
    print(f"   Estimated cost: ${0.40 * len(images):.2f}")
    print("   This will take ~45 seconds per clip (parallel)...")

    video_agent = VideoGeneratorAgent(settings.REPLICATE_API_KEY)

    # Convert images to format expected by video agent
    image_data_list = [
        {
            "id": f"img_{i}",
            "url": img["url"],
            "view_type": img["view_type"]
        }
        for i, img in enumerate(images)
    ]

    video_input = AgentInput(
        session_id="video_test",
        data={
            "approved_images": image_data_list,
            "video_prompt": "dynamic sneaker showcase with smooth camera movements",
            "clip_duration": 3.0,
            "model": "stable-video-diffusion"
        }
    )

    video_result = await video_agent.process(video_input)

    print("\n" + "=" * 80)
    print("  RESULTS")
    print("=" * 80)

    if video_result.success:
        print(f"\n✅ SUCCESS!")
        print(f"   Generated: {len(video_result.data['clips'])} video clips")
        print(f"   Video Cost: ${video_result.cost:.2f}")
        print(f"   Total Cost: ${image_result.cost + video_result.cost:.2f}")
        print(f"   Duration: {video_result.duration:.1f}s")

        print(f"\n📹 Video Clips:")
        for i, clip in enumerate(video_result.data["clips"], 1):
            print(f"\n  Clip {i}:")
            print(f"    URL: {clip['url']}")
            print(f"    Source View: {clip.get('source_image_id', 'unknown')}")
            print(f"    Duration: {clip['duration']}s @ {clip['fps']}fps")
            print(f"    Resolution: {clip['resolution']}")
            print(f"    Motion Intensity: {clip['motion_intensity']:.2f}")
            print(f"    Scene: {clip['scene_prompt'][:70]}...")
            print(f"    Generation Time: {clip['generation_time']:.1f}s")
            print(f"    Cost: ${clip['cost']:.2f}")

        if "scenes_planned" in video_result.data:
            print(f"\n🎭 Scene Planning:")
            for i, scene in enumerate(video_result.data["scenes_planned"], 1):
                print(f"\n  Scene {i} ({scene.get('image_view', 'unknown')}):")
                print(f"    Camera: {scene.get('camera_movement', 'static')}")
                print(f"    Motion: {scene.get('motion_intensity', 0.5):.2f}")
                print(f"    Prompt: {scene.get('scene_prompt', '')[:70]}...")

        print("\n" + "=" * 80)
        print("  🎉 Pipeline complete!")
        print(f"  Total Cost: ${image_result.cost + video_result.cost:.2f}")
        print("  All video clips generated successfully!")
        print("=" * 80)

    else:
        print(f"\n❌ Video generation FAILED!")
        print(f"   Error: {video_result.error}")
        print(f"   Cost: ${video_result.cost:.2f}")

        if video_result.data.get("errors"):
            print(f"\n   Individual Errors:")
            for error in video_result.data["errors"]:
                print(f"     - {error}")


if __name__ == "__main__":
    print("\n⚠️  WARNING: This will cost approximately $0.81")
    print("   - Image generation: ~$0.006 (2 images)")
    print("   - Video generation: ~$0.80 (2 clips × $0.40)")
    print("\n   Press Ctrl+C within 5 seconds to cancel...")

    try:
        import time
        for i in range(5, 0, -1):
            print(f"   Starting in {i}...", end="\r")
            time.sleep(1)
        print("\n")

        asyncio.run(main())

    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
