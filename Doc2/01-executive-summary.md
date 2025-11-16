# Executive Summary: AI Educational Video Generator

**Version:** 3.0 (Educational Pivot - Implementation-Ready)
**Owner:** Nani Skinner — Technical Project Manager
**Sprint Duration:** 48 Hours (+ 8-12 hours pre-sprint template preparation)
**Budget:** $200 development budget, target $10-15 per video production cost
**Target:** Middle School Science Education (Life Science focus)

---

## Project Goal

Build an AI-powered educational video generator that produces 60-second middle school science videos with:

- **Scientific accuracy** validated through 4-criteria Gemini rubric
- **Teacher control** at every stage (fact confirmation, script editing, visual approval)
- **Professional educational quality** (1080p, age-appropriate narration, clear diagrams)
- **Cost efficiency** (under $200 budget, target $10-15 per video)
- **Self-healing intelligence** (auto-corrects visual mismatches, falls back to text when needed)

---

## Core Innovation

**Hybrid Template + AI Pipeline with Self-Healing Validation**

- 10 hand-crafted scientifically accurate templates (5 topics × 2 variations each)
- AI generates custom variations when templates don't cover the need
- **Gemini Vision analyzes every frame** using 4-criteria rubric (scientific accuracy, label quality, age-appropriateness, visual clarity)
- **Educational Compositor self-heals** mismatches using LLM-powered decision-making
- **Auto-fallback to text slides** when visual generation fails (maintains educational integrity)
- Teacher-driven iterative workflow with strategic approval gates
- Intelligent orchestration across 5 specialized agents + frontend fact extraction

---

## Technical Stack

| Layer                   | Technology                                        | Rationale                                                                             |
| ----------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------- |
| **Frontend**            | Next.js 14 (App Router), TypeScript, Tailwind CSS | Modern React framework, handles fact extraction client-side, manages teacher workflow |
| **Backend**             | FastAPI (Python 3.11+), Pydantic v2               | High-performance async API, native type validation                                    |
| **Database**            | PostgreSQL 15 + SQLAlchemy 2.0                    | Session state, template metadata, Gemini analysis storage, cost tracking              |
| **Orchestration**       | Python Async/Await (direct function calls)        | Simple MVP pattern, easy migration to message queue post-MVP                          |
| **Script Generation**   | Replicate: Llama 3.1 70B Instruct                 | Free/low-cost, excellent structured educational output, 4-part narrative structure    |
| **Visual Templates**    | Hand-crafted PSD files (10 templates)             | Guaranteed scientific accuracy for core Life Science concepts                         |
| **Image Generation**    | DALL-E 3 (primary), Midjourney (fallback)         | Best for educational diagrams with accurate labeling and text                         |
| **Visual Validation**   | Google Gemini 1.5 Pro Vision API                  | Frame-by-frame analysis (30fps), 4-criteria rubric, scientific accuracy verification  |
| **Video Generation**    | Stable Video Diffusion (template animations)      | Cost-effective for diagram animations, template-based consistency                     |
| **LLM Decision Engine** | Replicate: Llama 3.1 70B Instruct                 | Powers Ed Compositor self-healing, substitution decisions, text slide generation      |
| **Voiceover (TTS)**     | ElevenLabs (primary), Play.ht (fallback)          | Natural-sounding, age-appropriate middle school voices                                |
| **Video Composition**   | FFmpeg 6.0 (via Python subprocess)                | Industry standard, precise timing control, supports separate audio tracks             |
| **File Storage**        | Temporary local storage → Frontend download       | No cloud storage for MVP, videos viewable/downloadable immediately                    |
| **Deployment**          | Vercel (Frontend), Railway (Backend + PostgreSQL) | Fast deployment, integrated database, demo credentials auth                           |

---

## MVP Scope (48 Hours)

### IN SCOPE:

✅ Single science domain (Life Science for middle school, ages 11-14)
✅ 10 core templates (5 topics × 2 variations):
- **Photosynthesis:** Overview + Chloroplast Detail
- **Cell Structure:** Animal Cell + Plant Cell
- **Cellular Respiration:** Mitochondria Detail + Process Flow
- **Food Chains:** Simple Chain + Food Web
- **Plant Anatomy:** Whole Plant + Vascular System

✅ 60-second educational videos (4-part structure: Hook → Concept → Process → Conclusion)
✅ Teacher input workflow: Topic + Learning Objective + Key Points + Optional uploads/links
✅ Next.js client-side fact extraction (OCR, URL parsing, text processing)
✅ AI script generation with editable 4-segment narration
✅ Template-based + AI hybrid visual generation (8-12 micro-scenes per video)
✅ Gemini frame-by-frame validation (30fps analysis, 4-criteria rubric)
✅ Self-healing Ed Compositor (LLM decisions, auto-generation, text slide fallback)
✅ 4 audio options: AI voiceover (TTS), teacher upload, instrumental music, no audio
✅ Separate audio file generation (for post-MVP editing)
✅ Real-time progress indicators (WebSocket)
✅ Cost tracking per stage ($200 development budget)
✅ Demo authentication (single shared credentials)
✅ Deployed web interface with video preview and download

### OUT OF SCOPE (Post-MVP):

❌ Multiple science domains (Physical Science, Earth Science, Chemistry)
❌ Educational song generation with lyrics
❌ Multiple grade levels (elementary, high school)
❌ Multiple video lengths (30s, 90s, 3min+)
❌ User authentication system (real accounts, personal libraries)
❌ Cloud video storage/library (permanent hosting)
❌ Video sharing features (embed codes, social sharing)
❌ A/B testing / batch generation
❌ Multiple aspect ratios (9:16, 1:1 for social media)
❌ Voiceover with multiple voice options (accents, languages)
❌ Advanced analytics (usage metrics, teacher engagement)
❌ Template library expansion beyond Life Science
❌ Message queue architecture (RabbitMQ/Redis)

---

## Cost Structure

### Per-Video Cost Breakdown (Target: $10-15)

| Component                                     | Model/Service          | Cost           | Notes                                             |
| --------------------------------------------- | ---------------------- | -------------- | ------------------------------------------------- |
| **Fact Extraction**                           | Next.js (client-side)  | $0.00          | Free - runs in browser                            |
| **Script Generation**                         | Llama 3.1 70B          | $0.01          | Nearly free LLM                                   |
| **Visual Scene Planning**                     | Llama 3.1 70B          | $0.01          | LLM-powered scene matching                        |
| **Template Customization**                    | Python/PIL/ImageMagick | $0.00          | Local processing                                  |
| **AI Image Generation** (4-6 images)          | DALL-E 3               | $0.16-0.24     | $0.04 per image, only when templates insufficient |
| **Gemini Validation** (150 frames × 8 scenes) | Gemini 1.5 Pro Vision  | $3.60          | $0.003 per frame, comprehensive analysis          |
| **Emergency Visual Generation** (0-2 images)  | DALL-E 3               | $0-0.08        | Only if self-healing needed                       |
| **TTS Voiceover** (60 seconds)                | ElevenLabs             | $0.50          | $0.30/1K chars, ~1.5K chars for 60s               |
| **Video Composition**                         | FFmpeg (local)         | $0.00          | Free - server processing                          |
| **Text Slide Generation** (if needed)         | FFmpeg (local)         | $0.00          | Fallback option                                   |
| **Total Estimated Cost**                      |                        | **$4.28-4.44** | Well under $15 target ✅                          |

**Cost Variability Factors:**
- More template matches = Lower cost (less AI generation)
- Self-healing success rate affects emergency generation costs
- Audio choice (TTS vs music vs none) changes cost
- Gemini validation is largest single cost but ensures quality

**MVP Development Budget:** $200 for testing/iteration during 48-hour sprint

---

## Key Architectural Decisions

### 1. Why Next.js Handles Fact Extraction (No Backend Agent)

- **Decision:** Frontend performs OCR, URL scraping, and fact extraction before backend involvement
- **Rationale:**
  - Reduces backend complexity (4 agents instead of 5)
  - Better user feedback (immediate client-side processing)
  - Teacher confirms facts locally before API calls
  - Eliminates network round-trip for fact validation
- **Implementation:** Next.js libraries for PDF parsing, URL fetching, text extraction

### 2. Why Gemini Runs AFTER Teacher Visual Approval

- **Decision:** Gemini analyzes visuals after teacher approves them, not before showing to teacher
- **Rationale:**
  - Reduces teacher wait time (2-3 min Gemini analysis happens during composition)
  - Teacher sees visuals faster (immediate feedback loop)
  - Ed Compositor has validation data when it needs it
  - Teacher approval is final gate (no changes after this point)
- **Trade-off:** Teacher might approve visuals that Gemini later flags (but Ed Compositor self-heals)

### 3. Why Text Slide Fallback for Failed Visuals

- **Decision:** Generate educational text slides when visual generation fails after 3 attempts
- **Rationale:**
  - **Educational integrity over aesthetics** - Never show scientifically incorrect content
  - Teacher always receives a complete 60-second video
  - Text slides are still pedagogically valuable (clear concept explanation)
  - Maintains trust (teachers won't use tools that mislead students)
  - Better than blank screens or mismatched visuals
- **Implementation:** Black background + white text + key terms highlighted + disclaimer

### 4. Why 4-Criteria Gemini Rubric

- **Decision:** Validate visuals on 4 dimensions instead of binary pass/fail
- **Criteria:**
  1. Scientific Accuracy (facts, processes, relationships)
  2. Label Quality (spelling, placement, clarity)
  3. Age-Appropriateness (middle school complexity)
  4. Visual Clarity (organization, readability)
- **Rationale:**
  - Multi-dimensional quality assessment
  - Actionable feedback for retry improvements
  - Better Ed Compositor decision-making (knows _why_ something failed)
  - Worth the slight cost increase ($0.003 vs $0.0025 per image)
- **Acceptance:** All 4 must pass + confidence >85%

### 5. Why 10 Templates (Not More)

- **Decision:** 5 topics × 2 variations = 10 total hand-crafted templates for MVP
- **Rationale:**
  - Achievable in pre-sprint preparation (8-12 hours work)
  - Covers most common middle school Life Science lessons
  - Leaves room for AI-generated variations when needed
  - Can expand to 15-20 templates post-MVP based on usage data
- **Coverage:** Photosynthesis, cells, respiration, food chains, plant anatomy

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Video generation time | <5 minutes | Login to download |
| Cost per video | <$5.00 | Database cost tracking |
| Template usage rate | >60% | Visual metadata analysis |
| Scientific accuracy | 100% | Gemini validation + teacher review |
| Student comprehension | >80% | Post-MVP quiz scores |

---

**Document Status:** Implementation-Ready
**Last Updated:** January 15, 2025
