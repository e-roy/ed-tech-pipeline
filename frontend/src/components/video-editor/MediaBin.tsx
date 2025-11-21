'use client';

import { useState, useCallback } from 'react';
import { Box, Tabs, Tab, Typography, IconButton, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Tooltip } from '@mui/material';
import { Upload, VideoFile, AudioFile, Image, TextFields } from '@mui/icons-material';
import { useEditorStore } from '@/stores/editorStore';

interface MediaBinProps {
  sessionId: string;
}

interface MediaFile {
  key: string;
  name: string;
  presigned_url: string;
  content_type: string;
}

export function MediaBin({ sessionId }: MediaBinProps) {
  const [tab, setTab] = useState(0);
  const [files, setFiles] = useState<MediaFile[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const addMedia = useEditorStore((state) => state.addMedia);
  const addText = useEditorStore((state) => state.addText);
  const currentTime = useEditorStore((state) => state.currentTime);

  const handleAddMedia = useCallback((file: MediaFile) => {
    const type = file.content_type.startsWith('video/') ? 'video' : file.content_type.startsWith('audio/') ? 'audio' : 'image';
    const defaultDuration = 5;

    addMedia({
      type,
      fileName: file.name,
      src: file.presigned_url,
      s3Key: file.key,
      startTime: 0,
      endTime: defaultDuration,
      duration: defaultDuration,
      positionStart: currentTime,
      positionEnd: currentTime + defaultDuration,
      playbackSpeed: 1,
      volume: 100,
      opacity: 100,
    });
  }, [addMedia, currentTime]);

  const handleAddText = useCallback(() => {
    addText({
      text: 'New Text',
      positionStart: currentTime,
      positionEnd: currentTime + 3,
      x: 100,
      y: 100,
      font: 'Arial',
      fontSize: 48,
      fontWeight: 'normal',
      fontStyle: 'normal',
      color: '#ffffff',
      backgroundColor: 'transparent',
      textAlign: 'center',
      opacity: 100,
      animation: 'none',
      animationDuration: 0.5,
    });
  }, [addText, currentTime]);

  const getFileIcon = (contentType: string) => {
    if (contentType.startsWith('video/')) return <VideoFile />;
    if (contentType.startsWith('audio/')) return <AudioFile />;
    return <Image />;
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="fullWidth" sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tab label="Media" />
        <Tab label="Text" />
      </Tabs>

      {tab === 0 && (
        <Box sx={{ flex: 1, overflow: 'auto' }}>
          <Box sx={{ p: 1, borderBottom: 1, borderColor: 'divider' }}>
            <Tooltip title="Upload Media"><IconButton size="small"><Upload fontSize="small" /></IconButton></Tooltip>
          </Box>
          <List dense>
            {isLoading ? (
              <ListItem><ListItemText primary="Loading..." /></ListItem>
            ) : files && files.length > 0 ? (
              files.map((file) => (
                <ListItemButton key={file.key} onClick={() => handleAddMedia(file)}>
                  <ListItemIcon sx={{ minWidth: 36 }}>{getFileIcon(file.content_type)}</ListItemIcon>
                  <ListItemText primary={file.name} primaryTypographyProps={{ variant: 'caption', noWrap: true }} />
                </ListItemButton>
              ))
            ) : (
              <ListItem><ListItemText primary="No media files" secondary="Upload files to get started" /></ListItem>
            )}
          </List>
        </Box>
      )}

      {tab === 1 && (
        <Box sx={{ flex: 1, p: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>Click to add text overlay</Typography>
          <ListItemButton onClick={handleAddText}>
            <ListItemIcon sx={{ minWidth: 36 }}><TextFields /></ListItemIcon>
            <ListItemText primary="Add Text" />
          </ListItemButton>
        </Box>
      )}
    </Box>
  );
}
