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
