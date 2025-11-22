# System Architecture Overview

This diagram shows the high-level component interactions, data flow, and infrastructure of the Educational Video Generator.

```mermaid
flowchart TB
    subgraph Frontend["Frontend (Vercel - Next.js 14)"]
        direction TB
        LandingPage[Landing Page]
        LoginPage[Login Page]
        DashboardPage[Dashboard]
        TopicInputPage[Topic Input Page]
        ScriptReviewPage[Script Review Page]
        VisualReviewPage[Visual Review Page]
        AudioSelectionPage[Audio Selection Page]
        VideoPage[Video Output Page]

        UIComponents[UI Components:<br/>shadcn/ui]
        Hooks[Custom Hooks:<br/>• useSession<br/>• useWebSocket<br/>• useFactExtraction<br/>• useVideoGeneration]

        LandingPage --> LoginPage
        LoginPage --> DashboardPage
        DashboardPage --> TopicInputPage
        TopicInputPage --> ScriptReviewPage
        ScriptReviewPage --> VisualReviewPage
        VisualReviewPage --> AudioSelectionPage
        AudioSelectionPage --> VideoPage
    end

    subgraph Backend["Backend (Railway - FastAPI)"]
        direction TB
        APIRouter[FastAPI Router]

        subgraph AuthEndpoints["Authentication Endpoints"]
            PostLogin[POST /api/auth/login]
            PostRegister[POST /api/auth/register]
        end

        subgraph SessionEndpoints["Session Endpoints"]
            PostCreateSession[POST /api/sessions/create]
            GetSession[GET /api/sessions/:id]
            GetSessionVideo[GET /api/sessions/:id/video]
            GetSessionCosts[GET /api/sessions/:id/costs]
        end

        subgraph GenerationEndpoints["Generation Endpoints"]
            PostGenerateScript[POST /api/generate-script]
            PostApproveScript[POST /api/approve-script]
            PostGenerateVisuals[POST /api/generate-visuals]
            PostApproveVisuals[POST /api/approve-visuals-final]
            PostSelectAudio[POST /api/select-audio]
        end

        subgraph UtilityEndpoints["Utility Endpoints"]
            GetFetchURL[GET /api/fetch-url]
            GetHealth[GET /health]
        end

        subgraph WebSocketEndpoint["WebSocket"]
            WSConnection[WS /ws/:session_id]
        end

        APIRouter --> AuthEndpoints
        APIRouter --> SessionEndpoints
        APIRouter --> GenerationEndpoints
        APIRouter --> UtilityEndpoints
        APIRouter --> WebSocketEndpoint
    end

    subgraph Database["PostgreSQL Database (Railway)"]
        direction TB
        UsersTable[(users)]
        SessionsTable[(sessions)]
        AssetsTable[(assets)]
        TemplatesTable[(templates)]
        GeminiValidationsTable[(gemini_validations)]
        CostsTable[(generation_costs)]

        SessionsTable -.->|FK| UsersTable
        AssetsTable -.->|FK| SessionsTable
        GeminiValidationsTable -.->|FK| AssetsTable
        CostsTable -.->|FK| SessionsTable
    end

    subgraph Orchestration["Orchestration Layer"]
        direction TB
        OrchestratorClass[VideoGenerationOrchestrator]
        CostTrackerClass[CostTracker]
        WSManagerClass[WebSocketManager]

        OrchestratorClass --> CostTrackerClass
        OrchestratorClass --> WSManagerClass
    end

    subgraph Agents["AI Agent Layer"]
        direction TB
        Agent2Class[NarrativeBuilderAgent]
        Agent3Class[VisualPipelineAgent]
        Agent4Class[AudioPipelineAgent]
        GeminiValidatorClass[GeminiVisionValidator]
        Agent5Class[EducationalCompositorAgent]
    end

    subgraph ExternalAPIs["External Services"]
        direction TB
        Replicate[Replicate API<br/>Llama 3.1 70B]
        OpenAI[OpenAI API<br/>DALL-E 3]
        GoogleAI[Google AI API<br/>Gemini 1.5 Pro Vision]
        ElevenLabs[ElevenLabs API<br/>Text-to-Speech]
    end

    subgraph Storage["File Storage"]
        direction TB
        LocalTemp[Temporary Local Storage<br/>Railway Container]
        S3Optional[S3/Cloudflare R2<br/>Optional Persistent]
    end

    subgraph ClientSideProcessing["Client-Side Processing"]
        direction TB
        PDFJS[PDF.js Library<br/>PDF Text Extraction]
        FactExtractionLogic[Fact Extraction Logic<br/>Concept Detection]
    end

    %% Frontend to Backend Connections
    Frontend -->|HTTPS REST API| APIRouter
    Frontend -->|WebSocket Connection| WSConnection
    Frontend -.->|Client-Side| ClientSideProcessing

    %% Backend to Database
    Backend --> Database

    %% Backend to Orchestration
    APIRouter --> OrchestratorClass

    %% Orchestration to Agents
    OrchestratorClass -->|1. Script| Agent2Class
    OrchestratorClass -->|2. Visuals| Agent3Class
    OrchestratorClass -->|3. Audio| Agent4Class
    OrchestratorClass -->|4. Validation| GeminiValidatorClass
    OrchestratorClass -->|5. Composition| Agent5Class

    %% Agents to External APIs
    Agent2Class -->|LLM Calls| Replicate
    Agent3Class -->|LLM Calls| Replicate
    Agent3Class -->|Image Gen| OpenAI
    Agent4Class -->|TTS| ElevenLabs
    GeminiValidatorClass -->|Vision Analysis| GoogleAI
    Agent5Class -->|Emergency Gen| OpenAI
    Agent5Class -->|LLM Decisions| Replicate

    %% Agents to Storage
    Agent3Class -->|Upload Visuals| Storage
    Agent4Class -->|Upload Audio| Storage
    Agent5Class -->|Upload Final Video| Storage

    %% Database to Storage
    Database -.->|Store URLs| Storage

    %% WebSocket Flow
    WSManagerClass -.->|Progress Updates| WSConnection
    Agents -.->|Progress Events| WSManagerClass

    %% Cost Tracking
    Agents -.->|Log Costs| CostTrackerClass
    CostTrackerClass --> CostsTable

    %% Styling
    classDef frontendClass fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef backendClass fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef databaseClass fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef agentClass fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef externalClass fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef storageClass fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef orchestrationClass fill:#ffe0b2,stroke:#e64a19,stroke-width:2px

    class Frontend,LandingPage,LoginPage,DashboardPage,TopicInputPage,ScriptReviewPage,VisualReviewPage,AudioSelectionPage,VideoPage frontendClass
    class Backend,APIRouter,AuthEndpoints,SessionEndpoints,GenerationEndpoints,UtilityEndpoints,WebSocketEndpoint backendClass
    class Database,UsersTable,SessionsTable,AssetsTable,TemplatesTable,GeminiValidationsTable,CostsTable databaseClass
    class Agents,Agent2Class,Agent3Class,Agent4Class,GeminiValidatorClass,Agent5Class agentClass
    class ExternalAPIs,Replicate,OpenAI,GoogleAI,ElevenLabs externalClass
    class Storage,LocalTemp,S3Optional storageClass
    class Orchestration,OrchestratorClass,CostTrackerClass,WSManagerClass orchestrationClass
```

## Data Flow Sequence

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Orchestrator
    participant Agents
    participant Database
    participant External APIs
    participant Storage

    User->>Frontend: 1. Login
    Frontend->>Backend: POST /api/auth/login
    Backend->>Database: Verify credentials
    Database-->>Backend: User data
    Backend-->>Frontend: JWT token
    Frontend-->>User: Dashboard

    User->>Frontend: 2. Create session + Enter facts
    Frontend->>Frontend: Client-side fact extraction
    Frontend->>Backend: POST /api/sessions/create
    Backend->>Database: Create session record
    Database-->>Backend: Session ID
    Backend-->>Frontend: Session created

    User->>Frontend: 3. Generate script
    Frontend->>Backend: POST /api/generate-script
    Backend->>Orchestrator: Trigger script generation

    activate Orchestrator
    Orchestrator->>Agents: Call Agent 2 (Narrative Builder)
    Agents->>External APIs: Llama 3.1 API call
    External APIs-->>Agents: Generated script JSON
    Agents-->>Orchestrator: Script result + cost
    Orchestrator->>Database: Save script + cost
    Orchestrator-->>Backend: Script ready
    deactivate Orchestrator

    Backend-->>Frontend: WebSocket: Script ready
    Frontend-->>User: Display script for review

    User->>Frontend: 4. Approve script + Generate visuals
    Frontend->>Backend: POST /api/approve-script
    Frontend->>Backend: POST /api/generate-visuals
    Backend->>Orchestrator: Trigger visual generation

    activate Orchestrator
    Orchestrator->>Agents: Call Agent 3 (Visual Pipeline)

    loop For each visual (parallel)
        Agents->>Database: Check template library
        alt Template match found
            Agents->>Storage: Customize template PSD
        else No template match
            Agents->>External APIs: DALL-E 3 generation
            External APIs-->>Agents: Generated image
        end
        Agents->>Storage: Upload visual
        Storage-->>Agents: Visual URL
    end

    Agents-->>Orchestrator: All visuals + costs
    Orchestrator->>Database: Save visuals + costs
    Orchestrator-->>Backend: Visuals ready
    deactivate Orchestrator

    Backend-->>Frontend: WebSocket: Visuals ready
    Frontend-->>User: Display visuals for review

    User->>Frontend: 5. Approve visuals + Select audio
    Frontend->>Backend: POST /api/approve-visuals-final
    Frontend->>Backend: POST /api/select-audio
    Backend->>Orchestrator: Trigger composition pipeline

    activate Orchestrator

    par Gemini Validation
        Orchestrator->>Agents: Call Gemini Validator
        Agents->>Storage: Download visuals
        Agents->>External APIs: Gemini frame analysis
        External APIs-->>Agents: Validation results
        Agents->>Database: Save validation JSONs
    and Audio Generation
        Orchestrator->>Agents: Call Agent 4 (Audio)
        Agents->>External APIs: ElevenLabs TTS
        External APIs-->>Agents: Audio segments
        Agents->>Storage: Upload audio
    end

    Orchestrator->>Agents: Call Agent 5 (Compositor)

    Agents->>Database: Read Gemini validations

    alt Mismatches detected
        Agents->>External APIs: LLM decision (self-healing)
        External APIs-->>Agents: Healing strategy

        alt Strategy: Emergency generate
            Agents->>External APIs: DALL-E 3 emergency
            External APIs-->>Agents: New visual
        else Strategy: Text slide
            Agents->>Agents: Generate text slide (FFmpeg)
        end
    end

    Agents->>Storage: Download all final assets
    Agents->>Agents: FFmpeg composition
    Agents->>Storage: Upload final video
    Storage-->>Agents: Final video URL

    Agents-->>Orchestrator: Composition complete + costs
    Orchestrator->>Database: Save final video + costs + logs
    Orchestrator-->>Backend: Video ready
    deactivate Orchestrator

    Backend-->>Frontend: WebSocket: Video ready
    Frontend-->>User: Display video + download options

    User->>Frontend: 6. Download video
    Frontend->>Backend: GET /api/sessions/:id/video
    Backend->>Storage: Fetch video file
    Storage-->>Backend: Video stream
    Backend-->>Frontend: Video download
    Frontend-->>User: Video file saved
```

## Technology Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **PDF Processing**: PDF.js
- **State Management**: React hooks (useState, useEffect)
- **WebSocket**: Native WebSocket API
- **Deployment**: Vercel

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.11
- **Database ORM**: SQLAlchemy
- **Authentication**: JWT (python-jose)
- **WebSocket**: FastAPI WebSockets
- **Video Processing**: FFmpeg
- **Image Processing**: Pillow, ImageMagick
- **Deployment**: Railway

### Database
- **RDBMS**: PostgreSQL 15
- **Hosting**: Railway PostgreSQL
- **Migrations**: Alembic

### AI/ML Services
- **LLM**: Llama 3.1 70B (via Replicate)
- **Image Generation**: DALL-E 3 (OpenAI)
- **Vision Validation**: Gemini 1.5 Pro Vision (Google AI)
- **Text-to-Speech**: ElevenLabs

### Storage
- **Temporary**: Railway container local storage
- **Optional Persistent**: S3 or Cloudflare R2

### Monitoring (Optional)
- **Error Tracking**: Sentry
- **Logging**: Python logging module

## Infrastructure Costs

### Development
- **Railway**: $5 free credit → $20/month
- **Vercel**: Free tier (100GB bandwidth)
- **PostgreSQL**: Included with Railway
- **Total Infrastructure**: $0-$20/month

### Per-Video Production
- **AI Services**: $4.18-$4.34
- **Storage**: ~$0.05
- **Total per Video**: ~$4.50

### Testing Budget
- **$200 total** = ~45 test videos during sprint

## Deployment Architecture

```mermaid
flowchart LR
    subgraph Internet["Internet"]
        User[End Users]
    end

    subgraph Vercel["Vercel (Global CDN)"]
        NextApp[Next.js App<br/>Static + SSR]
    end

    subgraph Railway["Railway (Cloud)"]
        FastAPIApp[FastAPI Backend<br/>+ WebSocket Server]
        PostgresDB[(PostgreSQL 15)]
        TempStorage[Temporary File Storage]
    end

    subgraph ExternalServices["External Services"]
        ReplicateAPI[Replicate]
        OpenAIAPI[OpenAI]
        GoogleAPI[Google AI]
        ElevenLabsAPI[ElevenLabs]
    end

    User <-->|HTTPS| Vercel
    Vercel <-->|API Calls| FastAPIApp
    Vercel <-.->|WebSocket| FastAPIApp
    FastAPIApp <--> PostgresDB
    FastAPIApp <--> TempStorage
    FastAPIApp --> ExternalServices

    classDef userClass fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef vercelClass fill:#000000,stroke:#ffffff,stroke-width:2px,color:#ffffff
    classDef railwayClass fill:#0b0d0e,stroke:#a259ff,stroke-width:2px,color:#ffffff
    classDef externalClass fill:#fce4ec,stroke:#c2185b,stroke-width:2px

    class User userClass
    class Vercel,NextApp vercelClass
    class Railway,FastAPIApp,PostgresDB,TempStorage railwayClass
    class ExternalServices,ReplicateAPI,OpenAIAPI,GoogleAPI,ElevenLabsAPI externalClass
```

## Security Considerations

1. **Authentication**: JWT tokens with expiration
2. **CORS**: Configured for production domains only
3. **Rate Limiting**: API rate limits per user/session
4. **Input Validation**: Pydantic models for all inputs
5. **File Upload**: Size limits, type validation
6. **Environment Variables**: Secrets stored securely
7. **Database**: Connection pooling, parameterized queries
8. **WebSocket**: Session-based authentication

## Scalability Considerations

### Current MVP (Single Server)
- Handles 1-5 concurrent video generations
- Railway auto-scaling up to allocated resources
- PostgreSQL connection pooling

### Post-MVP Scaling
- **Message Queue**: RabbitMQ or Redis for async processing
- **Worker Pools**: Distributed agent processing
- **CDN Storage**: Migrate to S3 + CloudFront
- **Database Replication**: Read replicas for sessions
- **Load Balancer**: Multiple backend instances
