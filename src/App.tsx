import React, { useState } from 'react';
import LayerGrid from './components/LayerGrid';
import PreviewControls from './components/PreviewControls';

export default function App() {
  const [tab, setTab] = useState<'live' | 'settings'>('live');

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <nav style={{ padding: 5 }}>
        <button onClick={() => setTab('live')}>Live Control</button>
        <button onClick={() => setTab('settings')}>Visual Settings</button>
      </nav>
      {tab === 'live' ? (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <div style={{ flex: 1, overflow: 'auto' }}>
            <LayerGrid />
          </div>
          <div style={{ flex: 1, borderTop: '1px solid #ccc' }}>
            <PreviewControls />
          </div>
        </div>
      ) : (
        <div style={{ padding: 20 }}>Settings coming soon...</div>
      )}
    </div>
  );
}
