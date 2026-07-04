import { useEffect } from 'react';

import { ChatWindow } from '@/components/chat/ChatWindow';
import { Notifications } from '@/components/common/Notifications';
import { SettingsModal } from '@/components/settings/SettingsModal';
import { Sidebar } from '@/components/sidebar/Sidebar';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { useTheme } from '@/hooks/useTheme';
import { useChatStore } from '@/stores/chatStore';
import { useUiStore } from '@/stores/uiStore';

export default function App() {
  useTheme();
  useKeyboardShortcuts();

  useEffect(() => {
    void useChatStore.getState().init();
  }, []);

  // React to the Electron-managed backend lifecycle when running in the shell.
  useEffect(() => {
    const bridge = window.exo;
    if (!bridge) {
      return;
    }
    return bridge.onBackendStatus((status) => {
      if (status.phase === 'ready') {
        void useChatStore.getState().init();
      } else if (status.phase === 'error') {
        useUiStore.getState().notify('error', status.detail ?? 'The backend failed to start.');
      }
    });
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-surface text-gray-900 dark:bg-surface-dark dark:text-gray-100">
      <Sidebar />
      <ChatWindow />
      <SettingsModal />
      <Notifications />
    </div>
  );
}
