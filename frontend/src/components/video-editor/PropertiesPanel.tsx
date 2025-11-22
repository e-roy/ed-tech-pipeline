'use client';

import { Box, Typography } from '@mui/material';
import { Settings, Tune } from '@mui/icons-material';
import { useShallow } from 'zustand/react/shallow';
import { useEditorStore } from '@/stores/editorStore';
import { colors } from './theme';
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
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        bgcolor: colors.bg.paper,
      }}
    >
      {/* Header */}
      <Box
        sx={{
          px: 2,
          py: 1.5,
          borderBottom: `1px solid ${colors.border.subtle}`,
          background: `linear-gradient(180deg, ${colors.bg.elevated} 0%, ${colors.bg.paper} 100%)`,
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <Tune sx={{ fontSize: 18, color: colors.text.secondary }} />
        <Typography
          variant="subtitle2"
          sx={{
            color: colors.text.primary,
            fontWeight: 600,
            fontSize: '0.8rem',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          Properties
        </Typography>
      </Box>

      {/* Content */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          '&::-webkit-scrollbar': {
            width: 6,
          },
          '&::-webkit-scrollbar-track': {
            background: colors.bg.darker,
          },
          '&::-webkit-scrollbar-thumb': {
            background: colors.border.strong,
            borderRadius: 3,
          },
        }}
      >
        {!activeElement ? (
          <Box
            sx={{
              p: 4,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              textAlign: 'center',
            }}
          >
            <Settings sx={{ fontSize: 48, color: colors.text.muted, opacity: 0.3, mb: 2 }} />
            <Typography
              variant="body2"
              sx={{ color: colors.text.secondary, fontSize: '0.85rem', mb: 0.5 }}
            >
              No element selected
            </Typography>
            <Typography
              variant="caption"
              sx={{ color: colors.text.muted }}
            >
              Select a clip or text to edit its properties
            </Typography>
          </Box>
        ) : activeElement.type === 'media' ? (
          <MediaProperties media={activeElement.element} />
        ) : (
          <TextProperties text={activeElement.element} />
        )}
      </Box>
    </Box>
  );
}
