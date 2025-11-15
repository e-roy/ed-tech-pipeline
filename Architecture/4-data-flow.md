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

    subgraph "Processing Stage 5"
        ANALYZE[Video Analysis Agent<br/>Extract frames @ 1s intervals]
        VISION[GPT-4 Vision API<br/>Analyze each frame]
        METADATA[JSON Metadata Files<br/>Per-second analysis]
        CONSISTENCY[Cross-Clip Analysis<br/>Consistency check]
    end

    subgraph "User Selection"
        APPROVED_CLIPS[Approved Clips<br/>User selects 3 of 4]
    end

    subgraph "Processing Stage 6"
        INTRO[Intro Card: 1s<br/>Product Name]
        STITCH[FFmpeg Stitching<br/>Transitions + Audio<br/>(Uses analysis metadata)]
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
    CLIP1 & CLIP2 & CLIP3 & CLIP4 --> ANALYZE
    ANALYZE --> VISION
    VISION --> METADATA
    METADATA --> CONSISTENCY
    CONSISTENCY --> APPROVED_CLIPS

    APPROVED_CLIPS --> STITCH
    INTRO --> STITCH
    OUTRO --> STITCH
    STITCH --> FINAL

    style PARSE fill:#9C27B0,stroke:#4A148C,stroke-width:2px
    style SCENE_PLAN fill:#9C27B0,stroke:#4A148C,stroke-width:2px
    style STITCH fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style FINAL fill:#2196F3,stroke:#0D47A1,stroke-width:3px
```
