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
