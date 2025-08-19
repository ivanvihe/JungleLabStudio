import React, { useState } from 'react';
import GridLayout from 'react-grid-layout';
import { invoke } from '@tauri-apps/api';

// Basic layer metadata used to render controls
const layers = [
  { id: 'A', midi: 14 },
  { id: 'B', midi: 15 },
  { id: 'C', midi: 16 },
];

// Pre-build a simple 4-pad layout (2x2) for each layer
const padLayout = [
  { i: '0', x: 0, y: 0, w: 1, h: 1 },
  { i: '1', x: 1, y: 0, w: 1, h: 1 },
  { i: '2', x: 0, y: 1, w: 1, h: 1 },
  { i: '3', x: 1, y: 1, w: 1, h: 1 },
];

type LayerId = 'A' | 'B' | 'C';

interface LayerState {
  opacity: number;
  fade: number;
  midi: number;
}

export default function LayerGrid() {
  const [state, setState] = useState<Record<LayerId, LayerState>>({
    A: { opacity: 1, fade: 0, midi: 14 },
    B: { opacity: 1, fade: 0, midi: 15 },
    C: { opacity: 1, fade: 0, midi: 16 },
  });

  const updateLayer = (layer: LayerId, values: Partial<LayerState>) => {
    const next = { ...state[layer], ...values };
    setState({ ...state, [layer]: next });
    if (values.opacity !== undefined) {
      invoke('set_layer_opacity', { layer, opacity: values.opacity });
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {layers.map((layer) => (
        <div
          key={layer.id}
          style={{ border: '1px solid #ccc', padding: 10, background: '#111', color: '#fff' }}
        >
          <h3 style={{ marginTop: 0 }}>Layer {layer.id}</h3>
          <GridLayout
            className="pads"
            layout={padLayout}
            cols={2}
            rowHeight={100}
            width={200}
            isDraggable={false}
            isResizable={false}
          >
            {padLayout.map((pad) => (
              <div
                key={pad.i}
                style={{
                  border: '1px solid #555',
                  background: '#333',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 12,
                }}
              >
                Pad {pad.i}
              </div>
            ))}
          </GridLayout>
          <div style={{ marginTop: 10, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <label>
              Opacity
              <input
                type="range"
                min={0}
                max={1}
                step={0.01}
                value={state[layer.id as LayerId].opacity}
                onChange={(e) =>
                  updateLayer(layer.id as LayerId, { opacity: parseFloat(e.target.value) })
                }
              />
            </label>
            <label>
              Fade (ms)
              <input
                type="number"
                min={0}
                value={state[layer.id as LayerId].fade}
                onChange={(e) =>
                  updateLayer(layer.id as LayerId, { fade: parseInt(e.target.value, 10) })
                }
                style={{ width: 80 }}
              />
            </label>
            <label>
              MIDI Ch
              <input
                type="number"
                min={0}
                max={127}
                value={state[layer.id as LayerId].midi}
                onChange={(e) =>
                  updateLayer(layer.id as LayerId, { midi: parseInt(e.target.value, 10) })
                }
                style={{ width: 60 }}
              />
            </label>
          </div>
        </div>
      ))}
    </div>
  );
}
