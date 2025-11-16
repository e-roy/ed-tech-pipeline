# Multi-Agent Architecture

**Document:** 03 - Multi-Agent Architecture
**Version:** 3.0
**Last Updated:** January 15, 2025

---

## Table of Contents

1. [System Architecture Diagram](#1-system-architecture-diagram)
2. [Agent Responsibilities](#2-agent-responsibilities)
3. [Data Flow Pattern](#3-data-flow-pattern)
4. [Communication Patterns](#4-communication-patterns)

---

## 1. System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 14)                         │
│  ┌──────────────┐  ┌───────────────┐  ┌────────────────────┐  │
│  │  Login UI    │→ │ Fact          │→ │  Script Review     │  │
│  │              │  │ Extraction    │  │  & Approval        │  │
│  │              │  │ (Client-Side) │  │                    │  │
│  └──────────────┘  └───────────────┘  └────────────────────┘  │
│                                                                  │
│  ┌──────────────┐  ┌───────────────┐  ┌────────────────────┐  │
│  │ Visual       │→ │ Audio         │→ │  Final Video       │  │
│  │ Review       │  │ Selection     │  │  Output            │  │
│  │ (FINAL GATE) │  │               │  │                    │  │
│  └──────────────┘  └───────────────┘  └────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API + WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│              BACKEND ORCHESTRATOR (FastAPI)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Session State Manager                           │  │
│  │  - Load/Save session from PostgreSQL                     │  │
│  │  - Track generation costs                                │  │
│  │  - Emit WebSocket progress events                        │  │
│  │  - Coordinate sequential agent execution                 │  │
│  └───────────────────┬──────────────────────────────────────┘  │
│                      │                                           │
│  ┌───────────────────▼──────────────────────────────────────┐  │
│  │        Agent Coordinator (Direct Async Calls)             │  │
│  │   Manages sequential agent execution with error handling │  │
│  └─┬──────────┬───────────┬──────────────┬──────────────────┘  │
│    │          │           │              │                      │
│ ┌──▼───────┐ ┌▼────────┐ ┌▼───────────┐ ┌▼──────────────────┐ │
│ │ Agent 2  │ │ Agent 3 │ │  Agent 4   │ │   Agent 5         │ │
│ │Narrative │ │ Visual  │ │   Audio    │ │  Educational      │ │
│ │ Builder  │ │Pipeline │ │  Pipeline  │ │  Compositor       │ │
│ │          │ │         │ │            │ │  (Self-Healing)   │ │
│ └──────────┘ └─────────┘ └────────────┘ └───────────────────┘ │
│                    │                              │              │
│                    │                              │              │
│                    ▼                              ▼              │
│           ┌─────────────────┐          ┌──────────────────┐    │
│           │  Template       │          │  LLM Decision    │    │
│           │  Library        │          │  Engine          │    │
│           │  (10 PSD files) │          │  (Llama 3.1)     │    │
│           └─────────────────┘          └──────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    EXTERNAL SERVICES                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │  Replicate   │  │  DALL-E 3    │  │  Gemini 1.5 Pro      │ │
│  │  Llama 3.1   │  │  (OpenAI)    │  │  Vision API          │ │
│  │  (LLM)       │  │  (Images)    │  │  (Validation)        │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │  Stable      │  │  ElevenLabs  │  │     FFmpeg           │ │
│  │  Video Diff  │  │  (TTS)       │  │  (Composition)       │ │
│  │  (Animation) │  │              │  │                      │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                  DATABASE (PostgreSQL)                           │
│  - sessions table (state management)                             │
│  - assets table (visual URLs, audio files)                      │
│  - gemini_validations table (frame analysis JSONs)              │
│  - generation_costs table (cost tracking)                        │
│  - templates table (template metadata)                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Agent Responsibilities

### Agent 1: REMOVED
**Fact extraction handled by Next.js frontend**

---

### Agent 2: Narrative Builder

**Responsibility:** Transform confirmed facts and learning objectives into a 4-part educational script

**Input:**
- Topic (string)
- Learning objective (string)
- Confirmed facts (key concepts, definitions, relationships)
- Target duration (60 seconds)
- Grade level (6-7)

**Output:**
- 4-part script (Hook → Concept → Process → Conclusion)
- Visual guidance for each segment
- Key concepts per segment
- Reading level analysis
- Cost: ~$0.01

**Technology:**
- Replicate: Llama 3.1 70B Instruct
- Structured JSON output
- 4-segment educational narrative

**Success Criteria:**
- Total duration 55-65 seconds
- Reading level 6-7
- All confirmed facts included
- Clear visual guidance provided

---

### Agent 3: Visual Pipeline

**Responsibility:** Generate 8-12 educational visuals using hybrid template + AI approach

**Input:**
- Approved script with 4 segments
- Topic category
- Template library access
- Visual guidance from script

**Output:**
- 8-12 visual URLs (images/animations)
- Mix of template-based and AI-generated
- Metadata (type, cost, source, duration)
- Total cost: $0.00-$0.24

**Technology:**
- Template library (10 hand-crafted PSDs)
- DALL-E 3 for AI generation
- PIL/ImageMagick for template customization
- Llama 3.1 for scene planning

**Success Criteria:**
- 60%+ template usage
- Visuals match script semantically
- All segments have visual coverage
- Scientific accuracy maintained

---

### Agent 4: Audio Pipeline

**Responsibility:** Generate or process audio for educational videos

**Input:**
- Audio choice (TTS / upload / music / none)
- Script segments (for TTS)
- Voice selection
- Audio file (for upload)

**Output:**
- 4 separate audio segment files
- Combined 60-second audio track
- Metadata (duration, format)
- Cost: $0.00-$0.50

**Technology:**
- ElevenLabs (primary TTS)
- Play.ht (fallback TTS)
- Stock music library
- Teacher upload processing

**Success Criteria:**
- Audio syncs with 60-second duration
- Clear, age-appropriate narration
- No clipping or distortion
- Segment files align with script

---

### Agent 5: Educational Compositor (Self-Healing)

**Responsibility:** Stitch all assets together with intelligent validation and self-healing

**Input:**
- Script (4 segments)
- Visuals (8-12 assets)
- Gemini validation JSONs
- Audio files (4 segments)
- Composition settings

**Output:**
- Final MP4 video (1080p, 60s)
- 4 separate audio MP3 files
- Self-healing summary
- Composition log
- Cost: $0.00-$0.08 (emergency generation)

**Technology:**
- FFmpeg 6.0 for composition
- Llama 3.1 for LLM decisions
- DALL-E 3 for emergency generation
- Text slide generator (fallback)

**Self-Healing Process:**
1. Read Gemini validation JSONs
2. Detect mismatches (4-criteria check)
3. LLM decision: substitute / generate / text slide
4. Execute healing action
5. Compose with FFmpeg

**Success Criteria:**
- 100% completion rate (never fails)
- Mismatches detected and corrected
- Text slides used as last resort
- Final video is 55-65 seconds

---

### Gemini Vision API (Critical Component)

**Responsibility:** Validate educational visuals frame-by-frame using 4-criteria rubric

**Called By:** Orchestrator (AFTER teacher visual approval, BEFORE compositor)

**Input:**
- Visual URLs (8-12 images/animations)
- Expected concepts from script
- Narration text

**Output:**
- Frame-by-frame analysis JSONs
- 4-criteria validation per visual:
  1. Scientific Accuracy
  2. Label Quality
  3. Age-Appropriateness
  4. Visual Clarity
- Overall confidence score
- Recommended action (accept/retry)
- Cost: $3.60 (30fps analysis)

**Technology:**
- Google Gemini 1.5 Pro Vision API
- Frame extraction (FFmpeg)
- Multi-dimensional rubric evaluation

**Success Criteria:**
- All 4 criteria pass + confidence >85%
- Actionable feedback for failures
- Frame-level granularity (30fps)

---

## 3. Data Flow Pattern

```
Teacher Input (Next.js)
    ↓
Confirmed Facts
    ↓
[Agent 2: Narrative Builder] → Script → [Teacher Approves] ✓
    ↓
[Agent 3: Visual Pipeline] → Visuals → [Teacher Approves] ✓✓ (FINAL GATE)
    ↓
[Gemini Vision Analysis] → Validation JSONs (Backend only, teacher doesn't see)
    ↓
[Agent 4: Audio Pipeline] → Audio Files
    ↓
[Agent 5: Ed Compositor]
    ├─ Reads Gemini JSONs
    ├─ Detects mismatches
    ├─ LLM makes decisions
    ├─ Self-heals (substitute/generate/text slide)
    └─ Renders final video
    ↓
Final MP4 + Separate Audio → Teacher Downloads
```

### Data Flow Characteristics

**Sequential Execution:**
- Agents run one after another (not parallel)
- Each agent waits for previous completion
- Teacher approval gates control flow

**State Management:**
- PostgreSQL stores session state
- Each agent updates database
- Orchestrator loads/saves state

**Error Handling:**
- Agents return success/failure
- Orchestrator handles retries
- Ed Compositor never fails (uses fallbacks)

---

## 4. Communication Patterns

### 4.1 Frontend → Backend

**Protocol:** REST API + WebSocket

**REST Endpoints:**
- `POST /api/generate-script` - Trigger script generation
- `POST /api/generate-visuals` - Trigger visual generation
- `POST /api/approve-visuals-final` - Final approval gate
- `POST /api/select-audio` - Trigger composition pipeline

**WebSocket:**
- Real-time progress updates (every 2-5 seconds)
- Cost tracking updates
- Stage transitions
- Error notifications

### 4.2 Orchestrator → Agents

**Protocol:** Direct async function calls (Python async/await)

**Pattern:**
```python
async def generate_video(session_id: str):
    # Load session
    session = await db.get_session(session_id)

    # Agent 2: Script
    script_result = await narrative_builder.process(
        AgentInput(session_id=session_id, data={...})
    )
    await db.save_script(session_id, script_result.data)
    await ws_manager.send_progress(session_id, "script_complete", 15)

    # Agent 3: Visuals
    visual_result = await visual_pipeline.process(
        AgentInput(session_id=session_id, data={...})
    )
    await db.save_visuals(session_id, visual_result.data)
    await ws_manager.send_progress(session_id, "visuals_complete", 60)

    # ... continue pipeline
```

**Error Handling:**
```python
try:
    result = await agent.process(input)
except Exception as e:
    await ws_manager.broadcast_error(session_id, str(e))
    await db.mark_failed(session_id)
    raise
```

### 4.3 Agents → External Services

**API Calls:**
- Replicate (Llama 3.1): Async HTTP POST
- OpenAI (DALL-E 3): Async HTTP POST with polling
- Google (Gemini Vision): Async HTTP POST
- ElevenLabs (TTS): Async HTTP POST

**Retry Logic:**
- Max 3 retries per API call
- Exponential backoff (2s, 4s, 8s)
- Circuit breaker for service outages

**Rate Limiting:**
- Respect API rate limits
- Queue requests if needed
- Cost tracking per call

---

## 5. Orchestrator Implementation

### 5.1 Session State Manager

```python
class SessionStateManager:
    def __init__(self, db: Session):
        self.db = db

    async def load_session(self, session_id: str) -> SessionModel:
        """Load session from database"""
        return await self.db.query(SessionModel).filter(
            SessionModel.id == session_id
        ).first()

    async def save_session(self, session: SessionModel):
        """Save session to database"""
        session.updated_at = datetime.now()
        await self.db.commit()

    async def update_stage(self, session_id: str, stage: SessionStage):
        """Update session stage"""
        session = await self.load_session(session_id)
        session.stage = stage
        await self.save_session(session)
```

### 5.2 Agent Coordinator

```python
class AgentCoordinator:
    def __init__(
        self,
        narrative_builder: NarrativeBuilderAgent,
        visual_pipeline: VisualPipelineAgent,
        audio_pipeline: AudioPipelineAgent,
        ed_compositor: EducationalCompositorAgent,
        ws_manager: WebSocketManager,
        db: Session
    ):
        self.narrative_builder = narrative_builder
        self.visual_pipeline = visual_pipeline
        self.audio_pipeline = audio_pipeline
        self.ed_compositor = ed_compositor
        self.ws_manager = ws_manager
        self.db = db

    async def generate_script(
        self,
        session_id: str,
        topic: str,
        learning_objective: str,
        confirmed_facts: dict
    ) -> dict:
        """Coordinate script generation"""

        # Update progress
        await self.ws_manager.send_progress(
            session_id, "script_generation", 0, "Starting script generation..."
        )

        # Call Agent 2
        input_data = AgentInput(
            session_id=session_id,
            data={
                "topic": topic,
                "learning_objective": learning_objective,
                "confirmed_facts": confirmed_facts,
                "target_duration": 60,
                "grade_level": "6-7"
            }
        )

        result = await self.narrative_builder.process(input_data)

        if result.success:
            # Save to database
            await self.db.save_script(session_id, result.data["script"])

            # Update progress
            await self.ws_manager.send_progress(
                session_id,
                "script_generation",
                100,
                "Script ready!",
                current_cost=result.cost
            )

            return {"status": "success", "script": result.data["script"]}
        else:
            await self.ws_manager.broadcast_error(session_id, result.error)
            return {"status": "error", "error": result.error}
```

---

## 6. Architecture Decision Records

### ADR-001: Why Direct Function Calls Instead of Message Queue?

**Context:** Need to coordinate 4 agents sequentially

**Decision:** Use Python async/await with direct function calls

**Rationale:**
- Simpler MVP implementation (48 hours)
- Fewer moving parts to debug
- Sequential execution is natural fit
- Easy to migrate to message queue post-MVP

**Consequences:**
- ✅ Faster development
- ✅ Easier debugging
- ✅ Lower operational complexity
- ❌ Agents must be in same process
- ❌ Harder to scale horizontally (post-MVP concern)

**Post-MVP Migration:** Replace with RabbitMQ or Redis Streams

---

### ADR-002: Why Next.js Handles Fact Extraction?

**Context:** Need to extract facts from PDFs and URLs

**Decision:** Implement in Next.js frontend (client-side)

**Rationale:**
- Reduces backend agent count (4 instead of 5)
- Better UX (immediate feedback)
- Teacher confirms facts before API calls
- Eliminates network round-trip

**Consequences:**
- ✅ Faster user feedback
- ✅ Simpler backend
- ✅ Reduced API calls
- ❌ Larger frontend bundle size
- ❌ Browser limitations (file size)

---

### ADR-003: Why Gemini After Teacher Approval?

**Context:** When to validate visuals with Gemini?

**Decision:** Run Gemini AFTER teacher approves visuals

**Rationale:**
- Teacher sees visuals faster (no 2-3 min wait)
- Ed Compositor has validation data when needed
- Teacher approval is final gate anyway
- Self-healing handles any issues

**Consequences:**
- ✅ Better UX (reduced wait time)
- ✅ Parallel processing possible
- ❌ Teacher might approve bad visuals
- ✅ Ed Compositor fixes them anyway

---

**Document Status:** Implementation-Ready
**Last Updated:** January 15, 2025
