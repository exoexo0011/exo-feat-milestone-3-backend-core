/**
 * EXO Electron preload script.
 *
 * Exposes a minimal, typed bridge to the renderer. All privileged
 * operations must go through explicit channels defined here — the
 * renderer never gets direct Node.js access.
 */
import { contextBridge } from 'electron';

contextBridge.exposeInMainWorld('exo', {
  platform: process.platform,
  appVersion: process.env.npm_package_version ?? '0.1.0',
});
