'use client';

import { useRef, useCallback, useEffect } from 'react';
import { Box, IconButton, Tooltip, Typography } from '@mui/material';
import { Add, Lock, LockOpen, Visibility, VisibilityOff, VolumeUp, VolumeOff, Videocam, MusicNote, TextFields } from '@mui/icons-material';
import { useEditorStore } from '@/stores/editorStore';
import { colors } from './theme';
import { TimeRuler } from './timeline/TimeRuler';
import { Playhead } from './timeline/Playhead';
import { Track } from './timeline/Track';

// Track type icon component
function TrackIcon({ type }: { type: 'video' | 'audio' | 'text' }) {
  const iconSx = { fontSize: 14 };
  switch (type) {
    case 'video':
      return <Videocam sx={{ ...iconSx, color: colors.tracks.video.main }} />;
    case 'audio':
      return <MusicNote sx={{ ...iconSx, color: colors.tracks.audio.main }} />;
    case 'text':
      return <TextFields sx={{ ...iconSx, color: colors.tracks.text.main }} />;
  }
}

export function Timeline() {
  const containerRef = useRef<HTMLDivElement>(null);
  const duration = useEditorStore((state) => state.duration);
  const timelineZoom = useEditorStore((state) => state.timelineZoom);
  const timelineScroll = useEditorStore((state) => state.timelineScroll);
  const currentTime = useEditorStore((state) => state.currentTime);
  const tracks = useEditorStore((state) => state.tracks);
  const setCurrentTime = useEditorStore((state) => state.setCurrentTime);
  const setTimelineScroll = useEditorStore((state) => state.setTimelineScroll);
  const setTimelineZoom = useEditorStore((state) => state.setTimelineZoom);
  const addTrack = useEditorStore((state) => state.addTrack);
  const updateTrack = useEditorStore((state) => state.updateTrack);

  const timelineWidth = Math.max(duration * timelineZoom, 1000);
  const trackHeaderWidth = 180;

  // Mouse wheel zoom handler (Ctrl/Cmd + scroll)
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleWheel = (e: WheelEvent) => {
      // Only zoom when Ctrl (Windows/Linux) or Meta (Mac) is pressed
      if (!e.ctrlKey && !e.metaKey) return;

      e.preventDefault();

      // Get cursor position relative to timeline content
      const rect = container.getBoundingClientRect();
      const cursorX = e.clientX - rect.left + container.scrollLeft - trackHeaderWidth;
      const cursorTime = cursorX / timelineZoom;

      // Calculate new zoom (zoom in on scroll up, out on scroll down)
      const zoomFactor = e.deltaY < 0 ? 1.15 : 1 / 1.15;
      const newZoom = Math.max(10, Math.min(500, timelineZoom * zoomFactor));

      // Calculate new scroll position to keep cursor position stable
      const newCursorX = cursorTime * newZoom;
      const newScrollLeft = newCursorX - (e.clientX - rect.left) + trackHeaderWidth;

      setTimelineZoom(newZoom);
      setTimelineScroll(Math.max(0, newScrollLeft));
      container.scrollLeft = Math.max(0, newScrollLeft);
    };

    container.addEventListener('wheel', handleWheel, { passive: false });
    return () => container.removeEventListener('wheel', handleWheel);
  }, [timelineZoom, setTimelineZoom, setTimelineScroll, trackHeaderWidth]);

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

  const getTrackColor = (type: 'video' | 'audio' | 'text') => {
    return colors.tracks[type];
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        bgcolor: colors.bg.dark,
      }}
    >
      {/* Header with Time Ruler */}
      <Box
        sx={{
          display: 'flex',
          bgcolor: colors.bg.paper,
          borderBottom: `1px solid ${colors.border.subtle}`,
        }}
      >
        <Box
          sx={{
            width: trackHeaderWidth,
            flexShrink: 0,
            borderRight: `1px solid ${colors.border.subtle}`,
            display: 'flex',
            alignItems: 'center',
            px: 1.5,
          }}
        >
          <Typography
            variant="caption"
            sx={{
              color: colors.text.muted,
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              fontSize: '0.65rem',
            }}
          >
            Tracks
          </Typography>
        </Box>
        <Box sx={{ flex: 1, overflow: 'hidden' }}>
          <TimeRuler duration={duration} zoom={timelineZoom} scrollLeft={timelineScroll} />
        </Box>
      </Box>

      {/* Tracks */}
      <Box
        ref={containerRef}
        sx={{
          flex: 1,
          display: 'flex',
          overflow: 'auto',
          '&::-webkit-scrollbar': {
            height: 8,
            width: 8,
          },
          '&::-webkit-scrollbar-track': {
            background: colors.bg.darker,
          },
          '&::-webkit-scrollbar-thumb': {
            background: colors.border.strong,
            borderRadius: 4,
            '&:hover': {
              background: colors.text.muted,
            },
          },
        }}
        onScroll={handleScroll}
        onClick={handleTimelineClick}
      >
        {/* Track Headers */}
        <Box
          sx={{
            width: trackHeaderWidth,
            flexShrink: 0,
            bgcolor: colors.bg.paper,
            borderRight: `1px solid ${colors.border.subtle}`,
            position: 'sticky',
            left: 0,
            zIndex: 2,
          }}
        >
          {tracks.map((track) => {
            const trackColor = getTrackColor(track.type);
            return (
              <Box
                key={track.id}
                sx={{
                  height: track.height,
                  display: 'flex',
                  alignItems: 'center',
                  px: 1,
                  borderBottom: `1px solid ${colors.border.subtle}`,
                  gap: 1,
                  transition: 'all 0.15s ease',
                  '&:hover': {
                    bgcolor: colors.bg.hover,
                  },
                }}
              >
                {/* Track type indicator */}
                <Box
                  sx={{
                    width: 3,
                    height: '60%',
                    borderRadius: 1,
                    bgcolor: trackColor.main,
                  }}
                />

                {/* Track icon and name */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, flex: 1, minWidth: 0 }}>
                  <TrackIcon type={track.type} />
                  <Typography
                    variant="caption"
                    sx={{
                      flex: 1,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      fontWeight: 500,
                      color: colors.text.primary,
                      fontSize: '0.75rem',
                    }}
                  >
                    {track.name}
                  </Typography>
                </Box>

                {/* Track controls */}
                <Box sx={{ display: 'flex', gap: 0.25 }}>
                  <Tooltip title={track.muted ? 'Unmute' : 'Mute'} arrow>
                    <IconButton
                      size="small"
                      onClick={(e) => { e.stopPropagation(); updateTrack(track.id, { muted: !track.muted }); }}
                      sx={{
                        p: 0.5,
                        color: track.muted ? colors.warning : colors.text.muted,
                        '&:hover': { color: colors.text.primary, bgcolor: colors.bg.hover },
                      }}
                    >
                      {track.muted ? <VolumeOff sx={{ fontSize: 14 }} /> : <VolumeUp sx={{ fontSize: 14 }} />}
                    </IconButton>
                  </Tooltip>
                  <Tooltip title={track.locked ? 'Unlock' : 'Lock'} arrow>
                    <IconButton
                      size="small"
                      onClick={(e) => { e.stopPropagation(); updateTrack(track.id, { locked: !track.locked }); }}
                      sx={{
                        p: 0.5,
                        color: track.locked ? colors.error : colors.text.muted,
                        '&:hover': { color: colors.text.primary, bgcolor: colors.bg.hover },
                      }}
                    >
                      {track.locked ? <Lock sx={{ fontSize: 14 }} /> : <LockOpen sx={{ fontSize: 14 }} />}
                    </IconButton>
                  </Tooltip>
                  <Tooltip title={track.visible ? 'Hide' : 'Show'} arrow>
                    <IconButton
                      size="small"
                      onClick={(e) => { e.stopPropagation(); updateTrack(track.id, { visible: !track.visible }); }}
                      sx={{
                        p: 0.5,
                        color: !track.visible ? colors.text.muted : colors.text.secondary,
                        opacity: track.visible ? 1 : 0.5,
                        '&:hover': { color: colors.text.primary, bgcolor: colors.bg.hover },
                      }}
                    >
                      {track.visible ? <Visibility sx={{ fontSize: 14 }} /> : <VisibilityOff sx={{ fontSize: 14 }} />}
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>
            );
          })}

          {/* Add track button */}
          <Box
            sx={{
              p: 1,
              display: 'flex',
              gap: 0.5,
              borderBottom: `1px solid ${colors.border.subtle}`,
            }}
          >
            <Tooltip title="Add Video Track" arrow>
              <IconButton
                size="small"
                onClick={() => addTrack('video')}
                sx={{
                  p: 0.5,
                  color: colors.tracks.video.main,
                  '&:hover': { bgcolor: colors.tracks.video.bg },
                }}
              >
                <Add sx={{ fontSize: 16 }} />
              </IconButton>
            </Tooltip>
            <Tooltip title="Add Audio Track" arrow>
              <IconButton
                size="small"
                onClick={() => addTrack('audio')}
                sx={{
                  p: 0.5,
                  color: colors.tracks.audio.main,
                  '&:hover': { bgcolor: colors.tracks.audio.bg },
                }}
              >
                <Add sx={{ fontSize: 16 }} />
              </IconButton>
            </Tooltip>
            <Tooltip title="Add Text Track" arrow>
              <IconButton
                size="small"
                onClick={() => addTrack('text')}
                sx={{
                  p: 0.5,
                  color: colors.tracks.text.main,
                  '&:hover': { bgcolor: colors.tracks.text.bg },
                }}
              >
                <Add sx={{ fontSize: 16 }} />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Track Content */}
        <Box
          sx={{
            position: 'relative',
            width: timelineWidth,
            minHeight: '100%',
            bgcolor: colors.bg.darker,
            backgroundImage: `
              linear-gradient(90deg, ${colors.border.subtle} 1px, transparent 1px),
              linear-gradient(${colors.border.subtle} 1px, transparent 1px)
            `,
            backgroundSize: `${timelineZoom * 1}px 100%, 100% 50px`,
          }}
        >
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
