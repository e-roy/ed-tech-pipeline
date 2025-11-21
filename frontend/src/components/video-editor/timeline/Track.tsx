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
