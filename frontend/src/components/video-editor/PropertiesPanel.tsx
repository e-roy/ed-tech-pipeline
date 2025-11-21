'use client';

import { Box, Typography } from '@mui/material';
import { useEditorStore, selectActiveElement } from '@/stores/editorStore';
import { MediaProperties } from './properties/MediaProperties';
import { TextProperties } from './properties/TextProperties';

export function PropertiesPanel() {
  const activeElement = useEditorStore(selectActiveElement);

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
