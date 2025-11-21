'use client';

import { useRef, useCallback } from 'react';
import { Box, IconButton, Tooltip, Typography } from '@mui/material';
import { Add, Lock, LockOpen, Visibility, VisibilityOff, VolumeUp, VolumeOff } from '@mui/icons-material';
import { useEditorStore } from '@/stores/editorStore';
import { TimeRuler } from './timeline/TimeRuler';
import { Playhead } from './timeline/Playhead';
import { Track } from './timeline/Track';

export function Timeline() {
  const containerRef = useRef<HTMLDivElement>(null);
  const duration = useEditorStore((state) => state.duration);
  const timelineZoom = useEditorStore((state) => state.timelineZoom);
  const timelineScroll = useEditorStore((state) => state.timelineScroll);
  const currentTime = useEditorStore((state) => state.currentTime);
  const tracks = useEditorStore((state) => state.tracks);
  const setCurrentTime = useEditorStore((state) => state.setCurrentTime);
  const setTimelineScroll = useEditorStore((state) => state.setTimelineScroll);
  const addTrack = useEditorStore((state) => state.addTrack);
  const updateTrack = useEditorStore((state) => state.updateTrack);

  const timelineWidth = Math.max(duration * timelineZoom, 1000);
  const trackHeaderWidth = 150;

  const handleTimelineClick = useCallback((e: React.MouseEvent) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const scrollLeft = containerRef.current.scrollLeft;
    const x = e.clientX - rect.left + scrollLeft - trackHeaderWidth;
    if (x >= 0) {
      const time = x / timelineZoom;
      setCurrentTime(Math.max(0, Math.min(time, duration)));
    }
  }, [timelineZoom, duration, setCurrentTime, trackHeaderWidth]);

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setTimelineScroll(e.currentTarget.scrollLeft);
  }, [setTimelineScroll]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header with Time Ruler */}
      <Box sx={{ display: 'flex', bgcolor: 'background.paper', borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ width: trackHeaderWidth, flexShrink: 0, borderRight: 1, borderColor: 'divider' }}>
          <Box sx={{ height: 24 }} />
        </Box>
        <Box sx={{ flex: 1, overflow: 'hidden' }}>
          <TimeRuler duration={duration} zoom={timelineZoom} scrollLeft={timelineScroll} />
        </Box>
      </Box>

      {/* Tracks */}
      <Box ref={containerRef} sx={{ flex: 1, display: 'flex', overflow: 'auto' }} onScroll={handleScroll} onClick={handleTimelineClick}>
        {/* Track Headers */}
        <Box sx={{ width: trackHeaderWidth, flexShrink: 0, bgcolor: 'background.paper', borderRight: 1, borderColor: 'divider', position: 'sticky', left: 0, zIndex: 2 }}>
          {tracks.map((track) => (
            <Box key={track.id} sx={{ height: track.height, display: 'flex', alignItems: 'center', px: 1, borderBottom: 1, borderColor: 'divider', gap: 0.5 }}>
              <Typography variant="caption" sx={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>{track.name}</Typography>
              <Tooltip title={track.muted ? 'Unmute' : 'Mute'}>
                <IconButton size="small" onClick={(e) => { e.stopPropagation(); updateTrack(track.id, { muted: !track.muted }); }} sx={{ p: 0.25 }}>
                  {track.muted ? <VolumeOff sx={{ fontSize: 14 }} /> : <VolumeUp sx={{ fontSize: 14 }} />}
                </IconButton>
              </Tooltip>
              <Tooltip title={track.locked ? 'Unlock' : 'Lock'}>
                <IconButton size="small" onClick={(e) => { e.stopPropagation(); updateTrack(track.id, { locked: !track.locked }); }} sx={{ p: 0.25 }}>
                  {track.locked ? <Lock sx={{ fontSize: 14 }} /> : <LockOpen sx={{ fontSize: 14 }} />}
                </IconButton>
              </Tooltip>
              <Tooltip title={track.visible ? 'Hide' : 'Show'}>
                <IconButton size="small" onClick={(e) => { e.stopPropagation(); updateTrack(track.id, { visible: !track.visible }); }} sx={{ p: 0.25 }}>
                  {track.visible ? <Visibility sx={{ fontSize: 14 }} /> : <VisibilityOff sx={{ fontSize: 14 }} />}
                </IconButton>
              </Tooltip>
            </Box>
          ))}
          <Box sx={{ p: 1 }}>
            <Tooltip title="Add Video Track"><IconButton size="small" onClick={() => addTrack('video')}><Add sx={{ fontSize: 14 }} /></IconButton></Tooltip>
          </Box>
        </Box>

        {/* Track Content */}
        <Box sx={{ position: 'relative', width: timelineWidth, minHeight: '100%' }}>
          <Playhead currentTime={currentTime} zoom={timelineZoom} />
          {tracks.map((track, index) => {
            const top = tracks.slice(0, index).reduce((sum, t) => sum + t.height, 0);
            return <Track key={track.id} track={track} top={top} zoom={timelineZoom} />;
          })}
        </Box>
      </Box>
    </Box>
  );
}
