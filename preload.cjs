const { contextBridge, ipcRenderer } = require('electron');
const fs = require('fs');

contextBridge.exposeInMainWorld('electronAPI', {
  applySettings: (settings) => ipcRenderer.send('apply-settings', settings),
  getDisplays: () => ipcRenderer.invoke('get-displays'),
  toggleFullscreen: (ids) => ipcRenderer.invoke('toggle-fullscreen', ids),
  // Frame reception in cloned windows
  onReceiveFrame: (callback) => ipcRenderer.on('receive-frame', callback),
  removeFrameListener: () => ipcRenderer.removeAllListeners('receive-frame'),

  // Notification when the main window exits fullscreen
  onMainLeaveFullscreen: (callback) => ipcRenderer.on('main-leave-fullscreen', callback),
  removeMainLeaveFullscreenListener: () => ipcRenderer.removeAllListeners('main-leave-fullscreen'),
  tcpRequest: (command, port, host) => ipcRenderer.invoke('tcp-request', command, port, host),
  // Basic filesystem helpers for renderer
  readTextFile: (path) => fs.promises.readFile(path, 'utf-8'),
  writeTextFile: (path, contents) => fs.promises.writeFile(path, contents),
  createDir: (dir) => fs.promises.mkdir(dir, { recursive: true }),
  exists: (path) => Promise.resolve(fs.existsSync(path))
});
