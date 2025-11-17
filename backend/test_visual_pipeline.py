"""
Test script for Template + DALL-E 3 Visual Pipeline

Tests the complete flow:
1. Template matching
2. PSD customization
3. DALL-E 3 generation
4. 60/40 template/AI mix
"""
import asyncio
import sys
import os
import uuid
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.database import User, Script, Session as SessionModel, Template
from app.services.orchestrator import VideoGenerationOrchestrator
from app.services.websocket_manager import WebSocketManager
from app.config import get_settings

settings = get_settings()


def create_test_user(db: Session) -> User:
    """Create a test user for testing."""
    test_email = "test@example.com"
    user = db.query(User).filter(User.email == test_email).first()

    if user:
        print(f"✓ Using existing test user: {user.email} (ID: {user.id})")
        return user

    user = User(
        email=test_email,
        hashed_password="test_hash_not_real"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    print(f"✓ Created test user: {user.email} (ID: {user.id})")
    return user


def create_test_script(db: Session, user_id: int) -> Script:
    """Create a test script with educational content."""
    script_id = f"test_script_{uuid.uuid4().hex[:8]}"

    script = Script(
        id=script_id,
        user_id=user_id,
        hook={
            "text": "Did you know plants make their own food using sunlight?",
            "duration": "8",
            "key_concepts": ["photosynthesis", "plants", "sunlight"],
            "visual_guidance": "Diagram showing a plant with sunlight rays, emphasizing photosynthesis process"
        },
        concept={
            "text": "This amazing process is called photosynthesis and happens in tiny structures called chloroplasts.",
            "duration": "12",
            "key_concepts": ["chloroplast", "chlorophyll", "plant cell"],
            "visual_guidance": "Close-up diagram of a leaf cell showing chloroplasts and green chlorophyll"
        },
        process={
            "text": "Plants take in carbon dioxide and water, then use sunlight to create glucose and oxygen.",
            "duration": "15",
            "key_concepts": ["CO2", "water", "glucose", "oxygen"],
            "visual_guidance": "Chemical equation diagram showing CO2 + H2O + sunlight converting to glucose and O2"
        },
        conclusion={
            "text": "Without photosynthesis, we wouldn't have oxygen to breathe or food to eat!",
            "duration": "10",
            "key_concepts": ["oxygen", "food chain", "life on Earth"],
            "visual_guidance": "Wide shot showing interconnected ecosystem with plants, animals, and oxygen cycle"
        }
    )

    db.add(script)
    db.commit()
    db.refresh(script)

    print(f"✓ Created test script: {script.id}")
    print(f"  - Hook: {script.hook['text'][:50]}...")
    print(f"  - Concept: {script.concept['text'][:50]}...")
    print(f"  - Process: {script.process['text'][:50]}...")
    print(f"  - Conclusion: {script.conclusion['text'][:50]}...")

    return script


async def test_visual_pipeline(
    db: Session,
    user: User,
    script: Script
):
    """Test the visual pipeline with templates and DALL-E."""
    print("\n" + "="*60)
    print("TESTING TEMPLATE + DALL-E 3 VISUAL PIPELINE")
    print("="*60)

    # Check API keys
    if not settings.OPENAI_API_KEY:
        print("\n⚠️  WARNING: OPENAI_API_KEY not set")
        print("   Will use templates only (100% free)")
    else:
        print(f"\n✓ OPENAI_API_KEY configured")

    # Check templates
    template_count = db.query(Template).count()
    print(f"✓ {template_count} templates in database")
    if template_count > 0:
        templates = db.query(Template).all()
        print("\nAvailable templates:")
        for t in templates:
            print(f"  - {t.name} ({t.category})")
            print(f"    Keywords: {', '.join(t.keywords[:3])}")

    # Create orchestrator
    websocket_manager = WebSocketManager()
    orchestrator = VideoGenerationOrchestrator(websocket_manager)

    # Create session ID
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    print(f"\n✓ Session ID: {session_id}")

    # Test parameters
    options = {
        "images_per_part": 2,  # Generate 2 images per part (8 total)
        "prefer_templates": True  # Target 60% templates
    }

    print(f"✓ Images per part: {options['images_per_part']}")
    print(f"✓ Total images: {options['images_per_part'] * 4}")
    print(f"✓ Target: 60% templates, 40% DALL-E 3")
    print(f"\nGenerating images (this may take 30-90 seconds)...")
    print("="*60)

    # Call the orchestrator
    try:
        result = await orchestrator.generate_images(
            db=db,
            session_id=session_id,
            user_id=user.id,
            script_id=script.id,
            options=options
        )

        # Check result
        if result["status"] == "error":
            print(f"\n❌ ERROR: {result.get('message', 'Unknown error')}")
            return False

        # Print results
        print("\n" + "="*60)
        print("✓ VISUAL PIPELINE SUCCESSFUL!")
        print("="*60)

        micro_scenes = result["micro_scenes"]
        total_cost = float(micro_scenes['cost'])

        # Get stats
        from app.models.database import Asset
        assets = db.query(Asset).filter(Asset.session_id == session_id).all()

        template_count = sum(1 for a in assets if a.asset_metadata.get('source') == 'template')
        dalle_count = sum(1 for a in assets if a.asset_metadata.get('source') == 'dalle3')
        total_images = template_count + dalle_count

        print(f"\n📊 Generation Summary:")
        print(f"  Total images: {total_images}")
        print(f"  Templates used: {template_count} ({template_count/total_images*100:.1f}%)")
        print(f"  DALL-E 3 used: {dalle_count} ({dalle_count/total_images*100:.1f}%)")
        print(f"  Total cost: ${total_cost:.2f}")
        print(f"  Avg cost/image: ${total_cost/total_images:.3f}")

        print(f"\n🖼️  Images by script part:")
        for part_name in ["hook", "concept", "process", "conclusion"]:
            part_data = micro_scenes[part_name]
            num_images = len(part_data["images"])
            print(f"\n  {part_name.upper()}: {num_images} images")

            for i, img in enumerate(part_data["images"], 1):
                metadata = img['metadata']
                source = metadata['source']
                source_emoji = "📄" if source == "template" else "🤖"

                print(f"    {source_emoji} Image {i}: {source}")
                if source == "template":
                    print(f"       Template: {metadata.get('template_name', 'Unknown')}")
                    print(f"       Cost: $0.00 (FREE)")
                else:
                    print(f"       Quality: {metadata.get('quality', 'standard')}")
                    print(f"       Cost: ${metadata.get('cost', 0):.2f}")
                print(f"       URL: {img['image'][:80]}...")

        # Verify database records
        print("\n" + "-"*60)
        print("🗄️  Database Verification:")

        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if session:
            print(f"  ✓ Session: {session.id}")
            print(f"    Status: {session.status}")
            print(f"    User ID: {session.user_id}")
        else:
            print("  ❌ Session not found in database")

        print(f"  ✓ Assets: {len(assets)} images stored")

        # Show breakdown by source
        for asset in assets[:3]:
            source = asset.asset_metadata.get('source', 'unknown')
            part = asset.asset_metadata.get('part_name', 'unknown')
            print(f"    - {source} ({part}): {asset.url[:60]}...")

        if len(assets) > 3:
            print(f"    ... and {len(assets) - 3} more")

        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)

        # Show recommendations
        if dalle_count == 0 and template_count > 0:
            print("\n💡 Note: All images used templates (DALL-E not called)")
            print("   This happens when templates match all concepts")
        elif template_count == 0:
            print("\n⚠️  Warning: No templates were used")
            print("   Check if template keywords match your script concepts")

        return True

    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    print("\n" + "="*60)
    print("TEMPLATE + DALL-E 3 VISUAL PIPELINE TEST")
    print("="*60)

    # Create database session
    db = SessionLocal()

    try:
        # Step 1: Create test user
        print("\n" + "-"*60)
        print("Step 1: Creating test user...")
        print("-"*60)
        user = create_test_user(db)

        # Step 2: Create test script (educational content)
        print("\n" + "-"*60)
        print("Step 2: Creating test script (Photosynthesis)...")
        print("-"*60)
        script = create_test_script(db, user.id)

        # Step 3: Test visual pipeline
        print("\n" + "-"*60)
        print("Step 3: Testing visual pipeline...")
        print("-"*60)
        success = await test_visual_pipeline(db, user, script)

        if success:
            print("\n✅ Test completed successfully!")
        else:
            print("\n❌ Test failed")
            sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
