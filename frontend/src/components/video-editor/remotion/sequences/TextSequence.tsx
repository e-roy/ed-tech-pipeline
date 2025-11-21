'use client';

import { Sequence, interpolate, useCurrentFrame } from 'remotion';
import { type TextElement } from '@/stores/editorStore';

interface TextSequenceProps {
  text: TextElement;
  fps: number;
}

export function TextSequence({ text, fps }: TextSequenceProps) {
  const frame = useCurrentFrame();

  const from = Math.round(text.positionStart * fps);
  const durationInFrames = Math.round((text.positionEnd - text.positionStart) * fps);
  const animationFrames = Math.round(text.animationDuration * fps);
  const localFrame = frame - from;

  const getAnimationStyle = (): React.CSSProperties & { visibleChars?: number } => {
    switch (text.animation) {
      case 'fade-in': {
        const opacity = interpolate(localFrame, [0, animationFrames], [0, 1], { extrapolateRight: 'clamp' });
        return { opacity: opacity * (text.opacity / 100) };
      }
      case 'slide-up': {
        const translateY = interpolate(localFrame, [0, animationFrames], [50, 0], { extrapolateRight: 'clamp' });
        const opacity = interpolate(localFrame, [0, animationFrames / 2], [0, 1], { extrapolateRight: 'clamp' });
        return { transform: `translateY(${translateY}px)`, opacity: opacity * (text.opacity / 100) };
      }
      case 'slide-left': {
        const translateX = interpolate(localFrame, [0, animationFrames], [100, 0], { extrapolateRight: 'clamp' });
        const opacity = interpolate(localFrame, [0, animationFrames / 2], [0, 1], { extrapolateRight: 'clamp' });
        return { transform: `translateX(${translateX}px)`, opacity: opacity * (text.opacity / 100) };
      }
      case 'zoom': {
        const scale = interpolate(localFrame, [0, animationFrames], [0.5, 1], { extrapolateRight: 'clamp' });
        const opacity = interpolate(localFrame, [0, animationFrames / 2], [0, 1], { extrapolateRight: 'clamp' });
        return { transform: `scale(${scale})`, opacity: opacity * (text.opacity / 100) };
      }
      case 'typewriter': {
        const progress = interpolate(localFrame, [0, animationFrames], [0, 1], { extrapolateRight: 'clamp' });
        return { visibleChars: Math.floor(text.text.length * progress) };
      }
      default:
        return { opacity: text.opacity / 100 };
    }
  };

  const animationStyle = getAnimationStyle();
  const displayText = 'visibleChars' in animationStyle
    ? text.text.substring(0, animationStyle.visibleChars)
    : text.text;

  // Remove visibleChars from style object
  const { visibleChars, ...styleProps } = animationStyle as React.CSSProperties & { visibleChars?: number };

  return (
    <Sequence from={from} durationInFrames={durationInFrames}>
      <div
        style={{
          position: 'absolute',
          left: text.x,
          top: text.y,
          width: text.width || 'auto',
          height: text.height || 'auto',
          fontFamily: text.font,
          fontSize: text.fontSize,
          fontWeight: text.fontWeight,
          fontStyle: text.fontStyle,
          color: text.color,
          backgroundColor: text.backgroundColor || 'transparent',
          textAlign: text.textAlign,
          opacity: text.opacity / 100,
          transform: text.rotation ? `rotate(${text.rotation}deg)` : undefined,
          zIndex: text.zIndex,
          ...styleProps,
        }}
      >
        {displayText}
      </div>
    </Sequence>
  );
}
