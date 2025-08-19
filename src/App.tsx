import React from 'react';
import LayerGrid from './components/LayerGrid';
import PreviewControls from './components/PreviewControls';

export default function App() {
  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 1, overflow: 'auto', borderBottom: '1px solid #ccc' }}>
        <LayerGrid />
      </div>
      <div style={{ flex: 1 }}>
        <PreviewControls />
      </div>
    </div>
  );
}
