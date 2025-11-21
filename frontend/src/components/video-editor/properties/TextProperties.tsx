'use client';

import { Box, Typography, TextField, Slider, Select, MenuItem, FormControl, InputLabel, ToggleButtonGroup, ToggleButton, Divider, SelectChangeEvent } from '@mui/material';
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
        <Select value={text.font} label="Font Family" onChange={(e: SelectChangeEvent<string>) => handleUpdate({ font: e.target.value })}>
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
        <Select value={text.animation} label="Animation" onChange={(e: SelectChangeEvent<TextElement['animation']>) => handleUpdate({ animation: e.target.value as TextElement['animation'] })}>
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
