'use client';

import { Box } from '@mui/material';
import { Toolbar } from './Toolbar';
import { MediaBin } from './MediaBin';
import { PreviewPlayer } from './PreviewPlayer';
import { Timeline } from './Timeline';
import { PropertiesPanel } from './PropertiesPanel';
import { useEditorStore } from '@/stores/editorStore';
import { useEffect } from 'react';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';

interface EditorLayoutProps {
  sessionId: string;
  videoUrl?: string;
}

export function EditorLayout({ sessionId, videoUrl }: EditorLayoutProps) {
  const initializeProject = useEditorStore((state) => state.initializeProject);
  const propertiesPanelOpen = useEditorStore((state) => state.propertiesPanelOpen);
  const addMedia = useEditorStore((state) => state.addMedia);

  // Enable keyboard shortcuts
  useKeyboardShortcuts();

  useEffect(() => {
    initializeProject(sessionId);

    // If a video URL is provided, add it as the first clip
    if (videoUrl) {
      // Create a video element to get duration
      const video = document.createElement('video');
      video.src = videoUrl;
      video.onloadedmetadata = () => {
        const duration = video.duration || 60; // Default to 60s if unknown
        addMedia({
          type: 'video',
          fileName: 'Source Video',
          src: videoUrl,
          startTime: 0,
          endTime: duration,
          duration: duration,
          positionStart: 0,
          positionEnd: duration,
          playbackSpeed: 1,
          volume: 100,
          opacity: 100,
        });
      };
      video.onerror = () => {
        // If we can't load metadata, add with default duration
        addMedia({
          type: 'video',
          fileName: 'Source Video',
          src: videoUrl,
          startTime: 0,
          endTime: 60,
          duration: 60,
          positionStart: 0,
          positionEnd: 60,
          playbackSpeed: 1,
          volume: 100,
          opacity: 100,
        });
      };
    }
  }, [sessionId, initializeProject, videoUrl, addMedia]);

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        bgcolor: 'background.default',
        color: 'text.primary',
      }}
    >
      {/* Top Toolbar */}
      <Toolbar />

      {/* Main Content */}
      <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left: Media Bin (280px) */}
        <Box sx={{ width: 280, borderRight: 1, borderColor: 'divider', display: 'flex', flexDirection: 'column' }}>
          <MediaBin sessionId={sessionId} />
        </Box>

        {/* Center: Preview + Timeline */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Preview */}
          <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: '#0a0a0a', minHeight: 300 }}>
            <PreviewPlayer />
          </Box>

          {/* Timeline */}
          <Box sx={{ height: 280, borderTop: 1, borderColor: 'divider' }}>
            <Timeline />
          </Box>
        </Box>

        {/* Right: Properties (300px) */}
        {propertiesPanelOpen && (
          <Box sx={{ width: 300, borderLeft: 1, borderColor: 'divider' }}>
            <PropertiesPanel />
          </Box>
        )}
      </Box>
    </Box>
  );
}
