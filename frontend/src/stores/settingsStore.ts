// Settings state (persisted to localStorage): theme preference and toggles.

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type ThemePreference = 'light' | 'dark' | 'system';

interface SettingsState {
  theme: ThemePreference;
  sendOnEnter: boolean;
  setTheme: (theme: ThemePreference) => void;
  setSendOnEnter: (value: boolean) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      theme: 'system',
      sendOnEnter: true,
      setTheme: (theme) => set({ theme }),
      setSendOnEnter: (sendOnEnter) => set({ sendOnEnter }),
    }),
    { name: 'exo-settings' },
  ),
);
