const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.cjs')
      // Removido webSecurity: false
    },
  });

  const startUrl = process.env.NODE_ENV === 'development'
    ? 'http://localhost:3000'  // Cambiado de 5173 a 3000 (puerto de Vite por defecto)
    : path.join(__dirname, 'dist', 'index.html');

  console.log('Loading URL:', startUrl);

  if (startUrl.startsWith('http')) {
    mainWindow.loadURL(startUrl);
  } else {
    mainWindow.loadFile(startUrl);
  }

  // Log cuando la página esté lista
  mainWindow.webContents.once('did-finish-load', () => {
    console.log('✅ Page loaded successfully');
  });

  // Log errores de carga
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('❌ Failed to load page:', errorCode, errorDescription);
  });

  // Log errores de consola de la página
  mainWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    console.log(`Console [${level}]:`, message);
  });
}

ipcMain.on('apply-settings', (event, settings) => {
  if (!mainWindow) return;
  if (settings.monitorId) {
    const displays = screen.getAllDisplays();
    const target = displays.find(d => d.id === settings.monitorId);
    if (target) {
      mainWindow.setBounds(target.bounds);
    }
  }
  if (settings.maximize) {
    mainWindow.maximize();
  }
  if (!mainWindow.isVisible()) {
    mainWindow.show();
  }
});

ipcMain.handle('get-displays', () => {
  return screen.getAllDisplays().map(d => ({
    id: d.id,
    label: d.label || `Monitor ${d.id}`,
    bounds: d.bounds,
    scaleFactor: d.scaleFactor,
    primary: d.primary
  }));
});

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// Para debugging
app.on('ready', () => {
  console.log('🚀 Electron app is ready');
  console.log('Environment:', process.env.NODE_ENV || 'production');
});