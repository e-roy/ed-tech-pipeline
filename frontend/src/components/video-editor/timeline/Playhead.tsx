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
