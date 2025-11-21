'use client';

import { Box, Typography, Slider, TextField, Select, MenuItem, FormControl, InputLabel, Divider, SelectChangeEvent } from '@mui/material';
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
        <Select value={media.playbackSpeed} label="Speed" onChange={(e: SelectChangeEvent<number>) => handleUpdate({ playbackSpeed: e.target.value as number })}>
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
