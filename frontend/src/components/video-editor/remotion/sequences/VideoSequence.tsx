'use client';

import { Sequence, OffthreadVideo, useVideoConfig } from 'remotion';
import { type MediaFile } from '@/stores/editorStore';

interface VideoSequenceProps {
  media: MediaFile;
  fps: number;
}

export function VideoSequence({ media, fps }: VideoSequenceProps) {
  const { width: compWidth, height: compHeight } = useVideoConfig();

  const from = Math.round(media.positionStart * fps);
  const durationInFrames = Math.max(1, Math.round((media.positionEnd - media.positionStart) * fps));

  const videoWidth = media.width || compWidth;
  const videoHeight = media.height || compHeight;
  const x = media.x || 0;
  const y = media.y || 0;
  const opacity = (media.opacity ?? 100) / 100;
  const rotation = media.rotation || 0;

  // Use trimBefore to skip to startTime in the source video
  const trimBefore = media.startTime;

  return (
    <Sequence from={from} durationInFrames={durationInFrames}>
      <OffthreadVideo
        src={media.src}
        transparent={false}
        trimBefore={trimBefore}
        playbackRate={media.playbackSpeed}
        volume={media.volume / 100}
        style={{
          position: 'absolute',
          left: x,
          top: y,
          width: videoWidth,
          height: videoHeight,
          opacity,
          transform: rotation ? `rotate(${rotation}deg)` : undefined,
          objectFit: 'contain',
        }}
        onError={(error) => {
          console.error('[VideoSequence] Video playback error:', error);
        }}
      />
    </Sequence>
  );
}
