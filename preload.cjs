const { contextBridge, ipcRenderer } = require('electron');
const fs = require('fs');
const path = require('path');

contextBridge.exposeInMainWorld('electronAPI', {
  applySettings: (settings) => ipcRenderer.send('apply-settings', settings),
  getDisplays: () => ipcRenderer.invoke('get-displays'),
  toggleFullscreen: (ids) => ipcRenderer.invoke('toggle-fullscreen', ids),
  // Recepción de frames en ventanas clon
  onReceiveFrame: (callback) => ipcRenderer.on('receive-frame', callback),
  removeFrameListener: () => ipcRenderer.removeAllListeners('receive-frame'),

  // Notificación cuando la ventana principal sale de fullscreen
  onMainLeaveFullscreen: (callback) => ipcRenderer.on('main-leave-fullscreen', callback),
  removeMainLeaveFullscreenListener: () => ipcRenderer.removeAllListeners('main-leave-fullscreen'),

  // File system helpers
  readTextFile: (filePath) => fs.promises.readFile(filePath, 'utf-8'),
  writeTextFile: async (filePath, data) => {
    const dir = path.dirname(filePath);
    await fs.promises.mkdir(dir, { recursive: true });
    await fs.promises.writeFile(filePath, data);
  },
  exists: async (filePath) => {
    try {
      await fs.promises.access(filePath);
      return true;
    } catch {
      return false;
    }
  }
});
