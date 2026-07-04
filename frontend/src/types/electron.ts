// Types for the secure bridge the Electron preload exposes on `window.exo`.
// In a plain browser (dev server) `window.exo` is undefined.

export type BackendPhase = 'starting' | 'ready' | 'stopped' | 'error';

export interface BackendStatus {
  phase: BackendPhase;
  detail?: string;
}

export interface NotifyPayload {
  title: string;
  body: string;
}

export interface ExoApi {
  /** Always true when running inside the Electron shell. */
  readonly isElectron: true;
  readonly platform: string;
  readonly appVersion: string;
  /** Subscribe to backend lifecycle changes; returns an unsubscribe function. */
  onBackendStatus(listener: (status: BackendStatus) => void): () => void;
  /** Ask the current backend status once. */
  getBackendStatus(): Promise<BackendStatus>;
  /** Show a native OS notification. */
  notify(payload: NotifyPayload): void;
}
