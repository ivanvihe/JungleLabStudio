import { app, BrowserWindow, nativeTheme } from 'electron';
import { existsSync } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DIST_PATH = path.join(__dirname, '..', 'dist');

const ensureDistBuilt = async () => {
  const indexPath = path.join(DIST_PATH, 'index.html');

  if (existsSync(indexPath)) {
    return indexPath;
  }

  console.warn('No se encontró dist/index.html. Generando build del renderer...');
  const buildScript = path.join(__dirname, '..', 'scripts', 'build.mjs');
  await import(buildScript);

  if (!existsSync(indexPath)) {
    throw new Error('La build del renderer falló: dist/index.html sigue sin existir.');
  }

  return indexPath;
};

const createWindow = (indexPath) => {
  const win = new BrowserWindow({
    width: 1280,
    height: 720,
    backgroundColor: '#04060a',
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  win.loadFile(indexPath);

  if (process.env.NODE_ENV === 'development') {
    win.webContents.openDevTools();
  }
};

app.whenReady().then(async () => {
  nativeTheme.themeSource = 'dark';
  const indexPath = await ensureDistBuilt();
  createWindow(indexPath);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow(indexPath);
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
