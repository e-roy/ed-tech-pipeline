'use client';

import { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Slider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  ToggleButtonGroup,
  ToggleButton,
  IconButton,
  Collapse,
  type SelectChangeEvent,
} from '@mui/material';
import {
  FormatBold,
  FormatItalic,
  FormatAlignLeft,
  FormatAlignCenter,
  FormatAlignRight,
  ExpandMore,
  ExpandLess,
  TextFields,
  Schedule,
  FontDownload,
  Palette,
  OpenWith,
  Animation,
} from '@mui/icons-material';
import { useEditorStore, type TextElement } from '@/stores/editorStore';
import { colors } from '../theme';

interface TextPropertiesProps {
  text: TextElement;
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
          userSelect: 'none',
          transition: 'background 0.15s ease',
          '&:hover': {
            bgcolor: colors.bg.hover,
          },
        }}
      >
        <Box sx={{ color: colors.tracks.text.main, display: 'flex' }}>{icon}</Box>
        <Typography
          variant="subtitle2"
          sx={{
            flex: 1,
            color: colors.text.primary,
            fontSize: '0.75rem',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.03em',
          }}
        >
          {title}
        </Typography>
        <IconButton size="small" sx={{ color: colors.text.muted, p: 0.5 }}>
          {open ? <ExpandLess sx={{ fontSize: 18 }} /> : <ExpandMore sx={{ fontSize: 18 }} />}
        </IconButton>
      </Box>
      <Collapse in={open}>
        <Box sx={{ px: 2, pb: 2 }}>{children}</Box>
      </Collapse>
    </Box>
  );
}

// Labeled slider component
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
            color: colors.text.primary,
            fontSize: '0.7rem',
            fontWeight: 500,
            fontFamily: '"SF Mono", monospace',
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
        sx={{
          color: colors.tracks.text.main,
          '& .MuiSlider-thumb': {
            width: 12,
            height: 12,
          },
          '& .MuiSlider-track': {
            height: 4,
          },
          '& .MuiSlider-rail': {
            height: 4,
            bgcolor: colors.bg.darker,
          },
        }}
      />
    </Box>
  );
}

// Input row for paired inputs
function InputRow({ children }: { children: React.ReactNode }) {
  return (
    <Box sx={{ display: 'flex', gap: 1, mb: 1.5 }}>{children}</Box>
  );
}

// Color picker with label
function ColorPicker({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <Box sx={{ flex: 1 }}>
      <Typography variant="caption" sx={{ color: colors.text.secondary, fontSize: '0.65rem', display: 'block', mb: 0.5 }}>
        {label}
      </Typography>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          bgcolor: colors.bg.darker,
          borderRadius: 1,
          p: 0.75,
          border: `1px solid ${colors.border.subtle}`,
        }}
      >
        <Box
          component="input"
          type="color"
          value={value}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => onChange(e.target.value)}
          sx={{
            width: 24,
            height: 24,
            border: 'none',
            borderRadius: 0.5,
            cursor: 'pointer',
            padding: 0,
            '&::-webkit-color-swatch-wrapper': { padding: 0 },
            '&::-webkit-color-swatch': { border: 'none', borderRadius: 4 },
          }}
        />
        <Typography
          variant="caption"
          sx={{
            color: colors.text.secondary,
            fontSize: '0.7rem',
            fontFamily: '"SF Mono", monospace',
            textTransform: 'uppercase',
          }}
        >
          {value}
        </Typography>
      </Box>
    </Box>
  );
}

export function TextProperties({ text }: TextPropertiesProps) {
  const updateText = useEditorStore((state) => state.updateText);
  const handleUpdate = (updates: Partial<TextElement>) => updateText(text.id, updates);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
      {/* Header with text preview */}
      <Box
        sx={{
          p: 2,
          borderBottom: `1px solid ${colors.border.subtle}`,
          background: `linear-gradient(180deg, ${colors.tracks.text.bg} 0%, transparent 100%)`,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
          <Box
            sx={{
              width: 36,
              height: 36,
              borderRadius: 1,
              bgcolor: colors.tracks.text.main,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <TextFields sx={{ fontSize: 20, color: '#fff' }} />
          </Box>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography
              variant="body2"
              sx={{
                color: colors.text.primary,
                fontWeight: 600,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {text.text.substring(0, 20)}{text.text.length > 20 ? '...' : ''}
            </Typography>
            <Typography variant="caption" sx={{ color: colors.text.muted, fontSize: '0.7rem' }}>
              Text Element
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Text Content */}
      <PropertySection title="Content" icon={<TextFields sx={{ fontSize: 16 }} />}>
        <TextField
          multiline
          rows={3}
          value={text.text}
          onChange={(e) => handleUpdate({ text: e.target.value })}
          size="small"
          fullWidth
          placeholder="Enter text..."
          sx={{
            '& .MuiOutlinedInput-root': {
              bgcolor: colors.bg.darker,
              fontSize: '0.85rem',
            },
          }}
        />
      </PropertySection>

      {/* Timeline */}
      <PropertySection title="Timeline" icon={<Schedule sx={{ fontSize: 16 }} />}>
        <InputRow>
          <TextField
            label="Start (s)"
            type="number"
            size="small"
            value={text.positionStart.toFixed(2)}
            onChange={(e) => handleUpdate({ positionStart: parseFloat(e.target.value) || 0 })}
            inputProps={{ step: 0.1, min: 0 }}
            sx={{ flex: 1, '& .MuiOutlinedInput-root': { bgcolor: colors.bg.darker } }}
          />
          <TextField
            label="End (s)"
            type="number"
            size="small"
            value={text.positionEnd.toFixed(2)}
            onChange={(e) => handleUpdate({ positionEnd: parseFloat(e.target.value) || 0 })}
            inputProps={{ step: 0.1, min: 0 }}
            sx={{ flex: 1, '& .MuiOutlinedInput-root': { bgcolor: colors.bg.darker } }}
          />
        </InputRow>
        <Typography variant="caption" sx={{ color: colors.text.muted, fontSize: '0.65rem' }}>
          Duration: {(text.positionEnd - text.positionStart).toFixed(2)}s
        </Typography>
      </PropertySection>

      {/* Font */}
      <PropertySection title="Font" icon={<FontDownload sx={{ fontSize: 16 }} />}>
        <FormControl size="small" fullWidth sx={{ mb: 1.5 }}>
          <InputLabel sx={{ fontSize: '0.8rem' }}>Font Family</InputLabel>
          <Select
            value={text.font}
            label="Font Family"
            onChange={(e: SelectChangeEvent<string>) => handleUpdate({ font: e.target.value })}
            sx={{ bgcolor: colors.bg.darker }}
          >
            <MenuItem value="Arial">Arial</MenuItem>
            <MenuItem value="Helvetica">Helvetica</MenuItem>
            <MenuItem value="Times New Roman">Times New Roman</MenuItem>
            <MenuItem value="Georgia">Georgia</MenuItem>
            <MenuItem value="Verdana">Verdana</MenuItem>
            <MenuItem value="Impact">Impact</MenuItem>
            <MenuItem value="Comic Sans MS">Comic Sans MS</MenuItem>
            <MenuItem value="Courier New">Courier New</MenuItem>
          </Select>
        </FormControl>

        <LabeledSlider
          label="Font Size"
          value={text.fontSize}
          onChange={(v) => handleUpdate({ fontSize: v })}
          min={8}
          max={200}
          unit="px"
        />

        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <Typography variant="caption" sx={{ color: colors.text.secondary, fontSize: '0.7rem', mr: 1 }}>
            Style:
          </Typography>
          <ToggleButtonGroup
            value={[
              text.fontWeight === 'bold' ? 'bold' : null,
              text.fontStyle === 'italic' ? 'italic' : null,
            ].filter(Boolean)}
            onChange={(_, values) =>
              handleUpdate({
                fontWeight: values.includes('bold') ? 'bold' : 'normal',
                fontStyle: values.includes('italic') ? 'italic' : 'normal',
              })
            }
            size="small"
            sx={{
              '& .MuiToggleButton-root': {
                border: `1px solid ${colors.border.default}`,
                color: colors.text.secondary,
                '&.Mui-selected': {
                  bgcolor: colors.tracks.text.bg,
                  color: colors.tracks.text.main,
                  borderColor: colors.tracks.text.border,
                },
              },
            }}
          >
            <ToggleButton value="bold">
              <FormatBold sx={{ fontSize: 18 }} />
            </ToggleButton>
            <ToggleButton value="italic">
              <FormatItalic sx={{ fontSize: 18 }} />
            </ToggleButton>
          </ToggleButtonGroup>

          <Box sx={{ width: 8 }} />

          <ToggleButtonGroup
            value={text.textAlign}
            exclusive
            onChange={(_, value) => value && handleUpdate({ textAlign: value })}
            size="small"
            sx={{
              '& .MuiToggleButton-root': {
                border: `1px solid ${colors.border.default}`,
                color: colors.text.secondary,
                '&.Mui-selected': {
                  bgcolor: colors.tracks.text.bg,
                  color: colors.tracks.text.main,
                  borderColor: colors.tracks.text.border,
                },
              },
            }}
          >
            <ToggleButton value="left">
              <FormatAlignLeft sx={{ fontSize: 18 }} />
            </ToggleButton>
            <ToggleButton value="center">
              <FormatAlignCenter sx={{ fontSize: 18 }} />
            </ToggleButton>
            <ToggleButton value="right">
              <FormatAlignRight sx={{ fontSize: 18 }} />
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
      </PropertySection>

      {/* Colors */}
      <PropertySection title="Colors" icon={<Palette sx={{ fontSize: 16 }} />}>
        <InputRow>
          <ColorPicker
            label="Text Color"
            value={text.color}
            onChange={(value) => handleUpdate({ color: value })}
          />
          <ColorPicker
            label="Background"
            value={text.backgroundColor || '#000000'}
            onChange={(value) => handleUpdate({ backgroundColor: value })}
          />
        </InputRow>
        <LabeledSlider
          label="Opacity"
          value={text.opacity}
          onChange={(v) => handleUpdate({ opacity: v })}
          unit="%"
        />
      </PropertySection>

      {/* Position */}
      <PropertySection title="Position" icon={<OpenWith sx={{ fontSize: 16 }} />}>
        <InputRow>
          <TextField
            label="X"
            type="number"
            size="small"
            value={text.x}
            onChange={(e) => handleUpdate({ x: parseInt(e.target.value) || 0 })}
            inputProps={{ min: 0, max: 1920 }}
            sx={{ flex: 1, '& .MuiOutlinedInput-root': { bgcolor: colors.bg.darker } }}
          />
          <TextField
            label="Y"
            type="number"
            size="small"
            value={text.y}
            onChange={(e) => handleUpdate({ y: parseInt(e.target.value) || 0 })}
            inputProps={{ min: 0, max: 1080 }}
            sx={{ flex: 1, '& .MuiOutlinedInput-root': { bgcolor: colors.bg.darker } }}
          />
        </InputRow>
        <Typography variant="caption" sx={{ color: colors.text.muted, fontSize: '0.65rem' }}>
          Canvas: 1920 x 1080
        </Typography>
      </PropertySection>

      {/* Animation */}
      <PropertySection title="Animation" icon={<Animation sx={{ fontSize: 16 }} />} defaultOpen={text.animation !== 'none'}>
        <FormControl size="small" fullWidth sx={{ mb: 1.5 }}>
          <InputLabel sx={{ fontSize: '0.8rem' }}>Effect</InputLabel>
          <Select
            value={text.animation}
            label="Effect"
            onChange={(e: SelectChangeEvent<TextElement['animation']>) =>
              handleUpdate({ animation: e.target.value as TextElement['animation'] })
            }
            sx={{ bgcolor: colors.bg.darker }}
          >
            <MenuItem value="none">None</MenuItem>
            <MenuItem value="fade-in">Fade In</MenuItem>
            <MenuItem value="slide-up">Slide Up</MenuItem>
            <MenuItem value="slide-left">Slide Left</MenuItem>
            <MenuItem value="zoom">Zoom</MenuItem>
            <MenuItem value="typewriter">Typewriter</MenuItem>
          </Select>
        </FormControl>

        {text.animation !== 'none' && (
          <LabeledSlider
            label="Duration"
            value={text.animationDuration * 10}
            onChange={(v) => handleUpdate({ animationDuration: v / 10 })}
            min={1}
            max={50}
            unit="s"
          />
        )}
      </PropertySection>
    </Box>
  );
}
