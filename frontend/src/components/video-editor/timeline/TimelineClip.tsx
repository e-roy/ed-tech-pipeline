'use client';

import { useRef, useState, useCallback, useMemo } from 'react';
import { Box, Typography } from '@mui/material';
import { Videocam, MusicNote, TextFields } from '@mui/icons-material';
import Moveable from 'react-moveable';
import { throttle } from 'lodash';
import { useEditorStore, type MediaFile, type TextElement } from '@/stores/editorStore';
import { colors } from '../theme';

interface TimelineClipProps {
  item: MediaFile | TextElement;
  trackType: 'video' | 'audio' | 'text';
  zoom: number;
  trackHeight: number;
}

export function TimelineClip({ item, trackType, zoom, trackHeight }: TimelineClipProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);

  const selectedIds = useEditorStore((state) => state.selectedIds);
  const updateMedia = useEditorStore((state) => state.updateMedia);
  const updateText = useEditorStore((state) => state.updateText);
  const select = useEditorStore((state) => state.select);
  const addToSelection = useEditorStore((state) => state.addToSelection);

  const isSelected = selectedIds.includes(item.id);
  const isMedia = 'type' in item && ['video', 'audio', 'image'].includes((item as MediaFile).type);

  const left = item.positionStart * zoom;
  const width = (item.positionEnd - item.positionStart) * zoom;

  const handleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    if (e.shiftKey || e.ctrlKey || e.metaKey) {
      addToSelection(item.id);
    } else {
      select([item.id]);
    }
  }, [item.id, select, addToSelection]);

  const handleDrag = useMemo(
    () => throttle((e: { left: number }) => {
      const newPositionStart = Math.max(0, e.left / zoom);
      const duration = item.positionEnd - item.positionStart;
      const newPositionEnd = newPositionStart + duration;
      if (isMedia) {
        updateMedia(item.id, { positionStart: newPositionStart, positionEnd: newPositionEnd });
      } else {
        updateText(item.id, { positionStart: newPositionStart, positionEnd: newPositionEnd });
      }
    }, 16),
    [item.id, item.positionEnd, item.positionStart, zoom, isMedia, updateMedia, updateText]
  );

  const handleResize = useMemo(
    () => throttle((e: { width: number; direction: number[] }) => {
      const newWidth = e.width / zoom;
      const direction = e.direction[0];
      if (direction === -1) {
        const newPositionStart = item.positionEnd - newWidth;
        if (newPositionStart >= 0) {
          if (isMedia) {
            const media = item as MediaFile;
            const trimAmount = item.positionStart - newPositionStart;
            updateMedia(item.id, { positionStart: newPositionStart, startTime: Math.max(0, media.startTime - trimAmount) });
          } else {
            updateText(item.id, { positionStart: newPositionStart });
          }
        }
      } else {
        const newPositionEnd = item.positionStart + newWidth;
        if (isMedia) {
          const media = item as MediaFile;
          const maxEnd = media.positionStart + (media.duration - media.startTime);
          updateMedia(item.id, { positionEnd: Math.min(newPositionEnd, maxEnd), endTime: Math.min(media.startTime + newWidth, media.duration) });
        } else {
          updateText(item.id, { positionEnd: newPositionEnd });
        }
      }
    }, 16),
    [item, zoom, isMedia, updateMedia, updateText]
  );

  const trackColors = colors.tracks[trackType];

  const getClipLabel = () => {
    if (isMedia) return (item as MediaFile).fileName;
    const textItem = item as TextElement;
    return textItem.text.substring(0, 20) + (textItem.text.length > 20 ? '...' : '');
  };

  const ClipIcon = () => {
    const sx = { fontSize: 12, opacity: 0.8 };
    switch (trackType) {
      case 'video': return <Videocam sx={sx} />;
      case 'audio': return <MusicNote sx={sx} />;
      case 'text': return <TextFields sx={sx} />;
    }
  };

  return (
    <>
      <Box
        ref={ref}
        onClick={handleClick}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        sx={{
          position: 'absolute',
          left,
          top: 4,
          width,
          height: trackHeight - 8,
          background: isSelected
            ? `linear-gradient(135deg, ${trackColors.main} 0%, ${trackColors.main}dd 100%)`
            : `linear-gradient(135deg, ${trackColors.main}cc 0%, ${trackColors.main}99 100%)`,
          borderRadius: 1.5,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 0.5,
          px: 1,
          overflow: 'hidden',
          border: isSelected
            ? `2px solid ${colors.text.primary}`
            : `1px solid ${trackColors.border}`,
          boxShadow: isSelected
            ? `0 0 12px ${trackColors.main}80, inset 0 1px 0 rgba(255,255,255,0.2)`
            : isHovered
            ? `0 2px 8px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)`
            : `inset 0 1px 0 rgba(255,255,255,0.1)`,
          transition: 'all 0.15s ease',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '50%',
            background: 'linear-gradient(180deg, rgba(255,255,255,0.1) 0%, transparent 100%)',
            borderRadius: '6px 6px 0 0',
            pointerEvents: 'none',
          },
        }}
      >
        <ClipIcon />
        <Typography
          variant="caption"
          sx={{
            color: colors.text.primary,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            fontSize: '0.7rem',
            fontWeight: 500,
            textShadow: '0 1px 2px rgba(0,0,0,0.3)',
          }}
        >
          {getClipLabel()}
        </Typography>

        {/* Duration indicator */}
        <Typography
          variant="caption"
          sx={{
            ml: 'auto',
            color: 'rgba(255,255,255,0.7)',
            fontSize: '0.6rem',
            fontFamily: 'monospace',
          }}
        >
          {(item.positionEnd - item.positionStart).toFixed(1)}s
        </Typography>
      </Box>

      {isSelected && (
        <Moveable
          target={ref}
          draggable
          resizable
          edge={['w', 'e']}
          onDrag={(e) => handleDrag({ left: e.left })}
          onResize={(e) => {
            if (e.target && e.target instanceof HTMLElement) {
              e.target.style.width = `${e.width}px`;
            }
            handleResize({ width: e.width, direction: e.direction });
          }}
          renderDirections={['w', 'e']}
          throttleDrag={0}
          throttleResize={0}
        />
      )}
    </>
  );
}
