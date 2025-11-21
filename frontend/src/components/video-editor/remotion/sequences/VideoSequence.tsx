'use client';

import { Sequence, Video, useVideoConfig } from 'remotion';
import { type MediaFile } from '@/stores/editorStore';

interface VideoSequenceProps {
  media: MediaFile;
  fps: number;
}

export function VideoSequence({ media, fps }: VideoSequenceProps) {
  const { width: compWidth, height: compHeight } = useVideoConfig();

  const from = Math.round(media.positionStart * fps);
  const durationInFrames = Math.round((media.positionEnd - media.positionStart) * fps);
  const startFrom = Math.round(media.startTime * fps);
  const endAt = Math.round(media.endTime * fps);

  const videoWidth = media.width || compWidth;
  const videoHeight = media.height || compHeight;
  const x = media.x || 0;
  const y = media.y || 0;
  const opacity = (media.opacity ?? 100) / 100;
  const rotation = media.rotation || 0;

  return (
    <Sequence from={from} durationInFrames={durationInFrames}>
      <Video
        src={media.src}
        startFrom={startFrom}
        endAt={endAt}
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
      />
    </Sequence>
  );
}
