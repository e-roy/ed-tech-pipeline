# Quick Reference Guide - Developer Cheat Sheet

**Document:** 11 - Quick Reference Guide
**Version:** 3.0
**Last Updated:** January 15, 2025

---

## 🚀 Getting Started (First 30 Minutes)

### Step 1: Clone & Setup (5 min)

```bash
# Clone repository
git clone <repository-url>
cd pipeline

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Environment variables
cp .env.example .env.local  # Edit with your API keys
```

### Step 2: Database Setup (5 min)

```bash
# Start PostgreSQL (Railway or local)
# Railway: Use provided DATABASE_URL
# Local: postgres://localhost:5432/edu_video_gen

# Run migrations
cd backend
alembic upgrade head

# Seed demo data
python seed.py
```

### Step 3: Run Locally (5 min)

```bash
# Terminal 1: Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Test connection
curl http://localhost:8000/health
```

### Step 4: Verify Setup (5 min)

1. Open http://localhost:3000
2. Login with demo@example.com / demo123
3. Create session (should succeed)
4. Check WebSocket connection in browser console

---

## 📁 Project Structure

```
pipeline/
├── backend/
│   ├── main.py                 # FastAPI app entry
│   ├── agents/
│   │   ├── narrative_builder.py   # Agent 2
│   │   ├── visual_pipeline.py     # Agent 3
│   │   ├── audio_pipeline.py      # Agent 4
│   │   └── ed_compositor.py       # Agent 5
│   ├── models/
│   │   ├── database.py         # SQLAlchemy models
│   │   └── pydantic.py         # Pydantic schemas
│   ├── routers/
│   │   ├── auth.py             # Login endpoints
│   │   ├── sessions.py         # Session management
│   │   └── generation.py       # Video generation
│   ├── orchestrator.py         # Agent coordinator
│   ├── websocket.py            # WebSocket manager
│   └── config.py               # Settings/env vars
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx            # Login page
│   │   ├── topic/page.tsx      # Fact extraction
│   │   ├── script/page.tsx     # Script review
│   │   ├── visuals/page.tsx    # Visual review
│   │   ├── audio/page.tsx      # Audio selection
│   │   └── video/page.tsx      # Final output
│   ├── components/
│   │   ├── TopicInput.tsx
│   │   ├── ScriptReview.tsx
│   │   ├── VisualGrid.tsx
│   │   ├── AudioSelector.tsx
│   │   └── ProgressTracker.tsx
│   ├── lib/
│   │   ├── api.ts              # API client
│   │   ├── websocket.ts        # WebSocket manager
│   │   └── fact-extraction.ts  # Client-side OCR
│   └── hooks/
│       ├── useSession.ts
│       ├── useWebSocket.ts
│       └── useFactExtraction.ts
│
└── templates/
    ├── photosynthesis_overview.psd
    ├── photosynthesis_chloroplast.psd
    ├── cell_structure_animal.psd
    ├── cell_structure_plant.psd
    └── ... (10 total)
```

---

## 🔑 Environment Variables

### Backend (.env)

```bash
# Required
DATABASE_URL=postgresql://user:pass@localhost:5432/db
REPLICATE_API_KEY=r8_xxxxx
OPENAI_API_KEY=sk-xxxxx
GOOGLE_API_KEY=AIzaSyxxxxx
ELEVENLABS_API_KEY=xxxxx
JWT_SECRET_KEY=your-secret-key-here

# Optional
FRONTEND_URL=http://localhost:3000
ENV=development
LOG_LEVEL=DEBUG
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## 🛠️ Common Development Tasks

### Add a New API Endpoint

```python
# backend/routers/generation.py
from fastapi import APIRouter, Depends
from models.pydantic import GenerateScriptRequest

router = APIRouter(prefix="/api", tags=["generation"])

@router.post("/generate-script")
async def generate_script(
    request: GenerateScriptRequest,
    db: Session = Depends(get_db)
):
    # Your logic here
    return {"status": "success"}
```

### Add a New Frontend Component

```typescript
// frontend/components/MyComponent.tsx
"use client";

import { useState } from "react";

export function MyComponent() {
  const [state, setState] = useState("");

  return (
    <div>
      {/* Your UI */}
    </div>
  );
}
```

### Add a Database Migration

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "Add new table"

# Review generated file in alembic/versions/

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Update Agent Logic

```python
# backend/agents/narrative_builder.py
class NarrativeBuilderAgent:
    async def process(self, input: AgentInput) -> AgentOutput:
        # 1. Extract input data
        topic = input.data["topic"]

        # 2. Call LLM
        response = await self._call_llm(topic)

        # 3. Validate output
        script = self._validate_script(response)

        # 4. Return result
        return AgentOutput(
            success=True,
            data={"script": script},
            cost=0.01,
            duration=3.2
        )
```

---

## 🎯 Key API Endpoints

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| POST | `/api/auth/login` | Login | `{email, password}` |
| POST | `/api/sessions/create` | Create session | `{user_id}` |
| GET | `/api/sessions/{id}` | Get session | - |
| POST | `/api/generate-script` | Generate script | `{session_id, topic, facts}` |
| POST | `/api/generate-visuals` | Generate visuals | `{session_id}` |
| POST | `/api/approve-visuals-final` | Final approval | `{session_id, double_confirmed}` |
| POST | `/api/select-audio` | Select audio + start composition | `{session_id, audio_choice}` |
| WS | `/ws/{session_id}` | WebSocket progress | - |

---

## 📊 Database Quick Reference

### Key Tables

```sql
-- Sessions (video generation state)
sessions (id, user_id, stage, topic, generated_script, total_cost, ...)

-- Assets (visuals, audio)
assets (id, session_id, asset_type, url, metadata, cost, ...)

-- Gemini Validations
gemini_validations (id, session_id, visual_id, scientific_accuracy, ...)

-- Templates
templates (id, template_id, topic, filename, covers_concepts, ...)

-- Generation Costs
generation_costs (id, session_id, agent_name, model_used, cost_usd, ...)
```

### Common Queries

```python
# Get session
session = db.query(Session).filter(Session.id == session_id).first()

# Get visuals for session
visuals = db.query(Asset).filter(
    Asset.session_id == session_id,
    Asset.asset_type == "image"
).all()

# Get Gemini validations
validations = db.query(GeminiValidation).filter(
    GeminiValidation.session_id == session_id
).all()

# Calculate total cost
total_cost = db.query(func.sum(GenerationCost.cost_usd)).filter(
    GenerationCost.session_id == session_id
).scalar()
```

---

## 🧪 Testing Commands

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_narrative_builder.py

# Run with coverage
pytest --cov=agents --cov-report=html

# Run integration tests
pytest tests/integration/

# Run specific test
pytest tests/test_narrative_builder.py::test_generates_valid_script
```

### Frontend Tests

```bash
cd frontend

# Run unit tests (Jest)
npm test

# Run E2E tests (Playwright)
npx playwright test

# Run specific E2E test
npx playwright test e2e/video-generation.spec.ts

# Run in headed mode (see browser)
npx playwright test --headed
```

---

## 🐛 Debugging Tips

### Backend Debugging

```python
# Add logging
import logging
logger = logging.getLogger(__name__)

logger.info(f"Processing session: {session_id}")
logger.debug(f"Input data: {input.data}")
logger.error(f"Failed to generate: {e}")

# Use breakpoint
import pdb; pdb.set_trace()

# Print pretty JSON
import json
print(json.dumps(data, indent=2))
```

### Frontend Debugging

```typescript
// Console logging
console.log("Session ID:", sessionId);
console.table(visuals); // Pretty table view
console.error("API error:", error);

// React DevTools
// Install browser extension

// Network inspection
// Check browser DevTools → Network tab

// WebSocket debugging
ws.addEventListener('message', (event) => {
  console.log('WS Message:', JSON.parse(event.data));
});
```

### Database Debugging

```bash
# Connect to PostgreSQL
psql $DATABASE_URL

# Common queries
SELECT * FROM sessions ORDER BY created_at DESC LIMIT 10;
SELECT session_id, SUM(cost_usd) FROM generation_costs GROUP BY session_id;
SELECT * FROM gemini_validations WHERE all_criteria_pass = false;

# Check table structure
\d sessions
\d assets

# Exit psql
\q
```

---

## 🚨 Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'agents'"

**Solution:**
```bash
cd backend
pip install -e .
# OR add PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: "WebSocket connection failed"

**Solution:**
1. Check backend is running on correct port
2. Verify NEXT_PUBLIC_WS_URL in .env.local
3. Check CORS settings in FastAPI
4. Ensure WebSocket route is registered

### Issue: "Database connection refused"

**Solution:**
```bash
# Check PostgreSQL is running
pg_isready

# Verify DATABASE_URL
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check Railway database status (if using Railway)
railway status
```

### Issue: "API key invalid"

**Solution:**
1. Verify .env file exists and has correct keys
2. Restart backend server after changing .env
3. Check key format matches service requirements
4. Test key with curl:
```bash
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

### Issue: "FFmpeg not found"

**Solution:**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html

# Verify installation
ffmpeg -version
```

---

## 📝 Code Snippets

### WebSocket Progress Update

```python
# Backend
await ws_manager.send_progress(
    session_id=session_id,
    stage="script_generation",
    progress=50,
    message="Generating educational script...",
    current_cost=0.01
)
```

```typescript
// Frontend
const { lastUpdate } = useWebSocket(sessionId);

<div>
  <p>{lastUpdate?.message}</p>
  <Progress value={lastUpdate?.progress} />
  <span>${lastUpdate?.current_cost.toFixed(2)}</span>
</div>
```

### Call External API with Retry

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_external_api(prompt: str) -> dict:
    response = await client.post(url, json={"prompt": prompt})
    return response.json()
```

### Client-Side Fact Extraction

```typescript
async function extractTextFromPDF(file: File): Promise<string> {
  const arrayBuffer = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;

  let fullText = "";
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const textContent = await page.getTextContent();
    const pageText = textContent.items.map((item: any) => item.str).join(" ");
    fullText += pageText + "\n";
  }

  return fullText;
}
```

---

## 🎬 Quick Demo Script

Want to show the system to someone? Follow this 3-minute demo:

1. **Login** (10s)
   - Navigate to http://localhost:3000
   - Click "Start Creating" (pre-filled credentials)

2. **Fact Extraction** (30s)
   - Topic: "Photosynthesis"
   - Objective: "Explain how plants make food from sunlight"
   - Key points: "chlorophyll, glucose, oxygen"
   - Click "Extract Key Facts"
   - Click "Continue to Script Generation"

3. **Script Review** (20s)
   - Review 4-part script
   - Show editable narration
   - Click "Approve Script & Generate Visuals"

4. **Visual Review** (30s)
   - Watch progress updates
   - Show template-based vs AI-generated badges
   - Point out cost tracker
   - Click "I Approve These Visuals" → Confirm

5. **Audio Selection** (15s)
   - Select "AI Voiceover"
   - Preview voice sample
   - Click "Generate Final Video"

6. **Final Output** (45s)
   - Watch progress stages (Gemini, Audio, Composition)
   - Show self-healing notes if any
   - Play final video
   - Show cost breakdown ($4-5)
   - Download video

**Total: 2min 50s** (leaves 10s buffer for questions)

---

## 📚 Additional Resources

### Documentation
- [Full PRD](./NewPRD.md) - Original comprehensive spec
- [Index](./00-INDEX.md) - Navigation guide
- [Architecture](./03-multi-agent-architecture.md) - System design

### External APIs
- [Replicate Docs](https://replicate.com/docs) - Llama 3.1
- [OpenAI DALL-E](https://platform.openai.com/docs/guides/images) - Image generation
- [Gemini Vision](https://ai.google.dev/gemini-api/docs/vision) - Validation
- [ElevenLabs](https://docs.elevenlabs.io/) - TTS

### Tools
- [FastAPI Docs](https://fastapi.tiangolo.com/) - Backend framework
- [Next.js Docs](https://nextjs.org/docs) - Frontend framework
- [SQLAlchemy](https://docs.sqlalchemy.org/) - Database ORM
- [Pydantic](https://docs.pydantic.dev/) - Data validation

---

**Last Updated:** January 15, 2025
**Status:** Ready for Implementation
