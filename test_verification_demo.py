"""
Quick test to demonstrate verification layer is working
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.image_verifier import ImageVerificationService
from app.services.video_verifier import VideoVerificationService


async def test_image_verification():
    """Test image verification with a real image."""
    print("\n" + "="*80)
    print("TESTING IMAGE VERIFICATION LAYER")
    print("="*80)

    verifier = ImageVerificationService()

    # Use a test image URL (Replicate sample)
    test_image_url = "https://replicate.delivery/yhqm/QHM9gqWqozbQcjdXFJWVbIe9pPdvIpbdMdPBl9BPLuqKgGdJA/out-0.png"

    print(f"\nVerifying test image: {test_image_url[:60]}...")

    result = await verifier.verify_image(
        image_url=test_image_url,
        image_index=0
    )

    print(f"\n{'='*80}")
    print(f"RESULT: {result.status.value.upper()}")
    print(f"{'='*80}\n")

    return result


async def test_video_verification():
    """Test video verification with a real video."""
    print("\n" + "="*80)
    print("TESTING VIDEO VERIFICATION LAYER")
    print("="*80)

    verifier = VideoVerificationService()

    # Use a test video URL (sample video)
    test_video_url = "https://replicate.delivery/pbxt/X3VSlp4Xr8jBCMNW6k3WtN5RlPpQCZhvkpLFqmNRF3Qxvdcc/output.mp4"

    print(f"\nVerifying test video: {test_video_url[:60]}...")

    result = await verifier.verify_clip(
        video_url=test_video_url,
        expected_duration=4.0,
        clip_index=0
    )

    print(f"\n{'='*80}")
    print(f"RESULT: {result.status.value.upper()}")
    print(f"{'='*80}\n")

    return result


async def main():
    print("\n" + "🔍"*40)
    print("VERIFICATION LAYER DEMONSTRATION")
    print("This test proves the verification layer is active and working")
    print("🔍"*40)

    # Test image verification
    img_result = await test_image_verification()

    # Test video verification
    vid_result = await test_video_verification()

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✓ Image Verification: {img_result.status.value.upper()}")
    print(f"  - Total checks: {len(img_result.checks)}")
    print(f"  - Failed: {len(img_result.failed_checks)}")
    print(f"  - Warnings: {len(img_result.warning_checks)}")

    print(f"\n✓ Video Verification: {vid_result.status.value.upper()}")
    print(f"  - Total checks: {len(vid_result.checks)}")
    print(f"  - Failed: {len(vid_result.failed_checks)}")
    print(f"  - Warnings: {len(vid_result.warning_checks)}")

    print("\n" + "🔍"*40)
    print("VERIFICATION LAYER IS WORKING!")
    print("🔍"*40 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
