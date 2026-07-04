/**
 * EXO Electron main process.
 *
 * Responsibilities:
 * - Create the app window with secure defaults and restored bounds.
 * - Manage the local backend process (start, health, auto-restart) and relay
 *   its status to the renderer over a secure IPC channel.
 * - Provide native notifications and a system tray; persist window state.
 */
import * as path from 'node:path';

import { app, BrowserWindow, ipcMain, Notification, type Tray } from 'electron';

import { BackendManager, type BackendStatus } from './backend';
import { createTray } from './tray';
import { loadWindowState, persistWindowState } from './windowState';

const DEV_SERVER_URL = process.env.VITE_DEV_SERVER_URL;

let mainWindow: BrowserWindow | null = null;
let backend: BackendManager | null = null;
let tray: Tray | null = null;
let quitting = false;
let lastStatus: BackendStatus = { phase: 'stopped' };

function broadcastStatus(status: BackendStatus): void {
  lastStatus = status;
  mainWindow?.webContents.send('backend:status', status);
}

function createWindow(): void {
  const state = loadWindowState();
  const win = new BrowserWindow({
    width: state.width,
    height: state.height,
    x: state.x,
    y: state.y,
    minWidth: 960,
    minHeight: 600,
    backgroundColor: '#0f1117',
    title: 'EXO',
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  mainWindow = win;

  win.once('ready-to-show', () => win.show());
  const save = (): void => persistWindowState(win);
  win.on('resize', save);
  win.on('move', save);
  win.on('close', (event) => {
    // Closing hides to tray unless the app is really quitting.
    if (!quitting) {
      event.preventDefault();
      win.hide();
    } else {
      persistWindowState(win);
    }
  });
  win.on('closed', () => {
    mainWindow = null;
  });

  if (DEV_SERVER_URL) {
    void win.loadURL(DEV_SERVER_URL);
    win.webContents.openDevTools({ mode: 'detach' });
  } else {
    void win.loadFile(path.join(__dirname, '../dist/index.html'));
  }
}

function bootstrap(): void {
  backend = new BackendManager(broadcastStatus);
  // In development the backend is run separately (bootstrap script); only the
  // packaged app owns the backend process.
  if (DEV_SERVER_URL) {
    broadcastStatus({ phase: 'ready' });
  } else {
    backend.start();
  }

  ipcMain.handle('backend:getStatus', () => lastStatus);
  ipcMain.on('notify', (_event, payload: { title: string; body: string }) => {
    if (Notification.isSupported()) {
      new Notification({ title: payload.title, body: payload.body }).show();
    }
  });

  createWindow();
  tray = createTray(
    () => mainWindow,
    () => {
      quitting = true;
      app.quit();
    },
  );

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
}

void app.whenReady().then(bootstrap);

app.on('before-quit', () => {
  quitting = true;
  backend?.stop();
  tray?.destroy();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin' && quitting) {
    app.quit();
  }
});
