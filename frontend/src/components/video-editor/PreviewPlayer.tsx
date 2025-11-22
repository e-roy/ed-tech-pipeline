'use client';

import { useRef, useEffect, useState } from 'react';
import { Player, type PlayerRef } from '@remotion/player';
import { Box, Typography, CircularProgress } from '@mui/material';
import { Videocam } from '@mui/icons-material';
import { useEditorStore } from '@/stores/editorStore';
import { EditorComposition } from './remotion/Composition';
import { colors } from './theme';

export function PreviewPlayer() {
  const playerRef = useRef<PlayerRef>(null);
  const [isLoading, setIsLoading] = useState(true);

  const duration = useEditorStore((state) => state.duration);
  const currentTime = useEditorStore((state) => state.currentTime);
  const isPlaying = useEditorStore((state) => state.isPlaying);
  const isMuted = useEditorStore((state) => state.isMuted);
  const volume = useEditorStore((state) => state.volume);
  const playbackRate = useEditorStore((state) => state.playbackRate);
  const inPoint = useEditorStore((state) => state.inPoint);
  const outPoint = useEditorStore((state) => state.outPoint);
  const setIsPlaying = useEditorStore((state) => state.setIsPlaying);
  const mediaFiles = useEditorStore((state) => state.mediaFiles);

  const fps = 30;
  const durationInFrames = Math.max(1, Math.floor(duration * fps) + 1);

  // Check if there's any media to show
  const hasMedia = mediaFiles.length > 0;

  // Simulate loading complete after initial render
  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 500);
    return () => clearTimeout(timer);
  }, []);

  // Sync volume to player
  useEffect(() => {
    if (!playerRef.current) return;
    if (isMuted) {
      playerRef.current.mute();
    } else {
      playerRef.current.unmute();
      playerRef.current.setVolume(volume / 100);
    }
  }, [isMuted, volume]);

  // Sync store time to player when not playing
  useEffect(() => {
    if (!playerRef.current || isPlaying) return;
    const frame = Math.round(currentTime * fps);
    playerRef.current.seekTo(frame);
  }, [currentTime, fps, isPlaying]);

  // Control playback
  useEffect(() => {
    if (!playerRef.current) return;
    if (isPlaying) {
      if (inPoint !== null && currentTime < inPoint) {
        playerRef.current.seekTo(Math.round(inPoint * fps));
      }
      playerRef.current.play();
    } else {
      playerRef.current.pause();
    }
  }, [isPlaying, inPoint, currentTime, fps]);

  // Monitor out-point
  useEffect(() => {
    if (!isPlaying || outPoint === null || !playerRef.current) return;
    const checkOutPoint = () => {
      if (playerRef.current) {
        const currentFrame = playerRef.current.getCurrentFrame();
        const currentSeconds = currentFrame / fps;
        if (currentSeconds >= outPoint) {
          playerRef.current.pause();
          playerRef.current.seekTo(Math.round(outPoint * fps));
          setIsPlaying(false);
        }
      }
    };
    const intervalId = setInterval(checkOutPoint, 100);
    return () => clearInterval(intervalId);
  }, [isPlaying, outPoint, fps, setIsPlaying]);

  return (
    <Box
      sx={{
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: colors.bg.darkest,
        // Checkerboard pattern for transparent areas
        backgroundImage: `
          linear-gradient(45deg, ${colors.bg.darker} 25%, transparent 25%),
          linear-gradient(-45deg, ${colors.bg.darker} 25%, transparent 25%),
          linear-gradient(45deg, transparent 75%, ${colors.bg.darker} 75%),
          linear-gradient(-45deg, transparent 75%, ${colors.bg.darker} 75%)
        `,
        backgroundSize: '20px 20px',
        backgroundPosition: '0 0, 0 10px, 10px -10px, -10px 0px',
        p: 2,
      }}
    >
      {/* Player frame */}
      <Box
        sx={{
          position: 'relative',
          width: '100%',
          maxWidth: '100%',
          aspectRatio: '16/9',
          bgcolor: colors.bg.darkest,
          borderRadius: 2,
          overflow: 'hidden',
          boxShadow: `
            0 0 0 1px ${colors.border.default},
            0 4px 20px rgba(0, 0, 0, 0.5),
            0 0 60px rgba(0, 0, 0, 0.3)
          `,
          // Inner glow effect
          '&::before': {
            content: '""',
            position: 'absolute',
            inset: 0,
            borderRadius: 2,
            padding: '1px',
            background: `linear-gradient(180deg, ${colors.border.strong} 0%, transparent 50%)`,
            mask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
            maskComposite: 'exclude',
            pointerEvents: 'none',
            zIndex: 2,
          },
        }}
      >
        {/* Loading overlay */}
        {isLoading && (
          <Box
            sx={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              bgcolor: colors.bg.darkest,
              zIndex: 3,
            }}
          >
            <CircularProgress
              size={48}
              sx={{
                color: colors.primary.main,
                mb: 2,
              }}
            />
            <Typography
              variant="body2"
              sx={{ color: colors.text.secondary }}
            >
              Loading preview...
            </Typography>
          </Box>
        )}

        {/* Empty state overlay */}
        {!hasMedia && !isLoading && (
          <Box
            sx={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              bgcolor: colors.bg.darkest,
              zIndex: 1,
            }}
          >
            <Box
              sx={{
                width: 80,
                height: 80,
                borderRadius: '50%',
                bgcolor: colors.bg.elevated,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mb: 2,
                border: `1px solid ${colors.border.subtle}`,
              }}
            >
              <Videocam sx={{ fontSize: 40, color: colors.text.muted, opacity: 0.5 }} />
            </Box>
            <Typography
              variant="body1"
              sx={{ color: colors.text.secondary, mb: 0.5 }}
            >
              No media in timeline
            </Typography>
            <Typography
              variant="caption"
              sx={{ color: colors.text.muted }}
            >
              Add clips from the Media Bin to get started
            </Typography>
          </Box>
        )}

        {/* Player */}
        <Player
          ref={playerRef}
          component={EditorComposition}
          durationInFrames={durationInFrames}
          compositionWidth={1920}
          compositionHeight={1080}
          fps={fps}
          style={{
            width: '100%',
            height: '100%',
            opacity: isLoading ? 0 : 1,
            transition: 'opacity 0.3s ease',
          }}
          controls={false}
          clickToPlay={false}
          acknowledgeRemotionLicense
          playbackRate={playbackRate}
        />

        {/* Safe area guides (optional visual) */}
        <Box
          sx={{
            position: 'absolute',
            inset: '5%',
            border: `1px dashed ${colors.border.subtle}`,
            borderRadius: 1,
            pointerEvents: 'none',
            opacity: 0,
            transition: 'opacity 0.2s ease',
            '.preview-container:hover &': {
              opacity: 0.3,
            },
          }}
        />

        {/* Corner markers for frame */}
        {['top-left', 'top-right', 'bottom-left', 'bottom-right'].map((corner) => (
          <Box
            key={corner}
            sx={{
              position: 'absolute',
              width: 16,
              height: 16,
              borderColor: colors.primary.main,
              borderStyle: 'solid',
              borderWidth: 0,
              opacity: 0.5,
              ...(corner === 'top-left' && { top: 8, left: 8, borderTopWidth: 2, borderLeftWidth: 2 }),
              ...(corner === 'top-right' && { top: 8, right: 8, borderTopWidth: 2, borderRightWidth: 2 }),
              ...(corner === 'bottom-left' && { bottom: 8, left: 8, borderBottomWidth: 2, borderLeftWidth: 2 }),
              ...(corner === 'bottom-right' && { bottom: 8, right: 8, borderBottomWidth: 2, borderRightWidth: 2 }),
            }}
          />
        ))}
      </Box>
    </Box>
  );
}
