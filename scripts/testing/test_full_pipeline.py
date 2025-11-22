"""
Full Pipeline Test: Generate Images → Generate Videos → Compose Final Video
This will generate fresh images and then create videos from them.
Cost: ~$0.01 (images) + $0.80 (videos) = ~$0.81
"""
import asyncio
import httpx


async def main():
    print("=" * 80)
    print("  FULL VIDEO PIPELINE TEST")
    print("  1. Generate fresh sneaker images")
    print("  2. Approve images automatically")
    print("  3. Generate video clips")
    print("=" * 80)

    base_url = "http://localhost:8000"

    # Step 1: Login
    print("\n📝 Step 1: Authenticating...")
    async with httpx.AsyncClient() as client:
        login_response = await client.post(
            f"{base_url}/api/auth/login",
            json={"email": "demo@example.com", "password": "demo123"}
        )
        login_response.raise_for_status()
        token = login_response.json()["access_token"]
        print(f"   ✓ Got auth token: {token[:20]}...")

        headers = {"Authorization": f"Bearer {token}"}

        # Step 2: Generate Images
        print("\n🎨 Step 2: Generating images...")
        print("   Prompt: red sneakers")
        print("   Estimated cost: $0.006")

        image_response = await client.post(
            f"{base_url}/api/generate-images",
            headers=headers,
            json={
                "prompt": "red sneakers",
                "num_images": 2,
                "aspect_ratio": "1:1",
                "model": "flux-schnell"
            },
            timeout=60.0
        )
        image_response.raise_for_status()
        image_result = image_response.json()

        session_id = image_result["session_id"]
        images = image_result["images"]

        print(f"   ✓ Generated {len(images)} images")
        print(f"   Session ID: {session_id}")
        for i, img in enumerate(images, 1):
            print(f"     {i}. {img['view_type']}: {img['url'][:60]}...")

        # Step 3: Approve Images (via database since we don't have API endpoint yet)
        print("\n✅ Step 3: Approving images...")

        from app.database import get_db
        from app.models.database import Asset

        db = next(get_db())
        db_images = db.query(Asset).filter(
            Asset.session_id == session_id,
            Asset.type == "image"
        ).all()

        for img in db_images:
            img.approved = True

        db.commit()
        print(f"   ✓ Approved {len(db_images)} images")

        # Step 4: Generate Videos (via direct agent call since we don't have API endpoint yet)
        print("\n🎬 Step 4: Generating video clips...")
        print("   This will take ~45 seconds per clip...")
        print("   Estimated cost: $0.80 (2 clips × $0.40)")

        from app.agents.video_generator import VideoGeneratorAgent
        from app.agents.base import AgentInput
        from app.config import get_settings

        settings = get_settings()
        video_agent = VideoGeneratorAgent(settings.REPLICATE_API_KEY)

        image_data_list = [
            {
                "id": str(img.id),
                "url": img.url,
                "view_type": img.asset_metadata.get("view_type", "unknown") if img.asset_metadata else "unknown"
            }
            for img in db_images
        ]

        video_input = AgentInput(
            session_id=session_id,
            data={
                "approved_images": image_data_list,
                "video_prompt": "dynamic sneaker showcase with smooth rotation",
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
            print(f"   Total Cost: ${video_result.cost:.2f}")
            print(f"   Duration: {video_result.duration:.1f}s")

            # Store clips in database
            for clip_data in video_result.data["clips"]:
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

            print(f"\n📹 Video Clips:")
            for i, clip in enumerate(video_result.data["clips"], 1):
                print(f"\n  Clip {i}:")
                print(f"    URL: {clip['url']}")
                print(f"    Duration: {clip['duration']}s @ {clip['fps']}fps")
                print(f"    Motion: {clip['motion_intensity']:.2f}")
                print(f"    Scene: {clip['scene_prompt'][:60]}...")
                print(f"    Time: {clip['generation_time']:.1f}s | Cost: ${clip['cost']:.2f}")

            print("\n" + "=" * 80)
            print("  🎉 Full pipeline test complete!")
            print(f"  Total Cost: ~${image_result.get('total_cost', 0.0) + video_result.cost:.2f}")
            print("=" * 80)

        else:
            print(f"\n❌ Video generation FAILED!")
            print(f"   Error: {video_result.error}")
            if video_result.data.get("errors"):
                for error in video_result.data["errors"]:
                    print(f"     - {error}")


if __name__ == "__main__":
    print("\n⚠️  WARNING: This will cost approximately $0.81")
    print("   - Images: $0.006")
    print("   - Videos: $0.80 (2 clips)")
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
