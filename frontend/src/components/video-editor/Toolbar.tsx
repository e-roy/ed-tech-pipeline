'use client';

import { useState } from 'react';
import { Box, IconButton, Button, Tooltip, Select, MenuItem, Typography, Slider, type SelectChangeEvent } from '@mui/material';
import { PlayArrow, Pause, SkipPrevious, SkipNext, VolumeUp, VolumeOff, Undo, Redo, ContentCut, ContentCopy, ContentPaste, Delete, ZoomIn, ZoomOut, FileDownload, FolderOpen, FitScreen } from '@mui/icons-material';
import { useEditorStore, selectCanUndo, selectCanRedo } from '@/stores/editorStore';
import { colors } from './theme';
import { ExportDialog } from './ExportDialog';

// Styled button group wrapper
function ButtonGroup({ children }: { children: React.ReactNode }) {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 0.5,
        bgcolor: colors.bg.darker,
        borderRadius: 1.5,
        p: 0.5,
        border: `1px solid ${colors.border.subtle}`,
      }}
    >
      {children}
    </Box>
  );
}

// Styled icon button with better visuals
function ToolbarIconButton({
  onClick,
  disabled,
  tooltip,
  children,
  active,
}: {
  onClick?: () => void;
  disabled?: boolean;
  tooltip: string;
  children: React.ReactNode;
  active?: boolean;
}) {
  return (
    <Tooltip title={tooltip} arrow>
      <span>
        <IconButton
          size="small"
          onClick={onClick}
          disabled={disabled}
          sx={{
            color: active ? colors.primary.main : colors.text.secondary,
            bgcolor: active ? `${colors.primary.main}20` : 'transparent',
            '&:hover': {
              bgcolor: colors.bg.hover,
              color: colors.text.primary,
            },
            '&.Mui-disabled': {
              color: colors.text.muted,
              opacity: 0.5,
            },
            transition: 'all 0.15s ease',
          }}
        >
          {children}
        </IconButton>
      </span>
    </Tooltip>
  );
}

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
  const zoomToFit = useEditorStore((state) => state.zoomToFit);
  const timelineZoom = useEditorStore((state) => state.timelineZoom);
  const setTimelineZoom = useEditorStore((state) => state.setTimelineZoom);

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
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          px: 2,
          py: 1,
          bgcolor: colors.bg.paper,
          borderBottom: `1px solid ${colors.border.subtle}`,
          background: `linear-gradient(180deg, ${colors.bg.elevated} 0%, ${colors.bg.paper} 100%)`,
        }}
      >
        {/* Project actions */}
        <ButtonGroup>
          <ToolbarIconButton tooltip="Open Project">
            <FolderOpen sx={{ fontSize: 18 }} />
          </ToolbarIconButton>
        </ButtonGroup>

        {/* History */}
        <ButtonGroup>
          <ToolbarIconButton tooltip="Undo (Ctrl+Z)" onClick={undo} disabled={!canUndo}>
            <Undo sx={{ fontSize: 18 }} />
          </ToolbarIconButton>
          <ToolbarIconButton tooltip="Redo (Ctrl+Shift+Z)" onClick={redo} disabled={!canRedo}>
            <Redo sx={{ fontSize: 18 }} />
          </ToolbarIconButton>
        </ButtonGroup>

        {/* Clipboard */}
        <ButtonGroup>
          <ToolbarIconButton tooltip="Cut (Ctrl+X)" onClick={cut} disabled={selectedIds.length === 0}>
            <ContentCut sx={{ fontSize: 18 }} />
          </ToolbarIconButton>
          <ToolbarIconButton tooltip="Copy (Ctrl+C)" onClick={copy} disabled={selectedIds.length === 0}>
            <ContentCopy sx={{ fontSize: 18 }} />
          </ToolbarIconButton>
          <ToolbarIconButton tooltip="Paste (Ctrl+V)" onClick={() => paste()}>
            <ContentPaste sx={{ fontSize: 18 }} />
          </ToolbarIconButton>
          <ToolbarIconButton tooltip="Delete (Del)" onClick={deleteSelected} disabled={selectedIds.length === 0}>
            <Delete sx={{ fontSize: 18 }} />
          </ToolbarIconButton>
        </ButtonGroup>

        {/* Playback controls */}
        <ButtonGroup>
          <ToolbarIconButton tooltip="Go to Start" onClick={() => setCurrentTime(0)}>
            <SkipPrevious sx={{ fontSize: 18 }} />
          </ToolbarIconButton>
          <ToolbarIconButton tooltip={isPlaying ? 'Pause (Space)' : 'Play (Space)'} onClick={togglePlayPause} active={isPlaying}>
            {isPlaying ? <Pause sx={{ fontSize: 20 }} /> : <PlayArrow sx={{ fontSize: 20 }} />}
          </ToolbarIconButton>
          <ToolbarIconButton tooltip="Go to End" onClick={() => setCurrentTime(duration)}>
            <SkipNext sx={{ fontSize: 18 }} />
          </ToolbarIconButton>
        </ButtonGroup>

        {/* Timecode display */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            bgcolor: colors.bg.darkest,
            borderRadius: 1.5,
            px: 1.5,
            py: 0.75,
            border: `1px solid ${colors.border.subtle}`,
          }}
        >
          <Typography
            variant="body2"
            sx={{
              fontFamily: '"SF Mono", "Fira Code", "Consolas", monospace',
              fontSize: '0.8rem',
              fontWeight: 500,
              color: colors.primary.light,
              letterSpacing: '0.05em',
            }}
          >
            {formatTime(currentTime)}
          </Typography>
          <Typography
            variant="body2"
            sx={{
              fontFamily: '"SF Mono", "Fira Code", "Consolas", monospace',
              fontSize: '0.7rem',
              color: colors.text.muted,
            }}
          >
            /
          </Typography>
          <Typography
            variant="body2"
            sx={{
              fontFamily: '"SF Mono", "Fira Code", "Consolas", monospace',
              fontSize: '0.8rem',
              fontWeight: 500,
              color: colors.text.secondary,
              letterSpacing: '0.05em',
            }}
          >
            {formatTime(duration)}
          </Typography>
        </Box>

        {/* Speed selector */}
        <Select
          size="small"
          value={playbackRate}
          onChange={(e: SelectChangeEvent<number>) => setPlaybackRate(e.target.value as number)}
          sx={{
            minWidth: 70,
            height: 32,
            '& .MuiSelect-select': {
              py: 0.5,
              fontSize: '0.8rem',
            },
          }}
        >
          <MenuItem value={0.25}>0.25x</MenuItem>
          <MenuItem value={0.5}>0.5x</MenuItem>
          <MenuItem value={1}>1x</MenuItem>
          <MenuItem value={1.5}>1.5x</MenuItem>
          <MenuItem value={2}>2x</MenuItem>
        </Select>

        {/* Volume */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <ToolbarIconButton tooltip={isMuted ? 'Unmute' : 'Mute'} onClick={() => setMuted(!isMuted)}>
            {isMuted ? <VolumeOff sx={{ fontSize: 18 }} /> : <VolumeUp sx={{ fontSize: 18 }} />}
          </ToolbarIconButton>
          <Slider
            size="small"
            value={isMuted ? 0 : volume}
            onChange={(_, value) => setVolume(value as number)}
            sx={{
              width: 70,
              '& .MuiSlider-thumb': {
                width: 12,
                height: 12,
              },
            }}
          />
        </Box>

        {/* Spacer */}
        <Box sx={{ flex: 1 }} />

        {/* Zoom */}
        <ButtonGroup>
          <ToolbarIconButton tooltip="Zoom Out (Ctrl+-)" onClick={zoomOut}>
            <ZoomOut sx={{ fontSize: 18 }} />
          </ToolbarIconButton>
          <Slider
            size="small"
            value={timelineZoom}
            min={10}
            max={500}
            onChange={(_, value) => setTimelineZoom(value as number)}
            sx={{
              width: 80,
              mx: 1,
              '& .MuiSlider-thumb': {
                width: 12,
                height: 12,
              },
            }}
          />
          <ToolbarIconButton tooltip="Zoom In (Ctrl+=)" onClick={zoomIn}>
            <ZoomIn sx={{ fontSize: 18 }} />
          </ToolbarIconButton>
          <Typography
            variant="caption"
            sx={{
              minWidth: 40,
              textAlign: 'center',
              color: colors.text.secondary,
              fontFamily: '"SF Mono", "Fira Code", monospace',
              fontSize: '0.7rem',
            }}
          >
            {Math.round(timelineZoom)}%
          </Typography>
          <ToolbarIconButton tooltip="Fit to View (Ctrl+0)" onClick={zoomToFit}>
            <FitScreen sx={{ fontSize: 18 }} />
          </ToolbarIconButton>
        </ButtonGroup>

        {/* Export button */}
        <Button
          variant="contained"
          size="small"
          startIcon={<FileDownload sx={{ fontSize: 18 }} />}
          onClick={() => setExportOpen(true)}
          sx={{
            px: 2,
            py: 0.75,
            fontWeight: 600,
            boxShadow: `0 2px 8px ${colors.primary.glow}`,
            '&:hover': {
              boxShadow: `0 4px 16px ${colors.primary.glow}`,
            },
          }}
        >
          Export
        </Button>
      </Box>

      <ExportDialog open={exportOpen} onClose={() => setExportOpen(false)} />
    </>
  );
}
