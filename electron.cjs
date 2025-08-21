const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');

let mainWindow;
// Ventanas usadas para monitores secundarios en fullscreen
let fullscreenWindows = [];
const startUrl = process.env.NODE_ENV === 'development'
  ? 'http://localhost:3000'  // Cambiado de 5173 a 3000 (puerto de Vite por defecto)
  : path.join(__dirname, 'dist', 'index.html');

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

  // Si el usuario sale del modo fullscreen manualmente, cerrar las ventanas
  // secundarias y notificar al renderer para que actualice su estado
  mainWindow.on('leave-full-screen', () => {
    fullscreenWindows.forEach(win => win.close());
    fullscreenWindows = [];
    mainWindow.webContents.send('main-leave-fullscreen');
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

ipcMain.handle('toggle-fullscreen', (event, ids = []) => {
  // Si ya hay ventanas de fullscreen abiertas, cerrar y restaurar principal
  if (fullscreenWindows.length) {
    fullscreenWindows.forEach(win => win.close());
    fullscreenWindows = [];
    if (mainWindow) {
      mainWindow.setFullScreen(false);
      mainWindow.show();
      if (startUrl.startsWith('http')) {
        mainWindow.loadURL(startUrl);
      } else {
        mainWindow.loadFile(startUrl);
      }
    }
    return;
  }

  const displays = screen.getAllDisplays();

  ids.forEach((id, index) => {
    const display = displays.find(d => d.id === id);
    if (!display) return;

    if (index === 0 && mainWindow) {
      // Usar la ventana principal para el primer monitor
      if (startUrl.startsWith('http')) {
        mainWindow.loadURL(`${startUrl}?fullscreen=true`);
      } else {
        mainWindow.loadFile(startUrl, { query: { fullscreen: 'true' } });
      }
      mainWindow.setBounds(display.bounds);
      mainWindow.setFullScreen(true);
      mainWindow.show();
    } else {
      // Ventanas clon para monitores secundarios
      const win = new BrowserWindow({
        x: display.bounds.x,
        y: display.bounds.y,
        width: display.bounds.width,
        height: display.bounds.height,
        frame: false,
        fullscreen: true,
        skipTaskbar: true,
        webPreferences: {
          nodeIntegration: false,
          contextIsolation: true,
          preload: path.join(__dirname, 'preload.cjs')
        }
      });

      win.loadFile(path.join(__dirname, 'clone.html'));

      win.on('closed', () => {
        fullscreenWindows = fullscreenWindows.filter(w => w !== win);
        if (fullscreenWindows.length === 0 && mainWindow) {
          mainWindow.setFullScreen(false);
          mainWindow.show();
        }
      });

      fullscreenWindows.push(win);
    }
  });
});

// Nuevo IPC para recibir frames de la ventana principal
ipcMain.on('broadcast-frame', (event, frameData) => {
  fullscreenWindows.forEach(win => {
    win.webContents.send('receive-frame', frameData);
  });
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