const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');

let controlWindow;  // Ventana de controles
let visualWindow;   // Ventana de visualización
// Ventanas usadas para monitores secundarios en fullscreen
let fullscreenWindows = [];
let mirrorInterval = null;
const isDev = process.env.NODE_ENV === 'development';
const baseUrl = isDev
  ? 'http://localhost:3000'
  : `file://${path.join(__dirname, 'dist', 'index.html')}`;

function closeFullscreenWindows() {
  fullscreenWindows.forEach(win => {
    if (!win.isDestroyed()) {
      win.close();
    }
  });
  fullscreenWindows = [];
  if (mirrorInterval) {
    clearInterval(mirrorInterval);
    mirrorInterval = null;
  }
}

function createWindow() {
  // Ventana de controles (sin canvas)
  controlWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    x: 100,
    y: 100,
    title: 'Jungle Lab Studio - Controls',
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.cjs')
    },
  });

  // Ventana de visualización (solo canvas)
  visualWindow = new BrowserWindow({
    width: 1920,
    height: 1080,
    x: 1500,
    y: 100,
    title: 'Jungle Lab Studio - Visual Output',
    backgroundColor: '#000000',
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.cjs')
    },
  });

  const controlUrl = `${baseUrl}${isDev ? '' : ''}?mode=control`;
  const visualUrl = `${baseUrl}${isDev ? '' : ''}?mode=visual`;

  console.log('Loading Control URL:', controlUrl);
  console.log('Loading Visual URL:', visualUrl);

  controlWindow.loadURL(controlUrl);
  visualWindow.loadURL(visualUrl);

  controlWindow.once('ready-to-show', () => {
    controlWindow.show();
  });

  visualWindow.once('ready-to-show', () => {
    visualWindow.show();
  });

  // Log when the pages are ready
  controlWindow.webContents.once('did-finish-load', () => {
    console.log('✅ Control window loaded successfully');
  });

  visualWindow.webContents.once('did-finish-load', () => {
    console.log('✅ Visual window loaded successfully');
  });

  // Log errores de carga
  controlWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('❌ Failed to load control window:', errorCode, errorDescription);
  });

  visualWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('❌ Failed to load visual window:', errorCode, errorDescription);
  });

  // Log console errors from the pages
  controlWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    console.log(`Control [${level}]:`, message);
  });

  visualWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    console.log(`Visual [${level}]:`, message);
  });

  // Si el usuario sale del modo fullscreen manualmente, cerrar las ventanas
  // secundarias y notificar al renderer para que actualice su estado
  controlWindow.on('leave-full-screen', () => {
    closeFullscreenWindows();
    controlWindow.webContents.send('main-leave-fullscreen');
  });

  controlWindow.on('closed', () => {
    controlWindow = null;
    // Cerrar también la ventana visual
    if (visualWindow && !visualWindow.isDestroyed()) {
      visualWindow.close();
    }
    closeFullscreenWindows();
    app.quit();
  });

  visualWindow.on('closed', () => {
    visualWindow = null;
    // Si cierran la ventana visual, cerrar también la de control
    if (controlWindow && !controlWindow.isDestroyed()) {
      controlWindow.close();
    }
  });
}

ipcMain.on('apply-settings', (event, settings) => {
  if (!visualWindow) return;
  if (settings.monitorId) {
    const displays = screen.getAllDisplays();
    // Allow monitor identifiers as strings to avoid precision issues
    const target = displays.find(d => d.id.toString() === settings.monitorId.toString());
    if (target) {
      visualWindow.setBounds(target.bounds);
    }
  }
  if (settings.maximize) {
    visualWindow.maximize();
  }
  if (!visualWindow.isVisible()) {
    visualWindow.show();
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
  // Si ya hay ventanas de fullscreen abiertas, cerrar y restaurar visual window
  if (fullscreenWindows.length) {
    closeFullscreenWindows();
    if (visualWindow) {
      visualWindow.setFullScreen(false);
      visualWindow.show();
    }
    return;
  }

  const displays = screen.getAllDisplays();

  ids.forEach((id, index) => {
    // Compare using string values to support large identifiers
    const display = displays.find(d => d.id.toString() === id.toString());
    if (!display) return;

    if (index === 0 && visualWindow) {
      // Usar la ventana visual para el primer monitor sin recargar
      visualWindow.setBounds(display.bounds);
      visualWindow.setFullScreen(true);
      visualWindow.show();
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
        if (fullscreenWindows.length === 0 && visualWindow) {
          visualWindow.setFullScreen(false);
          visualWindow.show();
          if (mirrorInterval) {
            clearInterval(mirrorInterval);
            mirrorInterval = null;
          }
        }
      });

      fullscreenWindows.push(win);
    }
  });

  if (fullscreenWindows.length && !mirrorInterval && visualWindow) {
    mirrorInterval = setInterval(() => {
      visualWindow.webContents.capturePage().then(image => {
        const buffer = image.toJPEG(70);
        fullscreenWindows.forEach(win => {
          win.webContents.send('receive-frame', buffer);
        });
      }).catch(err => console.error('capturePage error:', err));
    }, 33);
  }
});

const net = require('net');

ipcMain.handle('tcp-request', (event, command, port, host) => {
  return new Promise((resolve, reject) => {
    const socket = new net.Socket();
    let buffer = '';

    socket.connect(port, host, () => {
      socket.write(JSON.stringify(command));
    });

    socket.on('data', (chunk) => {
      buffer += chunk.toString('utf-8');
      try {
        const parsed = JSON.parse(buffer);
        if (parsed && parsed.status) {
          socket.destroy();
          if (parsed.status === 'ok') {
            resolve(parsed.result);
          } else {
            reject(new Error(parsed.message || 'Remote error'));
          }
        }
      } catch {
        // Wait for more data
      }
    });

    socket.on('error', (err) => {
      socket.destroy();
      reject(err);
    });

    setTimeout(() => {
      if (buffer.length === 0) {
        socket.destroy();
        reject(new Error('Remote timeout'));
      }
    }, 3000);
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
