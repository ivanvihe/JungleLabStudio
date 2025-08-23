const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  applySettings: (settings) => ipcRenderer.send('apply-settings', settings),
  getDisplays: () => ipcRenderer.invoke('get-displays'),
  toggleFullscreen: (ids) => ipcRenderer.invoke('toggle-fullscreen', ids),
  // Frame reception in cloned windows
  onReceiveFrame: (callback) => ipcRenderer.on('receive-frame', callback),
  removeFrameListener: () => ipcRenderer.removeAllListeners('receive-frame'),

  // Notification when the main window exits fullscreen
  onMainLeaveFullscreen: (callback) => ipcRenderer.on('main-leave-fullscreen', callback),
  removeMainLeaveFullscreenListener: () => ipcRenderer.removeAllListeners('main-leave-fullscreen')
});
