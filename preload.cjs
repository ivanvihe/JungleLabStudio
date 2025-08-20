const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  applySettings: (settings) => ipcRenderer.send('apply-settings', settings),
  getDisplays: () => ipcRenderer.invoke('get-displays')
});
