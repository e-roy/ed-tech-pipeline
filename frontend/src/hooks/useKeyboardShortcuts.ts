'use client';

import { useEffect } from 'react';
import { useEditorStore, selectCanUndo, selectCanRedo } from '@/stores/editorStore';

export function useKeyboardShortcuts() {
  const togglePlayPause = useEditorStore((state) => state.togglePlayPause);
  const setCurrentTime = useEditorStore((state) => state.setCurrentTime);
  const currentTime = useEditorStore((state) => state.currentTime);
  const duration = useEditorStore((state) => state.duration);
  const undo = useEditorStore((state) => state.undo);
  const redo = useEditorStore((state) => state.redo);
  const copy = useEditorStore((state) => state.copy);
  const cut = useEditorStore((state) => state.cut);
  const paste = useEditorStore((state) => state.paste);
  const deleteSelected = useEditorStore((state) => state.deleteSelected);
  const selectAll = useEditorStore((state) => state.selectAll);
  const selectedIds = useEditorStore((state) => state.selectedIds);
  const splitMedia = useEditorStore((state) => state.splitMedia);
  const canUndo = useEditorStore(selectCanUndo);
  const canRedo = useEditorStore(selectCanRedo);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

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
      if (e.code === 'KeyC' && !modifier && selectedIds.length === 1) { e.preventDefault(); splitMedia(selectedIds[0], currentTime); return; }

      // J/K/L - Playback control
      if (e.code === 'KeyJ') { e.preventDefault(); setCurrentTime(Math.max(0, currentTime - 5)); return; }
      if (e.code === 'KeyK') { e.preventDefault(); useEditorStore.getState().setIsPlaying(false); return; }
      if (e.code === 'KeyL') { e.preventDefault(); setCurrentTime(Math.min(duration, currentTime + 5)); return; }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [togglePlayPause, setCurrentTime, currentTime, duration, undo, redo, copy, cut, paste, deleteSelected, selectAll, selectedIds, splitMedia, canUndo, canRedo]);
}
