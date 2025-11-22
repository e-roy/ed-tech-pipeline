---
date: 2025-11-20T23:45:00Z
researcher: Claude (Sonnet 4.5)
git_commit: 6dad8061c7eb1cb5d6295706fa3ca91f7b790fee
branch: ClassCut
repository: pipeline
topic: "Implementation Plan Part 3: Properties, Export, and Keyboard Shortcuts"
tags: [implementation-plan, remotion, video-editing, export, ffmpeg]
status: complete
---

# Implementation Plan Part 3: Properties, Export, and Keyboard Shortcuts

## Phase 8: Toolbar Component

**File**: `frontend/src/components/video-editor/Toolbar.tsx` (NEW)

```typescript
'use client';

import { useState } from 'react';
import { Box, IconButton, Button, Tooltip, Divider, Select, MenuItem, Typography, Slider } from '@mui/material';
import { PlayArrow, Pause, SkipPrevious, SkipNext, VolumeUp, VolumeOff, Undo, Redo, ContentCut, ContentCopy, ContentPaste, Delete, ZoomIn, ZoomOut, FileDownload, Save } from '@mui/icons-material';
import { useEditorStore, selectCanUndo, selectCanRedo } from '@/stores/editorStore';
import { ExportDialog } from './ExportDialog';

export function Toolbar() {
  const [exportOpen, setExportOpen] = useState(false);

  const currentTime = useEditorStore((state) => state.currentTime);
  const duration = useEditorStore((state) => state.duration);
  const isPlaying = useEditorStore((state) => state.isPlaying);
  const isMuted = useEditorStore((state) => state.isMuted);
  const volume = useEditorStore((state) => state.volume);
  const playbackRate = useEditorStore((state) => state.playbackRate);

  const togglePlayPause = useEditorStore((state) => state.togglePlayPause);
  const setCurrentTime = useEditorStore((state) => state.setCurrentTime);
  const setMuted = useEditorStore((state) => state.setMuted);
  const setVolume = useEditorStore((state) => state.setVolume);
  const setPlaybackRate = useEditorStore((state) => state.setPlaybackRate);
  const undo = useEditorStore((state) => state.undo);
  const redo = useEditorStore((state) => state.redo);
  const copy = useEditorStore((state) => state.copy);
  const cut = useEditorStore((state) => state.cut);
  const paste = useEditorStore((state) => state.paste);
  const deleteSelected = useEditorStore((state) => state.deleteSelected);
  const zoomIn = useEditorStore((state) => state.zoomIn);
  const zoomOut = useEditorStore((state) => state.zoomOut);

  const canUndo = useEditorStore(selectCanUndo);
  const canRedo = useEditorStore(selectCanRedo);
  const selectedIds = useEditorStore((state) => state.selectedIds);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const frames = Math.floor((seconds % 1) * 30);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}:${frames.toString().padStart(2, '0')}`;
  };

  return (
    <>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2, py: 1, bgcolor: 'background.paper', borderBottom: 1, borderColor: 'divider' }}>
        <Tooltip title="Save Project"><IconButton size="small"><Save fontSize="small" /></IconButton></Tooltip>

        <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />

        <Tooltip title="Undo (Ctrl+Z)"><span><IconButton size="small" onClick={undo} disabled={!canUndo}><Undo fontSize="small" /></IconButton></span></Tooltip>
        <Tooltip title="Redo (Ctrl+Shift+Z)"><span><IconButton size="small" onClick={redo} disabled={!canRedo}><Redo fontSize="small" /></IconButton></span></Tooltip>

        <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />

        <Tooltip title="Cut (Ctrl+X)"><span><IconButton size="small" onClick={cut} disabled={selectedIds.length === 0}><ContentCut fontSize="small" /></IconButton></span></Tooltip>
        <Tooltip title="Copy (Ctrl+C)"><span><IconButton size="small" onClick={copy} disabled={selectedIds.length === 0}><ContentCopy fontSize="small" /></IconButton></span></Tooltip>
        <Tooltip title="Paste (Ctrl+V)"><IconButton size="small" onClick={() => paste()}><ContentPaste fontSize="small" /></IconButton></Tooltip>
        <Tooltip title="Delete (Del)"><span><IconButton size="small" onClick={deleteSelected} disabled={selectedIds.length === 0}><Delete fontSize="small" /></IconButton></span></Tooltip>

        <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />

        <Tooltip title="Go to Start"><IconButton size="small" onClick={() => setCurrentTime(0)}><SkipPrevious fontSize="small" /></IconButton></Tooltip>
        <Tooltip title={isPlaying ? 'Pause (Space)' : 'Play (Space)'}><IconButton size="small" onClick={togglePlayPause}>{isPlaying ? <Pause fontSize="small" /> : <PlayArrow fontSize="small" />}</IconButton></Tooltip>
        <Tooltip title="Go to End"><IconButton size="small" onClick={() => setCurrentTime(duration)}><SkipNext fontSize="small" /></IconButton></Tooltip>

        <Typography variant="body2" sx={{ fontFamily: 'monospace', minWidth: 120, textAlign: 'center', bgcolor: 'background.default', px: 1, py: 0.5, borderRadius: 1 }}>
          {formatTime(currentTime)} / {formatTime(duration)}
        </Typography>

        <Select size="small" value={playbackRate} onChange={(e) => setPlaybackRate(e.target.value as number)} sx={{ minWidth: 80 }}>
          <MenuItem value={0.25}>0.25x</MenuItem>
          <MenuItem value={0.5}>0.5x</MenuItem>
          <MenuItem value={1}>1x</MenuItem>
          <MenuItem value={1.5}>1.5x</MenuItem>
          <MenuItem value={2}>2x</MenuItem>
        </Select>

        <Tooltip title={isMuted ? 'Unmute' : 'Mute'}><IconButton size="small" onClick={() => setMuted(!isMuted)}>{isMuted ? <VolumeOff fontSize="small" /> : <VolumeUp fontSize="small" />}</IconButton></Tooltip>
        <Slider size="small" value={isMuted ? 0 : volume} onChange={(_, value) => setVolume(value as number)} sx={{ width: 80 }} />

        <Box sx={{ flex: 1 }} />

        <Tooltip title="Zoom Out"><IconButton size="small" onClick={zoomOut}><ZoomOut fontSize="small" /></IconButton></Tooltip>
        <Tooltip title="Zoom In"><IconButton size="small" onClick={zoomIn}><ZoomIn fontSize="small" /></IconButton></Tooltip>

        <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />

        <Button variant="contained" size="small" startIcon={<FileDownload />} onClick={() => setExportOpen(true)}>Export</Button>
      </Box>

      <ExportDialog open={exportOpen} onClose={() => setExportOpen(false)} />
    </>
  );
}
```

---

## Phase 9: Media Bin Component

**File**: `frontend/src/components/video-editor/MediaBin.tsx` (NEW)

```typescript
'use client';

import { useState, useCallback } from 'react';
import { Box, Tabs, Tab, Typography, IconButton, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Tooltip } from '@mui/material';
import { Upload, VideoFile, AudioFile, Image, TextFields } from '@mui/icons-material';
import { useEditorStore } from '@/stores/editorStore';
import { api } from '@/trpc/react';

interface MediaBinProps {
  sessionId: string;
}

export function MediaBin({ sessionId }: MediaBinProps) {
  const [tab, setTab] = useState(0);

  const addMedia = useEditorStore((state) => state.addMedia);
  const addText = useEditorStore((state) => state.addText);
  const currentTime = useEditorStore((state) => state.currentTime);

  const { data: files, isLoading } = api.storage.listFiles.useQuery({ folder: 'input' });

  const handleAddMedia = useCallback((file: { key: string; name: string; presigned_url: string; content_type: string }) => {
    const type = file.content_type.startsWith('video/') ? 'video' : file.content_type.startsWith('audio/') ? 'audio' : 'image';
    const defaultDuration = 5;

    addMedia({
      type,
      fileName: file.name,
      src: file.presigned_url,
      s3Key: file.key,
      startTime: 0,
      endTime: defaultDuration,
      duration: defaultDuration,
      positionStart: currentTime,
      positionEnd: currentTime + defaultDuration,
      playbackSpeed: 1,
      volume: 100,
      opacity: 100,
    });
  }, [addMedia, currentTime]);

  const handleAddText = useCallback(() => {
    addText({
      text: 'New Text',
      positionStart: currentTime,
      positionEnd: currentTime + 3,
      x: 100,
      y: 100,
      font: 'Arial',
      fontSize: 48,
      fontWeight: 'normal',
      fontStyle: 'normal',
      color: '#ffffff',
      backgroundColor: 'transparent',
      textAlign: 'center',
      opacity: 100,
      animation: 'none',
      animationDuration: 0.5,
    });
  }, [addText, currentTime]);

  const getFileIcon = (contentType: string) => {
    if (contentType.startsWith('video/')) return <VideoFile />;
    if (contentType.startsWith('audio/')) return <AudioFile />;
    return <Image />;
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="fullWidth" sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tab label="Media" />
        <Tab label="Text" />
      </Tabs>

      {tab === 0 && (
        <Box sx={{ flex: 1, overflow: 'auto' }}>
          <Box sx={{ p: 1, borderBottom: 1, borderColor: 'divider' }}>
            <Tooltip title="Upload Media"><IconButton size="small"><Upload fontSize="small" /></IconButton></Tooltip>
          </Box>
          <List dense>
            {isLoading ? (
              <ListItem><ListItemText primary="Loading..." /></ListItem>
            ) : files?.files && files.files.length > 0 ? (
              files.files.map((file) => (
                <ListItemButton key={file.key} onClick={() => handleAddMedia(file)}>
                  <ListItemIcon sx={{ minWidth: 36 }}>{getFileIcon(file.content_type)}</ListItemIcon>
                  <ListItemText primary={file.name} primaryTypographyProps={{ variant: 'caption', noWrap: true }} />
                </ListItemButton>
              ))
            ) : (
              <ListItem><ListItemText primary="No media files" secondary="Upload files to get started" /></ListItem>
            )}
          </List>
        </Box>
      )}

      {tab === 1 && (
        <Box sx={{ flex: 1, p: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>Click to add text overlay</Typography>
          <ListItemButton onClick={handleAddText}>
            <ListItemIcon sx={{ minWidth: 36 }}><TextFields /></ListItemIcon>
            <ListItemText primary="Add Text" />
          </ListItemButton>
        </Box>
      )}
    </Box>
  );
}
```

---

## Phase 10: Properties Panel

### 10.1 Properties Panel Container

**File**: `frontend/src/components/video-editor/PropertiesPanel.tsx` (NEW)

```typescript
'use client';

import { Box, Typography } from '@mui/material';
import { useEditorStore, selectActiveElement } from '@/stores/editorStore';
import { MediaProperties } from './properties/MediaProperties';
import { TextProperties } from './properties/TextProperties';

export function PropertiesPanel() {
  const activeElement = useEditorStore(selectActiveElement);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="subtitle2">Properties</Typography>
      </Box>
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        {!activeElement ? (
          <Typography variant="body2" color="text.secondary">Select an element to edit its properties</Typography>
        ) : activeElement.type === 'media' ? (
          <MediaProperties media={activeElement.element} />
        ) : (
          <TextProperties text={activeElement.element} />
        )}
      </Box>
    </Box>
  );
}
```

### 10.2 Media Properties

**File**: `frontend/src/components/video-editor/properties/MediaProperties.tsx` (NEW)

```typescript
'use client';

import { Box, Typography, Slider, TextField, Select, MenuItem, FormControl, InputLabel, Divider } from '@mui/material';
import { useEditorStore, type MediaFile } from '@/stores/editorStore';

interface MediaPropertiesProps {
  media: MediaFile;
}

export function MediaProperties({ media }: MediaPropertiesProps) {
  const updateMedia = useEditorStore((state) => state.updateMedia);
  const handleUpdate = (updates: Partial<MediaFile>) => updateMedia(media.id, updates);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Typography variant="caption" color="text.secondary">{media.fileName}</Typography>
      <Divider />

      <Typography variant="subtitle2">Timeline</Typography>
      <Box sx={{ display: 'flex', gap: 1 }}>
        <TextField label="Start" type="number" size="small" value={media.positionStart.toFixed(2)} onChange={(e) => handleUpdate({ positionStart: parseFloat(e.target.value) || 0 })} inputProps={{ step: 0.1 }} />
        <TextField label="End" type="number" size="small" value={media.positionEnd.toFixed(2)} onChange={(e) => handleUpdate({ positionEnd: parseFloat(e.target.value) || 0 })} inputProps={{ step: 0.1 }} />
      </Box>

      <Divider />
      <Typography variant="subtitle2">Source Trim</Typography>
      <Box sx={{ display: 'flex', gap: 1 }}>
        <TextField label="In" type="number" size="small" value={media.startTime.toFixed(2)} onChange={(e) => handleUpdate({ startTime: parseFloat(e.target.value) || 0 })} inputProps={{ step: 0.1, min: 0, max: media.duration }} />
        <TextField label="Out" type="number" size="small" value={media.endTime.toFixed(2)} onChange={(e) => handleUpdate({ endTime: parseFloat(e.target.value) || 0 })} inputProps={{ step: 0.1, min: 0, max: media.duration }} />
      </Box>

      <Divider />
      <Typography variant="subtitle2">Playback</Typography>
      <FormControl size="small" fullWidth>
        <InputLabel>Speed</InputLabel>
        <Select value={media.playbackSpeed} label="Speed" onChange={(e) => handleUpdate({ playbackSpeed: e.target.value as number })}>
          <MenuItem value={0.25}>0.25x</MenuItem>
          <MenuItem value={0.5}>0.5x</MenuItem>
          <MenuItem value={1}>1x</MenuItem>
          <MenuItem value={1.5}>1.5x</MenuItem>
          <MenuItem value={2}>2x</MenuItem>
        </Select>
      </FormControl>

      {(media.type === 'video' || media.type === 'audio') && (
        <Box>
          <Typography variant="caption" color="text.secondary">Volume: {media.volume}%</Typography>
          <Slider value={media.volume} onChange={(_, v) => handleUpdate({ volume: v as number })} min={0} max={100} />
        </Box>
      )}

      {(media.type === 'video' || media.type === 'image') && (
        <>
          <Divider />
          <Typography variant="subtitle2">Transform</Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField label="X" type="number" size="small" value={media.x || 0} onChange={(e) => handleUpdate({ x: parseInt(e.target.value) || 0 })} />
            <TextField label="Y" type="number" size="small" value={media.y || 0} onChange={(e) => handleUpdate({ y: parseInt(e.target.value) || 0 })} />
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField label="Width" type="number" size="small" value={media.width || ''} onChange={(e) => handleUpdate({ width: parseInt(e.target.value) || undefined })} placeholder="Auto" />
            <TextField label="Height" type="number" size="small" value={media.height || ''} onChange={(e) => handleUpdate({ height: parseInt(e.target.value) || undefined })} placeholder="Auto" />
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">Opacity: {media.opacity ?? 100}%</Typography>
            <Slider value={media.opacity ?? 100} onChange={(_, v) => handleUpdate({ opacity: v as number })} min={0} max={100} />
          </Box>
          <TextField label="Rotation" type="number" size="small" value={media.rotation || 0} onChange={(e) => handleUpdate({ rotation: parseFloat(e.target.value) || 0 })} inputProps={{ step: 1, min: -360, max: 360 }} />
        </>
      )}
    </Box>
  );
}
```

### 10.3 Text Properties

**File**: `frontend/src/components/video-editor/properties/TextProperties.tsx` (NEW)

```typescript
'use client';

import { Box, Typography, TextField, Slider, Select, MenuItem, FormControl, InputLabel, ToggleButtonGroup, ToggleButton, Divider } from '@mui/material';
import { FormatBold, FormatItalic, FormatAlignLeft, FormatAlignCenter, FormatAlignRight } from '@mui/icons-material';
import { useEditorStore, type TextElement } from '@/stores/editorStore';

interface TextPropertiesProps {
  text: TextElement;
}

export function TextProperties({ text }: TextPropertiesProps) {
  const updateText = useEditorStore((state) => state.updateText);
  const handleUpdate = (updates: Partial<TextElement>) => updateText(text.id, updates);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <TextField label="Text" multiline rows={3} value={text.text} onChange={(e) => handleUpdate({ text: e.target.value })} size="small" />
      <Divider />

      <Typography variant="subtitle2">Timeline</Typography>
      <Box sx={{ display: 'flex', gap: 1 }}>
        <TextField label="Start" type="number" size="small" value={text.positionStart.toFixed(2)} onChange={(e) => handleUpdate({ positionStart: parseFloat(e.target.value) || 0 })} inputProps={{ step: 0.1 }} />
        <TextField label="End" type="number" size="small" value={text.positionEnd.toFixed(2)} onChange={(e) => handleUpdate({ positionEnd: parseFloat(e.target.value) || 0 })} inputProps={{ step: 0.1 }} />
      </Box>

      <Divider />
      <Typography variant="subtitle2">Font</Typography>
      <FormControl size="small" fullWidth>
        <InputLabel>Font Family</InputLabel>
        <Select value={text.font} label="Font Family" onChange={(e) => handleUpdate({ font: e.target.value })}>
          <MenuItem value="Arial">Arial</MenuItem>
          <MenuItem value="Helvetica">Helvetica</MenuItem>
          <MenuItem value="Times New Roman">Times New Roman</MenuItem>
          <MenuItem value="Georgia">Georgia</MenuItem>
          <MenuItem value="Verdana">Verdana</MenuItem>
          <MenuItem value="Impact">Impact</MenuItem>
        </Select>
      </FormControl>
      <TextField label="Font Size" type="number" size="small" value={text.fontSize} onChange={(e) => handleUpdate({ fontSize: parseInt(e.target.value) || 24 })} inputProps={{ min: 8, max: 200 }} />

      <Box sx={{ display: 'flex', gap: 1 }}>
        <ToggleButtonGroup value={[text.fontWeight === 'bold' ? 'bold' : null, text.fontStyle === 'italic' ? 'italic' : null].filter(Boolean)} onChange={(_, values) => handleUpdate({ fontWeight: values.includes('bold') ? 'bold' : 'normal', fontStyle: values.includes('italic') ? 'italic' : 'normal' })} size="small">
          <ToggleButton value="bold"><FormatBold fontSize="small" /></ToggleButton>
          <ToggleButton value="italic"><FormatItalic fontSize="small" /></ToggleButton>
        </ToggleButtonGroup>
        <ToggleButtonGroup value={text.textAlign} exclusive onChange={(_, value) => value && handleUpdate({ textAlign: value })} size="small">
          <ToggleButton value="left"><FormatAlignLeft fontSize="small" /></ToggleButton>
          <ToggleButton value="center"><FormatAlignCenter fontSize="small" /></ToggleButton>
          <ToggleButton value="right"><FormatAlignRight fontSize="small" /></ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Divider />
      <Typography variant="subtitle2">Colors</Typography>
      <Box sx={{ display: 'flex', gap: 1 }}>
        <TextField label="Text Color" type="color" size="small" value={text.color} onChange={(e) => handleUpdate({ color: e.target.value })} sx={{ flex: 1 }} />
        <TextField label="Background" type="color" size="small" value={text.backgroundColor || '#000000'} onChange={(e) => handleUpdate({ backgroundColor: e.target.value })} sx={{ flex: 1 }} />
      </Box>

      <Divider />
      <Typography variant="subtitle2">Position</Typography>
      <Box sx={{ display: 'flex', gap: 1 }}>
        <TextField label="X" type="number" size="small" value={text.x} onChange={(e) => handleUpdate({ x: parseInt(e.target.value) || 0 })} />
        <TextField label="Y" type="number" size="small" value={text.y} onChange={(e) => handleUpdate({ y: parseInt(e.target.value) || 0 })} />
      </Box>
      <Box>
        <Typography variant="caption" color="text.secondary">Opacity: {text.opacity}%</Typography>
        <Slider value={text.opacity} onChange={(_, v) => handleUpdate({ opacity: v as number })} min={0} max={100} />
      </Box>

      <Divider />
      <Typography variant="subtitle2">Animation</Typography>
      <FormControl size="small" fullWidth>
        <InputLabel>Animation</InputLabel>
        <Select value={text.animation} label="Animation" onChange={(e) => handleUpdate({ animation: e.target.value as TextElement['animation'] })}>
          <MenuItem value="none">None</MenuItem>
          <MenuItem value="fade-in">Fade In</MenuItem>
          <MenuItem value="slide-up">Slide Up</MenuItem>
          <MenuItem value="slide-left">Slide Left</MenuItem>
          <MenuItem value="zoom">Zoom</MenuItem>
          <MenuItem value="typewriter">Typewriter</MenuItem>
        </Select>
      </FormControl>
      {text.animation !== 'none' && (
        <TextField label="Animation Duration" type="number" size="small" value={text.animationDuration} onChange={(e) => handleUpdate({ animationDuration: parseFloat(e.target.value) || 0.5 })} inputProps={{ step: 0.1, min: 0.1, max: 5 }} />
      )}
    </Box>
  );
}
```

---

## Phase 11: Export Dialog

**File**: `frontend/src/components/video-editor/ExportDialog.tsx` (NEW)

```typescript
'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, LinearProgress, Box, Alert } from '@mui/material';
import { useEditorStore } from '@/stores/editorStore';
import { useWebSocket } from '@/hooks/useWebSocket';

interface ExportDialogProps {
  open: boolean;
  onClose: () => void;
}

export function ExportDialog({ open, onClose }: ExportDialogProps) {
  const [error, setError] = useState<string | null>(null);
  const [exportedUrl, setExportedUrl] = useState<string | null>(null);

  const projectId = useEditorStore((state) => state.projectId);
  const duration = useEditorStore((state) => state.duration);
  const fps = useEditorStore((state) => state.fps);
  const resolution = useEditorStore((state) => state.resolution);
  const mediaFiles = useEditorStore((state) => state.mediaFiles);
  const textElements = useEditorStore((state) => state.textElements);
  const isExporting = useEditorStore((state) => state.isExporting);
  const exportProgress = useEditorStore((state) => state.exportProgress);
  const setExporting = useEditorStore((state) => state.setExporting);
  const setExportProgress = useEditorStore((state) => state.setExportProgress);

  const { lastMessage } = useWebSocket(isExporting ? projectId : null);

  useEffect(() => {
    if (!lastMessage) return;
    if (lastMessage.type === 'export_progress') setExportProgress(lastMessage.progress);
    else if (lastMessage.type === 'export_complete') { setExporting(false); setExportedUrl(lastMessage.video_url); }
    else if (lastMessage.type === 'export_error') { setExporting(false); setError(lastMessage.error); }
  }, [lastMessage, setExportProgress, setExporting]);

  const handleExport = async () => {
    setError(null);
    setExportedUrl(null);
    setExporting(true);
    setExportProgress(0);

    try {
      const exportData = {
        session_id: projectId,
        duration,
        fps,
        resolution,
        media_files: mediaFiles.map((m) => ({
          id: m.id, type: m.type, s3_key: m.s3Key || '',
          start_time: m.startTime, end_time: m.endTime,
          position_start: m.positionStart, position_end: m.positionEnd,
          playback_speed: m.playbackSpeed, volume: m.volume,
          x: m.x, y: m.y, width: m.width, height: m.height, opacity: m.opacity, z_index: m.zIndex,
        })),
        text_elements: textElements.map((t) => ({
          id: t.id, text: t.text,
          position_start: t.positionStart, position_end: t.positionEnd,
          x: t.x, y: t.y, font: t.font, font_size: t.fontSize,
          font_weight: t.fontWeight, font_style: t.fontStyle,
          color: t.color, background_color: t.backgroundColor, text_align: t.textAlign,
          opacity: t.opacity, animation: t.animation, animation_duration: t.animationDuration,
        })),
      };

      const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
      const response = await fetch(`${API_URL}/api/video/compose-edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(exportData),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Export failed');
      }
    } catch (err) {
      setExporting(false);
      setError(err instanceof Error ? err.message : 'Export failed');
    }
  };

  const handleDownload = () => {
    if (exportedUrl) {
      const link = document.createElement('a');
      link.href = exportedUrl;
      link.download = `video-${projectId}.mp4`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <Dialog open={open} onClose={isExporting ? undefined : onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Export Video</DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {exportedUrl ? (
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="h6" color="success.main" gutterBottom>Export Complete!</Typography>
            <Typography variant="body2" color="text.secondary">Your video is ready for download.</Typography>
          </Box>
        ) : isExporting ? (
          <Box sx={{ py: 2 }}>
            <Typography variant="body2" gutterBottom>Exporting video...</Typography>
            <LinearProgress variant="determinate" value={exportProgress} sx={{ mb: 1 }} />
            <Typography variant="caption" color="text.secondary">{exportProgress.toFixed(0)}% complete</Typography>
          </Box>
        ) : (
          <Box sx={{ py: 2 }}>
            <Typography variant="body2" gutterBottom>Export settings:</Typography>
            <Typography variant="caption" color="text.secondary" component="div">Resolution: {resolution.width}x{resolution.height}</Typography>
            <Typography variant="caption" color="text.secondary" component="div">Duration: {duration.toFixed(1)} seconds</Typography>
            <Typography variant="caption" color="text.secondary" component="div">Frame Rate: {fps} fps</Typography>
            <Typography variant="caption" color="text.secondary" component="div">Format: MP4 (H.264)</Typography>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        {exportedUrl ? (
          <>
            <Button onClick={onClose}>Close</Button>
            <Button variant="contained" onClick={handleDownload}>Download</Button>
          </>
        ) : (
          <>
            <Button onClick={onClose} disabled={isExporting}>Cancel</Button>
            <Button variant="contained" onClick={handleExport} disabled={isExporting}>{isExporting ? 'Exporting...' : 'Export'}</Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  );
}
```

---

## Phase 12: Keyboard Shortcuts

**File**: `frontend/src/hooks/useKeyboardShortcuts.ts` (NEW)

```typescript
'use client';

import { useEffect } from 'react';
import { useEditorStore, selectCanUndo, selectCanRedo } from '@/stores/editorStore';

export function useKeyboardShortcuts() {
  const togglePlayPause = useEditorStore((state) => state.togglePlayPause);
  const setCurrentTime = useEditorStore((state) => state.setCurrentTime);
  const currentTime = useEditorStore((state) => state.currentTime);
  const duration = useEditorStore((state) => state.duration);
  const undo = useEditorStore((state) => state.undo);
  const redo = useEditorStore((state) => state.redo);
  const copy = useEditorStore((state) => state.copy);
  const cut = useEditorStore((state) => state.cut);
  const paste = useEditorStore((state) => state.paste);
  const deleteSelected = useEditorStore((state) => state.deleteSelected);
  const selectAll = useEditorStore((state) => state.selectAll);
  const selectedIds = useEditorStore((state) => state.selectedIds);
  const splitMedia = useEditorStore((state) => state.splitMedia);
  const canUndo = useEditorStore(selectCanUndo);
  const canRedo = useEditorStore(selectCanRedo);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const modifier = isMac ? e.metaKey : e.ctrlKey;

      // Space - Play/Pause
      if (e.code === 'Space') { e.preventDefault(); togglePlayPause(); return; }

      // Arrow keys - Scrub
      if (e.code === 'ArrowLeft') { e.preventDefault(); setCurrentTime(Math.max(0, currentTime - (e.shiftKey ? 1 : 0.1))); return; }
      if (e.code === 'ArrowRight') { e.preventDefault(); setCurrentTime(Math.min(duration, currentTime + (e.shiftKey ? 1 : 0.1))); return; }

      // Home/End
      if (e.code === 'Home') { e.preventDefault(); setCurrentTime(0); return; }
      if (e.code === 'End') { e.preventDefault(); setCurrentTime(duration); return; }

      // Delete
      if (e.code === 'Delete' || e.code === 'Backspace') { e.preventDefault(); deleteSelected(); return; }

      // Undo/Redo
      if (modifier && e.code === 'KeyZ' && !e.shiftKey) { e.preventDefault(); if (canUndo) undo(); return; }
      if (modifier && e.code === 'KeyZ' && e.shiftKey) { e.preventDefault(); if (canRedo) redo(); return; }

      // Copy/Cut/Paste
      if (modifier && e.code === 'KeyC') { e.preventDefault(); copy(); return; }
      if (modifier && e.code === 'KeyX') { e.preventDefault(); cut(); return; }
      if (modifier && e.code === 'KeyV') { e.preventDefault(); paste(); return; }

      // Select All
      if (modifier && e.code === 'KeyA') { e.preventDefault(); selectAll(); return; }

      // C - Split at playhead
      if (e.code === 'KeyC' && !modifier && selectedIds.length === 1) { e.preventDefault(); splitMedia(selectedIds[0], currentTime); return; }

      // J/K/L - Playback control
      if (e.code === 'KeyJ') { e.preventDefault(); setCurrentTime(Math.max(0, currentTime - 5)); return; }
      if (e.code === 'KeyK') { e.preventDefault(); useEditorStore.getState().setIsPlaying(false); return; }
      if (e.code === 'KeyL') { e.preventDefault(); setCurrentTime(Math.min(duration, currentTime + 5)); return; }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [togglePlayPause, setCurrentTime, currentTime, duration, undo, redo, copy, cut, paste, deleteSelected, selectAll, selectedIds, splitMedia, canUndo, canRedo]);
}
```

---

## Phase 13: Backend Export Endpoint

**File**: `backend/app/routes/video_editor.py` (NEW)

```python
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import logging

from app.routes.auth import get_current_user
from app.services.websocket_manager import websocket_manager
from app.services.storage import StorageService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/video", tags=["video-editor"])
storage_service = StorageService()


class MediaFileExport(BaseModel):
    id: str
    type: str
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
    font_weight: Optional[str] = "normal"
    font_style: Optional[str] = "normal"
    color: Optional[str] = "#ffffff"
    background_color: Optional[str] = None
    text_align: Optional[str] = "center"
    opacity: Optional[int] = 100
    animation: Optional[str] = "none"
    animation_duration: Optional[float] = 0.5


class ComposeEditRequest(BaseModel):
    session_id: str
    duration: float
    fps: int = 30
    resolution: dict = {"width": 1920, "height": 1080}
    media_files: List[MediaFileExport]
    text_elements: List[TextElementExport]


async def process_video_edit(session_id: str, user_id: str, export_data: dict):
    """Background task to process video edit."""
    try:
        # Send initial progress
        await websocket_manager.send_progress(session_id, {
            "type": "export_progress",
            "progress": 0,
            "message": "Starting export..."
        })

        # TODO: Implement FFmpeg composition here
        # 1. Download media files from S3
        # 2. Build FFmpeg filter graph
        # 3. Execute FFmpeg
        # 4. Upload result to S3

        # Simulate progress for now
        for i in range(1, 11):
            await asyncio.sleep(1)
            await websocket_manager.send_progress(session_id, {
                "type": "export_progress",
                "progress": i * 10,
                "message": f"Processing... {i * 10}%"
            })

        # Send completion
        await websocket_manager.send_progress(session_id, {
            "type": "export_complete",
            "video_url": f"https://your-bucket.s3.amazonaws.com/users/{user_id}/{session_id}/final/edited_video.mp4"
        })

    except Exception as e:
        logger.error(f"Export failed: {e}")
        await websocket_manager.send_progress(session_id, {
            "type": "export_error",
            "error": str(e)
        })


@router.post("/compose-edit")
async def compose_edit(
    request: ComposeEditRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user)
):
    """Compose edited video from editing state."""

    # Validate user owns all referenced S3 assets
    for media in request.media_files:
        if media.s3_key and not media.s3_key.startswith(f"users/{user.id}/"):
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

**Add to `backend/app/main.py`:**

```python
from app.routes.video_editor import router as video_editor_router

# Add with other router includes
app.include_router(video_editor_router)
```

---

## Complete File List

### Frontend (New Files)

```
frontend/src/
├── stores/
│   └── editorStore.ts
├── hooks/
│   └── useKeyboardShortcuts.ts
├── components/
│   └── video-editor/
│       ├── theme.ts
│       ├── EditorLayout.tsx
│       ├── Toolbar.tsx
│       ├── PreviewPlayer.tsx
│       ├── Timeline.tsx
│       ├── MediaBin.tsx
│       ├── PropertiesPanel.tsx
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

### Backend (New Files)

```
backend/app/
└── routes/
    └── video_editor.py
```

### Files to Update

```
frontend/package.json          # Add dependencies
frontend/src/app/dashboard/editing/[id]/page.tsx  # Use EditorLayout
backend/app/main.py            # Include video_editor router
```

---

## Testing Checklist

- [ ] Dependencies install without conflicts
- [ ] MUI theme renders properly with CSS layers
- [ ] Zustand store initializes and persists
- [ ] Timeline displays with zoom/scroll
- [ ] Clips can be added, dragged, resized
- [ ] Remotion preview renders correctly
- [ ] Text overlays with animations work
- [ ] Properties panel updates in real-time
- [ ] Keyboard shortcuts function
- [ ] Export sends correct data to backend
- [ ] WebSocket progress updates work
- [ ] Final video downloads successfully

---

## Keyboard Shortcuts Reference

| Shortcut | Action |
|----------|--------|
| Space | Play/Pause |
| Left/Right Arrow | Scrub 0.1s |
| Shift + Left/Right | Scrub 1s |
| Home | Go to start |
| End | Go to end |
| Delete/Backspace | Delete selected |
| Cmd/Ctrl + Z | Undo |
| Cmd/Ctrl + Shift + Z | Redo |
| Cmd/Ctrl + C | Copy |
| Cmd/Ctrl + X | Cut |
| Cmd/Ctrl + V | Paste |
| Cmd/Ctrl + A | Select all |
| C | Split at playhead |
| J | Jump back 5s |
| K | Pause |
| L | Jump forward 5s |

---

**Implementation Complete!**

This three-part plan provides a complete roadmap for building the CapCut-like video editor with Remotion preview and MUI-based Premiere Pro-style UI.
