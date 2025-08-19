const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
      // Removido webSecurity: false
    },
  });

  // Para debugging, abrir DevTools automáticamente
  win.webContents.openDevTools();

  const startUrl = process.env.NODE_ENV === 'development'
    ? 'http://localhost:3000'  // Cambiado de 5173 a 3000 (puerto de Vite por defecto)
    : path.join(__dirname, 'dist', 'index.html');

  console.log('Loading URL:', startUrl);

  if (startUrl.startsWith('http')) {
    win.loadURL(startUrl);
  } else {
    win.loadFile(startUrl);
  }

  // Log cuando la página esté lista
  win.webContents.once('did-finish-load', () => {
    console.log('✅ Page loaded successfully');
  });

  // Log errores de carga
  win.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('❌ Failed to load page:', errorCode, errorDescription);
  });

  // Log errores de consola de la página
  win.webContents.on('console-message', (event, level, message, line, sourceId) => {
    console.log(`Console [${level}]:`, message);
  });
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

// Para debugging
app.on('ready', () => {
  console.log('🚀 Electron app is ready');
  console.log('Environment:', process.env.NODE_ENV || 'production');
});