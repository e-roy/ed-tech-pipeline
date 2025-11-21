'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, LinearProgress, Box, Alert } from '@mui/material';
import { useEditorStore } from '@/stores/editorStore';
import { useWebSocket } from '@/hooks/useWebSocket';

interface ExportDialogProps {
  open: boolean;
  onClose: () => void;
}

interface ExportMessage {
  type: string;
  progress?: number;
  video_url?: string;
  error?: string;
}

export function ExportDialog({ open, onClose }: ExportDialogProps) {
  const [error, setError] = useState<string | null>(null);
  const [exportedUrl, setExportedUrl] = useState<string | null>(null);

  const projectId = useEditorStore((state) => state.projectId);
  const duration = useEditorStore((state) => state.duration);
  const fps = useEditorStore((state) => state.fps);
  const resolution = useEditorStore((state) => state.resolution);
  const mediaFiles = useEditorStore((state) => state.mediaFiles);
  const textElements = useEditorStore((state) => state.textElements);
  const isExporting = useEditorStore((state) => state.isExporting);
  const exportProgress = useEditorStore((state) => state.exportProgress);
  const setExporting = useEditorStore((state) => state.setExporting);
  const setExportProgress = useEditorStore((state) => state.setExportProgress);

  const { lastMessage } = useWebSocket(isExporting ? projectId : null);

  useEffect(() => {
    if (!lastMessage) return;
    const message = lastMessage as unknown as ExportMessage;
    if (message.type === 'export_progress' && message.progress !== undefined) {
      setExportProgress(message.progress);
    } else if (message.type === 'export_complete' && message.video_url) {
      setExporting(false);
      setExportedUrl(message.video_url);
    } else if (message.type === 'export_error' && message.error) {
      setExporting(false);
      setError(message.error);
    }
  }, [lastMessage, setExportProgress, setExporting]);

  const handleExport = async () => {
    setError(null);
    setExportedUrl(null);
    setExporting(true);
    setExportProgress(0);

    try {
      const exportData = {
        session_id: projectId,
        duration,
        fps,
        resolution,
        media_files: mediaFiles.map((m) => ({
          id: m.id, type: m.type, s3_key: m.s3Key || '',
          start_time: m.startTime, end_time: m.endTime,
          position_start: m.positionStart, position_end: m.positionEnd,
          playback_speed: m.playbackSpeed, volume: m.volume,
          x: m.x, y: m.y, width: m.width, height: m.height, opacity: m.opacity, z_index: m.zIndex,
        })),
        text_elements: textElements.map((t) => ({
          id: t.id, text: t.text,
          position_start: t.positionStart, position_end: t.positionEnd,
          x: t.x, y: t.y, font: t.font, font_size: t.fontSize,
          font_weight: t.fontWeight, font_style: t.fontStyle,
          color: t.color, background_color: t.backgroundColor, text_align: t.textAlign,
          opacity: t.opacity, animation: t.animation, animation_duration: t.animationDuration,
        })),
      };

      const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
      const response = await fetch(`${API_URL}/api/video/compose-edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(exportData),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Export failed');
      }
    } catch (err) {
      setExporting(false);
      setError(err instanceof Error ? err.message : 'Export failed');
    }
  };

  const handleDownload = () => {
    if (exportedUrl) {
      const link = document.createElement('a');
      link.href = exportedUrl;
      link.download = `video-${projectId}.mp4`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <Dialog open={open} onClose={isExporting ? undefined : onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Export Video</DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {exportedUrl ? (
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="h6" color="success.main" gutterBottom>Export Complete!</Typography>
            <Typography variant="body2" color="text.secondary">Your video is ready for download.</Typography>
          </Box>
        ) : isExporting ? (
          <Box sx={{ py: 2 }}>
            <Typography variant="body2" gutterBottom>Exporting video...</Typography>
            <LinearProgress variant="determinate" value={exportProgress} sx={{ mb: 1 }} />
            <Typography variant="caption" color="text.secondary">{exportProgress.toFixed(0)}% complete</Typography>
          </Box>
        ) : (
          <Box sx={{ py: 2 }}>
            <Typography variant="body2" gutterBottom>Export settings:</Typography>
            <Typography variant="caption" color="text.secondary" component="div">Resolution: {resolution.width}x{resolution.height}</Typography>
            <Typography variant="caption" color="text.secondary" component="div">Duration: {duration.toFixed(1)} seconds</Typography>
            <Typography variant="caption" color="text.secondary" component="div">Frame Rate: {fps} fps</Typography>
            <Typography variant="caption" color="text.secondary" component="div">Format: MP4 (H.264)</Typography>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        {exportedUrl ? (
          <>
            <Button onClick={onClose}>Close</Button>
            <Button variant="contained" onClick={handleDownload}>Download</Button>
          </>
        ) : (
          <>
            <Button onClick={onClose} disabled={isExporting}>Cancel</Button>
            <Button variant="contained" onClick={handleExport} disabled={isExporting}>{isExporting ? 'Exporting...' : 'Export'}</Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  );
}
