/** System tray icon with show/hide and quit controls. */
import { Menu, Tray, nativeImage, type BrowserWindow } from 'electron';

export function createTray(getWindow: () => BrowserWindow | null, onQuit: () => void): Tray {
  // An empty image keeps the tray dependency-free; a packaged build would ship
  // a real icon asset here.
  const tray = new Tray(nativeImage.createEmpty());
  tray.setToolTip('EXO');

  const toggle = (): void => {
    const win = getWindow();
    if (!win) {
      return;
    }
    if (win.isVisible()) {
      win.hide();
    } else {
      win.show();
      win.focus();
    }
  };

  tray.setContextMenu(
    Menu.buildFromTemplate([
      {
        label: 'Show EXO',
        click: () => {
          const win = getWindow();
          win?.show();
          win?.focus();
        },
      },
      { type: 'separator' },
      { label: 'Quit EXO', click: onQuit },
    ]),
  );
  tray.on('click', toggle);
  return tray;
}
