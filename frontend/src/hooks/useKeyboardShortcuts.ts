'use client';

import { useEffect } from 'react';
import { useEditorStore } from '@/stores/editorStore';

export function useKeyboardShortcuts() {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      // Get current state from store
      const state = useEditorStore.getState();
      const {
        togglePlayPause,
        setCurrentTime,
        currentTime,
        duration,
        undo,
        redo,
        copy,
        cut,
        paste,
        deleteSelected,
        selectAll,
        selectedIds,
        splitMedia,
        zoomIn,
        zoomOut,
        zoomToFit,
        setIsPlaying,
        historyIndex,
        history,
      } = state;

      const canUndo = historyIndex > 0;
      const canRedo = historyIndex < history.length - 1;

      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const modifier = isMac ? e.metaKey : e.ctrlKey;

      // Space - Play/Pause
      if (e.code === 'Space') { e.preventDefault(); togglePlayPause(); return; }

      // Arrow keys - Scrub
      if (e.code === 'ArrowLeft') { e.preventDefault(); setCurrentTime(Math.max(0, currentTime - (e.shiftKey ? 1 : 0.1))); return; }
      if (e.code === 'ArrowRight') { e.preventDefault(); setCurrentTime(Math.min(duration, currentTime + (e.shiftKey ? 1 : 0.1))); return; }

      // Home/End
      if (e.code === 'Home') { e.preventDefault(); setCurrentTime(0); return; }
      if (e.code === 'End') { e.preventDefault(); setCurrentTime(duration); return; }

      // Delete
      if (e.code === 'Delete' || e.code === 'Backspace') { e.preventDefault(); deleteSelected(); return; }

      // Undo/Redo
      if (modifier && e.code === 'KeyZ' && !e.shiftKey) { e.preventDefault(); if (canUndo) undo(); return; }
      if (modifier && e.code === 'KeyZ' && e.shiftKey) { e.preventDefault(); if (canRedo) redo(); return; }

      // Copy/Cut/Paste
      if (modifier && e.code === 'KeyC') { e.preventDefault(); copy(); return; }
      if (modifier && e.code === 'KeyX') { e.preventDefault(); cut(); return; }
      if (modifier && e.code === 'KeyV') { e.preventDefault(); paste(); return; }

      // Select All
      if (modifier && e.code === 'KeyA') { e.preventDefault(); selectAll(); return; }

      // C - Split at playhead
      if (e.code === 'KeyC' && !modifier && selectedIds.length === 1 && selectedIds[0]) { e.preventDefault(); splitMedia(selectedIds[0], currentTime); return; }

      // J/K/L - Playback control
      if (e.code === 'KeyJ') { e.preventDefault(); setCurrentTime(Math.max(0, currentTime - 5)); return; }
      if (e.code === 'KeyK') { e.preventDefault(); setIsPlaying(false); return; }
      if (e.code === 'KeyL') { e.preventDefault(); setCurrentTime(Math.min(duration, currentTime + 5)); return; }

      // Zoom controls - Ctrl/Cmd + =/-/0
      if (modifier && (e.code === 'Equal' || e.code === 'NumpadAdd')) { e.preventDefault(); zoomIn(); return; }
      if (modifier && (e.code === 'Minus' || e.code === 'NumpadSubtract')) { e.preventDefault(); zoomOut(); return; }
      if (modifier && (e.code === 'Digit0' || e.code === 'Numpad0')) { e.preventDefault(); zoomToFit(); return; }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);
}
