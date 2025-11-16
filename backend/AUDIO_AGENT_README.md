# Audio Pipeline Agent - Setup & Usage (OpenAI TTS)

The Audio Pipeline Agent generates TTS (Text-to-Speech) narration from educational scripts using OpenAI's TTS API.

## Features

- ✅ Generates audio for 4-part educational scripts (hook, concept, process, conclusion)
- ✅ Uses OpenAI TTS-1 model (fast, cost-effective)
- ✅ Automatic cost calculation ($15 per 1M characters)
- ✅ Duration estimation based on speaking rate
- ✅ S3 upload integration via orchestrator
- ✅ Supports multiple audio options (TTS, upload, none, instrumental)
- ✅ 6 high-quality voice options
- ✅ MP3 output format

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

OpenAI is already included in requirements (`openai==1.54.0`).

### 2. Configure API Key

Your OPENAI_API_KEY should already be in `.env` for image generation. If not, add it:

```bash
# backend/.env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

Get your API key from: https://platform.openai.com/api-keys

### 3. Verify Installation

```bash
python test_audio_agent.py
```

This will:
- Test audio generation with a sample script
- Check if files are created in `/tmp/`
- Display costs and durations
- Test voice fetching

## Usage

### Via API Endpoint

**POST** `/api/generation/generate-audio`

**Headers:**
```
X-User-Email: user@example.com
Content-Type: application/json
```

**Request Body:**
```json
{
  "session_id": "sess_123",
  "script_id": "script_456",
  "voice": "alloy",
  "audio_option": "tts"
}
```

**Response:**
```json
{
  "session_id": "sess_123",
  "status": "success",
  "audio_files": [
    {
      "part": "hook",
      "filepath": "/tmp/audio_hook_sess_123.mp3",
      "url": "https://s3.../audio_hook.mp3",
      "duration": 9.8,
      "cost": 0.001,
      "character_count": 58,
      "file_size": 15680,
      "voice": "alloy"
    },
    ...
  ],
  "total_duration": 57.7,
  "total_cost": 0.06
}
```

### Directly via Orchestrator

```python
from app.services.orchestrator import VideoGenerationOrchestrator
from app.services.websocket_manager import WebSocketManager

# Initialize
ws_manager = WebSocketManager()
orchestrator = VideoGenerationOrchestrator(ws_manager)

# Generate audio
result = await orchestrator.generate_audio(
    db=db_session,
    session_id="sess_123",
    user_id=1,
    script_id="script_456",
    audio_config={
        "voice": "alloy",
        "audio_option": "tts"
    }
)
```

### Directly via Agent (Testing)

```python
from app.agents.audio_pipeline import AudioPipelineAgent
from app.agents.base import AgentInput

agent = AudioPipelineAgent()

input_data = AgentInput(
    session_id="test_001",
    data={
        "script": {
            "hook": {
                "text": "Your hook text here",
                "duration": "10",
                "key_concepts": ["concept1"],
                "visual_guidance": "..."
            },
            "concept": {...},
            "process": {...},
            "conclusion": {...}
        },
        "voice": "alloy",
        "audio_option": "tts"
    }
)

result = await agent.process(input_data)
```

## Script Format

The agent expects scripts in the new 4-part format:

```python
{
    "hook": {
        "text": str,           # Narration text
        "duration": str,       # Target duration (used for validation)
        "key_concepts": list,  # Key educational concepts
        "visual_guidance": str # What should be shown (not used by audio agent)
    },
    "concept": {...},
    "process": {...},
    "conclusion": {...}
}
```

## Voice Options

OpenAI TTS offers 6 high-quality voices:

| Voice | Description | Best For |
|-------|-------------|----------|
| **alloy** | Neutral, balanced | Educational content (default) |
| **echo** | Male, clear | Authoritative narration |
| **fable** | British, expressive | Engaging storytelling |
| **onyx** | Deep, authoritative | Serious, professional content |
| **nova** | Female, energetic | Dynamic, upbeat content |
| **shimmer** | Warm, friendly | Conversational, friendly tone |

### Get Available Voices

```python
agent = AudioPipelineAgent()
voices = await agent.get_available_voices()

for voice in voices:
    print(f"{voice['name']}: {voice['description']}")
```

Output:
```
Alloy: Neutral, balanced
Echo: Male, clear
Fable: British, expressive
Onyx: Deep, authoritative
Nova: Female, energetic
Shimmer: Warm, friendly
```

## Audio Options

The agent supports 4 audio options:

1. **tts** (default) - Generate using OpenAI TTS
2. **upload** - User uploads their own audio (not yet implemented)
3. **none** - No audio, silent video
4. **instrumental** - Background music only (not yet implemented)

## Cost Calculation

- **Pricing:** $15.00 per 1M characters
- **Example:** A 60-second script (~300 words, ~1500 characters) costs ~$0.02
- **Comparison:** ~20x cheaper than ElevenLabs!

The agent automatically calculates costs based on character count and includes it in the response.

### Cost Breakdown Example

For a typical 60-second educational video:
- Hook (10s): ~300 chars = $0.0045
- Concept (15s): ~450 chars = $0.0067
- Process (20s): ~600 chars = $0.0090
- Conclusion (15s): ~450 chars = $0.0067
- **Total:** ~1800 chars = **$0.027**

## Model Options

OpenAI offers two TTS models:

- **tts-1** (currently used): Faster, more cost-effective
- **tts-1-hd**: Higher quality, slightly more expensive

To use tts-1-hd, modify line 150 in `audio_pipeline.py`:
```python
model="tts-1-hd"  # Instead of "tts-1"
```

## File Storage Flow

1. **Agent generates** → Saves to `/tmp/audio_{part}_{session_id}.mp3`
2. **Orchestrator uploads** → Uploads to S3 bucket
3. **Database stores** → Saves S3 URL in `assets` table

## Database Schema

Audio files are stored as `Asset` records:

```python
Asset(
    session_id=session_id,
    type="audio",
    url="https://s3.../audio_hook.mp3",
    approved=True,  # Audio is auto-approved
    asset_metadata={
        "part": "hook",
        "duration": 9.8,
        "cost": 0.001,
        "character_count": 58,
        "file_size": 15680,
        "voice": "alloy",
        "asset_id": "audio_hook_a1b2c3d4"
    }
)
```

## Integration with Pipeline

The audio agent fits into the full pipeline:

```
1. User submits script → Next.js frontend
2. Script saved to DB → Postgres
3. Images generated → Visual Pipeline Agent
4. Images validated → Gemini Vision Agent
5. Audio generated → Audio Pipeline Agent ← YOU ARE HERE
6. Video composed → Educational Compositor Agent
```

## Testing

### Run Test Suite

```bash
python test_audio_agent.py
```

### Manual Test via cURL

```bash
curl -X POST http://localhost:8000/api/generation/generate-audio \
  -H "Content-Type: application/json" \
  -H "X-User-Email: test@example.com" \
  -d '{
    "session_id": "test_001",
    "script_id": "script_123",
    "voice": "alloy",
    "audio_option": "tts"
  }'
```

## Troubleshooting

### Audio generation fails with "API key not configured"

**Solution:** Check your `.env` file:
```bash
cat backend/.env | grep OPENAI_API_KEY
```

Should show:
```
OPENAI_API_KEY=sk-...
```

### Files not created in /tmp/

**Check permissions:**
```bash
ls -la /tmp/audio_*.mp3
```

**Check logs:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### S3 upload fails

The agent returns local filepaths if S3 upload fails. Check:
- AWS credentials in `.env`
- S3 bucket permissions
- StorageService configuration

### Cost seems high

Verify character count:
```python
text = "Your script text here"
char_count = len(text)
cost = (char_count / 1_000_000) * 15.00
print(f"Cost: ${cost:.4f}")
```

## Quality Comparison

### OpenAI TTS vs ElevenLabs

| Feature | OpenAI TTS | ElevenLabs |
|---------|-----------|------------|
| **Cost** | $15/1M chars | $0.30/1K chars (~$300/1M) |
| **Quality** | Excellent | Excellent |
| **Voices** | 6 | 100+ |
| **Speed** | Very fast | Fast |
| **Customization** | Limited | Advanced (voice cloning) |
| **Best for** | Cost-effective, high-quality | Custom voices, brand voice |

For educational content, OpenAI TTS provides excellent quality at a fraction of the cost.

## Architecture

```
┌──────────────────────────────────────────────────┐
│              Frontend (Next.js)                  │
│  - Audio selection UI                            │
│  - Voice picker (6 options)                      │
│  - Audio preview                                 │
└──────────────┬───────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│         API Endpoint                             │
│  POST /api/generation/generate-audio             │
│  - Validates user                                │
│  - Calls orchestrator                            │
└──────────────┬───────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│           Orchestrator                           │
│  - Fetches script from DB                        │
│  - Calls audio agent                             │
│  - Uploads to S3                                 │
│  - Saves to DB                                   │
│  - Broadcasts via WebSocket                      │
└──────────────┬───────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│       Audio Pipeline Agent                       │
│  - Validates input                               │
│  - Calls OpenAI TTS API                          │
│  - Generates MP3 files                           │
│  - Calculates costs                              │
│  - Returns file paths                            │
└──────────────────────────────────────────────────┘
```

## Next Steps

To complete the audio pipeline:

1. ✅ Agent created (OpenAI TTS)
2. ✅ Orchestrator integration
3. ✅ API endpoint
4. ⏳ Frontend audio selection UI (Phase 7)
5. ⏳ Implement "upload" option
6. ⏳ Implement "instrumental" option
7. ⏳ Add actual audio duration calculation (requires audio library like `pydub`)
8. ⏳ Add voice preview functionality

## Related Files

- **Agent:** `backend/app/agents/audio_pipeline.py`
- **Orchestrator:** `backend/app/services/orchestrator.py` (line 743)
- **API Route:** `backend/app/routes/generation.py` (line 316)
- **Config:** `backend/app/config.py` (line 21)
- **Test:** `backend/test_audio_agent.py`

## Questions?

Check the Doc2 tasks for detailed implementation plan:
- `Doc2/Tasks-07-Audio-Pipeline.md`

## Migration from ElevenLabs

If you want to switch back to ElevenLabs in the future, the agent interface remains the same. Just:
1. Change the TTS provider in `audio_pipeline.py`
2. Update the API key in `.env`
3. Adjust cost calculations

The orchestrator and API don't need to change.
