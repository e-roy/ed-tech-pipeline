# Team Work Breakdown - 48 Hour Sprint
## AI Ad Video Generator - 5 Person Team

**Sprint Start:** TBD
**Sprint End:** TBD (48 hours later)
**Team Size:** 5 developers

---

## Executive Summary

**Strategy:** Build orchestrator skeleton first (Hour 0-4), then parallelize everything else.

**Critical Path:** Person A (Backend Lead) → Orchestrator → Database → Agents

**Success Rate:** 85% if orchestrator ready by Hour 4

---

## Team Roles & Ownership

### Person A: Backend Lead (CRITICAL PATH) 🔥
**Skills Required:** Python, FastAPI, PostgreSQL, async/await, SQLAlchemy
**Owns:**
- Orchestrator skeleton (Hours 0-4)
- Database schema implementation
- All API endpoints
- Agent integration
- WebSocket manager

**Why Critical:** Everyone else blocks on orchestrator being ready

---

### Person B: Agent Developer 1 (Image Pipeline)
**Skills Required:** Python, LLM prompting, API integration, async
**Owns:**
- Prompt Parser Agent
- Batch Image Generator Agent
- Scene planning for videos
- Agent testing

**Dependencies:** Needs orchestrator interface by Hour 4

---

### Person C: Agent Developer 2 (Video Pipeline + FFmpeg)
**Skills Required:** Python, FFmpeg, subprocess, video processing
**Owns:**
- Video Generator Agent
- FFmpeg Composition Layer
- Storage Service (S3/R2)
- Video quality optimization

**Critical Task:** Validate FFmpeg on Railway by Hour 8

---

### Person D: Frontend Lead
**Skills Required:** React, TypeScript, Next.js 14, Tailwind CSS, WebSocket
**Owns:**
- All UI components
- WebSocket integration
- API client
- User flow implementation

**Can Start:** Hour 0 (uses stub API)

---

### Person E: DevOps + Integration
**Skills Required:** Railway, Vercel, Docker, testing, monitoring
**Owns:**
- Infrastructure setup
- CI/CD pipeline
- Production deployment
- Integration testing
- Monitoring & logging

**Can Start:** Hour 0 (fully parallel)

---

## Hour-by-Hour Task Breakdown

### PHASE 1: FOUNDATION (Hours 0-4)

#### Person A (Backend Lead) - Hours 0-4 🔥

**Hour 0-1: Project Setup**
```bash
# Tasks:
- [ ] Create FastAPI project structure
- [ ] Install dependencies: fastapi, sqlalchemy, psycopg2-binary, alembic, replicate, python-jose, passlib, websockets
- [ ] Create .env.example with all required variables
- [ ] Configure CORS for Next.js localhost:3000
- [ ] Create main.py with basic FastAPI app

# Deliverable: uvicorn main:app --reload works
```

**Hour 1-2: Database Implementation**
```bash
# Tasks:
- [ ] Copy DATABASE_SCHEMA.md tables to SQLAlchemy models
- [ ] Create models/database.py with all tables:
    - users
    - sessions
    - assets
    - generation_costs
    - websocket_connections
- [ ] Create alembic migration (alembic init, alembic revision --autogenerate)
- [ ] Test migration locally: alembic upgrade head
- [ ] Seed demo user: demo@example.com / demo123

# Deliverable: Database has all tables + demo user
```

**Hour 2-3: Orchestrator Skeleton**
```python
# Tasks:
- [ ] Create services/orchestrator.py
- [ ] Implement VideoGenerationOrchestrator class with stub methods:
    async def generate_images(session_id, user_prompt, options) -> dict
    async def generate_clips(session_id, video_prompt, clip_config) -> dict
    async def compose_final_video(session_id, text_config, audio_config) -> dict

- [ ] Each method should:
    - Create/update session in database
    - Return {"status": "success", "message": "Stub response"}

- [ ] Create services/websocket_manager.py
- [ ] Implement WebSocketManager with:
    - connect(websocket, session_id)
    - disconnect(websocket, session_id)
    - send_progress(session_id, message)

# Deliverable: Orchestrator exists, can be imported
```

**Hour 3-4: API Endpoints (Stubs)**
```python
# Tasks:
- [ ] Create routes/auth.py
    - POST /api/auth/login (returns JWT for demo user)

- [ ] Create routes/generation.py
    - POST /api/generate-images (calls orchestrator.generate_images)
    - POST /api/save-approved-images (updates session)
    - POST /api/generate-clips (calls orchestrator.generate_clips)
    - POST /api/save-approved-clips (updates session)
    - POST /api/compose-final-video (calls orchestrator.compose_final)

- [ ] Create routes/sessions.py
    - GET /api/sessions/{session_id} (returns session from DB)
    - GET /api/sessions/{session_id}/costs (returns cost breakdown)

- [ ] Create websocket endpoint
    - @app.websocket("/ws/{session_id}")

# Deliverable: All endpoints return 200 OK (even if stubbed)
# Test with: curl http://localhost:8000/api/sessions/test-id
```

**Hour 4 CHECKPOINT:**
```bash
# Verification:
✅ uvicorn main:app --reload runs without errors
✅ Database has all tables (check with psql or pgAdmin)
✅ Can login: POST /api/auth/login returns JWT token
✅ All generation endpoints return 200 OK
✅ WebSocket connection works: ws://localhost:8000/ws/test-session

# If ANY fail: STOP and fix before proceeding
```

---

#### Person B (Agent Developer 1) - Hours 0-4

**Hour 0-1: Environment Setup**
```bash
# Tasks:
- [ ] Clone repo, create branch: feature/agents-image-pipeline
- [ ] Set up Python virtual environment
- [ ] Get Replicate API key from account
- [ ] Install replicate SDK: pip install replicate
- [ ] Test basic Replicate call:
    import replicate
    output = replicate.run("meta/llama-3.1-70b-instruct", input={"prompt": "Hello"})
    print(list(output))

# Deliverable: Can call Replicate API successfully
```

**Hour 1-2: Agent Interface**
```python
# Tasks:
- [ ] Create agents/base.py
- [ ] Implement base classes from PRD Section 4.1:
    - AgentInput (Pydantic model)
    - AgentOutput (Pydantic model)
    - Agent (Protocol)

- [ ] Create agents/__init__.py

# Deliverable: Base agent interface defined
```

**Hour 2-4: Prompt Parser Agent (Prototype)**
```python
# Tasks:
- [ ] Create agents/prompt_parser.py
- [ ] Implement PromptParserAgent class
- [ ] Build LLM system prompt (from PRD Section 4.2)
- [ ] Test with Llama 3.1 API
- [ ] Verify JSON output parsing works
- [ ] Test with example: "pink tennis shoes" → should return 6 prompts with same seed

# Test script:
async def test_prompt_parser():
    agent = PromptParserAgent(replicate_api_key="...")
    result = await agent.process(AgentInput(
        session_id="test",
        data={"user_prompt": "pink tennis shoes", "options": {"num_images": 6}}
    ))
    assert result.success
    assert len(result.data["image_prompts"]) == 6
    assert result.data["consistency_seed"] > 0
    print("✅ Prompt Parser works!")

# Deliverable: Prompt parser returns structured prompts + seed
```

---

#### Person C (Agent Developer 2) - Hours 0-4

**Hour 0-2: FFmpeg Research & Testing**
```bash
# Tasks:
- [ ] Install FFmpeg locally: brew install ffmpeg (Mac) or apt install ffmpeg (Linux)
- [ ] Run all examples from FFMPEG_COMMANDS.md
- [ ] Test 1: Normalize clip to 1080p
    ffmpeg -i test_input.mp4 -vf "scale=1920:1080,fps=30" -c:v libx264 -crf 23 output.mp4

- [ ] Test 2: Concatenate 2 clips
    (create concat_list.txt, run concat command)

- [ ] Test 3: Add text overlay
    ffmpeg -i input.mp4 -vf "drawtext=text='TEST':fontsize=72:x=100:y=100" output.mp4

- [ ] Test 4: Add background music
    (test audio mixing command)

- [ ] Document any errors or issues

# Deliverable: All FFmpeg commands work locally
```

**Hour 2-4: Storage Service Setup**
```python
# Tasks:
- [ ] Choose storage: Cloudflare R2 (recommended) or AWS S3
- [ ] Create bucket/namespace
- [ ] Get access keys
- [ ] Create services/storage.py
- [ ] Implement StorageService class:
    - async def download_and_upload(replicate_url, asset_type, session_id, asset_id)
    - def generate_presigned_url(storage_path, expires_in=3600)

- [ ] Test uploading sample image
- [ ] Test generating presigned URL
- [ ] Verify URL is accessible in browser

# Test script:
async def test_storage():
    storage = StorageService()
    result = await storage.download_and_upload(
        replicate_url="https://replicate.delivery/pbxt/sample.png",
        asset_type="image",
        session_id="test",
        asset_id="img_001"
    )
    assert result["url"].startswith("https://")
    print(f"✅ Uploaded to: {result['url']}")

# Deliverable: Can upload file to S3/R2 and get URL back
```

---

#### Person D (Frontend Lead) - Hours 0-4

**Hour 0-1: Next.js Setup**
```bash
# Tasks:
- [ ] Create Next.js 14 app with App Router:
    npx create-next-app@latest frontend --typescript --tailwind --app

- [ ] Install dependencies:
    npm install @radix-ui/react-* (for shadcn/ui components)
    npm install clsx tailwind-merge

- [ ] Set up Tailwind CSS config
- [ ] Create components/ui/ folder for shadcn components
- [ ] Initialize shadcn/ui:
    npx shadcn-ui@latest init

# Deliverable: npm run dev works, see Next.js welcome page
```

**Hour 1-2: API Client & Types**
```typescript
# Tasks:
- [ ] Create lib/types.ts with TypeScript interfaces:
    - User, Session, Asset, ImageAsset, VideoAsset, GenerationCost
    - ProgressUpdate, TextConfig, AudioConfig

- [ ] Create lib/api.ts with fetch wrappers:
    - login(email, password)
    - generateImages(sessionId, prompt, options)
    - getSession(sessionId)
    - saveApprovedImages(sessionId, imageIds)
    - generateClips(sessionId, videoPrompt, clipConfig)
    - saveApprovedClips(sessionId, clipIds)
    - composeFinalVideo(sessionId, textConfig, audioConfig)

- [ ] Create lib/auth.ts:
    - getAuthToken(), setAuthToken(), isAuthenticated()

# Deliverable: API client can call (stubbed) backend endpoints
```

**Hour 2-3: WebSocket Hook**
```typescript
# Tasks:
- [ ] Create hooks/useWebSocket.ts (copy from TECHNICAL_ARCHITECTURE.md Section 4.3)
- [ ] Implement auto-reconnection with exponential backoff
- [ ] Test WebSocket connection to backend ws://localhost:8000/ws/test-session
- [ ] Add ping/pong heartbeat handling

# Test component:
const TestWebSocket = () => {
  const { isConnected, lastMessage } = useWebSocket("test-session")
  return <div>Connected: {isConnected ? "✅" : "❌"}</div>
}

# Deliverable: WebSocket connects and receives messages
```

**Hour 3-4: Login Screen**
```typescript
# Tasks:
- [ ] Create app/page.tsx (landing/login page)
- [ ] Create components/auth/LoginForm.tsx
- [ ] Implement login flow:
    - Email input (pre-filled: demo@example.com)
    - Password input (pre-filled: demo123)
    - "Start Creating" button
    - On success: store JWT, redirect to /generate/images

- [ ] Add loading state
- [ ] Add error handling
- [ ] Style with Tailwind CSS

# Deliverable: Can login and see redirect (even if target page blank)
```

---

#### Person E (DevOps) - Hours 0-4

**Hour 0-1: Railway Backend Setup**
```bash
# Tasks:
- [ ] Create Railway account (if needed)
- [ ] Install Railway CLI: npm install -g @railway/cli
- [ ] Login: railway login
- [ ] Create new Railway project: railway init
- [ ] Create PostgreSQL database in Railway dashboard
- [ ] Copy DATABASE_URL connection string
- [ ] Test connection locally:
    psql DATABASE_URL

# Deliverable: Railway project + PostgreSQL database exists
```

**Hour 1-2: Vercel Frontend Setup**
```bash
# Tasks:
- [ ] Create Vercel account (if needed)
- [ ] Install Vercel CLI: npm install -g vercel
- [ ] Login: vercel login
- [ ] Link frontend project: vercel link
- [ ] Set environment variables:
    vercel env add NEXT_PUBLIC_API_URL
    vercel env add NEXT_PUBLIC_WS_URL

# Deliverable: Vercel project configured
```

**Hour 2-3: Dockerfile for Backend**
```dockerfile
# Tasks:
- [ ] Create backend/Dockerfile (copy from TECHNICAL_ARCHITECTURE.md Section 9.2)
- [ ] Install FFmpeg in container
- [ ] Install fonts for text overlays
- [ ] Test build locally:
    docker build -t ai-ad-generator-backend .
    docker run -p 8000:8000 ai-ad-generator-backend

# Deliverable: Docker container runs FFmpeg successfully
```

**Hour 3-4: Deploy to Staging**
```bash
# Tasks:
- [ ] Configure railway.toml
- [ ] Deploy backend to Railway: railway up
- [ ] Set environment variables in Railway dashboard:
    - REPLICATE_API_KEY
    - DATABASE_URL (auto-provided)
    - JWT_SECRET_KEY (generate with: openssl rand -hex 32)
    - AWS_ACCESS_KEY_ID (if using S3)
    - AWS_SECRET_ACCESS_KEY

- [ ] Test health check: curl https://your-api.railway.app/health
- [ ] Deploy frontend to Vercel: vercel --prod
- [ ] Test deployment works

# Deliverable: Staging environment deployed and accessible
```

---

### SYNC CHECKPOINT #1 (Hour 4) - 15 Minutes ⚡

**All team members join sync call**

**Verification Checklist:**
```bash
Person A:
- [ ] Orchestrator skeleton deployed locally
- [ ] All API endpoints return 200 OK
- [ ] WebSocket connection works
- [ ] Database has all tables

Person B:
- [ ] Agent interface defined
- [ ] Prompt Parser Agent returns valid JSON

Person C:
- [ ] FFmpeg commands work locally
- [ ] S3/R2 storage service uploads files

Person D:
- [ ] Login screen works
- [ ] Can call backend API
- [ ] WebSocket connects

Person E:
- [ ] Railway backend deployed
- [ ] Vercel frontend deployed
- [ ] Database accessible
```

**Go/No-Go Decision:**
- ✅ If all checked: Proceed to Phase 2
- ❌ If Person A orchestrator not ready: Person B helps Person A, delay Phase 2 by 2 hours
- ❌ If FFmpeg doesn't work: Person C investigates, prepare Plan B

---

## API Contract Definitions

### Authentication

#### POST /api/auth/login
**Request:**
```json
{
  "email": "demo@example.com",
  "password": "demo123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "demo@example.com",
    "full_name": "Demo User"
  }
}
```

---

### Image Generation

#### POST /api/generate-images
**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000" (optional),
  "user_prompt": "pink tennis shoes with white laces",
  "options": {
    "num_images": 6,
    "style_keywords": ["professional", "studio"]
  }
}
```

**Response (immediate):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "generating",
  "message": "Image generation started"
}
```

**WebSocket Progress Messages:**
```json
{
  "stage": "prompt_parsing",
  "progress": 0,
  "message": "Analyzing your prompt..."
}
```
```json
{
  "stage": "image_generation",
  "progress": 50,
  "message": "Generating image 3 of 6...",
  "current_cost": 0.15
}
```
```json
{
  "stage": "complete",
  "progress": 100,
  "message": "Images ready for review!",
  "current_cost": 0.30,
  "asset_count": 6
}
```

---

#### GET /api/sessions/{session_id}
**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "reviewing_images",
  "user_product_prompt": "pink tennis shoes",
  "generated_images": [
    {
      "id": "img_001",
      "url": "https://storage.com/sessions/550e.../images/img_001.png",
      "view_type": "front",
      "cost": 0.05,
      "user_selected": false
    }
  ],
  "total_cost": 0.30
}
```

---

#### POST /api/save-approved-images
**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "approved_image_ids": ["img_001", "img_002", "img_003", "img_004"]
}
```

**Response:**
```json
{
  "status": "success",
  "approved_count": 4,
  "message": "Images saved to mood board"
}
```

---

### Video Generation

#### POST /api/generate-clips
**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "video_prompt": "girl running on outdoor track, golden hour lighting, dynamic motion",
  "clip_config": {
    "clip_duration_seconds": 3.0
  }
}
```

**Response:**
```json
{
  "status": "generating",
  "message": "Video clip generation started"
}
```

**WebSocket Progress:**
```json
{
  "stage": "video_generation",
  "progress": 25,
  "message": "Generating clip 1 of 4...",
  "current_cost": 2.10
}
```

---

#### POST /api/save-approved-clips
**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "approved_clip_ids": ["clip_001", "clip_002", "clip_003"]
}
```

**Response:**
```json
{
  "status": "success",
  "approved_count": 3,
  "total_duration_seconds": 9.4
}
```

---

### Final Composition

#### POST /api/compose-final-video
**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "text_config": {
    "product_name": "AirRun Pro",
    "call_to_action": "Shop Now",
    "text_color": "#FFFFFF",
    "text_font": "DejaVuSans-Bold"
  },
  "audio_config": {
    "enabled": true,
    "genre": "upbeat"
  }
}
```

**Response:**
```json
{
  "status": "composing",
  "message": "Final video composition started"
}
```

**WebSocket Progress:**
```json
{
  "stage": "composition",
  "progress": 75,
  "message": "Adding text overlays...",
  "current_cost": 3.15
}
```
```json
{
  "stage": "complete",
  "progress": 100,
  "message": "Your video is ready! 🎉",
  "final_video_url": "https://storage.com/sessions/550e.../final/final_video.mp4",
  "total_cost": 3.20
}
```

---

### Cost Tracking

#### GET /api/sessions/{session_id}/costs
**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_cost": 3.20,
  "breakdown": [
    {
      "agent": "prompt_parser",
      "model": "llama-3.1-70b",
      "cost": 0.001,
      "duration": 2.5
    },
    {
      "agent": "image_generator",
      "model": "flux-pro",
      "cost": 0.30,
      "duration": 45.0
    },
    {
      "agent": "video_generator",
      "model": "stable-video-diffusion",
      "cost": 2.40,
      "duration": 180.0
    },
    {
      "agent": "compositor",
      "model": "ffmpeg",
      "cost": 0.50,
      "duration": 35.0
    }
  ]
}
```

---

## Git Branching Strategy

### Branch Naming Convention
```
main                 (production)
├── develop          (integration branch)
├── feature/backend-orchestrator     (Person A)
├── feature/agents-image-pipeline    (Person B)
├── feature/agents-video-pipeline    (Person C)
├── feature/frontend-ui              (Person D)
└── feature/devops-infrastructure    (Person E)
```

### Workflow
1. All developers branch from `develop`
2. Fast-track PR reviews (max 30 min response time)
3. Merge to `develop` after approval
4. Deploy `develop` to staging continuously
5. Merge `develop` → `main` for production at Hour 40

### PR Template
```markdown
## Changes
- What did you build?
- Which API endpoints/components?

## Testing
- [ ] Tested locally
- [ ] Tested on staging
- [ ] Integration tests pass

## Dependencies
- Blocks: (other PRs/people)
- Blocked by: (waiting on)

## Screenshots (if UI)
[attach]
```

---

## Integration Testing Checklist

### Hour 12 Checkpoint: Image Flow
```bash
- [ ] Can login with demo credentials
- [ ] Can enter product prompt "pink tennis shoes"
- [ ] WebSocket shows real-time progress
- [ ] 6 images appear in grid
- [ ] Can select 4 images with checkboxes
- [ ] Click "Add to Mood Board" saves to database
- [ ] Approved images shown in mood board
- [ ] Cost tracker shows $0.30
- [ ] Can navigate to video prompt screen
```

### Hour 24 Checkpoint: Video Flow
```bash
- [ ] Approved images display as reference
- [ ] Can enter video prompt "girl running in sun"
- [ ] 4 video clips generate from approved images
- [ ] Clips play in browser
- [ ] Can select 3 clips
- [ ] Approved clips saved to mood board
- [ ] Can navigate to text overlay screen
- [ ] Can add product name "AirRun Pro"
- [ ] Can add CTA "Shop Now"
- [ ] Background music toggle works
- [ ] "Generate Final Video" button starts composition
- [ ] Final video appears and plays
- [ ] Total cost shown: ~$3.20
```

### Hour 40 Checkpoint: Production Ready
```bash
- [ ] End-to-end flow works on staging
- [ ] Production deployment successful
- [ ] HTTPS works on both frontend/backend
- [ ] WebSocket connects through production
- [ ] Can download final video
- [ ] All error states handled gracefully
- [ ] Loading states look good
- [ ] Cost tracking accurate
- [ ] Demo user works
```

---

## Communication Protocols

### Slack Channels
- `#pipeline-general` - All team chat
- `#pipeline-blockers` - URGENT blockers only
- `#pipeline-deploys` - Deployment notifications

### Blocker Protocol
If blocked:
1. Post in `#pipeline-blockers` immediately
2. @mention the person you're blocked by
3. Suggest a workaround if possible
4. Person A (Backend Lead) triages and redirects help

### Dependency Communication
2 hours before you need something:
```
Example:
"@PersonB - I'll need approved images in the database by Hour 12 for video generation.
Can you confirm that's on track?"
```

### Daily Standups (if multi-day)
- Morning (Hour 0, 24): 15 minutes
- What did you complete?
- What are you working on next?
- Any blockers?

---

## Success Criteria

### Minimum Viable Product (MUST HAVE):
- [ ] User can login
- [ ] User can generate 6 product images from text
- [ ] User can select approved images
- [ ] User can generate video clips from approved images
- [ ] User can select approved clips
- [ ] User can add text overlay (product name + CTA)
- [ ] System generates final stitched 1080p video
- [ ] Final video includes text overlays
- [ ] Real-time progress indicators work
- [ ] Cost tracking accurate (<$200/video)
- [ ] Deployed to production

### Nice to Have (If Time):
- [ ] Background music generation
- [ ] Drag-and-drop clip reordering
- [ ] Multiple font options
- [ ] Session recovery after refresh
- [ ] Mobile responsive
- [ ] Download button
- [ ] Share link

---

## Emergency Contacts & Escalation

### If Person A (Backend Lead) Falls Behind:
- Hour 0-4: Person B helps with orchestrator
- Hour 4-8: Person E helps with database queries
- Hour 8+: All hands meeting to redistribute work

### If FFmpeg Doesn't Work on Railway:
- Hour 8: Person C investigates Railway logs
- Hour 12: Try different Docker base image
- Hour 16: Fallback to Replicate video composition API (if exists)
- Hour 20: Nuclear option - ship without text overlays

### If Replicate Rate Limits:
- Switch to SDXL instead of Flux-Pro (cheaper)
- Reduce image count 6 → 4
- Use backup Replicate account

---

## Final Reminders

### Critical Success Factors:
1. **Orchestrator skeleton by Hour 4** - Everything depends on this
2. **FFmpeg validated by Hour 8** - High risk item
3. **Image flow by Hour 12** - Proves architecture works
4. **Video flow by Hour 24** - Validates end-to-end
5. **Production by Hour 40** - Leaves 8-hour buffer

### What NOT to Do:
- ❌ Don't skip sync checkpoints
- ❌ Don't work in isolation without communicating
- ❌ Don't optimize prematurely (ship first, optimize later)
- ❌ Don't add features outside MVP scope
- ❌ Don't merge without testing

### What TO Do:
- ✅ Communicate dependencies early
- ✅ Ask for help immediately when blocked
- ✅ Test integration points frequently
- ✅ Document as you go
- ✅ Commit often, push frequently

---

**Good luck team! You've got this! 💪**

---

## Appendix: Quick Reference

### Environment Variables Checklist
**Backend (.env):**
```
REPLICATE_API_KEY=
DATABASE_URL=
JWT_SECRET_KEY=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
S3_BUCKET_NAME=
FRONTEND_URL=
```

**Frontend (.env.local):**
```
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_WS_URL=
```

### Useful Commands
```bash
# Backend
cd backend
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm run dev

# Database
alembic upgrade head
alembic revision --autogenerate -m "message"

# Docker
docker build -t backend .
docker run -p 8000:8000 backend

# Deploy
railway up
vercel --prod
```

### Testing Endpoints
```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"demo123"}'

# Generate images
curl -X POST http://localhost:8000/api/generate-images \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"user_prompt":"pink tennis shoes","options":{"num_images":6}}'

# Get session
curl http://localhost:8000/api/sessions/SESSION_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```
