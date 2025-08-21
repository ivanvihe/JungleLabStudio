const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  applySettings: (settings) => ipcRenderer.send('apply-settings', settings),
  getDisplays: () => ipcRenderer.invoke('get-displays'),
  toggleFullscreen: (ids) => ipcRenderer.invoke('toggle-fullscreen', ids),
  // Recepción de frames en ventanas clon
  onReceiveFrame: (callback) => ipcRenderer.on('receive-frame', callback),
  removeFrameListener: () => ipcRenderer.removeAllListeners('receive-frame'),

  // Notificación cuando la ventana principal sale de fullscreen
  onMainLeaveFullscreen: (callback) => ipcRenderer.on('main-leave-fullscreen', callback),
  removeMainLeaveFullscreenListener: () => ipcRenderer.removeAllListeners('main-leave-fullscreen')
});
