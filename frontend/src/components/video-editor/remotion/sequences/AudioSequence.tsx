'use client';

import { Sequence, Audio, AbsoluteFill } from 'remotion';
import { type MediaFile } from '@/stores/editorStore';

interface AudioSequenceProps {
  media: MediaFile;
  fps: number;
}

export function AudioSequence({ media, fps }: AudioSequenceProps) {
  const from = Math.round(media.positionStart * fps);
  const durationInFrames = Math.round((media.positionEnd - media.positionStart) * fps);
  const startFrom = Math.round(media.startTime * fps);
  const endAt = Math.round(media.endTime * fps);

  return (
    <Sequence from={from} durationInFrames={durationInFrames}>
      <AbsoluteFill>
        <Audio
          src={media.src}
          startFrom={startFrom}
          endAt={endAt}
          playbackRate={media.playbackSpeed}
          volume={media.volume / 100}
        />
      </AbsoluteFill>
    </Sequence>
  );
}
