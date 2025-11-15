"""
Live Test: Generate Videos from Approved Shoe Images
This will cost approximately $0.80 (2 clips × $0.40 each)
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.database import get_db
from app.models.database import Asset
from app.agents.video_generator import VideoGeneratorAgent
from app.agents.base import AgentInput
from app.config import get_settings


async def main():
    print("=" * 80)
    print("  LIVE VIDEO GENERATION TEST")
    print("  Generating videos from approved shoe images")
    print("=" * 80)

    # Get settings
    settings = get_settings()
    if not settings.REPLICATE_API_KEY:
        print("\n❌ REPLICATE_API_KEY not set!")
        return

    # Get approved images from database
    db = next(get_db())

    session_id = "0a0cb199-51bb-4b5a-8b31-cdace4531ca3"

    approved_images = db.query(Asset).filter(
        Asset.session_id == session_id,
        Asset.type == "image",
        Asset.approved == True
    ).all()

    if not approved_images:
        print("\n❌ No approved images found!")
        return

    print(f"\n✓ Found {len(approved_images)} approved images:")
    for img in approved_images:
        metadata = img.asset_metadata or {}
        print(f"  - {metadata.get('view_type', 'unknown')}: {img.url[:60]}...")

    # Convert to format expected by Video Generator
    image_data_list = [
        {
            "id": str(img.id),
            "url": img.url,
            "view_type": img.asset_metadata.get("view_type", "unknown") if img.asset_metadata else "unknown"
        }
        for img in approved_images
    ]

    # Initialize Video Generator
    print(f"\n⏳ Initializing Video Generator Agent...")
    agent = VideoGeneratorAgent(settings.REPLICATE_API_KEY)

    # Create agent input
    agent_input = AgentInput(
        session_id=session_id,
        data={
            "approved_images": image_data_list,
            "video_prompt": "dynamic sneaker showcase with smooth camera movements highlighting the product design",
            "clip_duration": 3.0,
            "model": "stable-video-diffusion"
        }
    )

    print(f"\n🎬 Generating {len(image_data_list)} video clips...")
    print(f"   Prompt: dynamic sneaker showcase with smooth camera movements")
    print(f"   Duration: 3.0 seconds per clip")
    print(f"   Estimated cost: ${0.40 * len(image_data_list):.2f}")
    print(f"\n   This will take ~45 seconds per clip (running in parallel)...")

    # Generate videos
    result = await agent.process(agent_input)

    print("\n" + "=" * 80)
    print("  RESULTS")
    print("=" * 80)

    if result.success:
        print(f"\n✅ SUCCESS!")
        print(f"   Generated: {len(result.data['clips'])} clips")
        print(f"   Cost: ${result.cost:.2f}")
        print(f"   Duration: {result.duration:.1f}s")

        # Store clips in database
        print(f"\n💾 Storing clips in database...")
        for clip_data in result.data["clips"]:
            asset = Asset(
                session_id=session_id,
                type="video",
                url=clip_data["url"],
                approved=False,
                asset_metadata={
                    "source_image_id": clip_data["source_image_id"],
                    "duration": clip_data["duration"],
                    "resolution": clip_data["resolution"],
                    "fps": clip_data["fps"],
                    "model": clip_data["model"],
                    "scene_prompt": clip_data["scene_prompt"],
                    "motion_intensity": clip_data["motion_intensity"],
                    "cost": clip_data["cost"],
                    "generation_time": clip_data["generation_time"]
                }
            )
            db.add(asset)

        db.commit()

        print(f"\n📹 Generated Video Clips:")
        for i, clip in enumerate(result.data["clips"], 1):
            print(f"\n  Clip {i}:")
            print(f"    URL: {clip['url']}")
            print(f"    Source Image: {clip['source_image_id']}")
            print(f"    Duration: {clip['duration']}s")
            print(f"    Resolution: {clip['resolution']} @ {clip['fps']}fps")
            print(f"    Motion Intensity: {clip['motion_intensity']:.2f}")
            print(f"    Scene: {clip['scene_prompt'][:80]}...")
            print(f"    Generation Time: {clip['generation_time']:.1f}s")
            print(f"    Cost: ${clip['cost']:.2f}")

        if "scenes_planned" in result.data:
            print(f"\n🎭 Scene Planning:")
            for i, scene in enumerate(result.data["scenes_planned"], 1):
                print(f"\n  Scene {i}:")
                print(f"    View: {scene.get('image_view', 'unknown')}")
                print(f"    Camera: {scene.get('camera_movement', 'static')}")
                print(f"    Motion: {scene.get('motion_intensity', 0.5):.2f}")
                print(f"    Prompt: {scene.get('scene_prompt', '')[:80]}...")

        print(f"\n" + "=" * 80)
        print(f"  🎉 Video generation complete!")
        print(f"  Next steps:")
        print(f"    1. Approve clips in database")
        print(f"    2. Run composition to create final video")
        print("=" * 80)

    else:
        print(f"\n❌ FAILED!")
        print(f"   Error: {result.error}")
        print(f"   Cost: ${result.cost:.2f}")
        print(f"   Duration: {result.duration:.1f}s")

        if "errors" in result.data:
            print(f"\n   Errors:")
            for error in result.data["errors"]:
                print(f"     - {error}")


if __name__ == "__main__":
    print("\n⚠️  WARNING: This will cost approximately $0.80 (2 clips × $0.40 each)")
    print("   Press Ctrl+C within 5 seconds to cancel...")

    try:
        import time
        for i in range(5, 0, -1):
            print(f"   Starting in {i}...", end="\r")
            time.sleep(1)
        print("\n")

        asyncio.run(main())

    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
