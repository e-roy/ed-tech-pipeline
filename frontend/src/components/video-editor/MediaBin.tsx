'use client';

import { useState, useCallback, useRef } from 'react';
import { Box, Tabs, Tab, Typography, List, ListItemButton, ListItemIcon, ListItemText, CircularProgress } from '@mui/material';
import { VideoFile, AudioFile, Image, TextFields, Add, CloudUpload } from '@mui/icons-material';
import { useEditorStore } from '@/stores/editorStore';
import { colors } from './theme';

interface MediaBinProps {
  sessionId: string;
}

interface LocalMediaFile {
  id: string;
  name: string;
  url: string;
  content_type: string;
  duration?: number;
}

export function MediaBin({ sessionId }: MediaBinProps) {
  const [tab, setTab] = useState(0);
  const [files, setFiles] = useState<LocalMediaFile[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addMedia = useEditorStore((state) => state.addMedia);
  const addText = useEditorStore((state) => state.addText);
  const currentTime = useEditorStore((state) => state.currentTime);

  // Get media duration for video/audio files
  const getMediaDuration = (file: File): Promise<number> => {
    return new Promise((resolve) => {
      const url = URL.createObjectURL(file);
      if (file.type.startsWith('video/')) {
        const video = document.createElement('video');
        video.preload = 'metadata';
        video.onloadedmetadata = () => {
          URL.revokeObjectURL(url);
          resolve(video.duration || 5);
        };
        video.onerror = () => {
          URL.revokeObjectURL(url);
          resolve(5);
        };
        video.src = url;
      } else if (file.type.startsWith('audio/')) {
        const audio = document.createElement('audio');
        audio.preload = 'metadata';
        audio.onloadedmetadata = () => {
          URL.revokeObjectURL(url);
          resolve(audio.duration || 5);
        };
        audio.onerror = () => {
          URL.revokeObjectURL(url);
          resolve(5);
        };
        audio.src = url;
      } else {
        resolve(5); // Default duration for images
      }
    });
  };

  // Process files (from drop or file input)
  const processFiles = useCallback(async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;

    setIsLoading(true);
    const newFiles: LocalMediaFile[] = [];

    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i];
      // Only accept video, audio, and image files
      if (!file.type.startsWith('video/') && !file.type.startsWith('audio/') && !file.type.startsWith('image/')) {
        continue;
      }

      const duration = await getMediaDuration(file);
      const url = URL.createObjectURL(file);

      newFiles.push({
        id: `${Date.now()}-${i}`,
        name: file.name,
        url,
        content_type: file.type,
        duration,
      });
    }

    setFiles((prev) => [...prev, ...newFiles]);
    setIsLoading(false);
  }, []);

  // Handle file drop
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    processFiles(e.dataTransfer.files);
  }, [processFiles]);

  // Handle drag over
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  // Handle file input change
  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    processFiles(e.target.files);
    // Reset input so the same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [processFiles]);

  // Open file picker
  const handleUploadClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleAddMedia = useCallback((file: LocalMediaFile) => {
    const type = file.content_type.startsWith('video/') ? 'video' : file.content_type.startsWith('audio/') ? 'audio' : 'image';
    const duration = file.duration || 5;

    addMedia({
      type,
      fileName: file.name,
      src: file.url,
      startTime: 0,
      endTime: duration,
      duration: duration,
      positionStart: currentTime,
      positionEnd: currentTime + duration,
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
    const iconSx = { fontSize: 20 };
    if (contentType.startsWith('video/')) return <VideoFile sx={{ ...iconSx, color: colors.tracks.video.main }} />;
    if (contentType.startsWith('audio/')) return <AudioFile sx={{ ...iconSx, color: colors.tracks.audio.main }} />;
    return <Image sx={{ ...iconSx, color: colors.primary.main }} />;
  };

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
        }}
      >
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
          Media Bin
        </Typography>
      </Box>

      {/* Tabs */}
      <Tabs
        value={tab}
        onChange={(_, v) => setTab(v)}
        variant="fullWidth"
        sx={{
          minHeight: 36,
          borderBottom: `1px solid ${colors.border.subtle}`,
          '& .MuiTab-root': {
            minHeight: 36,
            py: 1,
          },
        }}
      >
        <Tab
          label="Media"
          icon={<VideoFile sx={{ fontSize: 16 }} />}
          iconPosition="start"
          sx={{ gap: 0.5 }}
        />
        <Tab
          label="Text"
          icon={<TextFields sx={{ fontSize: 16 }} />}
          iconPosition="start"
          sx={{ gap: 0.5 }}
        />
      </Tabs>

      {/* Content */}
      {tab === 0 && (
        <Box sx={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="video/*,audio/*,image/*"
            onChange={handleFileInputChange}
            style={{ display: 'none' }}
          />

          {/* Upload zone */}
          <Box
            onClick={handleUploadClick}
            onDragEnter={() => setIsDragging(true)}
            onDragLeave={() => setIsDragging(false)}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            sx={{
              m: 1.5,
              p: 2,
              borderRadius: 2,
              border: `2px dashed ${isDragging ? colors.primary.main : colors.border.default}`,
              bgcolor: isDragging ? `${colors.primary.main}10` : colors.bg.darker,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 1,
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              '&:hover': {
                borderColor: colors.primary.main,
                bgcolor: `${colors.primary.main}08`,
              },
            }}
          >
            {isLoading ? (
              <CircularProgress size={32} sx={{ color: colors.primary.main }} />
            ) : (
              <CloudUpload sx={{ fontSize: 32, color: isDragging ? colors.primary.main : colors.text.muted }} />
            )}
            <Typography variant="body2" sx={{ color: colors.text.secondary, fontSize: '0.75rem', textAlign: 'center' }}>
              {isLoading ? 'Processing...' : 'Drag & drop files here'}
            </Typography>
            <Typography variant="caption" sx={{ color: colors.text.muted, fontSize: '0.65rem' }}>
              {isLoading ? '' : 'or click to browse'}
            </Typography>
          </Box>

          {/* File list */}
          <List dense sx={{ flex: 1, px: 0.5 }}>
            {isLoading ? (
              <Box sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="caption" color="text.secondary">Loading...</Typography>
              </Box>
            ) : files && files.length > 0 ? (
              files.map((file) => (
                <ListItemButton
                  key={file.id}
                  onClick={() => handleAddMedia(file)}
                  sx={{
                    borderRadius: 1.5,
                    mx: 1,
                    mb: 0.5,
                    py: 1,
                    '&:hover': {
                      bgcolor: colors.bg.hover,
                    },
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 36 }}>{getFileIcon(file.content_type)}</ListItemIcon>
                  <ListItemText
                    primary={file.name}
                    primaryTypographyProps={{
                      variant: 'body2',
                      noWrap: true,
                      sx: { fontSize: '0.8rem', fontWeight: 500 },
                    }}
                  />
                </ListItemButton>
              ))
            ) : (
              <Box sx={{ p: 3, textAlign: 'center' }}>
                <VideoFile sx={{ fontSize: 40, color: colors.text.muted, opacity: 0.5, mb: 1 }} />
                <Typography variant="body2" sx={{ color: colors.text.secondary, fontSize: '0.8rem' }}>
                  No media files
                </Typography>
                <Typography variant="caption" sx={{ color: colors.text.muted, display: 'block', mt: 0.5 }}>
                  Upload files to get started
                </Typography>
              </Box>
            )}
          </List>
        </Box>
      )}

      {tab === 1 && (
        <Box sx={{ flex: 1, p: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Typography variant="body2" sx={{ color: colors.text.secondary, fontSize: '0.8rem' }}>
            Add text overlays to your video
          </Typography>

          {/* Text templates */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <ListItemButton
              onClick={handleAddText}
              sx={{
                borderRadius: 2,
                border: `1px solid ${colors.border.subtle}`,
                bgcolor: colors.bg.darker,
                py: 1.5,
                '&:hover': {
                  bgcolor: colors.bg.hover,
                  borderColor: colors.tracks.text.main,
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                <Add sx={{ color: colors.tracks.text.main }} />
              </ListItemIcon>
              <ListItemText
                primary="Add Text"
                secondary="Basic text overlay"
                primaryTypographyProps={{ fontWeight: 600, fontSize: '0.85rem' }}
                secondaryTypographyProps={{ fontSize: '0.7rem' }}
              />
            </ListItemButton>

            <ListItemButton
              onClick={() => {
                addText({
                  text: 'Title',
                  positionStart: currentTime,
                  positionEnd: currentTime + 3,
                  x: 960,
                  y: 540,
                  font: 'Arial',
                  fontSize: 72,
                  fontWeight: 'bold',
                  fontStyle: 'normal',
                  color: '#ffffff',
                  backgroundColor: 'transparent',
                  textAlign: 'center',
                  opacity: 100,
                  animation: 'fade-in',
                  animationDuration: 0.5,
                });
              }}
              sx={{
                borderRadius: 2,
                border: `1px solid ${colors.border.subtle}`,
                bgcolor: colors.bg.darker,
                py: 1.5,
                '&:hover': {
                  bgcolor: colors.bg.hover,
                  borderColor: colors.tracks.text.main,
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                <TextFields sx={{ color: colors.tracks.text.main }} />
              </ListItemIcon>
              <ListItemText
                primary="Title"
                secondary="Large centered text"
                primaryTypographyProps={{ fontWeight: 600, fontSize: '0.85rem' }}
                secondaryTypographyProps={{ fontSize: '0.7rem' }}
              />
            </ListItemButton>
          </Box>
        </Box>
      )}
    </Box>
  );
}
