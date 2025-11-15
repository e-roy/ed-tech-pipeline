# AI Ad Video Generator - Architecture Diagrams

### Version: 2.0

### Date: November 14, 2025

---

## Table of Contents

1. [High-Level System Architecture](#1-high-level-system-architecture)
2. [Multi-Agent Orchestration Flow](#2-multi-agent-orchestration-flow)
3. [Complete User Journey Flow](#3-complete-user-journey-flow)
4. [Data Flow Diagram](#4-data-flow-diagram)
5. [Database Schema Relationships](#5-database-schema-relationships)
6. [API Endpoint Architecture](#6-api-endpoint-architecture)
7. [WebSocket Communication Flow](#7-websocket-communication-flow)
8. [Image Generation Pipeline](#8-image-generation-pipeline)
9. [Video Generation Pipeline](#9-video-generation-pipeline)
10. [Final Composition Pipeline](#10-final-composition-pipeline)
11. [Cost Tracking Architecture](#11-cost-tracking-architecture)
12. [Deployment Architecture](#12-deployment-architecture)

---

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        UI[Next.js Frontend<br/>React + TypeScript]
        WS_CLIENT[WebSocket Client<br/>Real-time Updates]
    end

    subgraph "API Layer - FastAPI Backend"
        API[REST API Endpoints<br/>Authentication, CRUD]
        WS_SERVER[WebSocket Server<br/>Progress Broadcasts]
        ORCHESTRATOR[Orchestrator<br/>State Management]
    end

    subgraph "Agent Layer"
        PARSER[Prompt Parser Agent<br/>Llama 3.1 70B]
        IMG_GEN[Batch Image Generator<br/>Flux-Pro / SDXL]
        VIDEO_GEN[Video Generator Agent<br/>Stable Video Diffusion]
        COMPOSITOR[Composition Layer<br/>FFmpeg]
    end

    subgraph "External Services"
        REPLICATE[Replicate API<br/>AI Models]
        STORAGE[Cloud Storage<br/>S3 / R2]
    end

    subgraph "Data Layer"
        DB[(PostgreSQL<br/>State + Assets + Costs)]
        CACHE[(Redis Cache<br/>Session Data)]
    end

    UI --> API
    UI --> WS_CLIENT
    WS_CLIENT <--> WS_SERVER
    API --> ORCHESTRATOR
    WS_SERVER --> ORCHESTRATOR

    ORCHESTRATOR --> PARSER
    ORCHESTRATOR --> IMG_GEN
    ORCHESTRATOR --> VIDEO_GEN
    ORCHESTRATOR --> COMPOSITOR

    PARSER --> REPLICATE
    IMG_GEN --> REPLICATE
    VIDEO_GEN --> REPLICATE
    COMPOSITOR --> STORAGE

    ORCHESTRATOR --> DB
    ORCHESTRATOR --> CACHE

    style ORCHESTRATOR fill:#4CAF50,stroke:#2E7D32,stroke-width:3px
    style REPLICATE fill:#FF9800,stroke:#E65100,stroke-width:2px
    style DB fill:#2196F3,stroke:#0D47A1,stroke-width:2px
```

---

## 2. Multi-Agent Orchestration Flow

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
    participant Replicate

    User->>Frontend: Enter product prompt
    Frontend->>Orchestrator: POST /api/generate-images
    Orchestrator->>Database: Save session

    rect rgb(200, 220, 255)
        Note over Orchestrator,PromptParser: Stage 1: Prompt Parsing
        Orchestrator->>PromptParser: parse(user_prompt)
        PromptParser->>Replicate: Llama 3.1 API call
        Replicate-->>PromptParser: Structured JSON + seed
        PromptParser-->>Orchestrator: Parsed prompts
        Orchestrator->>Database: Save seed + prompts
    end

    rect rgb(200, 255, 220)
        Note over Orchestrator,ImageGen: Stage 2: Image Generation
        loop For each prompt
            Orchestrator->>ImageGen: generate(prompt + seed)
            ImageGen->>Replicate: Flux-Pro API call
            Replicate-->>ImageGen: Image URL
            ImageGen-->>Orchestrator: Image result
            Orchestrator->>Database: Save asset
            Orchestrator->>Frontend: WebSocket progress update
        end
    end

    Orchestrator-->>Frontend: Images complete
    Frontend-->>User: Display images

    User->>Frontend: Select approved images
    Frontend->>Orchestrator: POST /api/save-approved-images
    Orchestrator->>Database: Update session

    User->>Frontend: Enter video prompt
    Frontend->>Orchestrator: POST /api/generate-clips

    rect rgb(255, 220, 200)
        Note over Orchestrator,VideoGen: Stage 3: Video Generation
        Orchestrator->>PromptParser: plan_scenes(images, video_prompt)
        PromptParser->>Replicate: Llama 3.1 API call
        Replicate-->>PromptParser: Scene descriptions
        PromptParser-->>Orchestrator: Scene plan

        loop For each approved image
            Orchestrator->>VideoGen: generate(image, scene)
            VideoGen->>Replicate: Stable Video Diffusion
            Replicate-->>VideoGen: Video URL
            VideoGen-->>Orchestrator: Clip result
            Orchestrator->>Database: Save asset
            Orchestrator->>Frontend: WebSocket progress update
        end
    end

    Orchestrator-->>Frontend: Clips complete
    Frontend-->>User: Display clips

    User->>Frontend: Select clips + add text overlay
    Frontend->>Orchestrator: POST /api/compose-final-video

    rect rgb(255, 255, 200)
        Note over Orchestrator,Compositor: Stage 4: Final Composition
        Orchestrator->>Compositor: stitch(clips, text, audio)
        Compositor->>Compositor: Generate intro/outro
        Compositor->>Compositor: FFmpeg stitching
        Compositor->>Database: Save final video
        Compositor-->>Orchestrator: Final video URL
        Orchestrator->>Frontend: WebSocket complete
    end

    Frontend-->>User: Display final video
```

---

## 3. Complete User Journey Flow

```mermaid
graph TD
    START([User Visits App]) --> LOGIN[Login Screen<br/>demo@example.com]
    LOGIN --> CREATE_SESSION[Create Session<br/>POST /api/sessions/create]

    CREATE_SESSION --> PRODUCT_PROMPT[Enter Product Prompt<br/>'pink tennis shoes']
    PRODUCT_PROMPT --> GEN_IMAGES[Generate Images<br/>POST /api/generate-images]

    GEN_IMAGES --> WS_PROGRESS1[WebSocket Progress<br/>Image 1 of 6...]
    WS_PROGRESS1 --> DISPLAY_IMAGES[Display Image Grid<br/>6 images with checkboxes]

    DISPLAY_IMAGES --> SELECT_IMAGES{User Selects<br/>2+ Images?}
    SELECT_IMAGES -->|No| DISPLAY_IMAGES
    SELECT_IMAGES -->|Yes| SAVE_IMAGES[Save Approved Images<br/>POST /api/save-approved-images]

    SAVE_IMAGES --> MOOD_BOARD1[Mood Board - Images<br/>Show selected images]
    MOOD_BOARD1 --> VIDEO_PROMPT[Enter Video Prompt<br/>'girl running in sun']

    VIDEO_PROMPT --> GEN_CLIPS[Generate Clips<br/>POST /api/generate-clips]
    GEN_CLIPS --> WS_PROGRESS2[WebSocket Progress<br/>Clip 1 of 4...]
    WS_PROGRESS2 --> DISPLAY_CLIPS[Display Clip Grid<br/>4 clips with checkboxes]

    DISPLAY_CLIPS --> SELECT_CLIPS{User Selects<br/>1+ Clips?}
    SELECT_CLIPS -->|No| DISPLAY_CLIPS
    SELECT_CLIPS -->|Yes| SAVE_CLIPS[Save Approved Clips<br/>POST /api/save-approved-clips]

    SAVE_CLIPS --> MOOD_BOARD2[Mood Board - Clips<br/>Show selected clips]
    MOOD_BOARD2 --> TEXT_OVERLAY[Add Text Overlay<br/>Product Name + CTA]

    TEXT_OVERLAY --> AUDIO_SELECT{Enable<br/>Background Music?}
    AUDIO_SELECT -->|Yes| AUDIO_CONFIG[Select Music Genre]
    AUDIO_SELECT -->|No| COMPOSE
    AUDIO_CONFIG --> COMPOSE[Compose Final Video<br/>POST /api/compose-final-video]

    COMPOSE --> WS_PROGRESS3[WebSocket Progress<br/>Stitching clips...]
    WS_PROGRESS3 --> FINAL_VIDEO[Display Final Video<br/>Embedded player]

    FINAL_VIDEO --> DOWNLOAD[Download MP4<br/>or Generate Another]
    DOWNLOAD --> END([Complete])

    style START fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style END fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style GEN_IMAGES fill:#FF9800,stroke:#E65100,stroke-width:2px
    style GEN_CLIPS fill:#FF9800,stroke:#E65100,stroke-width:2px
    style COMPOSE fill:#FF9800,stroke:#E65100,stroke-width:2px
```

---

## 4. Data Flow Diagram

```mermaid
graph LR
    subgraph "Input"
        USER_PROMPT[User Prompt<br/>'pink tennis shoes']
        VIDEO_PROMPT[Video Prompt<br/>'girl running in sun']
    end

    subgraph "Processing Stage 1"
        PARSE[Prompt Parser<br/>Llama 3.1]
        SEED[Consistency Seed<br/>789456]
        PROMPTS[6 Enhanced Prompts<br/>+ View Types]
    end

    subgraph "Processing Stage 2"
        IMG1[Image 1: Front View]
        IMG2[Image 2: Side View]
        IMG3[Image 3: Back View]
        IMG4[Image 4: Top View]
        IMG5[Image 5: Detail]
        IMG6[Image 6: Lifestyle]
    end

    subgraph "User Selection"
        APPROVED_IMG[Approved Images<br/>User selects 4 of 6]
    end

    subgraph "Processing Stage 3"
        SCENE_PLAN[Scene Planner<br/>Llama 3.1]
        SCENES[4 Scene Descriptions<br/>+ Motion Intensity]
    end

    subgraph "Processing Stage 4"
        CLIP1[Clip 1: 3.2s<br/>Image-to-Video]
        CLIP2[Clip 2: 3.1s<br/>Image-to-Video]
        CLIP3[Clip 3: 3.0s<br/>Image-to-Video]
        CLIP4[Clip 4: 3.3s<br/>Image-to-Video]
    end

    subgraph "User Selection"
        APPROVED_CLIPS[Approved Clips<br/>User selects 3 of 4]
    end

    subgraph "Processing Stage 5"
        INTRO[Intro Card: 1s<br/>Product Name]
        STITCH[FFmpeg Stitching<br/>Transitions + Audio]
        OUTRO[Outro Card: 1s<br/>CTA]
    end

    subgraph "Output"
        FINAL[Final Video<br/>9.8s MP4<br/>1920x1080]
    end

    USER_PROMPT --> PARSE
    PARSE --> SEED
    PARSE --> PROMPTS

    PROMPTS --> IMG1 & IMG2 & IMG3 & IMG4 & IMG5 & IMG6
    IMG1 & IMG2 & IMG3 & IMG4 & IMG5 & IMG6 --> APPROVED_IMG

    APPROVED_IMG --> SCENE_PLAN
    VIDEO_PROMPT --> SCENE_PLAN
    SCENE_PLAN --> SCENES

    SCENES --> CLIP1 & CLIP2 & CLIP3 & CLIP4
    CLIP1 & CLIP2 & CLIP3 & CLIP4 --> APPROVED_CLIPS

    APPROVED_CLIPS --> STITCH
    INTRO --> STITCH
    OUTRO --> STITCH
    STITCH --> FINAL

    style PARSE fill:#9C27B0,stroke:#4A148C,stroke-width:2px
    style SCENE_PLAN fill:#9C27B0,stroke:#4A148C,stroke-width:2px
    style STITCH fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style FINAL fill:#2196F3,stroke:#0D47A1,stroke-width:3px
```

---

## 5. Database Schema Relationships

```mermaid
erDiagram
    USERS ||--o{ SESSIONS : creates
    SESSIONS ||--o{ ASSETS : contains
    SESSIONS ||--o{ GENERATION_COSTS : tracks

    USERS {
        int id PK
        string email UK
        string password_hash
        timestamp created_at
    }

    SESSIONS {
        string id PK
        int user_id FK
        string stage
        string product_prompt
        string video_prompt
        int consistency_seed
        jsonb style_keywords
        jsonb generated_image_ids
        jsonb approved_image_ids
        jsonb generated_clip_ids
        jsonb approved_clip_ids
        jsonb clip_order
        string final_video_id FK
        decimal total_cost
        timestamp created_at
        timestamp updated_at
    }

    ASSETS {
        string id PK
        string session_id FK
        string asset_type
        string url
        jsonb metadata
        decimal cost
        string model_used
        decimal generation_time
        timestamp created_at
    }

    GENERATION_COSTS {
        int id PK
        string session_id FK
        string agent_name
        string model_used
        decimal cost_usd
        decimal duration_seconds
        boolean success
        string error_message
        timestamp created_at
    }
```

---

## 6. API Endpoint Architecture

```mermaid
graph TB
    subgraph "Authentication Endpoints"
        AUTH_LOGIN[POST /api/auth/login<br/>Demo credentials]
    end

    subgraph "Session Management"
        SESSION_CREATE[POST /api/sessions/create<br/>Create new session]
        SESSION_GET[GET /api/sessions/:id<br/>Get session state]
    end

    subgraph "Image Generation Flow"
        IMG_GENERATE[POST /api/generate-images<br/>Trigger image generation]
        IMG_APPROVE[POST /api/save-approved-images<br/>Save selected images]
    end

    subgraph "Video Generation Flow"
        CLIP_GENERATE[POST /api/generate-clips<br/>Trigger clip generation]
        CLIP_APPROVE[POST /api/save-approved-clips<br/>Save selected clips]
    end

    subgraph "Final Composition"
        FINAL_COMPOSE[POST /api/compose-final-video<br/>Generate final video]
    end

    subgraph "Utility Endpoints"
        COSTS_GET[GET /api/sessions/:id/costs<br/>Cost breakdown]
        HEALTH[GET /health<br/>Health check]
    end

    subgraph "WebSocket"
        WS_CONNECT[WS /ws/:session_id<br/>Real-time progress]
    end

    AUTH_LOGIN --> SESSION_CREATE
    SESSION_CREATE --> IMG_GENERATE
    IMG_GENERATE --> WS_CONNECT
    IMG_GENERATE --> IMG_APPROVE
    IMG_APPROVE --> SESSION_GET
    SESSION_GET --> CLIP_GENERATE
    CLIP_GENERATE --> WS_CONNECT
    CLIP_GENERATE --> CLIP_APPROVE
    CLIP_APPROVE --> SESSION_GET
    SESSION_GET --> FINAL_COMPOSE
    FINAL_COMPOSE --> WS_CONNECT
    FINAL_COMPOSE --> COSTS_GET

    style IMG_GENERATE fill:#FF9800,stroke:#E65100,stroke-width:2px
    style CLIP_GENERATE fill:#FF9800,stroke:#E65100,stroke-width:2px
    style FINAL_COMPOSE fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style WS_CONNECT fill:#9C27B0,stroke:#4A148C,stroke-width:2px
```

---

## 7. WebSocket Communication Flow

```mermaid
sequenceDiagram
    participant Frontend
    participant WSServer as WebSocket Server
    participant Orchestrator
    participant Agent
    participant Database

    Frontend->>WSServer: Connect to /ws/{session_id}
    WSServer-->>Frontend: Connection accepted

    Frontend->>Orchestrator: POST /api/generate-images

    loop Image Generation Process
        Orchestrator->>Agent: Generate image
        Agent-->>Orchestrator: Image result
        Orchestrator->>Database: Save asset

        Orchestrator->>WSServer: send_progress({<br/>  stage: "image_generation",<br/>  progress: 33,<br/>  message: "Generating image 2 of 6...",<br/>  current_cost: 0.10<br/>})
        WSServer-->>Frontend: Progress update
        Frontend->>Frontend: Update UI (progress bar)
    end

    Orchestrator->>WSServer: send_progress({<br/>  stage: "complete",<br/>  progress: 100,<br/>  message: "Images ready!",<br/>  data: { images: [...] }<br/>})
    WSServer-->>Frontend: Completion event
    Frontend->>Frontend: Display images

    Frontend->>WSServer: Keep-alive ping
    WSServer-->>Frontend: Pong

    Note over Frontend,WSServer: Connection remains open<br/>for next generation stage
```

---

## 8. Image Generation Pipeline

```mermaid
flowchart TD
    START([User Submits Prompt]) --> VALIDATE{Valid Prompt?}
    VALIDATE -->|No| ERROR1[Return Error:<br/>Min 3 chars]
    VALIDATE -->|Yes| PARSE[Prompt Parser Agent]

    PARSE --> LLM1[Llama 3.1 API Call<br/>System Prompt:<br/>Generate 6 consistent prompts]
    LLM1 --> SEED[Generate Consistency Seed<br/>Random: 100000-999999]

    SEED --> PROMPTS[6 Enhanced Prompts<br/>Front, Side, Back,<br/>Top, Detail, Lifestyle]

    PROMPTS --> PARALLEL{Parallel Processing}

    PARALLEL --> IMG1[Generate Image 1<br/>Replicate Flux-Pro<br/>Seed: 789456]
    PARALLEL --> IMG2[Generate Image 2<br/>Replicate Flux-Pro<br/>Seed: 789456]
    PARALLEL --> IMG3[Generate Image 3<br/>Replicate Flux-Pro<br/>Seed: 789456]
    PARALLEL --> IMG4[Generate Image 4<br/>Replicate Flux-Pro<br/>Seed: 789456]
    PARALLEL --> IMG5[Generate Image 5<br/>Replicate Flux-Pro<br/>Seed: 789456]
    PARALLEL --> IMG6[Generate Image 6<br/>Replicate Flux-Pro<br/>Seed: 789456]

    IMG1 --> CHECK1{Generation<br/>Success?}
    IMG2 --> CHECK2{Generation<br/>Success?}
    IMG3 --> CHECK3{Generation<br/>Success?}
    IMG4 --> CHECK4{Generation<br/>Success?}
    IMG5 --> CHECK5{Generation<br/>Success?}
    IMG6 --> CHECK6{Generation<br/>Success?}

    CHECK1 -->|Yes| SAVE1[Save to Database<br/>Cost: $0.05]
    CHECK2 -->|Yes| SAVE2[Save to Database<br/>Cost: $0.05]
    CHECK3 -->|Yes| SAVE3[Save to Database<br/>Cost: $0.05]
    CHECK4 -->|Yes| SAVE4[Save to Database<br/>Cost: $0.05]
    CHECK5 -->|Yes| SAVE5[Save to Database<br/>Cost: $0.05]
    CHECK6 -->|Yes| SAVE6[Save to Database<br/>Cost: $0.05]

    CHECK1 -->|No| RETRY1[Retry Once]
    CHECK2 -->|No| RETRY2[Retry Once]
    CHECK3 -->|No| RETRY3[Retry Once]
    CHECK4 -->|No| RETRY4[Retry Once]
    CHECK5 -->|No| RETRY5[Retry Once]
    CHECK6 -->|No| RETRY6[Retry Once]

    RETRY1 --> CHECK1
    RETRY2 --> CHECK2
    RETRY3 --> CHECK3
    RETRY4 --> CHECK4
    RETRY5 --> CHECK5
    RETRY6 --> CHECK6

    SAVE1 & SAVE2 & SAVE3 & SAVE4 & SAVE5 & SAVE6 --> COLLECT[Collect All Results]

    COLLECT --> VALIDATE_COUNT{At least 4<br/>successful?}
    VALIDATE_COUNT -->|Yes| SUCCESS([Return Images<br/>to Frontend])
    VALIDATE_COUNT -->|No| ERROR2[Return Error:<br/>Too many failures]

    style PARSE fill:#9C27B0,stroke:#4A148C,stroke-width:2px
    style SEED fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style SUCCESS fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style ERROR1 fill:#F44336,stroke:#B71C1C,stroke-width:2px
    style ERROR2 fill:#F44336,stroke:#B71C1C,stroke-width:2px
```

---

## 9. Video Generation Pipeline

```mermaid
flowchart TD
    START([Approved Images + Video Prompt]) --> SCENE_PLAN[Scene Planner<br/>Llama 3.1]

    SCENE_PLAN --> LLM2[LLM System Prompt:<br/>Create scene descriptions<br/>for each image view]

    LLM2 --> SCENES[Scene Descriptions<br/>Front: 'running motion'<br/>Side: 'slow-motion stride'<br/>Detail: 'close-up texture'<br/>Lifestyle: 'outdoor action']

    SCENES --> PARALLEL{Parallel Video Generation}

    PARALLEL --> CLIP1[Video Clip 1<br/>Input: Image 1 URL<br/>Prompt: Scene 1<br/>Motion: 0.7<br/>Duration: 3s]
    PARALLEL --> CLIP2[Video Clip 2<br/>Input: Image 2 URL<br/>Prompt: Scene 2<br/>Motion: 0.6<br/>Duration: 3s]
    PARALLEL --> CLIP3[Video Clip 3<br/>Input: Image 3 URL<br/>Prompt: Scene 3<br/>Motion: 0.3<br/>Duration: 3s]
    PARALLEL --> CLIP4[Video Clip 4<br/>Input: Image 4 URL<br/>Prompt: Scene 4<br/>Motion: 0.8<br/>Duration: 3s]

    CLIP1 --> SVD1[Stable Video Diffusion<br/>Image-to-Video<br/>14 frames @ 30fps]
    CLIP2 --> SVD2[Stable Video Diffusion<br/>Image-to-Video<br/>14 frames @ 30fps]
    CLIP3 --> SVD3[Stable Video Diffusion<br/>Image-to-Video<br/>14 frames @ 30fps]
    CLIP4 --> SVD4[Stable Video Diffusion<br/>Image-to-Video<br/>14 frames @ 30fps]

    SVD1 --> CHECK1{Success?}
    SVD2 --> CHECK2{Success?}
    SVD3 --> CHECK3{Success?}
    SVD4 --> CHECK4{Success?}

    CHECK1 -->|Yes| SAVE1[Save Clip<br/>Cost: $0.80<br/>Duration: 3.2s]
    CHECK2 -->|Yes| SAVE2[Save Clip<br/>Cost: $0.80<br/>Duration: 3.1s]
    CHECK3 -->|Yes| SAVE3[Save Clip<br/>Cost: $0.80<br/>Duration: 3.0s]
    CHECK4 -->|Yes| SAVE4[Save Clip<br/>Cost: $0.80<br/>Duration: 3.3s]

    CHECK1 -->|No| RETRY1[Retry Once<br/>Adjust motion_bucket_id]
    CHECK2 -->|No| RETRY2[Retry Once<br/>Adjust motion_bucket_id]
    CHECK3 -->|No| RETRY3[Retry Once<br/>Adjust motion_bucket_id]
    CHECK4 -->|No| RETRY4[Retry Once<br/>Adjust motion_bucket_id]

    RETRY1 --> CHECK1
    RETRY2 --> CHECK2
    RETRY3 --> CHECK3
    RETRY4 --> CHECK4

    SAVE1 & SAVE2 & SAVE3 & SAVE4 --> COLLECT[Collect All Clips]

    COLLECT --> VALIDATE{At least 2<br/>successful?}
    VALIDATE -->|Yes| SUCCESS([Return Clips<br/>to Frontend])
    VALIDATE -->|No| ERROR[Return Error:<br/>Video generation failed]

    style SCENE_PLAN fill:#9C27B0,stroke:#4A148C,stroke-width:2px
    style SVD1 fill:#FF9800,stroke:#E65100,stroke-width:2px
    style SVD2 fill:#FF9800,stroke:#E65100,stroke-width:2px
    style SVD3 fill:#FF9800,stroke:#E65100,stroke-width:2px
    style SVD4 fill:#FF9800,stroke:#E65100,stroke-width:2px
    style SUCCESS fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style ERROR fill:#F44336,stroke:#B71C1C,stroke-width:2px
```

---

## 10. Final Composition Pipeline

```mermaid
flowchart TD
    START([Approved Clips + Text Overlay + Audio Config]) --> DOWNLOAD[Download All Clips<br/>to Temp Directory]

    DOWNLOAD --> INTRO[Generate Intro Card<br/>FFmpeg: 1s black screen<br/>+ Product Name text]

    INTRO --> OUTRO[Generate Outro Card<br/>FFmpeg: 1s black screen<br/>+ CTA text]

    OUTRO --> AUDIO_CHECK{Background<br/>Music Enabled?}

    AUDIO_CHECK -->|Yes| AUDIO_FETCH[Fetch Background Music<br/>Genre: upbeat<br/>Duration: 10s]
    AUDIO_CHECK -->|No| CONCAT_FILE

    AUDIO_FETCH --> CONCAT_FILE[Create FFmpeg<br/>Concat File<br/>List all clips in order]

    CONCAT_FILE --> FFMPEG[FFmpeg Composition<br/>Complex Filter]

    FFMPEG --> SCALE[Scale to 1920x1080<br/>Maintain aspect ratio<br/>Add padding if needed]

    SCALE --> TEXT_OVERLAY[Add Text Overlays<br/>drawtext filter<br/>Intro: 1-2s<br/>Outro: 9-10s]

    TEXT_OVERLAY --> TRANSITIONS[Add Transitions<br/>Crossfade: 0.5s<br/>between clips]

    TRANSITIONS --> AUDIO_MIX{Audio Track<br/>Exists?}

    AUDIO_MIX -->|Yes| MIX_AUDIO[Mix Audio<br/>Background music<br/>Fade in/out<br/>Volume: 0.7]
    AUDIO_MIX -->|No| ENCODE

    MIX_AUDIO --> ENCODE[Encode Final Video<br/>Codec: H.264<br/>CRF: 23<br/>Preset: medium<br/>AAC Audio: 192k]

    ENCODE --> OPTIMIZE[Web Optimization<br/>+faststart flag<br/>yuv420p pixel format]

    OPTIMIZE --> UPLOAD[Upload to Storage<br/>S3 / Cloudflare R2<br/>Content-Type: video/mp4]

    UPLOAD --> VERIFY{Verify File<br/>Size < 20MB?}

    VERIFY -->|Yes| SAVE_DB[Save to Database<br/>final_video_url<br/>Cost: $0.50]
    VERIFY -->|No| COMPRESS[Re-encode with<br/>higher CRF (25)]

    COMPRESS --> UPLOAD

    SAVE_DB --> SUCCESS([Return Final Video<br/>URL + Metadata])

    style FFMPEG fill:#4CAF50,stroke:#2E7D32,stroke-width:3px
    style ENCODE fill:#2196F3,stroke:#0D47A1,stroke-width:2px
    style SUCCESS fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
```

---

## 11. Cost Tracking Architecture

```mermaid
flowchart LR
    subgraph "API Calls"
        LLM_CALL[LLM API Call<br/>Llama 3.1<br/>$0.001]
        IMG_CALL[Image Generation<br/>Flux-Pro<br/>$0.05 each]
        VID_CALL[Video Generation<br/>SVD<br/>$0.80 each]
    end

    subgraph "Cost Logger"
        LOGGER[Cost Tracking Service]
    end

    subgraph "Database"
        COSTS_TABLE[(generation_costs table<br/>session_id, agent_name,<br/>model_used, cost_usd,<br/>duration_seconds)]
        SESSION_TABLE[(sessions table<br/>total_cost field)]
    end

    subgraph "Analytics"
        AGGREGATION[Cost Aggregation<br/>Per Session<br/>Per Agent<br/>Per Model]
        ALERTS[Cost Alerts<br/>If session > $10<br/>If total > $190]
    end

    subgraph "Reporting"
        BREAKDOWN[Cost Breakdown API<br/>GET /api/sessions/:id/costs]
        DASHBOARD[Cost Dashboard<br/>Real-time Tracking]
    end

    LLM_CALL --> LOGGER
    IMG_CALL --> LOGGER
    VID_CALL --> LOGGER

    LOGGER --> COSTS_TABLE
    LOGGER --> SESSION_TABLE

    COSTS_TABLE --> AGGREGATION
    SESSION_TABLE --> AGGREGATION

    AGGREGATION --> ALERTS
    AGGREGATION --> BREAKDOWN
    BREAKDOWN --> DASHBOARD

    style LOGGER fill:#FF9800,stroke:#E65100,stroke-width:2px
    style COSTS_TABLE fill:#2196F3,stroke:#0D47A1,stroke-width:2px
    style ALERTS fill:#F44336,stroke:#B71C1C,stroke-width:2px
    style DASHBOARD fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
```

---

## 12. Deployment Architecture

```mermaid
graph TB
    subgraph "Client Side"
        BROWSER[Web Browser]
        MOBILE[Mobile Browser]
    end

    subgraph "CDN - Vercel Edge Network"
        EDGE[Edge Locations<br/>Global CDN<br/>Static Assets]
    end

    subgraph "Frontend - Vercel"
        NEXTJS[Next.js 14 App<br/>React Components<br/>SSR + CSR]
    end

    subgraph "Backend - Railway"
        FASTAPI[FastAPI Application<br/>Uvicorn ASGI Server<br/>4 Workers]
        WS_SERVER[WebSocket Server<br/>Real-time Updates]
    end

    subgraph "Database - Railway"
        POSTGRES[(PostgreSQL 15<br/>10GB Storage<br/>Shared Instance)]
    end

    subgraph "Cache Layer"
        REDIS[(Redis<br/>Session Cache<br/>Optional MVP)]
    end

    subgraph "External Services"
        REPLICATE_API[Replicate API<br/>AI Model Inference]
        S3[AWS S3 / R2<br/>Video Storage<br/>CDN Delivery]
    end

    subgraph "Monitoring"
        LOGS[Railway Logs<br/>Application Logs]
        UPTIME[UptimeRobot<br/>Health Checks]
    end

    BROWSER --> EDGE
    MOBILE --> EDGE
    EDGE --> NEXTJS

    NEXTJS --> FASTAPI
    NEXTJS --> WS_SERVER

    FASTAPI --> POSTGRES
    FASTAPI --> REDIS
    FASTAPI --> REPLICATE_API
    FASTAPI --> S3

    WS_SERVER --> POSTGRES

    FASTAPI --> LOGS
    FASTAPI --> UPTIME

    style NEXTJS fill:#000000,stroke:#000000,stroke-width:2px,color:#FFFFFF
    style FASTAPI fill:#009688,stroke:#00695C,stroke-width:2px
    style POSTGRES fill:#336791,stroke:#1A3D5C,stroke-width:2px
    style REPLICATE_API fill:#FF9800,stroke:#E65100,stroke-width:2px
    style S3 fill:#FF9900,stroke:#CC7A00,stroke-width:2px
```

---

## Additional Diagrams

### Agent State Machine

```mermaid
stateDiagram-v2
    [*] --> Created: Session Created
    Created --> PromptParsing: User Submits Prompt
    PromptParsing --> ImageGeneration: Parsing Complete
    ImageGeneration --> ImageSelection: Images Generated
    ImageSelection --> ClipGeneration: Images Approved
    ClipGeneration --> ClipSelection: Clips Generated
    ClipSelection --> FinalComposition: Clips Approved
    FinalComposition --> Complete: Video Ready
    Complete --> [*]

    ImageGeneration --> Failed: Generation Error
    ClipGeneration --> Failed: Generation Error
    FinalComposition --> Failed: Composition Error
    Failed --> [*]
```

### Error Handling Flow

```mermaid
flowchart TD
    START([API Call]) --> TRY{Try Operation}

    TRY -->|Success| LOG_SUCCESS[Log Success<br/>+ Cost + Duration]
    TRY -->|Error| CATCH[Catch Exception]

    CATCH --> CHECK_RETRY{Retry Count<br/>< 1?}

    CHECK_RETRY -->|Yes| WAIT[Wait 5 seconds]
    CHECK_RETRY -->|No| LOG_FAIL[Log Failure<br/>+ Error Message]

    WAIT --> TRY

    LOG_FAIL --> NOTIFY_USER[Notify User via WebSocket<br/>'Generation failed']
    LOG_FAIL --> SAVE_ERROR[Save Error to Database]

    LOG_SUCCESS --> RETURN_SUCCESS([Return Result])
    NOTIFY_USER --> RETURN_ERROR([Return Error Response])

    style CATCH fill:#F44336,stroke:#B71C1C,stroke-width:2px
    style LOG_FAIL fill:#F44336,stroke:#B71C1C,stroke-width:2px
    style LOG_SUCCESS fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
```

### Session State Lifecycle

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Database

    User->>Frontend: Visit Application
    Frontend->>Backend: POST /api/sessions/create
    Backend->>Database: INSERT session (stage='created')
    Database-->>Backend: session_id
    Backend-->>Frontend: session_id

    Note over Database: stage: 'created'

    User->>Frontend: Submit product prompt
    Frontend->>Backend: POST /api/generate-images
    Backend->>Database: UPDATE stage='image_generation'

    Note over Database: stage: 'image_generation'

    Backend-->>Frontend: Images complete

    User->>Frontend: Select images
    Frontend->>Backend: POST /api/save-approved-images
    Backend->>Database: UPDATE approved_image_ids<br/>stage='image_selection'

    Note over Database: stage: 'image_selection'

    User->>Frontend: Submit video prompt
    Frontend->>Backend: POST /api/generate-clips
    Backend->>Database: UPDATE stage='clip_generation'

    Note over Database: stage: 'clip_generation'

    Backend-->>Frontend: Clips complete

    User->>Frontend: Select clips
    Frontend->>Backend: POST /api/save-approved-clips
    Backend->>Database: UPDATE approved_clip_ids<br/>stage='clip_selection'

    Note over Database: stage: 'clip_selection'

    User->>Frontend: Add text & compose
    Frontend->>Backend: POST /api/compose-final-video
    Backend->>Database: UPDATE stage='final_composition'

    Note over Database: stage: 'final_composition'

    Backend-->>Frontend: Video complete
    Backend->>Database: UPDATE final_video_url<br/>stage='complete'

    Note over Database: stage: 'complete'
```

---

## Summary

This architecture document provides comprehensive visual representations of:

1. **System Architecture** - High-level component organization
2. **Agent Orchestration** - Multi-agent coordination patterns
3. **User Journey** - Complete flow from login to download
4. **Data Flow** - Transformation stages through the pipeline
5. **Database Schema** - Relational structure and relationships
6. **API Design** - Endpoint organization and dependencies
7. **WebSocket Communication** - Real-time progress updates
8. **Image Pipeline** - Detailed image generation workflow
9. **Video Pipeline** - Video clip generation process
10. **Composition Pipeline** - Final video assembly
11. **Cost Tracking** - Financial monitoring system
12. **Deployment** - Production infrastructure

All diagrams use Mermaid syntax and can be:

- Rendered in GitHub README files
- Displayed in documentation tools (GitBook, Docusaurus)
- Converted to PNG/SVG using Mermaid CLI
- Embedded in presentations

---

**Document Version:** 2.0  
**Last Updated:** November 14, 2025  
**Compatible with:** PRD v2.0
