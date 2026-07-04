/** Persists and restores the main window's bounds across launches. */
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

import { app, type BrowserWindow } from 'electron';

export interface WindowState {
  width: number;
  height: number;
  x?: number;
  y?: number;
}

const DEFAULT_STATE: WindowState = { width: 1280, height: 840 };

function stateFile(): string {
  return join(app.getPath('userData'), 'window-state.json');
}

export function loadWindowState(): WindowState {
  try {
    const parsed = JSON.parse(readFileSync(stateFile(), 'utf-8')) as Partial<WindowState>;
    return { ...DEFAULT_STATE, ...parsed };
  } catch {
    return { ...DEFAULT_STATE };
  }
}

export function persistWindowState(win: BrowserWindow): void {
  if (win.isMinimized() || win.isDestroyed()) {
    return;
  }
  try {
    const bounds = win.getBounds();
    const state: WindowState = {
      width: bounds.width,
      height: bounds.height,
      x: bounds.x,
      y: bounds.y,
    };
    writeFileSync(stateFile(), JSON.stringify(state));
  } catch {
    // Non-fatal: window state persistence is best-effort.
  }
}
