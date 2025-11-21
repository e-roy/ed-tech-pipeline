'use client';

import { useRef, useEffect } from 'react';
import { Player, PlayerRef } from '@remotion/player';
import { Box } from '@mui/material';
import { useEditorStore } from '@/stores/editorStore';
import { EditorComposition } from './remotion/Composition';

export function PreviewPlayer() {
  const playerRef = useRef<PlayerRef>(null);

  const duration = useEditorStore((state) => state.duration);
  const currentTime = useEditorStore((state) => state.currentTime);
  const isPlaying = useEditorStore((state) => state.isPlaying);
  const isMuted = useEditorStore((state) => state.isMuted);
  const volume = useEditorStore((state) => state.volume);
  const playbackRate = useEditorStore((state) => state.playbackRate);
  const inPoint = useEditorStore((state) => state.inPoint);
  const outPoint = useEditorStore((state) => state.outPoint);
  const setIsPlaying = useEditorStore((state) => state.setIsPlaying);

  const fps = 30;
  const durationInFrames = Math.max(1, Math.floor(duration * fps) + 1);

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
    <Box sx={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Box sx={{ width: '100%', maxWidth: '100%', aspectRatio: '16/9' }}>
        <Player
          ref={playerRef}
          component={EditorComposition}
          durationInFrames={durationInFrames}
          compositionWidth={1920}
          compositionHeight={1080}
          fps={fps}
          style={{ width: '100%', height: '100%' }}
          controls={false}
          clickToPlay={false}
          acknowledgeRemotionLicense
          playbackRate={playbackRate}
          volume={isMuted ? 0 : volume / 100}
        />
      </Box>
    </Box>
  );
}
