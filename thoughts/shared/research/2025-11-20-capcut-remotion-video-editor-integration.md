---
date: 2025-11-20T23:29:58Z
researcher: Claude (Sonnet 4.5)
git_commit: 6dad8061c7eb1cb5d6295706fa3ca91f7b790fee
branch: ClassCut
repository: pipeline
topic: "Adding CapCut-like Editing Features with Remotion and Premiere Pro-style UI"
tags: [research, codebase, remotion, video-editing, capcut, premiere-pro, ui-architecture, mui]
status: complete
last_updated: 2025-11-20
last_updated_by: Claude (Sonnet 4.5)
---

# Research: Adding CapCut-like Editing Features with Remotion and Premiere Pro-style UI

**Date**: 2025-11-20T23:29:58Z
**Researcher**: Claude (Sonnet 4.5)
**Git Commit**: 6dad8061c7eb1cb5d6295706fa3ca91f7b790fee
**Branch**: ClassCut
**Repository**: pipeline

## Research Question

How to add CapCut-like editing features to the existing Gauntlet Pipeline codebase using Remotion, with a Premiere Pro-style UI? The implementation needs:
- Timeline-based editing (cuts, trims, splits)
- Text/caption overlays with animations
- Audio waveform visualization and editing
- Multi-track support
- Real-time preview while editing
- MP4 export (max 5 minutes)
- Integration with existing edit page at `/dashboard/editing/[id]`
- State management using Zustand
- Hybrid rendering (Remotion for preview, FFmpeg for export)
- MUI for Premiere Pro-style UI

## Summary

The Gauntlet Pipeline codebase is a **Next.js 16 + FastAPI** application for AI-generated video content. It currently has a placeholder editing page that displays finished videos with a "Coming Soon" edit button. Based on research of the existing codebase and the MatchaClip repository (which successfully implements Remotion-based video editing), here's what exists and what's needed:

**Current State:**
- Edit page exists at `frontend/src/app/dashboard/editing/[id]/editing-page-client.tsx` but only displays videos
- Backend has robust FFmpeg video processing via `educational_compositor.py` and `ffmpeg_compositor.py`
- WebSocket infrastructure for real-time updates already implemented
- S3 storage and video asset management fully operational
- FastAPI backend on EC2 with single-worker Uvicorn deployment
- Frontend uses shadcn/ui (Radix UI based) with Tailwind CSS v4

**Recommended Architecture (Based on MatchaClip Pattern):**
- Use **Remotion Player** for client-side real-time preview (not for final rendering)
- Build custom timeline UI using **react-moveable** for drag/resize interactions
- Use **MUI v7.1+** for Premiere Pro-style UI components with CSS Layers for Tailwind compatibility
- Store editing state in **Zustand** (already in codebase v5.0.8)
- Render final videos server-side using existing **FFmpeg infrastructure**
- Use **IndexedDB** for temporary local asset storage during editing (optional)

**Rendering Strategy:**
- **Real-time Preview**: Client-side using Remotion Player (instant feedback)
- **Final Export**: Server-side using existing FFmpeg compositor (professional quality, faster, no browser memory limits)

## Detailed Findings

### 1. MUI Compatibility Analysis

#### Can MUI and shadcn/ui Coexist?

**Yes, MUI and shadcn/ui can be used together**, but requires proper configuration to avoid CSS conflicts.

**Potential Conflicts:**

| Conflict Area | MUI Approach | shadcn/ui Approach |
|---------------|--------------|-------------------|
| Styling System | Emotion/CSS-in-JS | Tailwind CSS utilities |
| CSS Reset | CssBaseline | Tailwind Preflight |
| Theming | ThemeProvider + createTheme | CSS variables + Tailwind config |
| Design Language | Material Design | Radix primitives (unstyled) |

#### Recommended Integration: CSS Layers (MUI v7.1+)

MUI v7.1+ officially supports Tailwind CSS v4 through CSS layers. This is the cleanest approach:

```tsx
// app/layout.tsx (Next.js App Router)
import { AppRouterCacheProvider } from '@mui/material-nextjs/v15-appRouter';
import GlobalStyles from '@mui/material/GlobalStyles';
import { ThemeProvider, createTheme } from '@mui/material/styles';

const theme = createTheme({
  // Customize to match your design
});

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <AppRouterCacheProvider options={{ enableCssLayer: true }}>
          <GlobalStyles styles="@layer theme, base, mui, components, utilities;" />
          <ThemeProvider theme={theme}>
            {children}
          </ThemeProvider>
        </AppRouterCacheProvider>
      </body>
    </html>
  );
}
```

#### MUI + React 19 Compatibility

**Status: Fully compatible**
- MUI v7 (released March 2025) has full React 19 support
- MUI v5 and v6 also updated for React 19 compatibility
- MUI v7 uses Pigment CSS (zero-runtime CSS-in-JS) for better RSC compatibility

#### Dependencies to Add for MUI

```bash
cd frontend
npm install @mui/material @mui/material-nextjs @emotion/react @emotion/styled @emotion/cache
```

#### Alternative: Scope MUI to Video Editor Only

To minimize conflicts with existing shadcn components, scope MUI usage to just the video editor:

```tsx
// components/video-editor/EditorLayout.tsx
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

const editorTheme = createTheme({
  palette: {
    mode: 'dark', // Match Premiere Pro dark theme
    primary: { main: '#2196f3' },
    background: {
      default: '#1e1e1e',
      paper: '#252525',
    },
  },
});

export function EditorLayout({ children }) {
  return (
    <ThemeProvider theme={editorTheme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
}
```

### 2. Current Codebase Architecture

#### Frontend: Next.js 16 with App Router

**Framework Stack** (`frontend/package.json`):
- Next.js 16.0.3 (App Router)
- React 19.0.0
- TypeScript 5.8.2
- Tailwind CSS 4.0.15
- shadcn/ui component library (Radix UI based)
- Zustand 5.0.8 (state management)

**Existing Edit Page** (`frontend/src/app/dashboard/editing/[id]/editing-page-client.tsx`):
```typescript
// Lines 332-336: "Edit Video" button currently disabled
<Button variant="outline">
  <Scissors className="mr-2 h-4 w-4" />
  Edit Video
</Button>
```

The page currently:
- Displays video player with controls (lines 274-284)
- Shows video metadata (duration, resolution, created date) (lines 289-318)
- Has download functionality (lines 160-170)
- Polls backend for video completion via `/api/sessions/${sessionId}` (lines 100-146)

#### Backend: FastAPI on AWS EC2

**Framework** (`backend/app/main.py:28-34`):
- FastAPI 0.109.0
- Uvicorn 0.27.0 (single worker for WebSocket support)
- PostgreSQL database via SQLAlchemy
- S3 storage via boto3

**Video Processing** (`backend/app/services/ffmpeg_compositor.py`):
- FFmpegCompositor class (lines 20-405)
- Normalizes clips to 1920x1080@30fps H.264
- Supports text overlays using drawtext filter
- Audio mixing capabilities

### 3. MatchaClip Remotion Implementation Analysis

#### Overview

MatchaClip (ClipForge) is an Electron desktop app using Remotion 4.0.369 for preview-only rendering. Key architectural decisions:

**Remotion Setup** (`/tmp/MatchaClip/package.json:20-21`):
```json
"@remotion/player": "^4.0.369",
"@remotion/media-parser": "^4.0.369"
```

**No traditional `remotion.config.ts`** - Remotion is embedded as a React component via `<Player>` rather than a standalone Remotion project.

#### Timeline Architecture

**Multi-Track Implementation** (`/tmp/MatchaClip/app/types/index.ts:10-42`):
- Single `mediaFiles` array with type discriminator: `"video" | "audio" | "image"`
- Separate `textElements` array for text overlays
- Z-index based layering for visual stacking
- Position tracking in two coordinate spaces:
  - **Source space**: `startTime`, `endTime` (trim points within source file)
  - **Timeline space**: `positionStart`, `positionEnd` (position in final video)

**Timeline UI** (`/tmp/MatchaClip/app/components/editor/timeline/Timline.tsx:24-395`):
- Built with **react-moveable 0.56.0** (not Remotion's timeline)
- Zoom control: pixels-per-second scaling
- Playhead click-to-seek
- Split, duplicate, delete tools
- Separate track components per media type

**Drag & Resize** (`/tmp/MatchaClip/app/components/editor/timeline/elements-timeline/VideoTimeline.tsx:20-112`):
- Uses react-moveable for interactions
- Throttled at 16ms for 60fps smoothness using lodash.throttle

#### Remotion Composition

**Root Composition** (`/tmp/MatchaClip/app/components/editor/player/remotion/sequence/composition.tsx:8-59`):
- Reads editing state from Redux store
- Renders all media items dynamically using factory pattern
- Syncs Remotion frame to Redux state with throttling

**Preview Player** (`/tmp/MatchaClip/app/components/editor/player/remotion/Player.tsx:20-118`):
- 1920x1080 @ 30fps composition
- Bidirectional sync with Redux state
- In/out point monitoring for playback range

#### Export/Rendering Architecture

**Critical: Remotion NOT used for final rendering**

MatchaClip uses native FFmpeg via Electron IPC for all exports:
- **Performance**: Native FFmpeg is 10-100x faster than browser-based rendering
- **Memory**: No browser memory constraints
- **Quality**: Professional-grade encoding with full codec control

### 4. Rendering Options Analysis

#### Recommended: Hybrid Approach

**Architecture**:
1. **Preview**: Client-side Remotion Player (instant feedback)
2. **Final Export**: Server-side FFmpeg (quality + speed)

**Implementation**:
- Store editing state (cuts, overlays, effects) in Zustand
- Remotion Player renders preview from state
- Export button sends editing state to backend
- Backend translates state to FFmpeg commands
- FFmpeg processes and uploads final video to S3
- WebSocket sends progress updates

**Why This Works**:
- Best of both worlds: instant preview + fast export
- Matches MatchaClip architecture (proven successful)
- Leverages existing backend infrastructure
- No browser memory issues for 5-minute videos

### 5. WebSocket Real-Time Updates

**WebSocketManager** (`backend/app/services/websocket_manager.py:16-246`):
- In-memory connection tracking per worker
- Database-backed tracking for cross-worker support
- Session-based connection organization

**Frontend WebSocket Hook** (`frontend/src/hooks/useWebSocket.ts:1-102`):
- Exponential backoff reconnection (1s, 2s, 4s, 8s, 16s, 30s max)
- Max 5 reconnection attempts
- Returns: `{ isConnected, lastMessage, sendMessage }`

### 6. Integration Plan

#### Phase 1: Dependencies and Setup

**Install Required Packages**:
```bash
cd frontend
npm install remotion @remotion/player react-moveable @scena/react-guides lodash
npm install @mui/material @mui/material-nextjs @emotion/react @emotion/styled @emotion/cache
```

**Configure MUI with CSS Layers** (in root layout or editor-specific layout):
```tsx
import { AppRouterCacheProvider } from '@mui/material-nextjs/v15-appRouter';
import GlobalStyles from '@mui/material/GlobalStyles';

// Enable CSS layers for MUI + Tailwind compatibility
<AppRouterCacheProvider options={{ enableCssLayer: true }}>
  <GlobalStyles styles="@layer theme, base, mui, components, utilities;" />
  {children}
</AppRouterCacheProvider>
```

#### Phase 2: State Management with Zustand

**Editor Store** (`frontend/src/stores/editorStore.ts`):
```typescript
import { create } from 'zustand';

interface EditorState {
  // Project metadata
  projectId: string;
  duration: number;
  fps: number; // 30

  // Playback
  currentTime: number;
  isPlaying: boolean;
  isMuted: boolean;
  inPoint: number | null;
  outPoint: number | null;

  // Timeline
  timelineZoom: number; // pixels per second

  // Media items
  mediaFiles: MediaFile[];
  textElements: TextElement[];

  // Selection
  selectedItems: string[];

  // Actions
  addMedia: (media: MediaFile) => void;
  updateMedia: (id: string, updates: Partial<MediaFile>) => void;
  deleteMedia: (id: string) => void;
  splitMedia: (id: string, time: number) => void;
  setCurrentTime: (time: number) => void;
  setIsPlaying: (playing: boolean) => void;
}

interface MediaFile {
  id: string;
  type: "video" | "audio" | "image";
  startTime: number;
  endTime: number;
  duration: number;
  positionStart: number;
  positionEnd: number;
  src: string;
  fileName: string;
  playbackSpeed: number;
  volume: number;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  opacity?: number;
  zIndex: number;
}

interface TextElement {
  id: string;
  text: string;
  positionStart: number;
  positionEnd: number;
  x: number;
  y: number;
  font?: string;
  fontSize?: number;
  color?: string;
  backgroundColor?: string;
  opacity?: number;
  zIndex: number;
}

export const useEditorStore = create<EditorState>((set, get) => ({
  // Initial state
  projectId: '',
  duration: 0,
  fps: 30,
  currentTime: 0,
  isPlaying: false,
  isMuted: false,
  inPoint: null,
  outPoint: null,
  timelineZoom: 100,
  mediaFiles: [],
  textElements: [],
  selectedItems: [],

  // Actions
  addMedia: (media) => set((state) => ({
    mediaFiles: [...state.mediaFiles, media],
    duration: Math.max(state.duration, media.positionEnd)
  })),

  updateMedia: (id, updates) => set((state) => ({
    mediaFiles: state.mediaFiles.map(m =>
      m.id === id ? { ...m, ...updates } : m
    )
  })),

  deleteMedia: (id) => set((state) => ({
    mediaFiles: state.mediaFiles.filter(m => m.id !== id)
  })),

  splitMedia: (id, time) => {
    const state = get();
    const media = state.mediaFiles.find(m => m.id === id);
    if (!media || time <= media.positionStart || time >= media.positionEnd) return;

    const splitPoint = time - media.positionStart + media.startTime;
    const firstPart = { ...media, endTime: splitPoint, positionEnd: time };
    const secondPart = {
      ...media,
      id: `${id}_split_${Date.now()}`,
      startTime: splitPoint,
      positionStart: time
    };

    set((state) => ({
      mediaFiles: [
        ...state.mediaFiles.filter(m => m.id !== id),
        firstPart,
        secondPart
      ]
    }));
  },

  setCurrentTime: (time) => set({ currentTime: time }),
  setIsPlaying: (playing) => set({ isPlaying: playing }),
}));
```

#### Phase 3: Remotion Preview Integration

**Composition Root** (`frontend/src/components/video-editor/remotion/Composition.tsx`):
```typescript
import { useCurrentFrame, Sequence, AbsoluteFill, Audio, Video, Img } from 'remotion';
import { useEditorStore } from '@/stores/editorStore';

export const EditorComposition = () => {
  const frame = useCurrentFrame();
  const fps = useEditorStore(state => state.fps);
  const mediaFiles = useEditorStore(state => state.mediaFiles);
  const textElements = useEditorStore(state => state.textElements);

  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      {/* Render media files sorted by z-index */}
      {[...mediaFiles].sort((a, b) => a.zIndex - b.zIndex).map(media => (
        <MediaSequenceItem key={media.id} media={media} fps={fps} />
      ))}

      {/* Render text elements */}
      {textElements.map(text => (
        <TextSequenceItem key={text.id} text={text} fps={fps} />
      ))}
    </AbsoluteFill>
  );
};

const MediaSequenceItem = ({ media, fps }) => {
  const from = Math.round(media.positionStart * fps);
  const duration = Math.round((media.positionEnd - media.positionStart) * fps);

  return (
    <Sequence from={from} durationInFrames={duration}>
      {media.type === 'video' && (
        <Video
          src={media.src}
          startFrom={Math.round(media.startTime * fps)}
          endAt={Math.round(media.endTime * fps)}
          volume={media.volume / 100}
          style={{
            position: 'absolute',
            left: media.x || 0,
            top: media.y || 0,
            width: media.width || '100%',
            opacity: (media.opacity || 100) / 100,
          }}
        />
      )}
      {media.type === 'audio' && (
        <Audio
          src={media.src}
          startFrom={Math.round(media.startTime * fps)}
          endAt={Math.round(media.endTime * fps)}
          volume={media.volume / 100}
        />
      )}
      {media.type === 'image' && (
        <Img
          src={media.src}
          style={{
            position: 'absolute',
            left: media.x || 0,
            top: media.y || 0,
            width: media.width || '100%',
            opacity: (media.opacity || 100) / 100,
          }}
        />
      )}
    </Sequence>
  );
};

const TextSequenceItem = ({ text, fps }) => {
  const from = Math.round(text.positionStart * fps);
  const duration = Math.round((text.positionEnd - text.positionStart) * fps);

  return (
    <Sequence from={from} durationInFrames={duration}>
      <div
        style={{
          position: 'absolute',
          left: text.x,
          top: text.y,
          fontSize: text.fontSize || 24,
          fontFamily: text.font || 'Arial',
          color: text.color || '#ffffff',
          backgroundColor: text.backgroundColor || 'transparent',
          opacity: (text.opacity || 100) / 100,
          zIndex: text.zIndex,
        }}
      >
        {text.text}
      </div>
    </Sequence>
  );
};
```

**Preview Player** (`frontend/src/components/video-editor/PreviewPlayer.tsx`):
```typescript
import { Player, PlayerRef } from '@remotion/player';
import { useRef, useEffect } from 'react';
import { useEditorStore } from '@/stores/editorStore';
import { EditorComposition } from './remotion/Composition';

export const PreviewPlayer = () => {
  const playerRef = useRef<PlayerRef>(null);
  const duration = useEditorStore(state => state.duration);
  const currentTime = useEditorStore(state => state.currentTime);
  const isPlaying = useEditorStore(state => state.isPlaying);
  const setCurrentTime = useEditorStore(state => state.setCurrentTime);
  const fps = 30;

  // Sync player to store state
  useEffect(() => {
    if (!playerRef.current || isPlaying) return;
    const frame = Math.round(currentTime * fps);
    playerRef.current.seekTo(frame);
  }, [currentTime, fps, isPlaying]);

  // Control playback
  useEffect(() => {
    if (!playerRef.current) return;
    if (isPlaying) {
      playerRef.current.play();
    } else {
      playerRef.current.pause();
    }
  }, [isPlaying]);

  const durationInFrames = Math.max(1, Math.floor(duration * fps) + 1);

  return (
    <Player
      ref={playerRef}
      component={EditorComposition}
      durationInFrames={durationInFrames}
      compositionWidth={1920}
      compositionHeight={1080}
      fps={fps}
      style={{ width: '100%', height: '100%' }}
      controls={false}
      clickToPlay={false}
      acknowledgeRemotionLicense
    />
  );
};
```

#### Phase 4: MUI-Based Timeline UI

**Timeline Container** (`frontend/src/components/video-editor/Timeline.tsx`):
```typescript
import { Box, Slider, IconButton, Paper, Typography } from '@mui/material';
import { ZoomIn, ZoomOut, ContentCut, ContentCopy, Delete } from '@mui/icons-material';
import { useEditorStore } from '@/stores/editorStore';
import { VideoTrack } from './tracks/VideoTrack';
import { AudioTrack } from './tracks/AudioTrack';
import { TextTrack } from './tracks/TextTrack';
import { TimeRuler } from './TimeRuler';
import { Playhead } from './Playhead';

export const Timeline = () => {
  const timelineZoom = useEditorStore(state => state.timelineZoom);
  const duration = useEditorStore(state => state.duration);
  const currentTime = useEditorStore(state => state.currentTime);
  const setCurrentTime = useEditorStore(state => state.setCurrentTime);

  const handleTimelineClick = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const time = x / timelineZoom;
    setCurrentTime(Math.max(0, Math.min(time, duration)));
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', bgcolor: 'background.default' }}>
      {/* Toolbar */}
      <Paper sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 1, borderRadius: 0 }}>
        <IconButton size="small"><ContentCut /></IconButton>
        <IconButton size="small"><ContentCopy /></IconButton>
        <IconButton size="small"><Delete /></IconButton>

        <Box sx={{ flexGrow: 1 }} />

        <IconButton size="small"><ZoomOut /></IconButton>
        <Slider
          value={timelineZoom}
          min={20}
          max={200}
          sx={{ width: 100 }}
          size="small"
        />
        <IconButton size="small"><ZoomIn /></IconButton>
      </Paper>

      {/* Timeline tracks */}
      <Box
        sx={{ flex: 1, overflow: 'auto', position: 'relative' }}
        onClick={handleTimelineClick}
      >
        <TimeRuler zoom={timelineZoom} duration={duration} />
        <Playhead currentTime={currentTime} zoom={timelineZoom} />

        <Box sx={{ pt: 4 }}>
          <VideoTrack />
          <AudioTrack />
          <TextTrack />
        </Box>
      </Box>
    </Box>
  );
};
```

#### Phase 5: Export Pipeline

**Export Endpoint** (NEW: `backend/app/routes/video_editor.py`):
```python
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import asyncio

router = APIRouter(prefix="/api/video", tags=["video-editor"])

class MediaFileExport(BaseModel):
    id: str
    type: str  # "video" | "audio" | "image"
    s3_key: str
    start_time: float
    end_time: float
    position_start: float
    position_end: float
    playback_speed: float = 1.0
    volume: int = 100
    x: Optional[int] = None
    y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    opacity: Optional[int] = 100
    z_index: int = 0

class TextElementExport(BaseModel):
    id: str
    text: str
    position_start: float
    position_end: float
    x: int
    y: int
    font: Optional[str] = "Arial"
    font_size: Optional[int] = 24
    color: Optional[str] = "#ffffff"
    background_color: Optional[str] = None
    opacity: Optional[int] = 100

class ComposeEditRequest(BaseModel):
    session_id: str
    duration: float
    fps: int = 30
    resolution: dict = {"width": 1920, "height": 1080}
    media_files: List[MediaFileExport]
    text_elements: List[TextElementExport]

@router.post("/compose-edit")
async def compose_edit(
    request: ComposeEditRequest,
    background_tasks: BackgroundTasks,
    user = Depends(get_current_user)
):
    """Compose edited video from editing state."""

    # Validate user owns all referenced S3 assets
    for media in request.media_files:
        if not media.s3_key.startswith(f"users/{user.id}/"):
            raise HTTPException(403, "Unauthorized access to asset")

    # Start background processing
    background_tasks.add_task(
        process_video_edit,
        session_id=request.session_id,
        user_id=user.id,
        export_data=request.dict()
    )

    return {
        "success": True,
        "session_id": request.session_id,
        "message": "Video export started"
    }
```

## Code References

### Existing Codebase Files

**Frontend**:
- Current edit page: `frontend/src/app/dashboard/editing/[id]/editing-page-client.tsx:1-368`
- WebSocket hook: `frontend/src/hooks/useWebSocket.ts:1-102`
- Package.json: `frontend/package.json:1-121`

**Backend**:
- FFmpeg compositor: `backend/app/services/ffmpeg_compositor.py:20-405`
- WebSocket manager: `backend/app/services/websocket_manager.py:16-246`
- Storage service: `backend/app/services/storage.py:23-961`
- Main FastAPI app: `backend/app/main.py:1-746`

### MatchaClip Reference Files

**Remotion Implementation**:
- Composition root: `/tmp/MatchaClip/app/components/editor/player/remotion/sequence/composition.tsx:8-59`
- Preview player: `/tmp/MatchaClip/app/components/editor/player/remotion/Player.tsx:20-118`
- Text overlay: `/tmp/MatchaClip/app/components/editor/player/remotion/sequence/items/text-sequence-item.tsx:25-119`

**Timeline Implementation**:
- Main timeline: `/tmp/MatchaClip/app/components/editor/timeline/Timline.tsx:24-395`
- Video track: `/tmp/MatchaClip/app/components/editor/timeline/elements-timeline/VideoTimeline.tsx:20-112`

## Architecture Documentation

### Recommended Architecture

```
+-------------------------------------------------------------+
|                      Frontend (Next.js 16)                   |
|                                                              |
|  +-------------+  +-------------+  +-------------+          |
|  | Media Bin   |  | Preview     |  | Properties  |          |
|  | (S3 Assets) |  | (Remotion)  |  | Panel (MUI) |          |
|  +-------------+  +-------------+  +-------------+          |
|                                                              |
|  +----------------------------------------------------+     |
|  |           Timeline (MUI + react-moveable)          |     |
|  |   [Video Track] [Audio Track] [Text Track]         |     |
|  +----------------------------------------------------+     |
|                                                              |
|  State: Zustand Store                                       |
+-------------------------------------------------------------+
                            |
                            | WebSocket / REST API
                            v
+-------------------------------------------------------------+
|                      Backend (FastAPI)                       |
|                                                              |
|  +--------------------------------------------------+       |
|  |      Video Editor Compositor (NEW)               |       |
|  |  - Parse editing state from Zustand              |       |
|  |  - Download media from S3                        |       |
|  |  - Build FFmpeg filter graph                     |       |
|  |  - Execute FFmpeg render                         |       |
|  |  - Upload to S3                                  |       |
|  +--------------------------------------------------+       |
+-------------------------------------------------------------+
                            |
                            v
                    +---------------+
                    |   AWS S3      |
                    +---------------+
```

## Open Questions

1. **IndexedDB for Local Storage**: Should we use IndexedDB for temporary local asset storage, or rely solely on S3 presigned URLs?
   - **Recommendation**: Use presigned URLs initially for simplicity.

2. **MUI Theme Customization**: How closely should MUI components match the existing shadcn/ui design language?
   - **Recommendation**: Create a dark theme for the video editor that matches Premiere Pro aesthetics, keeping it visually distinct from the rest of the dashboard.

3. **Audio Waveform Generation**: Pre-generate on upload or render on-demand?
   - **Recommendation**: Pre-generate using FFmpeg `showwavespic` filter and cache in S3.

4. **Undo/Redo**: Should we implement undo/redo functionality?
   - **Recommendation**: Yes, use Zustand middleware like `temporal` for time-travel.

## Next Steps

### Week 1-2: Foundation
1. Install dependencies (Remotion, MUI, react-moveable)
2. Configure MUI with CSS Layers for Tailwind compatibility
3. Create Zustand editor store
4. Build basic timeline UI skeleton with MUI

### Week 3-4: Core Features
5. Integrate Remotion Player for preview
6. Implement drag & resize with react-moveable
7. Add text overlays
8. Build backend export endpoint

### Week 5-6: Polish
9. Add audio waveforms
10. Implement split/duplicate/delete tools
11. Add undo/redo
12. Test end-to-end flow

---

**Research Complete**: This document provides a comprehensive analysis for adding CapCut-like editing features with Remotion, MUI for Premiere Pro-style UI, Zustand for state management, and hybrid rendering (Remotion preview + FFmpeg export).
