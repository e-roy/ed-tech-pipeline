'use client';

import { useState } from 'react';
import { Box, Typography, Slider, TextField, Select, MenuItem, FormControl, InputLabel, Collapse, IconButton, type SelectChangeEvent } from '@mui/material';
import { ExpandMore, ExpandLess, Schedule, ContentCut, Speed, Transform, Opacity } from '@mui/icons-material';
import { useEditorStore, type MediaFile } from '@/stores/editorStore';
import { colors } from '../theme';

interface MediaPropertiesProps {
  media: MediaFile;
}

// Collapsible section component
function PropertySection({
  title,
  icon,
  children,
  defaultOpen = true,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <Box sx={{ borderBottom: `1px solid ${colors.border.subtle}` }}>
      <Box
        onClick={() => setOpen(!open)}
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          px: 2,
          py: 1.5,
          cursor: 'pointer',
          transition: 'all 0.15s ease',
          '&:hover': {
            bgcolor: colors.bg.hover,
          },
        }}
      >
        <Box sx={{ color: colors.primary.main, display: 'flex' }}>{icon}</Box>
        <Typography
          variant="subtitle2"
          sx={{
            flex: 1,
            color: colors.text.primary,
            fontWeight: 600,
            fontSize: '0.75rem',
            textTransform: 'uppercase',
            letterSpacing: '0.03em',
          }}
        >
          {title}
        </Typography>
        <IconButton size="small" sx={{ p: 0.25 }}>
          {open ? <ExpandLess sx={{ fontSize: 18 }} /> : <ExpandMore sx={{ fontSize: 18 }} />}
        </IconButton>
      </Box>
      <Collapse in={open}>
        <Box sx={{ px: 2, pb: 2, pt: 0.5 }}>{children}</Box>
      </Collapse>
    </Box>
  );
}

// Styled input row
function InputRow({ children }: { children: React.ReactNode }) {
  return (
    <Box sx={{ display: 'flex', gap: 1, mb: 1.5 }}>
      {children}
    </Box>
  );
}

// Slider with label
function LabeledSlider({
  label,
  value,
  onChange,
  min = 0,
  max = 100,
  unit = '',
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  unit?: string;
}) {
  return (
    <Box sx={{ mb: 1.5 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
        <Typography variant="caption" sx={{ color: colors.text.secondary, fontSize: '0.7rem' }}>
          {label}
        </Typography>
        <Typography
          variant="caption"
          sx={{
            color: colors.primary.light,
            fontSize: '0.7rem',
            fontFamily: 'monospace',
            fontWeight: 500,
          }}
        >
          {value}{unit}
        </Typography>
      </Box>
      <Slider
        size="small"
        value={value}
        onChange={(_, v) => onChange(v as number)}
        min={min}
        max={max}
      />
    </Box>
  );
}

export function MediaProperties({ media }: MediaPropertiesProps) {
  const updateMedia = useEditorStore((state) => state.updateMedia);
  const handleUpdate = (updates: Partial<MediaFile>) => updateMedia(media.id, updates);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
      {/* File info header */}
      <Box
        sx={{
          px: 2,
          py: 1.5,
          bgcolor: colors.bg.darker,
          borderBottom: `1px solid ${colors.border.subtle}`,
        }}
      >
        <Typography
          variant="body2"
          sx={{
            color: colors.text.primary,
            fontWeight: 600,
            fontSize: '0.8rem',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {media.fileName}
        </Typography>
        <Typography variant="caption" sx={{ color: colors.text.muted, fontSize: '0.7rem' }}>
          {media.type.charAt(0).toUpperCase() + media.type.slice(1)} • {media.duration.toFixed(1)}s
        </Typography>
      </Box>

      {/* Timeline Position */}
      <PropertySection title="Timeline" icon={<Schedule sx={{ fontSize: 16 }} />}>
        <InputRow>
          <TextField
            label="Start"
            type="number"
            size="small"
            fullWidth
            value={media.positionStart.toFixed(2)}
            onChange={(e) => handleUpdate({ positionStart: parseFloat(e.target.value) || 0 })}
            inputProps={{ step: 0.1 }}
          />
          <TextField
            label="End"
            type="number"
            size="small"
            fullWidth
            value={media.positionEnd.toFixed(2)}
            onChange={(e) => handleUpdate({ positionEnd: parseFloat(e.target.value) || 0 })}
            inputProps={{ step: 0.1 }}
          />
        </InputRow>
      </PropertySection>

      {/* Source Trim */}
      <PropertySection title="Source Trim" icon={<ContentCut sx={{ fontSize: 16 }} />}>
        <InputRow>
          <TextField
            label="In Point"
            type="number"
            size="small"
            fullWidth
            value={media.startTime.toFixed(2)}
            onChange={(e) => handleUpdate({ startTime: parseFloat(e.target.value) || 0 })}
            inputProps={{ step: 0.1, min: 0, max: media.duration }}
          />
          <TextField
            label="Out Point"
            type="number"
            size="small"
            fullWidth
            value={media.endTime.toFixed(2)}
            onChange={(e) => handleUpdate({ endTime: parseFloat(e.target.value) || 0 })}
            inputProps={{ step: 0.1, min: 0, max: media.duration }}
          />
        </InputRow>
      </PropertySection>

      {/* Playback */}
      <PropertySection title="Playback" icon={<Speed sx={{ fontSize: 16 }} />}>
        <FormControl size="small" fullWidth sx={{ mb: 1.5 }}>
          <InputLabel>Speed</InputLabel>
          <Select
            value={media.playbackSpeed}
            label="Speed"
            onChange={(e: SelectChangeEvent<number>) => handleUpdate({ playbackSpeed: e.target.value as number })}
          >
            <MenuItem value={0.25}>0.25x (Slow)</MenuItem>
            <MenuItem value={0.5}>0.5x</MenuItem>
            <MenuItem value={1}>1x (Normal)</MenuItem>
            <MenuItem value={1.5}>1.5x</MenuItem>
            <MenuItem value={2}>2x (Fast)</MenuItem>
          </Select>
        </FormControl>

        {(media.type === 'video' || media.type === 'audio') && (
          <LabeledSlider
            label="Volume"
            value={media.volume}
            onChange={(v) => handleUpdate({ volume: v })}
            unit="%"
          />
        )}
      </PropertySection>

      {/* Transform (for video/image only) */}
      {(media.type === 'video' || media.type === 'image') && (
        <>
          <PropertySection title="Transform" icon={<Transform sx={{ fontSize: 16 }} />}>
            <InputRow>
              <TextField
                label="X"
                type="number"
                size="small"
                fullWidth
                value={media.x || 0}
                onChange={(e) => handleUpdate({ x: parseInt(e.target.value) || 0 })}
              />
              <TextField
                label="Y"
                type="number"
                size="small"
                fullWidth
                value={media.y || 0}
                onChange={(e) => handleUpdate({ y: parseInt(e.target.value) || 0 })}
              />
            </InputRow>
            <InputRow>
              <TextField
                label="Width"
                type="number"
                size="small"
                fullWidth
                value={media.width || ''}
                onChange={(e) => handleUpdate({ width: parseInt(e.target.value) || undefined })}
                placeholder="Auto"
              />
              <TextField
                label="Height"
                type="number"
                size="small"
                fullWidth
                value={media.height || ''}
                onChange={(e) => handleUpdate({ height: parseInt(e.target.value) || undefined })}
                placeholder="Auto"
              />
            </InputRow>
            <TextField
              label="Rotation"
              type="number"
              size="small"
              fullWidth
              value={media.rotation || 0}
              onChange={(e) => handleUpdate({ rotation: parseFloat(e.target.value) || 0 })}
              inputProps={{ step: 1, min: -360, max: 360 }}
              sx={{ mb: 1.5 }}
            />
          </PropertySection>

          <PropertySection title="Opacity" icon={<Opacity sx={{ fontSize: 16 }} />} defaultOpen={false}>
            <LabeledSlider
              label="Opacity"
              value={media.opacity ?? 100}
              onChange={(v) => handleUpdate({ opacity: v })}
              unit="%"
            />
          </PropertySection>
        </>
      )}
    </Box>
  );
}
