// Global keyboard shortcuts:
//   Ctrl/Cmd+N  -> new chat
//   Ctrl/Cmd+K  -> focus conversation search
//   Ctrl/Cmd+,  -> open settings
//   Escape      -> close settings

import { useEffect } from 'react';

import { useChatStore } from '@/stores/chatStore';
import { useUiStore } from '@/stores/uiStore';

export function useKeyboardShortcuts(): void {
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const meta = event.ctrlKey || event.metaKey;
      if (meta && event.key.toLowerCase() === 'n') {
        event.preventDefault();
        useChatStore.getState().newConversation();
        return;
      }
      if (meta && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        document.getElementById('conversation-search')?.focus();
        return;
      }
      if (meta && event.key === ',') {
        event.preventDefault();
        useUiStore.getState().openSettings();
        return;
      }
      if (event.key === 'Escape' && useUiStore.getState().settingsOpen) {
        useUiStore.getState().closeSettings();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);
}
