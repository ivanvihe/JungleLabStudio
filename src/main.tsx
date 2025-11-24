import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Ensure the global cronJobs placeholder exists so any late-binding scripts
// (e.g. from Electron preload) don't hit a ReferenceError before React mounts.
declare global {
  interface Window {
    cronJobs?: unknown;
  }
}

if (typeof window !== 'undefined' && typeof window.cronJobs === 'undefined') {
  window.cronJobs = [];
}

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
