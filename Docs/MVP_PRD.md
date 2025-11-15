# MVP PRD: AI Ad Video Generator

### Version: 2.0 (Implementation-Ready)

### Owner: Nani Skinner — Technical Project Manager

### Sprint Duration: 48 Hours

### Budget: $200 per video generation

### Target: Video Ad Generation Competition

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [User Journey & UI Specifications](#2-user-journey--ui-specifications)
3. [Multi-Agent Architecture](#3-multi-agent-architecture)
4. [Agent Specifications](#4-agent-specifications)
5. [Data Models & Database Schema](#5-data-models--database-schema)
6. [API Endpoints](#6-api-endpoints)
7. [Frontend Components](#7-frontend-components)
8. [Model Selection & Cost Strategy](#8-model-selection--cost-strategy)
9. [Progress Indicators & WebSocket](#9-progress-indicators--websocket)
10. [Implementation Sequence](#10-implementation-sequence)
11. [Success Criteria](#11-success-criteria)
12. [Testing Strategy](#12-testing-strategy)
13. [Deployment Plan](#13-deployment-plan)

---

## 1. Executive Summary

### 1.1 Project Goal

Build an AI-powered ad video generator that produces 8-12 second product advertisement videos with:

- **Visual consistency** across all clips (same product appearance)
- **User control** at every stage (image selection, clip selection)
- **Professional output** (1080p, synchronized audio, text overlays)
- **Cost efficiency** (under $200 per final video)

### 1.2 Core Innovation

**Image-to-Video Pipeline with Multi-Agent Orchestration**

- Generate consistent product images using seed-controlled generation
- Convert approved images into video clips (Image-to-Video prevents hallucination)
- User-driven iterative workflow with selection gates
- Intelligent LLM orchestration across 4 specialized agents

### 1.3 Technical Stack

| Layer                 | Technology                                                    | Rationale                                                 |
| --------------------- | ------------------------------------------------------------- | --------------------------------------------------------- |
| **Frontend**          | Next.js 14 (App Router), TypeScript, Tailwind CSS             | Modern React framework, type safety, rapid UI development |
| **Backend**           | FastAPI (Python 3.11+), Pydantic v2                           | High-performance async API, native type validation        |
| **Database**          | PostgreSQL 15 + SQLAlchemy 2.0                                | Persistent mood board, session state management           |
| **Orchestration**     | Python Async/Await (direct function calls)                    | Simple MVP pattern, easy migration to message queue       |
| **Image Generation**  | Replicate: Flux-Pro (primary), SDXL (fallback)                | Best product photography quality, seed support            |
| **Video Generation**  | Replicate: Stable Video Diffusion (MVP), Runway Gen-2 (final) | Image-to-Video capability, cost-effective                 |
| **LLM Agents**        | Replicate: Llama 3.1 70B Instruct                             | Free/low-cost, excellent structured output                |
| **Audio Generation**  | Replicate: MusicGen (optional feature)                        | Background music for ads                                  |
| **Video Composition** | FFmpeg 6.0 (via Python subprocess)                            | Industry standard, powerful stitching                     |
| **Deployment**        | Vercel (Frontend), Railway (Backend + PostgreSQL)             | Fast deployment, integrated database                      |

### 1.4 MVP Scope (48 Hours)

**IN SCOPE:**
✅ Single product type (footwear) ad generation
✅ 4-8 image generation with seed consistency
✅ Image selection with mood board (PostgreSQL-backed)
✅ 2-6 video clip generation from approved images
✅ Clip selection and final composition (8-12 seconds)
✅ Text overlay (product name, CTA)
✅ Background music (optional toggle)
✅ Real-time progress indicators (WebSocket)
✅ Cost tracking per stage
✅ Deployed web interface

**OUT OF SCOPE (Post-MVP):**
❌ Multiple product categories
❌ A/B testing / batch generation
❌ Multiple aspect ratios (9:16, 1:1)
❌ Advanced style transfer / LoRA models
❌ Voiceover generation
❌ User authentication (demo credentials only)
❌ Message queue architecture

---

## 2. User Journey & UI Specifications

### 2.1 Complete User Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Orchestrator
    participant PromptParser
    participant ImageGen
    participant VideoGen
    participant Compositor
    participant Database

    User->>Frontend: 1. Login (demo credentials)
    Frontend->>Orchestrator: Create session
    Orchestrator->>Database: Save session

    User->>Frontend: 2. Enter product prompt
    Frontend->>Orchestrator: POST /api/generate-images
    Orchestrator->>PromptParser: Parse prompt
    PromptParser-->>Orchestrator: Structured prompts + seed
    Orchestrator->>ImageGen: Generate 4-8 images
    ImageGen-->>Orchestrator: Image URLs
    Orchestrator->>Database: Save images
    Orchestrator-->>Frontend: WebSocket: Progress updates
    Frontend-->>User: Display images with checkboxes

    User->>Frontend: 3. Select approved images
    Frontend->>Orchestrator: POST /api/save-approved-images
    Orchestrator->>Database: Update session

    User->>Frontend: 4. Enter video prompt
    Frontend->>Orchestrator: POST /api/generate-clips
    Orchestrator->>VideoGen: Generate clips from images
    VideoGen-->>Orchestrator: Video clip URLs
    Orchestrator->>Database: Save clips
    Orchestrator-->>Frontend: WebSocket: Progress updates
    Frontend-->>User: Display clips with checkboxes

    User->>Frontend: 5. Select approved clips
    Frontend->>Orchestrator: POST /api/save-approved-clips
    Orchestrator->>Database: Update session

    User->>Frontend: 6. Enter text overlay
    Frontend->>Orchestrator: POST /api/compose-final-video
    Orchestrator->>Compositor: Stitch clips + audio + text
    Compositor-->>Orchestrator: Final MP4 URL
    Orchestrator->>Database: Save final video
    Orchestrator-->>Frontend: WebSocket: Complete
    Frontend-->>User: Display video + download
```

### 2.2 Screen-by-Screen Breakdown

#### Screen 1: Login

**UI Elements:**

- Simple centered card with:
  - "AI Ad Video Generator" heading
  - Email input (pre-filled: `demo@example.com`)
  - Password input (pre-filled: `demo123`)
  - "Start Creating" button
- **Action:** Creates session in database, redirects to product prompt

#### Screen 2: Product Prompt & Image Generation

**UI Elements:**

- **Header:** "Step 1: Generate Product Images"
- **Main Input:**
  - Large textarea: "Describe your product..."
  - Placeholder: "pink tennis shoes with white laces"
  - Character limit: 200
- **Advanced Options (collapsible):**
  - Number of images: Slider (4-8, default: 6)
  - Style keywords: Multi-select chips (professional, studio, lifestyle, etc.)
- **Action Button:** "Generate Images" → Shows loading state
- **Progress Indicator:**
  - "Parsing prompt..." → "Generating image 1 of 6..." → "Complete!"
  - Progress bar (0-100%)

**Generated Images Display:**

- Grid layout (2x3 for 6 images)
- Each image card:
  - Image preview (aspect ratio 1:1)
  - Checkbox overlay (top-right)
  - Generation cost badge (bottom-right): "$0.05"
- **Footer:**
  - "Selected: 4 of 6 images"
  - Total cost: "$0.30"
  - "Add to Mood Board" button (disabled until ≥2 selected)

#### Screen 3: Mood Board (Images)

**UI Elements:**

- **Header:** "Mood Board - Product Images"
- **Approved Images Section:**
  - Grid of selected images (larger size)
  - Each with "Remove" button
- **Right Panel:**
  - Session info: Product name, date
  - Cost tracker: "Images: $0.30"
- **Action:**
  - "Continue to Video Prompt" button

#### Screen 4: Video Prompt & Clip Generation

**UI Elements:**

- **Header:** "Step 2: Generate Video Clips"
- **Reference Images (collapsed):** Show approved images for context
- **Main Input:**
  - Textarea: "Describe the scene/action..."
  - Placeholder: "girl running in sun, outdoor track, golden hour lighting"
  - Character limit: 300
- **Options:**
  - Clip duration: Dropdown (2s, 3s, 4s - default: 3s)
  - Number of clips: Auto (based on approved images)
- **Action Button:** "Generate Clips"
- **Progress Indicator:**
  - "Planning scenes..." → "Generating clip 1 of 4..." → "Complete!"

**Generated Clips Display:**

- Grid layout (2x2 for 4 clips)
- Each clip card:
  - Video preview with play button
  - Checkbox overlay
  - Duration badge: "3.2s"
  - Cost badge: "$0.80"
- **Footer:**
  - "Selected: 3 of 4 clips"
  - Total cost: "$2.40"
  - "Add to Mood Board" button

#### Screen 5: Mood Board (Clips)

**UI Elements:**

- **Header:** "Mood Board - Video Clips"
- **Approved Clips Section:**
  - Grid of selected clips
  - Drag handles (for reordering - optional MVP feature)
- **Right Panel:**
  - Session info
  - Cost tracker: "Images: $0.30 | Clips: $2.40"
  - Estimated final duration: "9.6 seconds"
- **Action:**
  - "Continue to Final Composition" button

#### Screen 6: Text Overlay & Final Composition

**UI Elements:**

- **Header:** "Step 3: Add Finishing Touches"
- **Text Overlay Section:**
  - Input: Product name (e.g., "AirRun Pro")
  - Input: Call-to-action (e.g., "Shop Now")
  - Color picker for text
  - Font selector (3-4 options)
- **Audio Section:**
  - Toggle: "Add background music"
  - If enabled: Genre selector (upbeat, chill, energetic)
- **Preview Section:**
  - Show clip sequence with timestamps
  - Total duration display
- **Action Button:** "Generate Final Video"
- **Progress Indicator:**
  - "Adding text overlays..." → "Generating music..." → "Stitching clips..." → "Complete!"

#### Screen 7: Final Output

**UI Elements:**

- **Header:** "Your Video is Ready! 🎉"
- **Video Player:**
  - Large embedded player (controls enabled)
  - Autoplay on load
- **Video Info:**
  - Duration: "9.8 seconds"
  - Resolution: "1920x1080 (Full HD)"
  - File size: "12.4 MB"
  - Total cost: "$3.20"
- **Actions:**
  - "Download MP4" button (primary)
  - "Generate Another Video" button (secondary)
  - "Share Link" button (copies URL)
- **Session Summary:**
  - Images generated: 6 ($0.30)
  - Clips generated: 4 ($2.40)
  - Final composition: ($0.50)
  - Total: $3.20

---

## 3. Multi-Agent Architecture

### 3.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                       │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  Login UI   │→ │  Generation  │→ │  Mood Board UI     │    │
│  │             │  │  Workflow UI │  │  (PostgreSQL)      │    │
│  └─────────────┘  └──────────────┘  └────────────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API + WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│                   BACKEND ORCHESTRATOR (FastAPI)                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Session State Manager                        │  │
│  │  - Load/Save session from PostgreSQL                     │  │
│  │  - Track generation costs                                │  │
│  │  - Emit WebSocket progress events                        │  │
│  └───────────────────┬──────────────────────────────────────┘  │
│                      │                                           │
│  ┌───────────────────▼──────────────────────────────────────┐  │
│  │           Agent Coordinator (Direct Calls)                │  │
│  │  Manages sequential agent execution with error handling  │  │
│  └─┬─────────┬──────────┬───────────────┬───────────────────┘  │
│    │         │          │               │                       │
│ ┌──▼────┐ ┌─▼──────┐ ┌─▼──────────┐ ┌─▼────────────────┐     │
│ │ Prompt│ │ Batch  │ │   Video    │ │   Composition    │     │
│ │ Parser│ │ Image  │ │  Generator │ │     Layer        │     │
│ │ Agent │ │ Gen    │ │   Agent    │ │  (FFmpeg)        │     │
│ └───────┘ └────────┘ └────────────┘ └──────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    EXTERNAL SERVICES                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │  Replicate   │  │  Replicate   │  │     Replicate        │ │
│  │  Llama 3.1   │  │  Flux-Pro    │  │  Stable Video Diff   │ │
│  │  (LLM)       │  │  (Images)    │  │  (Video)             │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                  DATABASE (PostgreSQL)                           │
│  - sessions table (state management)                             │
│  - generation_costs table (cost tracking)                        │
│  - assets table (image/video URLs)                              │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Agent Communication Pattern

**MVP: Direct Function Calls with Async/Await**

```python
# Orchestrator coordinates agents sequentially
class VideoGenerationOrchestrator:
    def __init__(
        self,
        db: DatabaseService,
        ws_manager: WebSocketManager,
        prompt_parser: PromptParserAgent,
        image_gen: BatchImageGeneratorAgent,
        video_gen: VideoGeneratorAgent,
        compositor: CompositionLayer
    ):
        self.db = db
        self.ws_manager = ws_manager
        self.agents = {
            "prompt_parser": prompt_parser,
            "image_gen": image_gen,
            "video_gen": video_gen,
            "compositor": compositor
        }

    async def generate_images(self, session_id: str, user_prompt: str):
        """Orchestrate image generation flow"""
        try:
            # Load session
            session = await self.db.get_session(session_id)

            # Stage 1: Parse prompt
            await self.ws_manager.send_progress(session_id, {
                "stage": "prompt_parsing",
                "progress": 0,
                "message": "Analyzing your prompt..."
            })

            parsed = await self.agents["prompt_parser"].parse(user_prompt)
            session.consistency_seed = parsed["consistency_seed"]
            session.style_keywords = parsed["style_keywords"]

            # Stage 2: Generate images
            for i, prompt_data in enumerate(parsed["image_prompts"]):
                await self.ws_manager.send_progress(session_id, {
                    "stage": "image_generation",
                    "progress": int((i / len(parsed["image_prompts"])) * 100),
                    "message": f"Generating image {i+1} of {len(parsed['image_prompts'])}..."
                })

                image_result = await self.agents["image_gen"].generate(prompt_data)

                # Save to database
                asset = await self.db.create_asset(
                    session_id=session_id,
                    type="image",
                    url=image_result["url"],
                    cost=image_result["cost"],
                    metadata=image_result["metadata"]
                )
                session.generated_images.append(asset.id)

            # Save session
            await self.db.save_session(session)

            # Completion
            await self.ws_manager.send_progress(session_id, {
                "stage": "complete",
                "progress": 100,
                "message": "Images ready for review!"
            })

            return {"status": "success", "image_count": len(parsed["image_prompts"])}

        except Exception as e:
            await self.handle_error(session_id, "image_generation", e)
            raise
```

**Key Design Principles:**

1. **Sequential Execution:** Agents run one after another (not parallel) for MVP simplicity, also have a feature to call the agent before sending the request to make sure the agent is available.
2. **State Persistence:** Every stage saves to PostgreSQL before proceeding
3. **Progress Tracking:** WebSocket updates at every substep
4. **Error Handling:** Try-catch at orchestrator level, single retry logic
5. **Cost Tracking:** Log cost after each API call

### 3.3 Data Flow

```
User Input → Orchestrator → Agent → External API → Orchestrator → Database → Frontend

Example: Image Generation Flow
1. User: "pink tennis shoes" → Frontend
2. Frontend POST /api/generate-images → Orchestrator
3. Orchestrator → PromptParserAgent.parse()
4. PromptParserAgent → Replicate Llama 3.1 API
5. Replicate returns structured JSON → PromptParserAgent
6. PromptParserAgent → Orchestrator (parsed prompts)
7. Orchestrator → BatchImageGeneratorAgent.generate()
8. BatchImageGeneratorAgent → Replicate Flux-Pro API (6 times)
9. Replicate returns image URLs → BatchImageGeneratorAgent
10. BatchImageGeneratorAgent → Orchestrator (image results)
11. Orchestrator → Database (save assets + session)
12. Orchestrator → WebSocketManager (progress updates)
13. WebSocketManager → Frontend (real-time updates)
14. Frontend → User (display images)
```

---

## 4. Agent Specifications

### 4.1 Agent Interface Standard

All agents implement this interface for future queue compatibility:

```python
from typing import Protocol, TypedDict, Any
from pydantic import BaseModel

class AgentInput(BaseModel):
    """Base input model for all agents"""
    session_id: str
    data: dict[str, Any]
    metadata: dict[str, Any] = {}

class AgentOutput(BaseModel):
    """Base output model for all agents"""
    success: bool
    data: dict[str, Any]
    cost: float  # USD
    duration: float  # seconds
    error: str | None = None

class Agent(Protocol):
    """Standard interface for all agents"""
    async def process(self, input: AgentInput) -> AgentOutput:
        """Process input and return output"""
        ...
```

---

### 4.2 Prompt Parser Agent

**Purpose:** Transform user's natural language prompt into structured, optimized prompts for image generation with visual consistency controls.

**Input:**

```python
{
    "user_prompt": "pink tennis shoes",
    "options": {
        "num_images": 6,
        "style_keywords": ["professional", "studio"]
    }
}
```

**Output:**

```python
{
    "success": True,
    "consistency_seed": 789456,  # Random seed for all images
    "style_keywords": ["athletic", "professional", "vibrant"],
    "product_category": "footwear",
    "image_prompts": [
        {
            "prompt": "Professional product photography of pink athletic tennis shoes with white laces, front view, white background, studio lighting, commercial photography, sharp focus, 8K resolution",
            "negative_prompt": "blurry, distorted, low quality, watermark, text",
            "seed": 789456,
            "guidance_scale": 7.5,
            "variation_strength": 0.3
        },
        {
            "prompt": "Professional product photography of pink athletic tennis shoes with white laces, side profile view, white background, studio lighting, commercial photography, sharp focus, 8K resolution",
            "negative_prompt": "blurry, distorted, low quality, watermark, text",
            "seed": 789456,
            "guidance_scale": 7.5,
            "variation_strength": 0.3
        },
        # ... 4 more prompts (back view, top view, detail shot, lifestyle shot)
    ],
    "cost": 0.001,  # Llama 3.1 is nearly free
    "duration": 2.5
}
```

**LLM Implementation:**

```python
class PromptParserAgent:
    def __init__(self, replicate_api_key: str):
        self.api_key = replicate_api_key
        self.model = "meta/llama-3.1-70b-instruct"

    async def process(self, input: AgentInput) -> AgentOutput:
        user_prompt = input.data["user_prompt"]
        num_images = input.data.get("options", {}).get("num_images", 6)

        # Generate consistency seed
        consistency_seed = random.randint(100000, 999999)

        # Build LLM system prompt
        system_prompt = """You are a product photography AI assistant that generates detailed, consistent image prompts.

Your task:
1. Analyze the user's product description
2. Generate {num_images} distinct prompts for different angles/views
3. Maintain visual consistency using the same core description
4. Optimize for professional product photography
5. Extract style keywords

Rules:
- ALL prompts must describe the SAME product (same colors, style, design)
- Use professional photography terminology
- Include lighting, background, and quality descriptors
- Vary only the ANGLE/VIEW (front, side, back, top, detail, lifestyle)
- Output valid JSON only

Output JSON structure:
{{
    "product_category": "string",
    "style_keywords": ["keyword1", "keyword2", ...],
    "image_prompts": [
        {{
            "prompt": "detailed prompt with angle/view specified",
            "negative_prompt": "things to avoid",
            "view_type": "front|side|back|top|detail|lifestyle"
        }},
        ...
    ]
}}"""

        # Call Replicate Llama 3.1
        start_time = time.time()
        response = await self._call_replicate_llm(
            system_prompt=system_prompt.format(num_images=num_images),
            user_prompt=f"Product description: {user_prompt}\n\nGenerate {num_images} consistent image prompts."
        )
        duration = time.time() - start_time

        # Parse JSON response
        parsed_data = json.loads(response)

        # Add seed and generation parameters to each prompt
        for prompt_obj in parsed_data["image_prompts"]:
            prompt_obj["seed"] = consistency_seed
            prompt_obj["guidance_scale"] = 7.5
            prompt_obj["variation_strength"] = 0.3

        return AgentOutput(
            success=True,
            data={
                "consistency_seed": consistency_seed,
                "style_keywords": parsed_data["style_keywords"],
                "product_category": parsed_data["product_category"],
                "image_prompts": parsed_data["image_prompts"]
            },
            cost=0.001,  # Llama 3.1 is free/very cheap
            duration=duration
        )

    async def _call_replicate_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call Replicate Llama 3.1 API"""
        import replicate

        output = await replicate.async_run(
            self.model,
            input={
                "system_prompt": system_prompt,
                "prompt": user_prompt,
                "max_tokens": 2000,
                "temperature": 0.7,
                "top_p": 0.9
            }
        )

        # Concatenate streaming output
        full_response = "".join(output)
        return full_response
```

**Example LLM Output:**

```json
{
  "product_category": "athletic footwear",
  "style_keywords": ["athletic", "vibrant", "professional", "modern"],
  "image_prompts": [
    {
      "prompt": "Professional product photography of pink athletic tennis shoes with white laces, front view facing camera, white seamless background, studio lighting with soft shadows, commercial photography style, sharp focus, high detail, 8K resolution",
      "negative_prompt": "blurry, distorted, low quality, watermark, text, logos, multiple shoes, hands, people",
      "view_type": "front"
    },
    {
      "prompt": "Professional product photography of pink athletic tennis shoes with white laces, side profile view showing shoe design, white seamless background, studio lighting with soft shadows, commercial photography style, sharp focus, high detail, 8K resolution",
      "negative_prompt": "blurry, distorted, low quality, watermark, text, logos, multiple shoes, hands, people",
      "view_type": "side"
    },
    {
      "prompt": "Professional product photography of pink athletic tennis shoes with white laces, back view showing heel design, white seamless background, studio lighting with soft shadows, commercial photography style, sharp focus, high detail, 8K resolution",
      "negative_prompt": "blurry, distorted, low quality, watermark, text, logos, multiple shoes, hands, people",
      "view_type": "back"
    },
    {
      "prompt": "Professional product photography of pink athletic tennis shoes with white laces, top-down view showing laces and upper design, white seamless background, studio lighting with soft shadows, commercial photography style, sharp focus, high detail, 8K resolution",
      "negative_prompt": "blurry, distorted, low quality, watermark, text, logos, multiple shoes, hands, people",
      "view_type": "top"
    },
    {
      "prompt": "Professional product photography of pink athletic tennis shoes with white laces, extreme close-up detail shot of shoe texture and materials, white seamless background, macro photography, studio lighting, sharp focus, high detail, 8K resolution",
      "negative_prompt": "blurry, distorted, low quality, watermark, text, logos",
      "view_type": "detail"
    },
    {
      "prompt": "Lifestyle product photography of pink athletic tennis shoes with white laces on concrete outdoor surface, natural sunlight, urban athletic setting, professional photography, sharp focus, high detail, 8K resolution",
      "negative_prompt": "blurry, distorted, low quality, watermark, text, indoor, studio",
      "view_type": "lifestyle"
    }
  ]
}
```

**Cost & Performance:**

- **Model:** Replicate Llama 3.1 70B Instruct
- **Cost:** ~$0.001 per request (essentially free)
- **Duration:** 2-4 seconds
- **Tokens:** ~500 input + 1500 output = 2000 total

---

### 4.3 Batch Image Generator Agent

**Purpose:** Generate multiple product images in parallel using structured prompts from Prompt Parser Agent, ensuring visual consistency via seed control.

**Input:**

```python
{
    "image_prompts": [
        {
            "prompt": "detailed prompt...",
            "negative_prompt": "...",
            "seed": 789456,
            "guidance_scale": 7.5,
            "view_type": "front"
        },
        # ... more prompts
    ],
    "model": "flux-pro"  # or "sdxl"
}
```

**Output:**

```python
{
    "success": True,
    "images": [
        {
            "url": "https://replicate.delivery/pbxt/abc123.png",
            "view_type": "front",
            "seed": 789456,
            "cost": 0.05,
            "duration": 8.2,
            "model": "flux-pro",
            "resolution": "1024x1024"
        },
        # ... more images
    ],
    "total_cost": 0.30,
    "total_duration": 45.6
}
```

**Implementation:**

```python
class BatchImageGeneratorAgent:
    def __init__(self, replicate_api_key: str):
        self.api_key = replicate_api_key
        self.models = {
            "flux-pro": "black-forest-labs/flux-pro",
            "sdxl": "stability-ai/sdxl:latest"
        }

    async def process(self, input: AgentInput) -> AgentOutput:
        image_prompts = input.data["image_prompts"]
        model_name = input.data.get("model", "flux-pro")

        # Generate images in parallel (asyncio.gather)
        tasks = []
        for prompt_data in image_prompts:
            task = self._generate_single_image(
                model=model_name,
                prompt_data=prompt_data
            )
            tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_duration = time.time() - start_time

        # Process results
        images = []
        total_cost = 0.0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Log error but continue with other images
                logger.error(f"Image generation failed: {result}")
                continue

            images.append(result)
            total_cost += result["cost"]

        return AgentOutput(
            success=len(images) > 0,
            data={
                "images": images,
                "total_cost": total_cost
            },
            cost=total_cost,
            duration=total_duration,
            error=None if len(images) > 0 else "All image generations failed"
        )

    async def _generate_single_image(self, model: str, prompt_data: dict) -> dict:
        """Generate a single image via Replicate API"""
        import replicate

        model_id = self.models[model]

        # Build model input based on model type
        if model == "flux-pro":
            model_input = {
                "prompt": prompt_data["prompt"],
                "guidance": prompt_data["guidance_scale"],
                "num_outputs": 1,
                "aspect_ratio": "1:1",
                "output_format": "png",
                "output_quality": 100,
                "safety_tolerance": 2,
                "seed": prompt_data["seed"]
            }
        else:  # SDXL
            model_input = {
                "prompt": prompt_data["prompt"],
                "negative_prompt": prompt_data["negative_prompt"],
                "width": 1024,
                "height": 1024,
                "guidance_scale": prompt_data["guidance_scale"],
                "num_inference_steps": 50,
                "seed": prompt_data["seed"]
            }

        start = time.time()
        output = await replicate.async_run(model_id, input=model_input)
        duration = time.time() - start

        # Extract image URL (output format varies by model)
        image_url = output[0] if isinstance(output, list) else output

        # Estimate cost (Flux-Pro: $0.05, SDXL: $0.01)
        cost = 0.05 if model == "flux-pro" else 0.01

        return {
            "url": image_url,
            "view_type": prompt_data.get("view_type", "unknown"),
            "seed": prompt_data["seed"],
            "cost": cost,
            "duration": duration,
            "model": model,
            "resolution": "1024x1024"
        }
```

**Model Selection Strategy:**

| Model        | Cost/Image | Quality   | Speed | Use Case                                        |
| ------------ | ---------- | --------- | ----- | ----------------------------------------------- |
| **Flux-Pro** | $0.05      | Excellent | 8-12s | **MVP & Final Demo** (best product photography) |
| **SDXL**     | $0.01      | Good      | 6-10s | **Testing/Iteration** (cost-effective)          |

**Cost Example:**

- 6 images × $0.05 (Flux-Pro) = **$0.30 per generation session**
- Budget: $200 per video
- Remaining: $199.70 for video generation + composition

---

### 4.4 Video Generator Agent

**Purpose:** Convert approved product images into animated video clips using Image-to-Video models, maintaining visual consistency and applying user's scene description.

**Input:**

```python
{
    "approved_images": [
        {
            "id": "img_001",
            "url": "https://replicate.delivery/pbxt/image1.png",
            "view_type": "front"
        },
        {
            "id": "img_002",
            "url": "https://replicate.delivery/pbxt/image2.png",
            "view_type": "side"
        }
    ],
    "video_prompt": "girl running in sun, outdoor track, golden hour lighting, dynamic motion",
    "clip_duration": 3.0,
    "model": "stable-video-diffusion"  # or "runway-gen2"
}
```

**Output:**

```python
{
    "success": True,
    "clips": [
        {
            "id": "clip_001",
            "url": "https://replicate.delivery/pbxt/video1.mp4",
            "source_image_id": "img_001",
            "duration": 3.2,
            "resolution": "1024x576",
            "fps": 30,
            "cost": 0.80,
            "generation_time": 45.0,
            "model": "stable-video-diffusion"
        },
        {
            "id": "clip_002",
            "url": "https://replicate.delivery/pbxt/video2.mp4",
            "source_image_id": "img_002",
            "duration": 3.1,
            "resolution": "1024x576",
            "fps": 30,
            "cost": 0.80,
            "generation_time": 43.0,
            "model": "stable-video-diffusion"
        }
    ],
    "total_cost": 1.60,
    "total_duration": 88.0
}
```

**Scene Planning with LLM:**

Before generating videos, use Llama 3.1 to create scene-specific prompts for each image:

```python
async def _plan_video_scenes(
    self,
    approved_images: list[dict],
    video_prompt: str
) -> list[dict]:
    """Use LLM to create scene descriptions for each image"""

    system_prompt = """You are a video scene director for product advertisements.

Given:
- Multiple product images with different views (front, side, back, detail, lifestyle)
- User's overall scene description

Your task:
Create specific scene descriptions for each image that:
1. Maintain the user's creative vision
2. Enhance each image's unique angle/view
3. Add appropriate motion and cinematography

Output JSON:
{{
    "scenes": [
        {{
            "image_view": "front",
            "scene_prompt": "detailed scene description with motion",
            "camera_movement": "slow zoom in|pan left|static|...",
            "motion_intensity": 0.0-1.0
        }},
        ...
    ]
}}"""

    user_prompt = f"""User's scene description: {video_prompt}

Product images:
{json.dumps([{"view": img["view_type"]} for img in approved_images], indent=2)}

Create scene-specific prompts for each image view."""

    # Call Llama 3.1
    response = await self._call_replicate_llm(system_prompt, user_prompt)
    scenes = json.loads(response)

    return scenes["scenes"]
```

**Example Scene Planning Output:**

```json
{
  "scenes": [
    {
      "image_view": "front",
      "scene_prompt": "Pink tennis shoes in sharp focus as runner's feet pound outdoor track, golden hour sunlight creating dramatic shadows, dynamic forward motion with slight camera shake for energy",
      "camera_movement": "follow cam tracking forward",
      "motion_intensity": 0.7
    },
    {
      "image_view": "side",
      "scene_prompt": "Side profile of pink tennis shoes mid-stride on sunny outdoor track, warm golden light highlighting shoe details, smooth slow-motion capture of running motion",
      "camera_movement": "slow pan following motion",
      "motion_intensity": 0.6
    },
    {
      "image_view": "detail",
      "scene_prompt": "Extreme close-up of pink tennis shoe texture and materials, subtle breathing motion as if camera gently moves closer, golden hour rim lighting creating depth",
      "camera_movement": "slow zoom in",
      "motion_intensity": 0.3
    }
  ]
}
```

**Video Generation Implementation:**

```python
class VideoGeneratorAgent:
    def __init__(self, replicate_api_key: str):
        self.api_key = replicate_api_key
        self.models = {
            "stable-video-diffusion": "stability-ai/stable-video-diffusion:latest",
            "runway-gen2": "stability-ai/stable-video-diffusion:latest"  # Update with actual Runway model
        }

    async def process(self, input: AgentInput) -> AgentOutput:
        approved_images = input.data["approved_images"]
        video_prompt = input.data["video_prompt"]
        clip_duration = input.data.get("clip_duration", 3.0)
        model_name = input.data.get("model", "stable-video-diffusion")

        # Step 1: Plan scenes with LLM
        scenes = await self._plan_video_scenes(approved_images, video_prompt)

        # Step 2: Generate video clips in parallel
        tasks = []
        for i, image_data in enumerate(approved_images):
            # Match scene to image
            scene = next(
                (s for s in scenes if s["image_view"] == image_data["view_type"]),
                scenes[0]  # Fallback to first scene
            )

            task = self._generate_single_clip(
                model=model_name,
                image_url=image_data["url"],
                scene_prompt=scene["scene_prompt"],
                motion_intensity=scene["motion_intensity"],
                duration=clip_duration,
                source_image_id=image_data["id"]
            )
            tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_duration = time.time() - start_time

        # Process results
        clips = []
        total_cost = 0.0
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Video generation failed: {result}")
                continue

            clips.append(result)
            total_cost += result["cost"]

        return AgentOutput(
            success=len(clips) > 0,
            data={
                "clips": clips,
                "total_cost": total_cost
            },
            cost=total_cost,
            duration=total_duration,
            error=None if len(clips) > 0 else "All video generations failed"
        )

    async def _generate_single_clip(
        self,
        model: str,
        image_url: str,
        scene_prompt: str,
        motion_intensity: float,
        duration: float,
        source_image_id: str
    ) -> dict:
        """Generate a single video clip via Replicate API"""
        import replicate

        model_id = self.models[model]

        # Stable Video Diffusion input
        model_input = {
            "image": image_url,
            "motion_bucket_id": int(motion_intensity * 255),  # 0-255 scale
            "cond_aug": 0.02,
            "decoding_t": 14,
            "video_length": "14_frames_with_svd" if duration <= 3 else "25_frames_with_svd_xt",
            "sizing_strategy": "maintain_aspect_ratio",
            "frames_per_second": 30
        }

        start = time.time()
        output = await replicate.async_run(model_id, input=model_input)
        generation_time = time.time() - start

        # Extract video URL
        video_url = output if isinstance(output, str) else output[0]

        # Estimate cost (SVD: ~$0.25-0.30 per 3s clip)
        cost = 0.80 if model == "stable-video-diffusion" else 1.50  # Runway more expensive

        return {
            "id": f"clip_{uuid.uuid4().hex[:8]}",
            "url": video_url,
            "source_image_id": source_image_id,
            "duration": duration,
            "resolution": "1024x576",
            "fps": 30,
            "cost": cost,
            "generation_time": generation_time,
            "model": model
        }
```

**Model Selection Strategy:**

| Model                      | Cost/Clip (3s) | Quality   | Speed  | Use Case                         |
| -------------------------- | -------------- | --------- | ------ | -------------------------------- |
| **Stable Video Diffusion** | $0.80          | Good      | 40-50s | **MVP Testing** (cost-effective) |
| **Runway Gen-2**           | $1.50          | Excellent | 60-90s | **Final Demo** (best quality)    |

**Cost Example:**

- 4 clips × $0.80 (SVD) = **$3.20** for MVP testing
- 4 clips × $1.50 (Runway) = **$6.00** for final demo
- Well within $200 budget

---

### 4.5 Composition Layer

**Purpose:** Stitch approved video clips with intro/outro cards, text overlays, transitions, and optional background music into final ad video.

**Input:**

```python
{
    "selected_clips": [
        {
            "id": "clip_001",
            "url": "https://replicate.delivery/pbxt/video1.mp4",
            "duration": 3.2,
            "order": 1
        },
        {
            "id": "clip_002",
            "url": "https://replicate.delivery/pbxt/video2.mp4",
            "duration": 3.1,
            "order": 2
        }
    ],
    "text_overlay": {
        "product_name": "AirRun Pro",
        "cta": "Shop Now",
        "font": "Montserrat-Bold",
        "color": "#FFFFFF"
    },
    "audio": {
        "enabled": true,
        "genre": "upbeat"
    },
    "intro_duration": 1.0,
    "outro_duration": 1.0
}
```

**Output:**

```python
{
    "success": True,
    "final_video": {
        "url": "https://storage.example.com/final_video_xyz.mp4",
        "duration": 9.8,
        "resolution": "1920x1080",
        "fps": 30,
        "file_size_mb": 12.4,
        "format": "mp4"
    },
    "cost": 0.50,  # Cloud storage + processing
    "duration": 35.0
}
```

**Implementation (FFmpeg):**

```python
import subprocess
import tempfile
import os
from pathlib import Path

class CompositionLayer:
    def __init__(self, storage_service: StorageService):
        self.storage = storage_service

    async def process(self, input: AgentInput) -> AgentOutput:
        selected_clips = input.data["selected_clips"]
        text_overlay = input.data["text_overlay"]
        audio_config = input.data.get("audio", {})
        intro_duration = input.data.get("intro_duration", 1.0)
        outro_duration = input.data.get("outro_duration", 1.0)

        start_time = time.time()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Step 1: Download all clips
            clip_paths = await self._download_clips(selected_clips, temp_path)

            # Step 2: Generate intro card
            intro_path = await self._generate_intro_card(
                text_overlay["product_name"],
                intro_duration,
                temp_path
            )

            # Step 3: Generate outro card
            outro_path = await self._generate_outro_card(
                text_overlay["cta"],
                outro_duration,
                temp_path
            )

            # Step 4: Generate or select background music
            audio_path = None
            if audio_config.get("enabled"):
                audio_path = await self._get_background_music(
                    genre=audio_config.get("genre", "upbeat"),
                    duration=intro_duration + sum(c["duration"] for c in selected_clips) + outro_duration,
                    temp_path=temp_path
                )

            # Step 5: Stitch everything with FFmpeg
            final_video_path = await self._stitch_video(
                intro_path=intro_path,
                clip_paths=clip_paths,
                outro_path=outro_path,
                audio_path=audio_path,
                text_overlay=text_overlay,
                output_path=temp_path / "final_video.mp4"
            )

            # Step 6: Upload to storage
            final_url = await self.storage.upload_file(
                final_video_path,
                content_type="video/mp4"
            )

            duration = time.time() - start_time
            file_size_mb = os.path.getsize(final_video_path) / (1024 * 1024)

            return AgentOutput(
                success=True,
                data={
                    "final_video": {
                        "url": final_url,
                        "duration": sum(c["duration"] for c in selected_clips) + intro_duration + outro_duration,
                        "resolution": "1920x1080",
                        "fps": 30,
                        "file_size_mb": round(file_size_mb, 2),
                        "format": "mp4"
                    }
                },
                cost=0.50,  # Estimate for storage/processing
                duration=duration
            )

    async def _stitch_video(
        self,
        intro_path: Path,
        clip_paths: list[Path],
        outro_path: Path,
        audio_path: Path | None,
        text_overlay: dict,
        output_path: Path
    ) -> Path:
        """Stitch video using FFmpeg"""

        # Create concat file for FFmpeg
        concat_file = output_path.parent / "concat.txt"
        with open(concat_file, "w") as f:
            f.write(f"file '{intro_path}'\n")
            for clip_path in clip_paths:
                f.write(f"file '{clip_path}'\n")
            f.write(f"file '{outro_path}'\n")

        # Build FFmpeg command
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
        ]

        # Add audio if provided
        if audio_path:
            cmd.extend(["-i", str(audio_path)])

        # Video filters (scale to 1080p, add text overlays)
        vf_filters = [
            "scale=1920:1080:force_original_aspect_ratio=decrease",
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
            f"drawtext=text='{text_overlay['product_name']}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontsize=72:fontcolor={text_overlay['color']}:x=(w-text_w)/2:y=50:enable='between(t,1,2)'",
            f"drawtext=text='{text_overlay['cta']}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontsize=56:fontcolor={text_overlay['color']}:x=(w-text_w)/2:y=(h-text_h-50):enable='gte(t,{sum([c.duration for c in clip_paths])+1})'"
        ]

        cmd.extend([
            "-vf", ",".join(vf_filters),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
        ])

        if audio_path:
            cmd.extend([
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest"  # End when shortest stream ends
            ])

        cmd.extend([
            "-movflags", "+faststart",  # Web optimization
            "-y",  # Overwrite output
            str(output_path)
        ])

        # Execute FFmpeg
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"FFmpeg failed: {stderr.decode()}")

        return output_path

    async def _generate_intro_card(
        self,
        product_name: str,
        duration: float,
        temp_path: Path
    ) -> Path:
        """Generate intro card using FFmpeg"""
        intro_path = temp_path / "intro.mp4"

        cmd = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", f"color=c=black:s=1920x1080:d={duration}",
            "-vf", f"drawtext=text='{product_name}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontsize=96:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-y",
            str(intro_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()

        return intro_path

    async def _generate_outro_card(
        self,
        cta: str,
        duration: float,
        temp_path: Path
    ) -> Path:
        """Generate outro card using FFmpeg"""
        outro_path = temp_path / "outro.mp4"

        cmd = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", f"color=c=black:s=1920x1080:d={duration}",
            "-vf", f"drawtext=text='{cta}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontsize=96:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-y",
            str(outro_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()

        return outro_path

    async def _get_background_music(
        self,
        genre: str,
        duration: float,
        temp_path: Path
    ) -> Path:
        """Generate or fetch background music"""
        # Option A: Use Replicate MusicGen (for MVP)
        # Option B: Use stock music library (simpler for MVP)

        # For MVP, using stock music is faster
        # TODO: Implement MusicGen generation post-MVP

        # Placeholder: Download stock music from predefined library
        music_library = {
            "upbeat": "https://storage.example.com/music/upbeat_30s.mp3",
            "chill": "https://storage.example.com/music/chill_30s.mp3",
            "energetic": "https://storage.example.com/music/energetic_30s.mp3"
        }

        music_url = music_library.get(genre, music_library["upbeat"])
        music_path = temp_path / "background_music.mp3"

        # Download music file
        await self._download_file(music_url, music_path)

        return music_path
```

**Cost Breakdown:**

- Intro/outro generation: Free (FFmpeg local)
- Video stitching: Free (FFmpeg local)
- Background music: $0.00 (stock) or $0.30 (MusicGen)
- Cloud storage: $0.20 (S3/GCS)
- **Total: ~$0.50 per final video**

---

## 5. Data Models & Database Schema

### 5.1 Pydantic Models

```python
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from enum import Enum
from typing import Optional

class SessionStage(str, Enum):
    CREATED = "created"
    IMAGE_GENERATION = "image_generation"
    IMAGE_SELECTION = "image_selection"
    CLIP_GENERATION = "clip_generation"
    CLIP_SELECTION = "clip_selection"
    FINAL_COMPOSITION = "final_composition"
    COMPLETE = "complete"
    FAILED = "failed"

class AssetType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FINAL_VIDEO = "final_video"

# ==================== REQUEST MODELS ====================

class GenerateImagesRequest(BaseModel):
    session_id: str
    product_prompt: str = Field(..., min_length=3, max_length=200)
    num_images: int = Field(default=6, ge=4, le=8)
    style_keywords: list[str] = Field(default_factory=list)

class SaveApprovedImagesRequest(BaseModel):
    session_id: str
    approved_image_ids: list[str] = Field(..., min_items=2)

class GenerateClipsRequest(BaseModel):
    session_id: str
    video_prompt: str = Field(..., min_length=10, max_length=300)
    clip_duration: float = Field(default=3.0, ge=2.0, le=4.0)

class SaveApprovedClipsRequest(BaseModel):
    session_id: str
    approved_clip_ids: list[str]
    clip_order: list[str]  # Order of clips in final video

class TextOverlay(BaseModel):
    product_name: str = Field(..., max_length=50)
    cta: str = Field(..., max_length=30)
    font: str = Field(default="Montserrat-Bold")
    color: str = Field(default="#FFFFFF")

class AudioConfig(BaseModel):
    enabled: bool = Field(default=False)
    genre: str = Field(default="upbeat")

class ComposeFinalVideoRequest(BaseModel):
    session_id: str
    text_overlay: TextOverlay
    audio: AudioConfig = Field(default_factory=AudioConfig)
    intro_duration: float = Field(default=1.0)
    outro_duration: float = Field(default=1.0)

# ==================== RESPONSE MODELS ====================

class ImageAsset(BaseModel):
    id: str
    url: HttpUrl
    view_type: str
    seed: int
    cost: float
    created_at: datetime

class VideoAsset(BaseModel):
    id: str
    url: HttpUrl
    source_image_id: str
    duration: float
    resolution: str
    fps: int
    cost: float
    created_at: datetime

class FinalVideo(BaseModel):
    url: HttpUrl
    duration: float
    resolution: str
    fps: int
    file_size_mb: float
    format: str

class SessionResponse(BaseModel):
    id: str
    user_id: int
    stage: SessionStage
    product_prompt: Optional[str]
    video_prompt: Optional[str]
    consistency_seed: Optional[int]
    generated_images: list[ImageAsset]
    approved_images: list[str]  # Image IDs
    generated_clips: list[VideoAsset]
    approved_clips: list[str]  # Clip IDs
    final_video: Optional[FinalVideo]
    total_cost: float
    created_at: datetime
    updated_at: datetime

class ProgressUpdate(BaseModel):
    session_id: str
    stage: str
    progress: int  # 0-100
    message: str
    timestamp: datetime

# ==================== DATABASE MODELS (SQLAlchemy) ====================

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, nullable=False, default=1)  # Demo user for MVP
    stage = Column(SQLEnum(SessionStage), nullable=False, default=SessionStage.CREATED)

    # Prompts
    product_prompt = Column(String(200), nullable=True)
    video_prompt = Column(String(300), nullable=True)

    # Generation metadata
    consistency_seed = Column(Integer, nullable=True)
    style_keywords = Column(JSON, nullable=True)  # Array of strings

    # Asset references (JSON arrays of IDs)
    generated_image_ids = Column(JSON, default=[])
    approved_image_ids = Column(JSON, default=[])
    generated_clip_ids = Column(JSON, default=[])
    approved_clip_ids = Column(JSON, default=[])
    clip_order = Column(JSON, default=[])  # Ordered list of clip IDs
    final_video_id = Column(String(36), nullable=True)

    # Cost tracking
    total_cost = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), nullable=False, index=True)
    asset_type = Column(SQLEnum(AssetType), nullable=False)

    # Asset data
    url = Column(String(500), nullable=False)
    metadata = Column(JSON, nullable=True)  # Flexible metadata storage

    # Cost tracking
    cost = Column(Float, nullable=False, default=0.0)
    model_used = Column(String(100), nullable=True)
    generation_time = Column(Float, nullable=True)  # seconds

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class GenerationCost(Base):
    __tablename__ = "generation_costs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, index=True)
    agent_name = Column(String(50), nullable=False)
    model_used = Column(String(100), nullable=False)
    cost_usd = Column(Float, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### 5.2 Database Schema (SQL)

```sql
-- Sessions table (main state management)
CREATE TABLE sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,
    stage VARCHAR(50) NOT NULL DEFAULT 'created',

    -- Prompts
    product_prompt VARCHAR(200),
    video_prompt VARCHAR(300),

    -- Generation metadata
    consistency_seed INTEGER,
    style_keywords JSONB,

    -- Asset references
    generated_image_ids JSONB DEFAULT '[]'::jsonb,
    approved_image_ids JSONB DEFAULT '[]'::jsonb,
    generated_clip_ids JSONB DEFAULT '[]'::jsonb,
    approved_clip_ids JSONB DEFAULT '[]'::jsonb,
    clip_order JSONB DEFAULT '[]'::jsonb,
    final_video_id VARCHAR(36),

    -- Cost tracking
    total_cost DECIMAL(10, 4) DEFAULT 0.0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_stage ON sessions(stage);
CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);

-- Assets table (images, videos, audio)
CREATE TABLE assets (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    asset_type VARCHAR(20) NOT NULL,

    -- Asset data
    url VARCHAR(500) NOT NULL,
    metadata JSONB,

    -- Cost tracking
    cost DECIMAL(10, 4) NOT NULL DEFAULT 0.0,
    model_used VARCHAR(100),
    generation_time DECIMAL(10, 2),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX idx_assets_session_id ON assets(session_id);
CREATE INDEX idx_assets_type ON assets(asset_type);

-- Generation costs table (detailed cost tracking)
CREATE TABLE generation_costs (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    agent_name VARCHAR(50) NOT NULL,
    model_used VARCHAR(100) NOT NULL,
    cost_usd DECIMAL(10, 4) NOT NULL,
    duration_seconds DECIMAL(10, 2) NOT NULL,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX idx_generation_costs_session_id ON generation_costs(session_id);
CREATE INDEX idx_generation_costs_agent_name ON generation_costs(agent_name);

-- Users table (simple demo auth)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert demo user
INSERT INTO users (email, password_hash) VALUES
('demo@example.com', '$2b$12$demo_hash_placeholder');
```

---

## 6. API Endpoints

### 6.1 FastAPI Application Structure

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uuid

app = FastAPI(title="AI Ad Video Generator API", version="1.0.0")

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-vercel-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# WebSocket manager
ws_manager = WebSocketManager()
```

### 6.2 Endpoint Specifications

#### POST /api/auth/login

**Purpose:** Demo authentication (creates session for user)

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
  "success": true,
  "user_id": 1,
  "email": "demo@example.com",
  "session_token": "jwt_token_here"
}
```

#### POST /api/sessions/create

**Purpose:** Create new generation session

**Request:**

```json
{
  "user_id": 1
}
```

**Response:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "created",
  "created_at": "2025-11-14T10:30:00Z"
}
```

#### POST /api/generate-images

**Purpose:** Generate product images from prompt

**Request:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "product_prompt": "pink tennis shoes with white laces",
  "num_images": 6,
  "style_keywords": ["professional", "studio"]
}
```

**Response (Async - sends progress via WebSocket):**

```json
{
  "status": "processing",
  "estimated_duration": 45,
  "message": "Image generation started. Connect to WebSocket for progress updates."
}
```

**WebSocket Progress Updates:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "prompt_parsing",
  "progress": 10,
  "message": "Analyzing your prompt...",
  "timestamp": "2025-11-14T10:30:05Z"
}
```

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "image_generation",
  "progress": 50,
  "message": "Generating image 3 of 6...",
  "current_cost": 0.15,
  "timestamp": "2025-11-14T10:30:25Z"
}
```

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "complete",
  "progress": 100,
  "message": "Images ready for review!",
  "data": {
    "images": [
      {
        "id": "img_001",
        "url": "https://replicate.delivery/pbxt/abc123.png",
        "view_type": "front",
        "cost": 0.05
      }
      // ... more images
    ],
    "total_cost": 0.3
  },
  "timestamp": "2025-11-14T10:31:00Z"
}
```

#### GET /api/sessions/{session_id}

**Purpose:** Get current session state

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "image_selection",
  "product_prompt": "pink tennis shoes with white laces",
  "consistency_seed": 789456,
  "generated_images": [
    {
      "id": "img_001",
      "url": "https://replicate.delivery/pbxt/abc123.png",
      "view_type": "front",
      "cost": 0.05
    }
    // ... more
  ],
  "approved_images": [],
  "total_cost": 0.3,
  "created_at": "2025-11-14T10:30:00Z",
  "updated_at": "2025-11-14T10:31:00Z"
}
```

#### POST /api/save-approved-images

**Purpose:** Save user's approved images to mood board

**Request:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "approved_image_ids": ["img_001", "img_003", "img_005", "img_006"]
}
```

**Response:**

```json
{
  "success": true,
  "approved_count": 4,
  "message": "Images saved to mood board"
}
```

#### POST /api/generate-clips

**Purpose:** Generate video clips from approved images

**Request:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "video_prompt": "girl running in sun, outdoor track, golden hour lighting",
  "clip_duration": 3.0
}
```

**Response:**

```json
{
  "status": "processing",
  "estimated_duration": 180,
  "message": "Video clip generation started"
}
```

#### POST /api/save-approved-clips

**Purpose:** Save user's approved clips in desired order

**Request:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "approved_clip_ids": ["clip_001", "clip_003", "clip_004"],
  "clip_order": ["clip_001", "clip_004", "clip_003"]
}
```

**Response:**

```json
{
  "success": true,
  "approved_count": 3,
  "estimated_duration": 9.6,
  "message": "Clips saved to mood board"
}
```

#### POST /api/compose-final-video

**Purpose:** Generate final ad video with all elements

**Request:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "text_overlay": {
    "product_name": "AirRun Pro",
    "cta": "Shop Now",
    "font": "Montserrat-Bold",
    "color": "#FFFFFF"
  },
  "audio": {
    "enabled": true,
    "genre": "upbeat"
  },
  "intro_duration": 1.0,
  "outro_duration": 1.0
}
```

**Response:**

```json
{
  "status": "processing",
  "estimated_duration": 35,
  "message": "Final video composition started"
}
```

**WebSocket Final Update:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "complete",
  "progress": 100,
  "message": "Your video is ready!",
  "data": {
    "final_video": {
      "url": "https://storage.example.com/final_video_xyz.mp4",
      "duration": 9.8,
      "resolution": "1920x1080",
      "fps": 30,
      "file_size_mb": 12.4,
      "format": "mp4"
    },
    "total_cost": 3.2
  },
  "timestamp": "2025-11-14T10:45:00Z"
}
```

#### GET /api/sessions/{session_id}/costs

**Purpose:** Get detailed cost breakdown

**Response:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_cost": 3.2,
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
      "cost": 0.3,
      "duration": 45.0
    },
    {
      "agent": "video_generator",
      "model": "stable-video-diffusion",
      "cost": 2.4,
      "duration": 180.0
    },
    {
      "agent": "compositor",
      "model": "ffmpeg",
      "cost": 0.5,
      "duration": 35.0
    }
  ]
}
```

---

## 7. Frontend Components (Next.js 14)

### 7.1 Project Structure

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx (landing/login)
│   ├── dashboard/
│   │   └── page.tsx
│   ├── generate/
│   │   ├── images/page.tsx
│   │   ├── clips/page.tsx
│   │   └── final/page.tsx
│   └── result/
│       └── [sessionId]/page.tsx
├── components/
│   ├── auth/
│   │   └── LoginForm.tsx
│   ├── generation/
│   │   ├── PromptInput.tsx
│   │   ├── ImageGrid.tsx
│   │   ├── VideoGrid.tsx
│   │   ├── ProgressIndicator.tsx
│   │   └── MoodBoard.tsx
│   ├── composition/
│   │   ├── TextOverlayForm.tsx
│   │   ├── AudioSelector.tsx
│   │   └── FinalPreview.tsx
│   └── ui/
│       ├── Button.tsx
│       ├── Input.tsx
│       ├── Card.tsx
│       └── Modal.tsx
├── lib/
│   ├── api.ts (API client)
│   ├── websocket.ts (WebSocket manager)
│   └── types.ts (TypeScript interfaces)
└── hooks/
    ├── useSession.ts
    ├── useWebSocket.ts
    └── useGeneration.ts
```

### 7.2 Key Components

#### ProgressIndicator.tsx

```typescript
"use client";

import { useEffect, useState } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";
import { Progress } from "@/components/ui/progress";

interface ProgressUpdate {
  stage: string;
  progress: number;
  message: string;
  current_cost?: number;
}

export function ProgressIndicator({ sessionId }: { sessionId: string }) {
  const [update, setUpdate] = useState<ProgressUpdate | null>(null);
  const { isConnected, lastMessage } = useWebSocket(sessionId);

  useEffect(() => {
    if (lastMessage) {
      setUpdate(JSON.parse(lastMessage));
    }
  }, [lastMessage]);

  if (!update) return null;

  return (
    <div className="fixed bottom-4 right-4 w-96 bg-white shadow-lg rounded-lg p-6">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-lg">Generating...</h3>
        <span className="text-sm text-gray-500">{update.progress}%</span>
      </div>

      <Progress value={update.progress} className="mb-3" />

      <p className="text-sm text-gray-700 mb-2">{update.message}</p>

      {update.current_cost && (
        <p className="text-xs text-gray-500">
          Cost so far: ${update.current_cost.toFixed(2)}
        </p>
      )}

      <div className="flex items-center mt-2">
        <div
          className={`w-2 h-2 rounded-full mr-2 ${
            isConnected ? "bg-green-500" : "bg-red-500"
          }`}
        />
        <span className="text-xs text-gray-500">
          {isConnected ? "Connected" : "Disconnected"}
        </span>
      </div>
    </div>
  );
}
```

#### ImageGrid.tsx

```typescript
"use client";

import { useState } from "react";
import Image from "next/image";
import { ImageAsset } from "@/lib/types";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";

interface ImageGridProps {
  images: ImageAsset[];
  onApprove: (imageIds: string[]) => void;
}

export function ImageGrid({ images, onApprove }: ImageGridProps) {
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const toggleSelect = (imageId: string) => {
    const newSelected = new Set(selected);
    if (newSelected.has(imageId)) {
      newSelected.delete(imageId);
    } else {
      newSelected.add(imageId);
    }
    setSelected(newSelected);
  };

  const handleApprove = () => {
    onApprove(Array.from(selected));
  };

  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-6 mb-6">
        {images.map((image) => (
          <div
            key={image.id}
            className={`relative aspect-square rounded-lg overflow-hidden cursor-pointer transition-all ${
              selected.has(image.id)
                ? "ring-4 ring-blue-500"
                : "hover:ring-2 hover:ring-gray-300"
            }`}
            onClick={() => toggleSelect(image.id)}
          >
            <Image
              src={image.url}
              alt={`Product ${image.view_type}`}
              fill
              className="object-cover"
            />

            <div className="absolute top-2 right-2">
              <Checkbox checked={selected.has(image.id)} />
            </div>

            <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
              ${image.cost.toFixed(2)}
            </div>

            <div className="absolute bottom-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
              {image.view_type}
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">
            Selected: {selected.size} of {images.length}
          </p>
          <p className="text-xs text-gray-500">
            Total cost: $
            {images.reduce((sum, img) => sum + img.cost, 0).toFixed(2)}
          </p>
        </div>

        <Button onClick={handleApprove} disabled={selected.size < 2} size="lg">
          Add to Mood Board ({selected.size})
        </Button>
      </div>
    </div>
  );
}
```

#### useWebSocket.ts Hook

```typescript
"use client";

import { useEffect, useState, useRef } from "react";

export function useWebSocket(sessionId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);

    ws.onopen = () => {
      console.log("WebSocket connected");
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      console.log("WebSocket message:", event.data);
      setLastMessage(event.data);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      setIsConnected(false);
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [sessionId]);

  return { isConnected, lastMessage };
}
```

---

## 8. Model Selection & Cost Strategy

### 8.1 Cost Analysis

**Target: $200 per video maximum**

| Component                       | Model           | Cost   | Notes              |
| ------------------------------- | --------------- | ------ | ------------------ |
| **Prompt Parsing**              | Llama 3.1 70B   | $0.001 | Essentially free   |
| **Image Generation** (6 images) | Flux-Pro        | $0.30  | MVP & Final        |
| **Image Generation** (6 images) | SDXL (fallback) | $0.06  | Testing only       |
| **Video Scene Planning**        | Llama 3.1 70B   | $0.001 | Essentially free   |
| **Video Generation** (4 clips)  | SVD             | $3.20  | MVP testing        |
| **Video Generation** (4 clips)  | Runway Gen-2    | $6.00  | Final demo         |
| **Background Music**            | Stock library   | $0.00  | MVP (pre-existing) |
| **Background Music**            | MusicGen        | $0.30  | Post-MVP           |
| **Composition**                 | FFmpeg          | $0.50  | Storage/processing |

**MVP Total Cost:**

- Flux-Pro (images): $0.30
- Llama 3.1 (parsing + planning): $0.002
- SVD (video): $3.20
- FFmpeg (composition): $0.50
- **Total: $4.00 per video**

**Final Demo Cost:**

- Flux-Pro (images): $0.30
- Runway Gen-2 (video): $6.00
- FFmpeg (composition): $0.50
- **Total: $6.80 per video**

**Budget Remaining:** $200 - $6.80 = **$193.20 per video** ✅

### 8.2 Optimization Strategies

1. **Tiered Model Usage:**

   ```python
   def get_model_config(stage: str):
       if os.getenv("ENV") == "production":
           return PRODUCTION_MODELS[stage]
       else:
           return MVP_MODELS[stage]
   ```

2. **Caching:**

   - Cache Prompt Parser outputs (same product = reuse prompts)
   - Cache generated images for 24 hours
   - Implement Redis for fast retrieval

3. **Batch Processing:**

   - Generate images in parallel (asyncio.gather)
   - Generate video clips in parallel
   - Reduces total wall-clock time

4. **Cost Tracking:**
   - Log every API call cost in database
   - Alert if session exceeds $10
   - Dashboard showing cumulative costs

---

## 9. Progress Indicators & WebSocket

### 9.1 WebSocket Implementation (FastAPI)

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        print(f"WebSocket connected: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            print(f"WebSocket disconnected: {session_id}")

    async def send_progress(self, session_id: str, data: dict):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_json(data)
            except Exception as e:
                print(f"Error sending progress: {e}")
                self.disconnect(session_id)

ws_manager = WebSocketManager()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await ws_manager.connect(session_id, websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id)
```

### 9.2 Progress Stages

| Stage                 | Progress Range | Messages                     |
| --------------------- | -------------- | ---------------------------- |
| **Prompt Parsing**    | 0-10%          | "Analyzing your prompt..."   |
| **Image Generation**  | 10-50%         | "Generating image X of Y..." |
| **Image Complete**    | 50%            | "Images ready for review!"   |
| **Video Planning**    | 50-55%         | "Planning video scenes..."   |
| **Video Generation**  | 55-90%         | "Generating clip X of Y..."  |
| **Video Complete**    | 90%            | "Clips ready for review!"    |
| **Final Composition** | 90-95%         | "Adding text overlays..."    |
| **Final Composition** | 95-98%         | "Stitching clips..."         |
| **Final Complete**    | 100%           | "Your video is ready!"       |

---

## 10. Implementation Sequence (48-Hour Sprint)

### Day 1 (Friday, 24 hours)

#### Hour 0-6: Foundation Setup

**Priority: Infrastructure**

- [ ] **Hour 0-2:** Project initialization
  - Create GitHub repo
  - Set up FastAPI backend structure
  - Set up Next.js 14 frontend (App Router)
  - PostgreSQL setup (Railway)
  - Environment variables (.env files)
- [ ] **Hour 2-4:** Database & Models

  - SQLAlchemy models (Session, Asset, GenerationCost)
  - Database migrations (Alembic)
  - Pydantic request/response models
  - Test database connection

- [ ] **Hour 4-6:** Authentication & Session Management
  - Demo login endpoint
  - JWT token generation (simple)
  - Session creation endpoint
  - Frontend login page

**Deliverable:** Working login → session creation flow

#### Hour 6-16: Core Agent Implementation

**Priority: Orchestrator + Agents**

- [ ] **Hour 6-8:** Orchestrator Base

  - VideoGenerationOrchestrator class
  - WebSocket manager
  - Error handling framework
  - Cost tracking logic

- [ ] **Hour 8-10:** Prompt Parser Agent

  - Llama 3.1 integration
  - System prompt engineering
  - JSON output validation
  - Test with sample prompts

- [ ] **Hour 10-13:** Batch Image Generator Agent

  - Replicate Flux-Pro integration
  - Parallel image generation (asyncio.gather)
  - Error handling with fallback to SDXL
  - Test with 6 image generation

- [ ] **Hour 13-16:** Image Generation Flow (End-to-End)
  - `/api/generate-images` endpoint
  - WebSocket progress updates
  - Database persistence
  - Frontend image display component

**Deliverable:** Working prompt → images flow with progress tracking

#### Hour 16-24: Video Generation

**Priority: Video Agent + Clips**

- [ ] **Hour 16-18:** Video Scene Planning

  - LLM scene planner (Llama 3.1)
  - Scene prompt generation per image
  - Motion intensity calculation

- [ ] **Hour 18-21:** Video Generator Agent

  - Stable Video Diffusion integration
  - Image-to-Video conversion
  - Parallel clip generation
  - Test with 2-4 clips

- [ ] **Hour 21-24:** Clip Generation Flow (End-to-End)
  - `/api/generate-clips` endpoint
  - Video preview components
  - Clip selection UI
  - Database persistence

**Deliverable:** Working approved images → video clips flow

**END OF DAY 1 CHECKPOINT:**

- ✅ Images generated from prompt
- ✅ Clips generated from images
- ✅ WebSocket progress working
- ✅ Basic UI functional

---

### Day 2 (Saturday, 24 hours)

#### Hour 24-32: Composition Layer

**Priority: Final Video Assembly**

- [ ] **Hour 24-26:** Intro/Outro Card Generation

  - FFmpeg card generation
  - Text overlay rendering
  - Test intro/outro separately

- [ ] **Hour 26-29:** Video Stitching

  - FFmpeg concat implementation
  - Transition effects (crossfade)
  - Audio mixing
  - Test full composition

- [ ] **Hour 29-32:** Text Overlay System
  - Dynamic text rendering
  - Font selection
  - Color customization
  - Timing control

**Deliverable:** Working clip stitching with text overlays

#### Hour 32-40: Frontend Polish & Integration

**Priority: UI/UX**

- [ ] **Hour 32-34:** Mood Board Components

  - Image mood board UI
  - Clip mood board UI
  - Drag-to-reorder (optional)
  - Selection state management

- [ ] **Hour 34-37:** Composition UI

  - Text overlay form
  - Audio selector
  - Preview panel
  - Final generation button

- [ ] **Hour 37-40:** Final Output Page
  - Video player component
  - Download button
  - Cost summary
  - Share functionality

**Deliverable:** Complete UI flow from login to download

#### Hour 40-46: Testing & Optimization

**Priority: Quality Assurance**

- [ ] **Hour 40-42:** End-to-End Testing

  - Test full flow 3 times
  - Different product types
  - Different video prompts
  - Edge cases (errors, timeouts)

- [ ] **Hour 42-44:** Performance Optimization

  - Reduce API call redundancy
  - Implement caching (Redis)
  - Optimize FFmpeg settings
  - Database query optimization

- [ ] **Hour 44-46:** Cost Optimization
  - Switch to cheaper models for non-critical stages
  - Implement cost alerts
  - Verify staying under $200 budget
  - Generate cost report

**Deliverable:** Stable, optimized pipeline

#### Hour 46-48: Final Polish & Deployment

**Priority: Deployment Ready**

- [ ] **Hour 46:** Generate Demo Videos

  - 2 complete ad videos (different products)
  - Use best quality models (Runway Gen-2)
  - Save to outputs folder
  - Take screenshots for demo

- [ ] **Hour 47:** Deployment

  - Deploy backend to Railway
  - Deploy frontend to Vercel
  - Configure environment variables
  - Test deployed version

- [ ] **Hour 48:** Documentation
  - Update README with setup instructions
  - Architecture diagram
  - Cost breakdown document
  - Demo video preparation

**MVP COMPLETE ✅**

---

## 11. Success Criteria

### 11.1 Functional Requirements

| Requirement             | Success Criteria                        | How to Test                                         |
| ----------------------- | --------------------------------------- | --------------------------------------------------- |
| **Login**               | User can log in with demo credentials   | Enter `demo@example.com` / `demo123` → Dashboard    |
| **Image Generation**    | 6 product images generated in <60s      | Submit "pink tennis shoes" → 6 images appear        |
| **Visual Consistency**  | All images show same product design     | Compare generated images side-by-side               |
| **Image Selection**     | User can select 2+ images               | Click checkboxes → "Add to Mood Board" enabled      |
| **Mood Board**          | Selected images persist across sessions | Refresh page → Images still selected                |
| **Video Prompt**        | User can describe scene                 | Enter "girl running in sun" → Accepted              |
| **Clip Generation**     | 2-4 video clips generated in <180s      | Submit video prompt → Clips appear                  |
| **Clip Consistency**    | Clips visually match product images     | Compare clips to source images                      |
| **Clip Selection**      | User can select and reorder clips       | Select 3 clips → Reorder → Saved                    |
| **Text Overlay**        | Product name and CTA appear in video    | Enter "AirRun Pro" / "Shop Now" → Visible in output |
| **Audio (Optional)**    | Background music plays in video         | Enable audio toggle → Music in final video          |
| **Final Video**         | 8-12 second 1080p MP4 generated         | Final video: 9.8s, 1920x1080, <15MB                 |
| **Download**            | User can download MP4 file              | Click "Download" → File downloads                   |
| **Cost Tracking**       | Total cost displayed and <$10           | Check cost summary → <$10.00                        |
| **Progress Indicators** | Real-time updates during generation     | Watch progress bar → Updates every 2-5s             |

### 11.2 Performance Requirements

| Metric                     | Target      | Acceptable Range  |
| -------------------------- | ----------- | ----------------- |
| **Image Generation Time**  | 45 seconds  | 30-60 seconds     |
| **Video Generation Time**  | 150 seconds | 120-180 seconds   |
| **Final Composition Time** | 30 seconds  | 20-45 seconds     |
| **Total End-to-End Time**  | <5 minutes  | 4-7 minutes       |
| **Cost per Video**         | $4.00 (MVP) | $3.50-$6.00       |
| **Video Resolution**       | 1920x1080   | Minimum 1920x1080 |
| **Video FPS**              | 30          | 24-30             |
| **File Size**              | <15 MB      | 10-20 MB          |

### 11.3 Quality Requirements

**Visual Quality:**

- [ ] Product clearly visible in all images
- [ ] Consistent product design across images (same color, style)
- [ ] No distortions or artifacts
- [ ] Professional lighting and composition

**Video Quality:**

- [ ] Smooth motion (no jittering)
- [ ] Product recognizable in all clips
- [ ] Clips match scene description
- [ ] Transitions are smooth

**Audio Quality:**

- [ ] No clipping or distortion
- [ ] Music synced to video length
- [ ] Appropriate volume level

**Text Overlay Quality:**

- [ ] Text readable and prominent
- [ ] Correct timing (intro/outro)
- [ ] No overlapping with product

---

## 12. Testing Strategy

### 12.1 Unit Tests

```python
# test_agents.py
import pytest
from agents.prompt_parser import PromptParserAgent
from agents.image_generator import BatchImageGeneratorAgent

@pytest.mark.asyncio
async def test_prompt_parser():
    agent = PromptParserAgent(api_key=os.getenv("REPLICATE_API_KEY"))

    input_data = AgentInput(
        session_id="test_session",
        data={"user_prompt": "pink tennis shoes", "options": {"num_images": 4}}
    )

    result = await agent.process(input_data)

    assert result.success is True
    assert result.data["consistency_seed"] is not None
    assert len(result.data["image_prompts"]) == 4
    assert all(p["seed"] == result.data["consistency_seed"] for p in result.data["image_prompts"])

@pytest.mark.asyncio
async def test_image_generator():
    agent = BatchImageGeneratorAgent(api_key=os.getenv("REPLICATE_API_KEY"))

    input_data = AgentInput(
        session_id="test_session",
        data={
            "image_prompts": [
                {
                    "prompt": "Professional photo of pink tennis shoes",
                    "negative_prompt": "blurry, distorted",
                    "seed": 12345,
                    "guidance_scale": 7.5
                }
            ],
            "model": "flux-pro"
        }
    )

    result = await agent.process(input_data)

    assert result.success is True
    assert len(result.data["images"]) == 1
    assert result.data["images"][0]["url"].startswith("https://")
    assert result.cost > 0
```

### 12.2 Integration Tests

```python
# test_integration.py
import pytest
from orchestrator import VideoGenerationOrchestrator

@pytest.mark.asyncio
async def test_full_image_generation_flow():
    """Test complete flow from prompt to images"""

    # Create session
    session_id = await db.create_session(user_id=1)

    # Generate images
    orchestrator = VideoGenerationOrchestrator(...)
    result = await orchestrator.generate_images(
        session_id=session_id,
        user_prompt="pink tennis shoes",
        num_images=4
    )

    assert result["status"] == "success"
    assert result["image_count"] == 4

    # Verify database
    session = await db.get_session(session_id)
    assert len(session.generated_images) == 4
    assert session.total_cost > 0
```

### 12.3 End-to-End Tests

```python
# test_e2e.py
import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_complete_user_flow():
    """Test complete flow from UI perspective"""

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # 1. Login
        await page.goto("http://localhost:3000")
        await page.fill('input[name="email"]', "demo@example.com")
        await page.fill('input[name="password"]', "demo123")
        await page.click('button:has-text("Start Creating")')

        # 2. Generate images
        await page.fill('textarea[name="product_prompt"]', "pink tennis shoes")
        await page.click('button:has-text("Generate Images")')

        # Wait for images to appear
        await page.wait_for_selector('.image-grid', timeout=60000)

        # 3. Select images
        image_checkboxes = page.locator('.image-card input[type="checkbox"]')
        for i in range(4):
            await image_checkboxes.nth(i).check()

        await page.click('button:has-text("Add to Mood Board")')

        # 4. Generate clips
        await page.fill('textarea[name="video_prompt"]', "girl running in sun")
        await page.click('button:has-text("Generate Clips")')

        # Wait for clips
        await page.wait_for_selector('.video-grid', timeout=180000)

        # 5. Select clips
        clip_checkboxes = page.locator('.clip-card input[type="checkbox"]')
        await clip_checkboxes.first.check()
        await clip_checkboxes.nth(1).check()

        await page.click('button:has-text("Add to Mood Board")')

        # 6. Final composition
        await page.fill('input[name="product_name"]', "AirRun Pro")
        await page.fill('input[name="cta"]', "Shop Now")
        await page.click('button:has-text("Generate Final Video")')

        # Wait for final video
        await page.wait_for_selector('video', timeout=60000)

        # 7. Verify download button
        download_button = page.locator('button:has-text("Download")')
        assert await download_button.is_visible()

        await browser.close()
```

### 12.4 Test Product Descriptions

Use these for consistent testing:

1. **Pink Tennis Shoes**

   - Product: "pink athletic tennis shoes with white laces"
   - Video: "girl running on outdoor track in golden hour sunlight"

2. **Luxury Watch**

   - Product: "luxury gold watch with leather strap on marble surface"
   - Video: "slow rotation on black velvet display, dramatic lighting"

3. **Minimalist Skincare**
   - Product: "white minimalist skincare bottle on clean background"
   - Video: "product floating with water droplets, fresh aesthetic"

---

## 13. Deployment Plan

### 13.1 Infrastructure

| Service          | Platform                | Purpose                  | Cost                |
| ---------------- | ----------------------- | ------------------------ | ------------------- |
| **Frontend**     | Vercel                  | Next.js hosting          | Free (Hobby plan)   |
| **Backend API**  | Railway                 | FastAPI hosting          | $5/month (Dev plan) |
| **Database**     | Railway PostgreSQL      | State management         | Included in Railway |
| **File Storage** | AWS S3 or Cloudflare R2 | Video/image storage      | ~$1/month           |
| **Domain**       | Vercel/Railway          | Custom domain (optional) | Free with platform  |

**Total Monthly Cost:** ~$6/month for MVP

### 13.2 Environment Variables

**Backend (.env):**

```bash
# API Keys
REPLICATE_API_KEY=r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx (optional)

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Storage
AWS_ACCESS_KEY_ID=xxxxxxxxxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxx
S3_BUCKET_NAME=ai-ad-videos

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256

# CORS
FRONTEND_URL=https://your-app.vercel.app

# Environment
ENV=production  # or 'development'
```

**Frontend (.env.local):**

```bash
NEXT_PUBLIC_API_URL=https://your-api.railway.app
NEXT_PUBLIC_WS_URL=wss://your-api.railway.app
```

### 13.3 Deployment Commands

**Backend (Railway):**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up

# Set environment variables
railway variables set REPLICATE_API_KEY=xxx
railway variables set DATABASE_URL=xxx
```

**Frontend (Vercel):**

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel --prod

# Set environment variables
vercel env add NEXT_PUBLIC_API_URL
```

### 13.4 Pre-Deployment Checklist

- [ ] All environment variables configured
- [ ] Database migrations run
- [ ] Demo user created in production DB
- [ ] CORS settings allow frontend domain
- [ ] S3 bucket created and accessible
- [ ] FFmpeg installed on Railway (add to Dockerfile)
- [ ] WebSocket endpoint accessible
- [ ] Health check endpoint working (`/health`)
- [ ] Error logging configured (Sentry optional)
- [ ] Cost tracking verified in production

### 13.5 Post-Deployment Testing

1. **Smoke Tests:**

   - [ ] Login works
   - [ ] Image generation works
   - [ ] Video generation works
   - [ ] Final video downloads

2. **Performance:**

   - [ ] Page load < 3 seconds
   - [ ] API response < 2 seconds
   - [ ] WebSocket connects immediately

3. **Monitoring:**
   - [ ] Set up uptime monitoring (UptimeRobot)
   - [ ] Monitor error rates in logs
   - [ ] Track API costs (Replicate dashboard)

---

## Appendix A: Error Handling

### Common Errors & Solutions

| Error                        | Cause                 | Solution                                   |
| ---------------------------- | --------------------- | ------------------------------------------ |
| **Replicate API timeout**    | Model overloaded      | Retry after 30s, fallback to cheaper model |
| **Out of memory (FFmpeg)**   | Video too large       | Reduce resolution, split processing        |
| **WebSocket disconnect**     | Network issue         | Auto-reconnect, show "reconnecting..."     |
| **Database connection lost** | Railway restart       | Implement connection pooling, retry logic  |
| **Image generation failed**  | NSFW filter triggered | Retry with modified prompt, inform user    |
| **Cost limit exceeded**      | Too many retries      | Halt generation, show error to user        |

---

## Appendix B: Future Enhancements (Post-MVP)

1. **Message Queue Architecture**

   - Replace direct calls with RabbitMQ/Redis
   - Enable distributed processing
   - Better retry logic

2. **Advanced Features**

   - A/B testing (generate multiple variations)
   - Multiple aspect ratios (9:16, 1:1)
   - LoRA model training for brand consistency
   - Voiceover generation (text-to-speech)
   - Custom music generation (MusicGen)

3. **UI/UX Improvements**

   - Drag-and-drop clip reordering
   - Real-time video preview during composition
   - Style presets (luxury, modern, energetic)
   - Batch generation dashboard

4. **Cost Optimization**
   - Self-hosted models (Stable Diffusion, SVD)
   - GPU server (RunPod, Vast.ai)
   - Aggressive caching
   - Model distillation

---

## Appendix C: Quick Reference Commands

```bash
# Backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run dev

# Database migrations
alembic upgrade head

# Run tests
pytest tests/ -v

# Format code
black .
ruff check .

# Type check
mypy .
```

---

## Document Metadata

- **Version:** 2.0
- **Last Updated:** November 14, 2025
- **Owner:** Nani Skinner
- **Status:** Implementation-Ready
- **Estimated Completion:** 48 hours

---

**END OF MVP PRD** ✅

This document is ready for immediate implementation. All agents, endpoints, data models, and UI components are fully specified with code examples. Follow the 48-hour implementation sequence for optimal results.
