import React, { useState } from 'react';
import GridLayout from 'react-grid-layout';
import { invoke } from '@tauri-apps/api';

const layers = [
  { id: 'A', midi: 14 },
  { id: 'B', midi: 15 },
  { id: 'C', midi: 16 },
];

export default function LayerGrid() {
  const [opacities, setOpacities] = useState({ A: 1, B: 1, C: 1 });

  const layout = layers.map((l, i) => ({ i: l.id, x: 0, y: i, w: 1, h: 1 }));

  const handleChange = (layer: 'A' | 'B' | 'C', value: number) => {
    setOpacities({ ...opacities, [layer]: value });
    invoke('set_layer_opacity', { layer, opacity: value });
  };

  return (
    <GridLayout className="layout" layout={layout} cols={1} rowHeight={100} width={300}>
      {layers.map((layer) => (
        <div key={layer.id} style={{ padding: 10 }}>
          <h3>Layer {layer.id} (MIDI {layer.midi})</h3>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={opacities[layer.id as 'A' | 'B' | 'C']}
            onChange={(e) =>
              handleChange(layer.id as 'A' | 'B' | 'C', parseFloat(e.target.value))
            }
          />
        </div>
      ))}
    </GridLayout>
  );
}
