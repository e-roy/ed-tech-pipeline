"""
Test the orchestrator's audio generation flow.
This simulates what happens when the API endpoint calls the orchestrator.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.orchestrator import VideoGenerationOrchestrator
from app.services.websocket_manager import WebSocketManager
from app.database import SessionLocal
from app.models.database import Script, Session as SessionModel, Asset, User


async def test_orchestrator_audio():
    """Test the full orchestrator audio generation flow."""
    print("=" * 60)
    print("Testing Orchestrator Audio Generation")
    print("=" * 60)

    # Initialize
    ws_manager = WebSocketManager()
    orchestrator = VideoGenerationOrchestrator(ws_manager)
    db = SessionLocal()

    try:
        # Create test user
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            print("\n⚠️  Creating test user...")
            test_user = User(
                email="test@example.com",
                hashed_password="test_hash"
            )
            db.add(test_user)
            db.commit()
            print(f"✓ Created user: {test_user.email}")
        else:
            print(f"\n✓ Found existing user: {test_user.email}")

        # Create test script
        print("\n📝 Creating test script...")
        test_script = Script(
            id="test_script_001",
            user_id=test_user.id,
            hook={
                "text": "Have you ever wondered how plants make their own food?",
                "duration": "10",
                "key_concepts": ["photosynthesis"],
                "visual_guidance": "Show a plant in sunlight"
            },
            concept={
                "text": "Plants use photosynthesis to convert sunlight into energy.",
                "duration": "15",
                "key_concepts": ["photosynthesis", "energy"],
                "visual_guidance": "Diagram of photosynthesis"
            },
            process={
                "text": "Chloroplasts in plant cells capture sunlight and use it to make glucose from water and carbon dioxide.",
                "duration": "20",
                "key_concepts": ["chloroplasts", "glucose"],
                "visual_guidance": "Animated chloroplast"
            },
            conclusion={
                "text": "So plants are basically solar-powered food factories!",
                "duration": "10",
                "key_concepts": ["solar energy"],
                "visual_guidance": "Happy plant"
            }
        )
        db.merge(test_script)
        db.commit()
        print(f"✓ Script created: {test_script.id}")

        # Create test session
        print("\n🎬 Creating test session...")
        test_session = SessionModel(
            id="test_session_orch_001",
            user_id=test_user.id,
            status="pending"
        )
        db.merge(test_session)
        db.commit()
        print(f"✓ Session created: {test_session.id}")

        # Test audio generation
        print("\n🔊 Calling orchestrator.generate_audio()...")
        print("-" * 60)

        result = await orchestrator.generate_audio(
            db=db,
            session_id=test_session.id,
            user_id=test_user.id,
            script_id=test_script.id,
            audio_config={
                "voice": "nova",  # Use different voice to verify it's passed correctly
                "audio_option": "tts"
            }
        )

        print("-" * 60)

        # Check results
        print("\n📊 Orchestrator Result:")
        print(f"  Status: {result['status']}")

        if result['status'] == 'success':
            print(f"  Session ID: {result['session_id']}")
            print(f"  Audio Files: {len(result['audio_files'])}")
            print(f"  Total Duration: {result['total_duration']}s")
            print(f"  Total Cost: ${result['total_cost']:.4f}")

            # Check database
            print("\n💾 Database Check:")
            audio_assets = db.query(Asset).filter(
                Asset.session_id == test_session.id,
                Asset.type == "audio"
            ).all()

            print(f"  Assets in DB: {len(audio_assets)}")

            if audio_assets:
                for asset in audio_assets:
                    metadata = asset.asset_metadata
                    print(f"\n  Asset #{asset.id}:")
                    print(f"    Part: {metadata.get('part')}")
                    print(f"    URL: {asset.url[:50]}..." if asset.url else "    URL: (local)")
                    print(f"    Duration: {metadata.get('duration')}s")
                    print(f"    Cost: ${metadata.get('cost'):.4f}")
                    print(f"    Voice: {metadata.get('voice')}")
                    print(f"    File Size: {metadata.get('file_size')} bytes")
                    print(f"    Approved: {asset.approved}")

            # Check session status
            updated_session = db.query(SessionModel).filter(
                SessionModel.id == test_session.id
            ).first()
            print(f"\n  Session Status: {updated_session.status}")

            # Verify files exist
            print("\n📁 File Verification:")
            for audio_file in result['audio_files']:
                filepath = audio_file['filepath']
                exists = os.path.exists(filepath)
                size = os.path.getsize(filepath) if exists else 0
                print(f"  {audio_file['part']:12} - {'✓' if exists else '✗'} {filepath}")
                if exists:
                    print(f"               Size: {size} bytes")

            print("\n✅ SUCCESS! Orchestrator handles audio correctly!")

        else:
            print(f"  Error: {result.get('message', 'Unknown error')}")
            print("\n❌ FAILED!")

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        db.query(Asset).filter(Asset.session_id == "test_session_orch_001").delete()
        db.query(SessionModel).filter(SessionModel.id == "test_session_orch_001").delete()
        db.query(Script).filter(Script.id == "test_script_001").delete()
        # Don't delete user in case they have other data
        db.commit()
        db.close()
        print("✓ Cleanup complete")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_orchestrator_audio())
