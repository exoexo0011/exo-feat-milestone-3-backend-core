// Transient UI state: toast notifications and the settings modal.

import { create } from 'zustand';

export type NotificationKind = 'info' | 'success' | 'error';

export interface Notification {
  id: string;
  kind: NotificationKind;
  message: string;
}

interface UiState {
  notifications: Notification[];
  settingsOpen: boolean;
  notify: (kind: NotificationKind, message: string) => void;
  dismiss: (id: string) => void;
  openSettings: () => void;
  closeSettings: () => void;
}

let counter = 0;
const nextId = (): string => {
  counter += 1;
  return `n${counter}-${Date.now()}`;
};

export const useUiStore = create<UiState>((set) => ({
  notifications: [],
  settingsOpen: false,
  notify: (kind, message) =>
    set((state) => ({
      notifications: [...state.notifications, { id: nextId(), kind, message }],
    })),
  dismiss: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
  openSettings: () => set({ settingsOpen: true }),
  closeSettings: () => set({ settingsOpen: false }),
}));
