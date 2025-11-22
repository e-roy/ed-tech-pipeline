---
date: 2025-11-20T23:45:00Z
researcher: Claude (Sonnet 4.5)
git_commit: 6dad8061c7eb1cb5d6295706fa3ca91f7b790fee
branch: ClassCut
repository: pipeline
topic: "Implementation Plan Part 1: Setup and Foundation"
tags: [implementation-plan, remotion, video-editing, mui, zustand]
status: complete
---

# Implementation Plan Part 1: Setup and Foundation

## Overview

This is Part 1 of the implementation plan for adding CapCut-like editing features to the Gauntlet Pipeline application.

**Parts:**
- Part 1: Setup and Foundation (this file)
- Part 2: Timeline and Remotion Preview
- Part 3: Properties and Export

### Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Preview Engine | Remotion Player | ^4.0.369 |
| UI Framework | MUI (Material UI) | ^7.1.0 |
| State Management | Zustand | 5.0.8 (existing) |
| Timeline Interactions | react-moveable | ^0.56.0 |
| Audio Waveforms | wavesurfer.js | ^7.4.4 |
| Final Rendering | FFmpeg | (existing backend) |

---

## Phase 1: Install Dependencies

### 1.1 NPM Packages

```bash
cd frontend

# Remotion packages
npm install remotion @remotion/player

# MUI packages
npm install @mui/material @mui/material-nextjs @emotion/react @emotion/styled @emotion/cache @mui/icons-material

# Timeline interaction packages
npm install react-moveable @scena/react-guides

# Utilities
npm install lodash
npm install -D @types/lodash

# Audio waveforms
npm install wavesurfer.js
```

### 1.2 Expected package.json Additions

```json
{
  "dependencies": {
    "remotion": "^4.0.369",
    "@remotion/player": "^4.0.369",
    "@mui/material": "^7.1.0",
    "@mui/material-nextjs": "^7.1.0",
    "@mui/icons-material": "^7.1.0",
    "@emotion/react": "^11.13.0",
    "@emotion/styled": "^11.13.0",
    "@emotion/cache": "^11.13.0",
    "react-moveable": "^0.56.0",
    "@scena/react-guides": "^0.33.0",
    "lodash": "^4.17.21",
    "wavesurfer.js": "^7.4.4"
  },
  "devDependencies": {
    "@types/lodash": "^4.17.0"
  }
}
```

---

## Phase 2: Configure MUI with CSS Layers

### 2.1 Editor Layout with MUI Provider

**File**: `frontend/src/app/dashboard/editing/[id]/layout.tsx` (NEW)

```typescript
import { AppRouterCacheProvider } from '@mui/material-nextjs/v15-appRouter';
import GlobalStyles from '@mui/material/GlobalStyles';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { editorTheme } from '@/components/video-editor/theme';

export default function EditingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AppRouterCacheProvider options={{ enableCssLayer: true }}>
      <GlobalStyles
        styles={`
          @layer theme, base, mui, components, utilities;
        `}
      />
      <ThemeProvider theme={editorTheme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </AppRouterCacheProvider>
  );
}
```

---

## Phase 3: Create Editor Theme

**File**: `frontend/src/components/video-editor/theme.ts` (NEW)

```typescript
'use client';

import { createTheme } from '@mui/material/styles';

export const editorTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#2196f3',
      light: '#64b5f6',
      dark: '#1976d2',
    },
    secondary: {
      main: '#9c27b0',
    },
    background: {
      default: '#1a1a1a',
      paper: '#232323',
    },
    divider: '#3a3a3a',
    text: {
      primary: '#e0e0e0',
      secondary: '#a0a0a0',
    },
    action: {
      hover: 'rgba(255, 255, 255, 0.08)',
      selected: 'rgba(33, 150, 243, 0.16)',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    fontSize: 13,
    button: {
      textTransform: 'none',
    },
  },
  shape: {
    borderRadius: 4,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          minWidth: 'auto',
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          borderRadius: 4,
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: '#424242',
          fontSize: '0.75rem',
        },
      },
    },
    MuiSlider: {
      styleOverrides: {
        root: {
          height: 4,
        },
        thumb: {
          width: 12,
          height: 12,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});
```

---

## Phase 4: Create Zustand Editor Store

**File**: `frontend/src/stores/editorStore.ts` (NEW)

```typescript
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { nanoid } from 'nanoid';

// ============================================
// Type Definitions
// ============================================

export type MediaType = 'video' | 'audio' | 'image';

export interface MediaFile {
  id: string;
  type: MediaType;
  fileName: string;
  src: string;
  s3Key?: string;

  // Source trim (within original file)
  startTime: number;
  endTime: number;
  duration: number;

  // Timeline position
  positionStart: number;
  positionEnd: number;

  // Playback
  playbackSpeed: number;
  volume: number;

  // Visual properties
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  rotation?: number;
  opacity?: number;
  zIndex: number;
  trackId: string;
}

export interface TextElement {
  id: string;
  text: string;
  positionStart: number;
  positionEnd: number;
  x: number;
  y: number;
  width?: number;
  height?: number;
  font: string;
  fontSize: number;
  fontWeight: 'normal' | 'bold';
  fontStyle: 'normal' | 'italic';
  color: string;
  backgroundColor: string;
  textAlign: 'left' | 'center' | 'right';
  opacity: number;
  rotation?: number;
  animation: 'none' | 'fade-in' | 'slide-up' | 'slide-left' | 'zoom' | 'typewriter';
  animationDuration: number;
  zIndex: number;
  trackId: string;
}

export interface Track {
  id: string;
  name: string;
  type: 'video' | 'audio' | 'text';
  height: number;
  muted: boolean;
  locked: boolean;
  visible: boolean;
}

export interface EditorState {
  // Project
  projectId: string;
  projectName: string;
  duration: number;
  fps: number;
  resolution: { width: number; height: number };

  // Playback
  currentTime: number;
  isPlaying: boolean;
  isMuted: boolean;
  volume: number;
  playbackRate: number;
  inPoint: number | null;
  outPoint: number | null;

  // Timeline
  timelineZoom: number;
  timelineScroll: number;

  // Data
  mediaFiles: MediaFile[];
  textElements: TextElement[];
  tracks: Track[];

  // Selection
  selectedIds: string[];
  activeElementId: string | null;

  // Clipboard & History
  clipboard: (MediaFile | TextElement)[];
  historyIndex: number;
  history: { mediaFiles: MediaFile[]; textElements: TextElement[]; tracks: Track[] }[];

  // Export
  isExporting: boolean;
  exportProgress: number;

  // UI
  sidebarTab: 'media' | 'text' | 'audio' | 'effects';
  propertiesPanelOpen: boolean;
}

// Initial tracks
const initialTracks: Track[] = [
  { id: 'video-1', name: 'Video 1', type: 'video', height: 60, muted: false, locked: false, visible: true },
  { id: 'audio-1', name: 'Audio 1', type: 'audio', height: 40, muted: false, locked: false, visible: true },
  { id: 'text-1', name: 'Text 1', type: 'text', height: 40, muted: false, locked: false, visible: true },
];

const initialState: EditorState = {
  projectId: '',
  projectName: 'Untitled Project',
  duration: 0,
  fps: 30,
  resolution: { width: 1920, height: 1080 },
  currentTime: 0,
  isPlaying: false,
  isMuted: false,
  volume: 100,
  playbackRate: 1,
  inPoint: null,
  outPoint: null,
  timelineZoom: 100,
  timelineScroll: 0,
  mediaFiles: [],
  textElements: [],
  tracks: initialTracks,
  selectedIds: [],
  activeElementId: null,
  clipboard: [],
  historyIndex: -1,
  history: [],
  isExporting: false,
  exportProgress: 0,
  sidebarTab: 'media',
  propertiesPanelOpen: true,
};

// ============================================
// Store
// ============================================

export const useEditorStore = create<EditorState & EditorActions>()(
  subscribeWithSelector((set, get) => ({
    ...initialState,

    // Project
    initializeProject: (projectId, name) => {
      set({ ...initialState, projectId, projectName: name || 'Untitled Project', tracks: [...initialTracks] });
    },
    setProjectName: (name) => set({ projectName: name }),

    // Playback
    setCurrentTime: (time) => {
      const { duration } = get();
      set({ currentTime: Math.max(0, Math.min(time, duration)) });
    },
    setIsPlaying: (playing) => set({ isPlaying: playing }),
    togglePlayPause: () => set((state) => ({ isPlaying: !state.isPlaying })),
    setVolume: (volume) => set({ volume: Math.max(0, Math.min(100, volume)) }),
    setMuted: (muted) => set({ isMuted: muted }),
    setPlaybackRate: (rate) => set({ playbackRate: rate }),
    setInPoint: (time) => set({ inPoint: time }),
    setOutPoint: (time) => set({ outPoint: time }),

    // Timeline
    setTimelineZoom: (zoom) => set({ timelineZoom: Math.max(10, Math.min(500, zoom)) }),
    setTimelineScroll: (scroll) => set({ timelineScroll: Math.max(0, scroll) }),
    zoomIn: () => set((state) => ({ timelineZoom: Math.min(500, state.timelineZoom * 1.25) })),
    zoomOut: () => set((state) => ({ timelineZoom: Math.max(10, state.timelineZoom / 1.25) })),
    zoomToFit: () => {
      const { duration } = get();
      const zoom = duration > 0 ? 1000 / duration : 100;
      set({ timelineZoom: Math.max(10, Math.min(500, zoom)) });
    },

    // Media
    addMedia: (media) => {
      const id = nanoid();
      const { mediaFiles, tracks } = get();
      const trackType = media.type === 'audio' ? 'audio' : 'video';
      const track = tracks.find(t => t.type === trackType) || tracks[0];

      const newMedia: MediaFile = {
        ...media,
        id,
        zIndex: mediaFiles.length,
        trackId: track?.id || 'video-1',
      };

      set((state) => ({ mediaFiles: [...state.mediaFiles, newMedia] }));
      get().recalculateDuration();
      get().saveSnapshot();
      return id;
    },

    updateMedia: (id, updates) => {
      set((state) => ({
        mediaFiles: state.mediaFiles.map((m) => m.id === id ? { ...m, ...updates } : m),
      }));
      get().recalculateDuration();
    },

    deleteMedia: (id) => {
      set((state) => ({
        mediaFiles: state.mediaFiles.filter((m) => m.id !== id),
        selectedIds: state.selectedIds.filter((sid) => sid !== id),
      }));
      get().recalculateDuration();
      get().saveSnapshot();
    },

    splitMedia: (id, time) => {
      const { mediaFiles } = get();
      const media = mediaFiles.find((m) => m.id === id);
      if (!media || time <= media.positionStart || time >= media.positionEnd) return;

      const relativeTime = time - media.positionStart;
      const splitSourceTime = media.startTime + relativeTime * media.playbackSpeed;

      const firstPart: MediaFile = { ...media, endTime: splitSourceTime, positionEnd: time };
      const secondPart: MediaFile = {
        ...media,
        id: nanoid(),
        startTime: splitSourceTime,
        positionStart: time,
        zIndex: mediaFiles.length,
      };

      set((state) => ({
        mediaFiles: [...state.mediaFiles.filter((m) => m.id !== id), firstPart, secondPart],
      }));
      get().saveSnapshot();
    },

    // Text
    addText: (text) => {
      const id = nanoid();
      const { textElements, tracks } = get();
      const track = tracks.find(t => t.type === 'text') || tracks[tracks.length - 1];

      const newText: TextElement = {
        ...text,
        id,
        zIndex: 1000 + textElements.length,
        trackId: track?.id || 'text-1',
      };

      set((state) => ({ textElements: [...state.textElements, newText] }));
      get().recalculateDuration();
      get().saveSnapshot();
      return id;
    },

    updateText: (id, updates) => {
      set((state) => ({
        textElements: state.textElements.map((t) => t.id === id ? { ...t, ...updates } : t),
      }));
      get().recalculateDuration();
    },

    deleteText: (id) => {
      set((state) => ({
        textElements: state.textElements.filter((t) => t.id !== id),
        selectedIds: state.selectedIds.filter((sid) => sid !== id),
      }));
      get().recalculateDuration();
      get().saveSnapshot();
    },

    // Tracks
    addTrack: (type, name) => {
      const id = nanoid();
      const { tracks } = get();
      const trackCount = tracks.filter(t => t.type === type).length + 1;
      const defaultName = name || `${type.charAt(0).toUpperCase() + type.slice(1)} ${trackCount}`;

      const newTrack: Track = {
        id,
        name: defaultName,
        type,
        height: type === 'video' ? 60 : 40,
        muted: false,
        locked: false,
        visible: true,
      };

      set((state) => ({ tracks: [...state.tracks, newTrack] }));
      return id;
    },

    updateTrack: (id, updates) => {
      set((state) => ({
        tracks: state.tracks.map((t) => t.id === id ? { ...t, ...updates } : t),
      }));
    },

    deleteTrack: (id) => {
      set((state) => ({
        tracks: state.tracks.filter((t) => t.id !== id),
        mediaFiles: state.mediaFiles.filter((m) => m.trackId !== id),
        textElements: state.textElements.filter((t) => t.trackId !== id),
      }));
      get().recalculateDuration();
      get().saveSnapshot();
    },

    // Selection
    select: (ids) => set({ selectedIds: ids, activeElementId: ids[0] || null }),
    addToSelection: (id) => set((state) => ({
      selectedIds: state.selectedIds.includes(id) ? state.selectedIds : [...state.selectedIds, id],
    })),
    removeFromSelection: (id) => set((state) => ({
      selectedIds: state.selectedIds.filter((sid) => sid !== id),
    })),
    clearSelection: () => set({ selectedIds: [], activeElementId: null }),
    selectAll: () => {
      const { mediaFiles, textElements } = get();
      const allIds = [...mediaFiles.map(m => m.id), ...textElements.map(t => t.id)];
      set({ selectedIds: allIds, activeElementId: allIds[0] || null });
    },
    setActiveElement: (id) => set({ activeElementId: id }),

    // Clipboard
    copy: () => {
      const { selectedIds, mediaFiles, textElements } = get();
      const clipboard: (MediaFile | TextElement)[] = [];
      for (const id of selectedIds) {
        const media = mediaFiles.find(m => m.id === id);
        if (media) { clipboard.push({ ...media }); continue; }
        const text = textElements.find(t => t.id === id);
        if (text) { clipboard.push({ ...text }); }
      }
      set({ clipboard });
    },
    cut: () => { get().copy(); get().deleteSelected(); },
    paste: (time) => {
      const { clipboard, currentTime, mediaFiles, textElements } = get();
      const pasteTime = time ?? currentTime;
      if (clipboard.length === 0) return;

      const earliestPosition = Math.min(...clipboard.map(item =>
        'type' in item && ['video', 'audio', 'image'].includes(item.type as string)
          ? (item as MediaFile).positionStart
          : (item as TextElement).positionStart
      ));
      const offset = pasteTime - earliestPosition;

      const newMediaFiles: MediaFile[] = [];
      const newTextElements: TextElement[] = [];

      for (const item of clipboard) {
        if ('type' in item && ['video', 'audio', 'image'].includes(item.type as string)) {
          const media = item as MediaFile;
          newMediaFiles.push({
            ...media,
            id: nanoid(),
            positionStart: media.positionStart + offset,
            positionEnd: media.positionEnd + offset,
            zIndex: mediaFiles.length + newMediaFiles.length,
          });
        } else {
          const text = item as TextElement;
          newTextElements.push({
            ...text,
            id: nanoid(),
            positionStart: text.positionStart + offset,
            positionEnd: text.positionEnd + offset,
            zIndex: 1000 + textElements.length + newTextElements.length,
          });
        }
      }

      set((state) => ({
        mediaFiles: [...state.mediaFiles, ...newMediaFiles],
        textElements: [...state.textElements, ...newTextElements],
        selectedIds: [...newMediaFiles.map(m => m.id), ...newTextElements.map(t => t.id)],
      }));
      get().recalculateDuration();
      get().saveSnapshot();
    },

    // History
    saveSnapshot: () => {
      const { mediaFiles, textElements, tracks, history, historyIndex } = get();
      const snapshot = {
        mediaFiles: JSON.parse(JSON.stringify(mediaFiles)),
        textElements: JSON.parse(JSON.stringify(textElements)),
        tracks: JSON.parse(JSON.stringify(tracks)),
      };
      const newHistory = history.slice(0, historyIndex + 1);
      newHistory.push(snapshot);
      if (newHistory.length > 50) newHistory.shift();
      set({ history: newHistory, historyIndex: newHistory.length - 1 });
    },

    undo: () => {
      const { historyIndex, history } = get();
      if (historyIndex <= 0) return;
      const newIndex = historyIndex - 1;
      const snapshot = history[newIndex];
      if (snapshot) {
        set({
          mediaFiles: JSON.parse(JSON.stringify(snapshot.mediaFiles)),
          textElements: JSON.parse(JSON.stringify(snapshot.textElements)),
          tracks: JSON.parse(JSON.stringify(snapshot.tracks)),
          historyIndex: newIndex,
        });
        get().recalculateDuration();
      }
    },

    redo: () => {
      const { historyIndex, history } = get();
      if (historyIndex >= history.length - 1) return;
      const newIndex = historyIndex + 1;
      const snapshot = history[newIndex];
      if (snapshot) {
        set({
          mediaFiles: JSON.parse(JSON.stringify(snapshot.mediaFiles)),
          textElements: JSON.parse(JSON.stringify(snapshot.textElements)),
          tracks: JSON.parse(JSON.stringify(snapshot.tracks)),
          historyIndex: newIndex,
        });
        get().recalculateDuration();
      }
    },

    // Delete
    deleteSelected: () => {
      const { selectedIds } = get();
      set((state) => ({
        mediaFiles: state.mediaFiles.filter((m) => !selectedIds.includes(m.id)),
        textElements: state.textElements.filter((t) => !selectedIds.includes(t.id)),
        selectedIds: [],
        activeElementId: null,
      }));
      get().recalculateDuration();
      get().saveSnapshot();
    },

    // Duration
    recalculateDuration: () => {
      const { mediaFiles, textElements } = get();
      let maxDuration = 0;
      for (const media of mediaFiles) {
        if (media.positionEnd > maxDuration) maxDuration = media.positionEnd;
      }
      for (const text of textElements) {
        if (text.positionEnd > maxDuration) maxDuration = text.positionEnd;
      }
      set({ duration: maxDuration + 1 });
    },

    // Export
    setExporting: (exporting) => set({ isExporting: exporting }),
    setExportProgress: (progress) => set({ exportProgress: progress }),

    // UI
    setSidebarTab: (tab) => set({ sidebarTab: tab }),
    setPropertiesPanelOpen: (open) => set({ propertiesPanelOpen: open }),

    // Reset
    reset: () => set({ ...initialState, tracks: [...initialTracks] }),
  }))
);

// Actions interface (for TypeScript)
interface EditorActions {
  initializeProject: (projectId: string, name?: string) => void;
  setProjectName: (name: string) => void;
  setCurrentTime: (time: number) => void;
  setIsPlaying: (playing: boolean) => void;
  togglePlayPause: () => void;
  setVolume: (volume: number) => void;
  setMuted: (muted: boolean) => void;
  setPlaybackRate: (rate: number) => void;
  setInPoint: (time: number | null) => void;
  setOutPoint: (time: number | null) => void;
  setTimelineZoom: (zoom: number) => void;
  setTimelineScroll: (scroll: number) => void;
  zoomIn: () => void;
  zoomOut: () => void;
  zoomToFit: () => void;
  addMedia: (media: Omit<MediaFile, 'id' | 'zIndex' | 'trackId'>) => string;
  updateMedia: (id: string, updates: Partial<MediaFile>) => void;
  deleteMedia: (id: string) => void;
  splitMedia: (id: string, time: number) => void;
  addText: (text: Omit<TextElement, 'id' | 'zIndex' | 'trackId'>) => string;
  updateText: (id: string, updates: Partial<TextElement>) => void;
  deleteText: (id: string) => void;
  addTrack: (type: Track['type'], name?: string) => string;
  updateTrack: (id: string, updates: Partial<Track>) => void;
  deleteTrack: (id: string) => void;
  select: (ids: string[]) => void;
  addToSelection: (id: string) => void;
  removeFromSelection: (id: string) => void;
  clearSelection: () => void;
  selectAll: () => void;
  setActiveElement: (id: string | null) => void;
  copy: () => void;
  cut: () => void;
  paste: (time?: number) => void;
  undo: () => void;
  redo: () => void;
  saveSnapshot: () => void;
  deleteSelected: () => void;
  recalculateDuration: () => void;
  setExporting: (exporting: boolean) => void;
  setExportProgress: (progress: number) => void;
  setSidebarTab: (tab: EditorState['sidebarTab']) => void;
  setPropertiesPanelOpen: (open: boolean) => void;
  reset: () => void;
}

// Selectors
export const selectMediaById = (id: string) => (state: EditorState) =>
  state.mediaFiles.find((m) => m.id === id);

export const selectTextById = (id: string) => (state: EditorState) =>
  state.textElements.find((t) => t.id === id);

export const selectMediaByTrack = (trackId: string) => (state: EditorState) =>
  state.mediaFiles.filter((m) => m.trackId === trackId);

export const selectTextByTrack = (trackId: string) => (state: EditorState) =>
  state.textElements.filter((t) => t.trackId === trackId);

export const selectActiveElement = (state: EditorState) => {
  if (!state.activeElementId) return null;
  const media = state.mediaFiles.find((m) => m.id === state.activeElementId);
  if (media) return { type: 'media' as const, element: media };
  const text = state.textElements.find((t) => t.id === state.activeElementId);
  if (text) return { type: 'text' as const, element: text };
  return null;
};

export const selectCanUndo = (state: EditorState) => state.historyIndex > 0;
export const selectCanRedo = (state: EditorState) => state.historyIndex < state.history.length - 1;
```

---

## Directory Structure

Create this directory structure:

```
frontend/src/
├── stores/
│   └── editorStore.ts
├── components/
│   └── video-editor/
│       ├── theme.ts
│       ├── EditorLayout.tsx
│       ├── Toolbar.tsx
│       ├── PreviewPlayer.tsx
│       ├── Timeline.tsx
│       ├── PropertiesPanel.tsx
│       ├── MediaBin.tsx
│       ├── ExportDialog.tsx
│       ├── remotion/
│       │   ├── Composition.tsx
│       │   └── sequences/
│       │       ├── VideoSequence.tsx
│       │       ├── AudioSequence.tsx
│       │       ├── ImageSequence.tsx
│       │       └── TextSequence.tsx
│       ├── timeline/
│       │   ├── TimeRuler.tsx
│       │   ├── Playhead.tsx
│       │   ├── Track.tsx
│       │   └── TimelineClip.tsx
│       └── properties/
│           ├── MediaProperties.tsx
│           └── TextProperties.tsx
└── app/
    └── dashboard/
        └── editing/
            └── [id]/
                └── layout.tsx
```

---

**Continue to Part 2: Timeline and Remotion Preview**
