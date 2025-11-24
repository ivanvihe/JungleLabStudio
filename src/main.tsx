import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Ensure global placeholders exist so any late-binding scripts (e.g. from
// Electron preload) don't hit a ReferenceError before React mounts.
declare global {
  interface Window {
    cronJobs?: unknown;
    projects?: unknown;
  }
}

if (typeof window !== 'undefined' && typeof window.cronJobs === 'undefined') {
  window.cronJobs = [];
}

if (typeof window !== 'undefined' && typeof window.projects === 'undefined') {
  window.projects = [];
}

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
