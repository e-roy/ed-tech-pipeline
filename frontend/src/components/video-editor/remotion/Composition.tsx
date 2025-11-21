'use client';

import { useCurrentFrame, AbsoluteFill } from 'remotion';
import { useEditorStore } from '@/stores/editorStore';
import { VideoSequence } from './sequences/VideoSequence';
import { AudioSequence } from './sequences/AudioSequence';
import { ImageSequence } from './sequences/ImageSequence';
import { TextSequence } from './sequences/TextSequence';
import { useEffect, useRef } from 'react';

export const EditorComposition = () => {
  const frame = useCurrentFrame();
  const fps = useEditorStore((state) => state.fps);
  const mediaFiles = useEditorStore((state) => state.mediaFiles);
  const textElements = useEditorStore((state) => state.textElements);
  const setCurrentTime = useEditorStore((state) => state.setCurrentTime);
  const isPlaying = useEditorStore((state) => state.isPlaying);

  const lastDispatchedTime = useRef(0);

  useEffect(() => {
    if (!isPlaying) return;
    const currentTimeInSeconds = frame / fps;
    if (Math.abs(currentTimeInSeconds - lastDispatchedTime.current) > 0.05) {
      setCurrentTime(currentTimeInSeconds);
      lastDispatchedTime.current = currentTimeInSeconds;
    }
  }, [frame, fps, setCurrentTime, isPlaying]);

  const sortedMedia = [...mediaFiles].sort((a, b) => a.zIndex - b.zIndex);

  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      {sortedMedia.map((media) => {
        switch (media.type) {
          case 'video': return <VideoSequence key={media.id} media={media} fps={fps} />;
          case 'audio': return <AudioSequence key={media.id} media={media} fps={fps} />;
          case 'image': return <ImageSequence key={media.id} media={media} fps={fps} />;
          default: return null;
        }
      })}
      {textElements.map((text) => (
        <TextSequence key={text.id} text={text} fps={fps} />
      ))}
    </AbsoluteFill>
  );
};
