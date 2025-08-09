import { app, BrowserWindow, ipcMain } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';

let visualWindow;
let controlWindow;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function createVisualWindow() {
    visualWindow = new BrowserWindow({
        width: 1920,
        height: 1080,
        frame: false,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false
        }
    });
    visualWindow.loadFile(path.join(__dirname, 'renderer', 'main.html'));
}

function createControlWindow() {
    controlWindow = new BrowserWindow({
        width: 400,
        height: 600,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false
        }
    });
    controlWindow.loadFile(path.join(__dirname, 'renderer', 'controls.html'));
}

app.whenReady().then(() => {
    createVisualWindow();
    createControlWindow();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});

ipcMain.on('control-change', (_event, data) => {
    if (visualWindow) {
        visualWindow.webContents.send('control-change', data);
    }
});
