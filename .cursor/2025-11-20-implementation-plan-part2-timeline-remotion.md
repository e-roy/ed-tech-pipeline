---
date: 2025-11-20T23:45:00Z
researcher: Claude (Sonnet 4.5)
git_commit: 6dad8061c7eb1cb5d6295706fa3ca91f7b790fee
branch: ClassCut
repository: pipeline
topic: "Implementation Plan Part 2: Timeline and Remotion Preview"
tags: [implementation-plan, remotion, video-editing, timeline, mui]
status: complete
---

# Implementation Plan Part 2: Timeline and Remotion Preview

## Phase 5: Editor Layout Component

**File**: `frontend/src/components/video-editor/EditorLayout.tsx` (NEW)

```typescript
'use client';

import { Box } from '@mui/material';
import { Toolbar } from './Toolbar';
import { MediaBin } from './MediaBin';
import { PreviewPlayer } from './PreviewPlayer';
import { Timeline } from './Timeline';
import { PropertiesPanel } from './PropertiesPanel';
import { useEditorStore } from '@/stores/editorStore';
import { useEffect } from 'react';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';

interface EditorLayoutProps {
  sessionId: string;
}

export function EditorLayout({ sessionId }: EditorLayoutProps) {
  const initializeProject = useEditorStore((state) => state.initializeProject);
  const propertiesPanelOpen = useEditorStore((state) => state.propertiesPanelOpen);

  // Enable keyboard shortcuts
  useKeyboardShortcuts();

  useEffect(() => {
    initializeProject(sessionId);
  }, [sessionId, initializeProject]);

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        bgcolor: 'background.default',
        color: 'text.primary',
      }}
    >
      {/* Top Toolbar */}
      <Toolbar />

      {/* Main Content */}
      <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left: Media Bin (280px) */}
        <Box sx={{ width: 280, borderRight: 1, borderColor: 'divider', display: 'flex', flexDirection: 'column' }}>
          <MediaBin sessionId={sessionId} />
        </Box>

        {/* Center: Preview + Timeline */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Preview */}
          <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: '#0a0a0a', minHeight: 300 }}>
            <PreviewPlayer />
          </Box>

          {/* Timeline */}
          <Box sx={{ height: 280, borderTop: 1, borderColor: 'divider' }}>
            <Timeline />
          </Box>
        </Box>

        {/* Right: Properties (300px) */}
        {propertiesPanelOpen && (
          <Box sx={{ width: 300, borderLeft: 1, borderColor: 'divider' }}>
            <PropertiesPanel />
          </Box>
        )}
      </Box>
    </Box>
  );
}
```

---

## Phase 6: Timeline Components

### 6.1 Main Timeline

**File**: `frontend/src/components/video-editor/Timeline.tsx` (NEW)

```typescript
'use client';

import { useRef, useCallback } from 'react';
import { Box, IconButton, Tooltip, Typography } from '@mui/material';
import { Add, Lock, LockOpen, Visibility, VisibilityOff, VolumeUp, VolumeOff } from '@mui/icons-material';
import { useEditorStore, selectMediaByTrack, selectTextByTrack } from '@/stores/editorStore';
import { TimeRuler } from './timeline/TimeRuler';
import { Playhead } from './timeline/Playhead';
import { Track } from './timeline/Track';

export function Timeline() {
  const containerRef = useRef<HTMLDivElement>(null);
  const duration = useEditorStore((state) => state.duration);
  const timelineZoom = useEditorStore((state) => state.timelineZoom);
  const timelineScroll = useEditorStore((state) => state.timelineScroll);
  const currentTime = useEditorStore((state) => state.currentTime);
  const tracks = useEditorStore((state) => state.tracks);
  const setCurrentTime = useEditorStore((state) => state.setCurrentTime);
  const setTimelineScroll = useEditorStore((state) => state.setTimelineScroll);
  const addTrack = useEditorStore((state) => state.addTrack);
  const updateTrack = useEditorStore((state) => state.updateTrack);

  const timelineWidth = Math.max(duration * timelineZoom, 1000);
  const trackHeaderWidth = 150;

  const handleTimelineClick = useCallback((e: React.MouseEvent) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const scrollLeft = containerRef.current.scrollLeft;
    const x = e.clientX - rect.left + scrollLeft - trackHeaderWidth;
    if (x >= 0) {
      const time = x / timelineZoom;
      setCurrentTime(Math.max(0, Math.min(time, duration)));
    }
  }, [timelineZoom, duration, setCurrentTime, trackHeaderWidth]);

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setTimelineScroll(e.currentTarget.scrollLeft);
  }, [setTimelineScroll]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header with Time Ruler */}
      <Box sx={{ display: 'flex', bgcolor: 'background.paper', borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ width: trackHeaderWidth, flexShrink: 0, borderRight: 1, borderColor: 'divider' }}>
          <Box sx={{ height: 24 }} />
        </Box>
        <Box sx={{ flex: 1, overflow: 'hidden' }}>
          <TimeRuler duration={duration} zoom={timelineZoom} scrollLeft={timelineScroll} />
        </Box>
      </Box>

      {/* Tracks */}
      <Box ref={containerRef} sx={{ flex: 1, display: 'flex', overflow: 'auto' }} onScroll={handleScroll} onClick={handleTimelineClick}>
        {/* Track Headers */}
        <Box sx={{ width: trackHeaderWidth, flexShrink: 0, bgcolor: 'background.paper', borderRight: 1, borderColor: 'divider', position: 'sticky', left: 0, zIndex: 2 }}>
          {tracks.map((track) => (
            <Box key={track.id} sx={{ height: track.height, display: 'flex', alignItems: 'center', px: 1, borderBottom: 1, borderColor: 'divider', gap: 0.5 }}>
              <Typography variant="caption" sx={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>{track.name}</Typography>
              <Tooltip title={track.muted ? 'Unmute' : 'Mute'}>
                <IconButton size="small" onClick={() => updateTrack(track.id, { muted: !track.muted })} sx={{ p: 0.25 }}>
                  {track.muted ? <VolumeOff sx={{ fontSize: 14 }} /> : <VolumeUp sx={{ fontSize: 14 }} />}
                </IconButton>
              </Tooltip>
              <Tooltip title={track.locked ? 'Unlock' : 'Lock'}>
                <IconButton size="small" onClick={() => updateTrack(track.id, { locked: !track.locked })} sx={{ p: 0.25 }}>
                  {track.locked ? <Lock sx={{ fontSize: 14 }} /> : <LockOpen sx={{ fontSize: 14 }} />}
                </IconButton>
              </Tooltip>
              <Tooltip title={track.visible ? 'Hide' : 'Show'}>
                <IconButton size="small" onClick={() => updateTrack(track.id, { visible: !track.visible })} sx={{ p: 0.25 }}>
                  {track.visible ? <Visibility sx={{ fontSize: 14 }} /> : <VisibilityOff sx={{ fontSize: 14 }} />}
                </IconButton>
              </Tooltip>
            </Box>
          ))}
          <Box sx={{ p: 1 }}>
            <Tooltip title="Add Video Track"><IconButton size="small" onClick={() => addTrack('video')}><Add sx={{ fontSize: 14 }} /></IconButton></Tooltip>
          </Box>
        </Box>

        {/* Track Content */}
        <Box sx={{ position: 'relative', width: timelineWidth, minHeight: '100%' }}>
          <Playhead currentTime={currentTime} zoom={timelineZoom} />
          {tracks.map((track, index) => {
            const top = tracks.slice(0, index).reduce((sum, t) => sum + t.height, 0);
            return <Track key={track.id} track={track} top={top} zoom={timelineZoom} />;
          })}
        </Box>
      </Box>
    </Box>
  );
}
```

### 6.2 Time Ruler

**File**: `frontend/src/components/video-editor/timeline/TimeRuler.tsx` (NEW)

```typescript
'use client';

import { useMemo } from 'react';
import { Box, Typography } from '@mui/material';

interface TimeRulerProps {
  duration: number;
  zoom: number;
  scrollLeft: number;
}

export function TimeRuler({ duration, zoom, scrollLeft }: TimeRulerProps) {
  const markers = useMemo(() => {
    const result: { time: number; label: string; major: boolean }[] = [];
    let interval = 1;
    if (zoom < 30) interval = 10;
    else if (zoom < 60) interval = 5;
    else if (zoom < 120) interval = 2;
    else if (zoom > 200) interval = 0.5;

    const totalTime = Math.max(duration, 10);
    for (let time = 0; time <= totalTime; time += interval) {
      const isMajor = time % (interval * 5) === 0 || interval >= 5;
      const mins = Math.floor(time / 60);
      const secs = Math.floor(time % 60);
      const label = isMajor ? `${mins}:${secs.toString().padStart(2, '0')}` : '';
      result.push({ time, label, major: isMajor });
    }
    return result;
  }, [duration, zoom]);

  return (
    <Box sx={{ position: 'relative', height: 24, bgcolor: 'background.default', borderBottom: 1, borderColor: 'divider', overflow: 'hidden' }}>
      <Box sx={{ position: 'absolute', top: 0, left: -scrollLeft, height: '100%' }}>
        {markers.map(({ time, label, major }) => (
          <Box key={time} sx={{ position: 'absolute', left: time * zoom, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Box sx={{ width: 1, height: major ? 12 : 6, bgcolor: major ? 'text.secondary' : 'divider', mt: 'auto' }} />
            {label && <Typography variant="caption" sx={{ position: 'absolute', top: 2, left: 4, fontSize: 10, color: 'text.secondary', whiteSpace: 'nowrap' }}>{label}</Typography>}
          </Box>
        ))}
      </Box>
    </Box>
  );
}
```

### 6.3 Playhead

**File**: `frontend/src/components/video-editor/timeline/Playhead.tsx` (NEW)

```typescript
'use client';

import { Box } from '@mui/material';

interface PlayheadProps {
  currentTime: number;
  zoom: number;
}

export function Playhead({ currentTime, zoom }: PlayheadProps) {
  const left = currentTime * zoom;

  return (
    <Box
      sx={{
        position: 'absolute',
        top: 0,
        bottom: 0,
        left,
        width: 2,
        bgcolor: 'error.main',
        zIndex: 10,
        pointerEvents: 'none',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: -4,
          left: -5,
          width: 0,
          height: 0,
          borderLeft: '6px solid transparent',
          borderRight: '6px solid transparent',
          borderTop: '8px solid',
          borderTopColor: 'error.main',
        },
      }}
    />
  );
}
```

### 6.4 Track

**File**: `frontend/src/components/video-editor/timeline/Track.tsx` (NEW)

```typescript
'use client';

import { Box } from '@mui/material';
import { useEditorStore, selectMediaByTrack, selectTextByTrack, type Track as TrackType } from '@/stores/editorStore';
import { TimelineClip } from './TimelineClip';

interface TrackProps {
  track: TrackType;
  top: number;
  zoom: number;
}

export function Track({ track, top, zoom }: TrackProps) {
  const mediaFiles = useEditorStore(selectMediaByTrack(track.id));
  const textElements = useEditorStore(selectTextByTrack(track.id));
  const items = track.type === 'text' ? textElements : mediaFiles;

  return (
    <Box
      sx={{
        position: 'absolute',
        top,
        left: 0,
        right: 0,
        height: track.height,
        bgcolor: track.type === 'video' ? 'rgba(33, 150, 243, 0.05)' :
                 track.type === 'audio' ? 'rgba(76, 175, 80, 0.05)' : 'rgba(255, 152, 0, 0.05)',
        borderBottom: 1,
        borderColor: 'divider',
        opacity: track.visible ? 1 : 0.5,
        pointerEvents: track.locked ? 'none' : 'auto',
      }}
    >
      {items.map((item) => (
        <TimelineClip key={item.id} item={item} trackType={track.type} zoom={zoom} trackHeight={track.height} />
      ))}
    </Box>
  );
}
```

### 6.5 Timeline Clip (with react-moveable)

**File**: `frontend/src/components/video-editor/timeline/TimelineClip.tsx` (NEW)

```typescript
'use client';

import { useRef, useState, useCallback } from 'react';
import { Box, Typography } from '@mui/material';
import Moveable from 'react-moveable';
import { throttle } from 'lodash';
import { useEditorStore, type MediaFile, type TextElement } from '@/stores/editorStore';

interface TimelineClipProps {
  item: MediaFile | TextElement;
  trackType: 'video' | 'audio' | 'text';
  zoom: number;
  trackHeight: number;
}

export function TimelineClip({ item, trackType, zoom, trackHeight }: TimelineClipProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);

  const selectedIds = useEditorStore((state) => state.selectedIds);
  const updateMedia = useEditorStore((state) => state.updateMedia);
  const updateText = useEditorStore((state) => state.updateText);
  const select = useEditorStore((state) => state.select);
  const addToSelection = useEditorStore((state) => state.addToSelection);

  const isSelected = selectedIds.includes(item.id);
  const isMedia = 'type' in item && ['video', 'audio', 'image'].includes((item as MediaFile).type);

  const left = item.positionStart * zoom;
  const width = (item.positionEnd - item.positionStart) * zoom;

  const handleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    if (e.shiftKey || e.ctrlKey || e.metaKey) {
      addToSelection(item.id);
    } else {
      select([item.id]);
    }
  }, [item.id, select, addToSelection]);

  const handleDrag = useCallback(
    throttle((e: { left: number }) => {
      const newPositionStart = Math.max(0, e.left / zoom);
      const duration = item.positionEnd - item.positionStart;
      const newPositionEnd = newPositionStart + duration;
      if (isMedia) {
        updateMedia(item.id, { positionStart: newPositionStart, positionEnd: newPositionEnd });
      } else {
        updateText(item.id, { positionStart: newPositionStart, positionEnd: newPositionEnd });
      }
    }, 16),
    [item, zoom, isMedia, updateMedia, updateText]
  );

  const handleResize = useCallback(
    throttle((e: { width: number; direction: number[] }) => {
      const newWidth = e.width / zoom;
      const direction = e.direction[0];
      if (direction === -1) {
        const newPositionStart = item.positionEnd - newWidth;
        if (newPositionStart >= 0) {
          if (isMedia) {
            const media = item as MediaFile;
            const trimAmount = item.positionStart - newPositionStart;
            updateMedia(item.id, { positionStart: newPositionStart, startTime: Math.max(0, media.startTime - trimAmount) });
          } else {
            updateText(item.id, { positionStart: newPositionStart });
          }
        }
      } else {
        const newPositionEnd = item.positionStart + newWidth;
        if (isMedia) {
          const media = item as MediaFile;
          const maxEnd = media.positionStart + (media.duration - media.startTime);
          updateMedia(item.id, { positionEnd: Math.min(newPositionEnd, maxEnd), endTime: Math.min(media.startTime + newWidth, media.duration) });
        } else {
          updateText(item.id, { positionEnd: newPositionEnd });
        }
      }
    }, 16),
    [item, zoom, isMedia, updateMedia, updateText]
  );

  const getClipColor = () => {
    switch (trackType) {
      case 'video': return isSelected ? '#2196f3' : '#1976d2';
      case 'audio': return isSelected ? '#4caf50' : '#388e3c';
      case 'text': return isSelected ? '#ff9800' : '#f57c00';
      default: return '#666';
    }
  };

  const getClipLabel = () => {
    if (isMedia) return (item as MediaFile).fileName;
    const textItem = item as TextElement;
    return textItem.text.substring(0, 20) + (textItem.text.length > 20 ? '...' : '');
  };

  return (
    <>
      <Box
        ref={ref}
        onClick={handleClick}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        sx={{
          position: 'absolute',
          left,
          top: 4,
          width,
          height: trackHeight - 8,
          bgcolor: getClipColor(),
          borderRadius: 1,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          px: 1,
          overflow: 'hidden',
          border: isSelected ? '2px solid #fff' : 'none',
          boxShadow: isSelected ? '0 0 8px rgba(33, 150, 243, 0.5)' : 'none',
          transition: 'box-shadow 0.2s',
          '&:hover': { boxShadow: '0 0 4px rgba(255, 255, 255, 0.3)' },
        }}
      >
        <Typography variant="caption" sx={{ color: '#fff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontSize: 11 }}>
          {getClipLabel()}
        </Typography>
      </Box>

      {isSelected && (
        <Moveable
          target={ref}
          draggable
          resizable
          edge={['w', 'e']}
          onDrag={(e) => handleDrag({ left: e.left })}
          onResize={(e) => {
            e.target.style.width = `${e.width}px`;
            handleResize({ width: e.width, direction: e.direction });
          }}
          renderDirections={['w', 'e']}
          throttleDrag={0}
          throttleResize={0}
        />
      )}
    </>
  );
}
```

---

## Phase 7: Remotion Preview

### 7.1 Composition Root

**File**: `frontend/src/components/video-editor/remotion/Composition.tsx` (NEW)

```typescript
'use client';

import { useCurrentFrame, AbsoluteFill } from 'remotion';
import { useEditorStore } from '@/stores/editorStore';
import { VideoSequence } from './sequences/VideoSequence';
import { AudioSequence } from './sequences/AudioSequence';
import { ImageSequence } from './sequences/ImageSequence';
import { TextSequence } from './sequences/TextSequence';
import { useEffect, useRef } from 'react';

export const EditorComposition = () => {
  const frame = useCurrentFrame();
  const fps = useEditorStore((state) => state.fps);
  const mediaFiles = useEditorStore((state) => state.mediaFiles);
  const textElements = useEditorStore((state) => state.textElements);
  const setCurrentTime = useEditorStore((state) => state.setCurrentTime);
  const isPlaying = useEditorStore((state) => state.isPlaying);

  const lastDispatchedTime = useRef(0);

  useEffect(() => {
    if (!isPlaying) return;
    const currentTimeInSeconds = frame / fps;
    if (Math.abs(currentTimeInSeconds - lastDispatchedTime.current) > 0.05) {
      setCurrentTime(currentTimeInSeconds);
      lastDispatchedTime.current = currentTimeInSeconds;
    }
  }, [frame, fps, setCurrentTime, isPlaying]);

  const sortedMedia = [...mediaFiles].sort((a, b) => a.zIndex - b.zIndex);

  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      {sortedMedia.map((media) => {
        switch (media.type) {
          case 'video': return <VideoSequence key={media.id} media={media} fps={fps} />;
          case 'audio': return <AudioSequence key={media.id} media={media} fps={fps} />;
          case 'image': return <ImageSequence key={media.id} media={media} fps={fps} />;
          default: return null;
        }
      })}
      {textElements.map((text) => (
        <TextSequence key={text.id} text={text} fps={fps} />
      ))}
    </AbsoluteFill>
  );
};
```

### 7.2 Video Sequence

**File**: `frontend/src/components/video-editor/remotion/sequences/VideoSequence.tsx` (NEW)

```typescript
'use client';

import { Sequence, Video, useVideoConfig } from 'remotion';
import { type MediaFile } from '@/stores/editorStore';

interface VideoSequenceProps {
  media: MediaFile;
  fps: number;
}

export function VideoSequence({ media, fps }: VideoSequenceProps) {
  const { width: compWidth, height: compHeight } = useVideoConfig();

  const from = Math.round(media.positionStart * fps);
  const durationInFrames = Math.round((media.positionEnd - media.positionStart) * fps);
  const startFrom = Math.round(media.startTime * fps);
  const endAt = Math.round(media.endTime * fps);

  const videoWidth = media.width || compWidth;
  const videoHeight = media.height || compHeight;
  const x = media.x || 0;
  const y = media.y || 0;
  const opacity = (media.opacity ?? 100) / 100;
  const rotation = media.rotation || 0;

  return (
    <Sequence from={from} durationInFrames={durationInFrames}>
      <Video
        src={media.src}
        startFrom={startFrom}
        endAt={endAt}
        playbackRate={media.playbackSpeed}
        volume={media.volume / 100}
        style={{
          position: 'absolute',
          left: x,
          top: y,
          width: videoWidth,
          height: videoHeight,
          opacity,
          transform: rotation ? `rotate(${rotation}deg)` : undefined,
          objectFit: 'contain',
        }}
      />
    </Sequence>
  );
}
```

### 7.3 Audio Sequence

**File**: `frontend/src/components/video-editor/remotion/sequences/AudioSequence.tsx` (NEW)

```typescript
'use client';

import { Sequence, Audio, AbsoluteFill } from 'remotion';
import { type MediaFile } from '@/stores/editorStore';

interface AudioSequenceProps {
  media: MediaFile;
  fps: number;
}

export function AudioSequence({ media, fps }: AudioSequenceProps) {
  const from = Math.round(media.positionStart * fps);
  const durationInFrames = Math.round((media.positionEnd - media.positionStart) * fps);
  const startFrom = Math.round(media.startTime * fps);
  const endAt = Math.round(media.endTime * fps);

  return (
    <Sequence from={from} durationInFrames={durationInFrames}>
      <AbsoluteFill>
        <Audio
          src={media.src}
          startFrom={startFrom}
          endAt={endAt}
          playbackRate={media.playbackSpeed}
          volume={media.volume / 100}
        />
      </AbsoluteFill>
    </Sequence>
  );
}
```

### 7.4 Image Sequence

**File**: `frontend/src/components/video-editor/remotion/sequences/ImageSequence.tsx` (NEW)

```typescript
'use client';

import { Sequence, Img, useVideoConfig } from 'remotion';
import { type MediaFile } from '@/stores/editorStore';

interface ImageSequenceProps {
  media: MediaFile;
  fps: number;
}

export function ImageSequence({ media, fps }: ImageSequenceProps) {
  const { width: compWidth, height: compHeight } = useVideoConfig();

  const from = Math.round(media.positionStart * fps);
  const durationInFrames = Math.round((media.positionEnd - media.positionStart) * fps);

  const imageWidth = media.width || compWidth;
  const imageHeight = media.height || compHeight;
  const x = media.x || 0;
  const y = media.y || 0;
  const opacity = (media.opacity ?? 100) / 100;
  const rotation = media.rotation || 0;

  return (
    <Sequence from={from} durationInFrames={durationInFrames}>
      <Img
        src={media.src}
        style={{
          position: 'absolute',
          left: x,
          top: y,
          width: imageWidth,
          height: imageHeight,
          opacity,
          transform: rotation ? `rotate(${rotation}deg)` : undefined,
          objectFit: 'contain',
        }}
      />
    </Sequence>
  );
}
```

### 7.5 Text Sequence (with animations)

**File**: `frontend/src/components/video-editor/remotion/sequences/TextSequence.tsx` (NEW)

```typescript
'use client';

import { Sequence, interpolate, useCurrentFrame } from 'remotion';
import { type TextElement } from '@/stores/editorStore';

interface TextSequenceProps {
  text: TextElement;
  fps: number;
}

export function TextSequence({ text, fps }: TextSequenceProps) {
  const frame = useCurrentFrame();

  const from = Math.round(text.positionStart * fps);
  const durationInFrames = Math.round((text.positionEnd - text.positionStart) * fps);
  const animationFrames = Math.round(text.animationDuration * fps);
  const localFrame = frame - from;

  const getAnimationStyle = () => {
    switch (text.animation) {
      case 'fade-in': {
        const opacity = interpolate(localFrame, [0, animationFrames], [0, 1], { extrapolateRight: 'clamp' });
        return { opacity: opacity * (text.opacity / 100) };
      }
      case 'slide-up': {
        const translateY = interpolate(localFrame, [0, animationFrames], [50, 0], { extrapolateRight: 'clamp' });
        const opacity = interpolate(localFrame, [0, animationFrames / 2], [0, 1], { extrapolateRight: 'clamp' });
        return { transform: `translateY(${translateY}px)`, opacity: opacity * (text.opacity / 100) };
      }
      case 'slide-left': {
        const translateX = interpolate(localFrame, [0, animationFrames], [100, 0], { extrapolateRight: 'clamp' });
        const opacity = interpolate(localFrame, [0, animationFrames / 2], [0, 1], { extrapolateRight: 'clamp' });
        return { transform: `translateX(${translateX}px)`, opacity: opacity * (text.opacity / 100) };
      }
      case 'zoom': {
        const scale = interpolate(localFrame, [0, animationFrames], [0.5, 1], { extrapolateRight: 'clamp' });
        const opacity = interpolate(localFrame, [0, animationFrames / 2], [0, 1], { extrapolateRight: 'clamp' });
        return { transform: `scale(${scale})`, opacity: opacity * (text.opacity / 100) };
      }
      case 'typewriter': {
        const progress = interpolate(localFrame, [0, animationFrames], [0, 1], { extrapolateRight: 'clamp' });
        return { visibleChars: Math.floor(text.text.length * progress) };
      }
      default:
        return { opacity: text.opacity / 100 };
    }
  };

  const animationStyle = getAnimationStyle();
  const displayText = 'visibleChars' in animationStyle
    ? text.text.substring(0, animationStyle.visibleChars)
    : text.text;

  return (
    <Sequence from={from} durationInFrames={durationInFrames}>
      <div
        style={{
          position: 'absolute',
          left: text.x,
          top: text.y,
          width: text.width || 'auto',
          height: text.height || 'auto',
          fontFamily: text.font,
          fontSize: text.fontSize,
          fontWeight: text.fontWeight,
          fontStyle: text.fontStyle,
          color: text.color,
          backgroundColor: text.backgroundColor || 'transparent',
          textAlign: text.textAlign,
          opacity: text.opacity / 100,
          transform: text.rotation ? `rotate(${text.rotation}deg)` : undefined,
          zIndex: text.zIndex,
          ...animationStyle,
        }}
      >
        {displayText}
      </div>
    </Sequence>
  );
}
```

### 7.6 Preview Player

**File**: `frontend/src/components/video-editor/PreviewPlayer.tsx` (NEW)

```typescript
'use client';

import { useRef, useEffect } from 'react';
import { Player, PlayerRef } from '@remotion/player';
import { Box } from '@mui/material';
import { useEditorStore } from '@/stores/editorStore';
import { EditorComposition } from './remotion/Composition';

export function PreviewPlayer() {
  const playerRef = useRef<PlayerRef>(null);

  const duration = useEditorStore((state) => state.duration);
  const currentTime = useEditorStore((state) => state.currentTime);
  const isPlaying = useEditorStore((state) => state.isPlaying);
  const isMuted = useEditorStore((state) => state.isMuted);
  const volume = useEditorStore((state) => state.volume);
  const playbackRate = useEditorStore((state) => state.playbackRate);
  const inPoint = useEditorStore((state) => state.inPoint);
  const outPoint = useEditorStore((state) => state.outPoint);
  const setIsPlaying = useEditorStore((state) => state.setIsPlaying);

  const fps = 30;
  const durationInFrames = Math.max(1, Math.floor(duration * fps) + 1);

  // Sync store time to player when not playing
  useEffect(() => {
    if (!playerRef.current || isPlaying) return;
    const frame = Math.round(currentTime * fps);
    playerRef.current.seekTo(frame);
  }, [currentTime, fps, isPlaying]);

  // Control playback
  useEffect(() => {
    if (!playerRef.current) return;
    if (isPlaying) {
      if (inPoint !== null && currentTime < inPoint) {
        playerRef.current.seekTo(Math.round(inPoint * fps));
      }
      playerRef.current.play();
    } else {
      playerRef.current.pause();
    }
  }, [isPlaying, inPoint, currentTime, fps]);

  // Monitor out-point
  useEffect(() => {
    if (!isPlaying || outPoint === null || !playerRef.current) return;
    const checkOutPoint = () => {
      if (playerRef.current) {
        const currentFrame = playerRef.current.getCurrentFrame();
        const currentSeconds = currentFrame / fps;
        if (currentSeconds >= outPoint) {
          playerRef.current.pause();
          playerRef.current.seekTo(Math.round(outPoint * fps));
          setIsPlaying(false);
        }
      }
    };
    const intervalId = setInterval(checkOutPoint, 100);
    return () => clearInterval(intervalId);
  }, [isPlaying, outPoint, fps, setIsPlaying]);

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Box sx={{ width: '100%', maxWidth: '100%', aspectRatio: '16/9' }}>
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
          playbackRate={playbackRate}
          volume={isMuted ? 0 : volume / 100}
        />
      </Box>
    </Box>
  );
}
```

---

**Continue to Part 3: Properties and Export**
