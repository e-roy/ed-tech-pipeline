'use client';

import { Box, Typography } from '@mui/material';
import { useShallow } from 'zustand/react/shallow';
import { useEditorStore } from '@/stores/editorStore';
import { MediaProperties } from './properties/MediaProperties';
import { TextProperties } from './properties/TextProperties';

export function PropertiesPanel() {
  // Use useShallow to prevent infinite re-render from new object references
  const activeElement = useEditorStore(
    useShallow((state) => {
      if (!state.activeElementId) return null;
      const media = state.mediaFiles.find((m) => m.id === state.activeElementId);
      if (media) return { type: 'media' as const, element: media };
      const text = state.textElements.find((t) => t.id === state.activeElementId);
      if (text) return { type: 'text' as const, element: text };
      return null;
    })
  );

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="subtitle2">Properties</Typography>
      </Box>
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        {!activeElement ? (
          <Typography variant="body2" color="text.secondary">Select an element to edit its properties</Typography>
        ) : activeElement.type === 'media' ? (
          <MediaProperties media={activeElement.element} />
        ) : (
          <TextProperties text={activeElement.element} />
        )}
      </Box>
    </Box>
  );
}
