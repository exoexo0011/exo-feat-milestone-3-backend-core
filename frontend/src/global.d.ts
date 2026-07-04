import type { ExoApi } from './types/electron';

declare global {
  interface Window {
    /** Present only inside the Electron shell (see electron/preload.ts). */
    exo?: ExoApi;
  }
}

export {};
