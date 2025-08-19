import React, { useState } from 'react';
import LayerGrid from './components/LayerGrid';

export default function App() {
  const [tab, setTab] = useState<'live' | 'settings'>('live');

  return (
    <div>
      <nav>
        <button onClick={() => setTab('live')}>Live Control</button>
        <button onClick={() => setTab('settings')}>Visual Settings</button>
      </nav>
      {tab === 'live' ? <LayerGrid /> : <div>Settings coming soon...</div>}
    </div>
  );
}
