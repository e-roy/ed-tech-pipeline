'use client';

import { Sequence, Img, useVideoConfig } from 'remotion';
import { type MediaFile } from '@/stores/editorStore';

interface ImageSequenceProps {
  media: MediaFile;
  fps: number;
}

export function ImageSequence({ media, fps }: ImageSequenceProps) {
  const { width: compWidth, height: compHeight } = useVideoConfig();

  const from = Math.round(media.positionStart * fps);
  const durationInFrames = Math.max(1, Math.round((media.positionEnd - media.positionStart) * fps));

  const imageWidth = media.width || compWidth;
  const imageHeight = media.height || compHeight;
  const x = media.x || 0;
  const y = media.y || 0;
  const opacity = (media.opacity ?? 100) / 100;
  const rotation = media.rotation || 0;

  return (
    <Sequence from={from} durationInFrames={durationInFrames}>
      <Img
        src={media.src}
        style={{
          position: 'absolute',
          left: x,
          top: y,
          width: imageWidth,
          height: imageHeight,
          opacity,
          transform: rotation ? `rotate(${rotation}deg)` : undefined,
          objectFit: 'contain',
        }}
      />
    </Sequence>
  );
}
