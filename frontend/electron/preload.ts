/**
 * EXO Electron preload script.
 *
 * Exposes a minimal, typed bridge on `window.exo`. The renderer never gets
 * direct Node.js/Electron access; all privileged operations go through the
 * explicit IPC channels defined here.
 */
import { contextBridge, ipcRenderer, type IpcRendererEvent } from 'electron';

type BackendPhase = 'starting' | 'ready' | 'stopped' | 'error';

interface BackendStatus {
  phase: BackendPhase;
  detail?: string;
}

interface NotifyPayload {
  title: string;
  body: string;
}

contextBridge.exposeInMainWorld('exo', {
  isElectron: true,
  platform: process.platform,
  appVersion: process.env.npm_package_version ?? '0.9.0',

  onBackendStatus(listener: (status: BackendStatus) => void): () => void {
    const channel = 'backend:status';
    const handler = (_event: IpcRendererEvent, status: BackendStatus): void => listener(status);
    ipcRenderer.on(channel, handler);
    return () => {
      ipcRenderer.removeListener(channel, handler);
    };
  },

  getBackendStatus(): Promise<BackendStatus> {
    return ipcRenderer.invoke('backend:getStatus') as Promise<BackendStatus>;
  },

  notify(payload: NotifyPayload): void {
    ipcRenderer.send('notify', payload);
  },
});
