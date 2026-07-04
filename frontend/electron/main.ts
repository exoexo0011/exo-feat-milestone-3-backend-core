/**
 * EXO Electron main process.
 *
 * Responsibilities:
 * - Create the application window with secure defaults
 *   (contextIsolation on, nodeIntegration off).
 * - Load the Vite dev server in development or the built bundle in production.
 *
 * Backend lifecycle management (spawning the Python server in packaged
 * builds) is added in Milestone 7.
 */
import { app, BrowserWindow } from 'electron';
import * as path from 'node:path';

const DEV_SERVER_URL = process.env.VITE_DEV_SERVER_URL;

function createWindow(): void {
  const win = new BrowserWindow({
    width: 1280,
    height: 840,
    minWidth: 960,
    minHeight: 600,
    backgroundColor: '#0f1117',
    title: 'EXO',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  if (DEV_SERVER_URL) {
    void win.loadURL(DEV_SERVER_URL);
    win.webContents.openDevTools({ mode: 'detach' });
  } else {
    void win.loadFile(path.join(__dirname, '../dist/index.html'));
  }
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
