import React from 'react';

const layers = ['1', '2', '3'];

// Load all visual preset modules at startup
const presetModules = import.meta.glob('../../visuals/presets/*.ts', { eager: true }) as Record<string, { default: { name: string } }>;
const presets = Object.values(presetModules).map((m) => m.default.name);

export default function LayerGrid() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      {layers.map((layer, layerIndex) => (
        <div
          key={layer}
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: '8px 0',
            borderBottom: layerIndex < layers.length - 1 ? '1px solid #444' : undefined,
          }}
        >
          <span style={{ width: 70 }}>Layer {layer}</span>
          <div style={{ display: 'flex', gap: 10, flex: 1 }}>
            {presets.map((name, i) => (
              <button
                key={i}
                style={{
                  flex: 1,
                  padding: 20,
                  background: '#333',
                  color: '#fff',
                  border: '1px solid #555',
                  cursor: 'pointer',
                }}
              >
                {name}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
