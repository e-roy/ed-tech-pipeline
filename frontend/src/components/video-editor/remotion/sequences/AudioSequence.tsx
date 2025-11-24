'use client';

import { Sequence, Audio, AbsoluteFill } from 'remotion';
import { type MediaFile } from '@/stores/editorStore';

interface AudioSequenceProps {
  media: MediaFile;
  fps: number;
}

export function AudioSequence({ media, fps }: AudioSequenceProps) {
  const from = Math.round(media.positionStart * fps);
  const durationInFrames = Math.max(1, Math.round((media.positionEnd - media.positionStart) * fps));

  return (
    <Sequence from={from} durationInFrames={durationInFrames}>
      <AbsoluteFill>
        <Audio
          src={media.src}
          trimBefore={media.startTime}
          playbackRate={media.playbackSpeed}
          volume={media.volume / 100}
        />
      </AbsoluteFill>
    </Sequence>
  );
}
