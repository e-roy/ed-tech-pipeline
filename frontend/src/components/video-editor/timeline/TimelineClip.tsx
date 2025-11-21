'use client';

import { useRef, useState, useCallback, useMemo } from 'react';
import { Box, Typography } from '@mui/material';
import Moveable from 'react-moveable';
import { throttle } from 'lodash';
import { useEditorStore, type MediaFile, type TextElement } from '@/stores/editorStore';

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

  const getClipColor = () => {
    switch (trackType) {
      case 'video': return isSelected ? '#2196f3' : '#1976d2';
      case 'audio': return isSelected ? '#4caf50' : '#388e3c';
      case 'text': return isSelected ? '#ff9800' : '#f57c00';
      default: return '#666';
    }
  };

  const getClipLabel = () => {
    if (isMedia) return (item as MediaFile).fileName;
    const textItem = item as TextElement;
    return textItem.text.substring(0, 20) + (textItem.text.length > 20 ? '...' : '');
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
          bgcolor: getClipColor(),
          borderRadius: 1,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          px: 1,
          overflow: 'hidden',
          border: isSelected ? '2px solid #fff' : 'none',
          boxShadow: isSelected ? '0 0 8px rgba(33, 150, 243, 0.5)' : 'none',
          transition: 'box-shadow 0.2s',
          '&:hover': { boxShadow: '0 0 4px rgba(255, 255, 255, 0.3)' },
        }}
      >
        <Typography variant="caption" sx={{ color: '#fff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontSize: 11 }}>
          {getClipLabel()}
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
