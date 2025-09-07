import React, { useState, useEffect } from 'react';
import { LoadedPreset } from '../core/PresetLoader';

interface VFXControlsProps {
  preset: LoadedPreset;
  assignedLayers: string[];
  onToggle: (layerId: string, effect: string, enabled: boolean) => void;
}

const VFXControls: React.FC<VFXControlsProps> = ({ preset, assignedLayers, onToggle }) => {
  const [enabled, setEnabled] = useState<Record<string, Set<string>>>({});

  useEffect(() => {
    const initial: Record<string, Set<string>> = {};
    assignedLayers.forEach(l => {
      initial[l] = new Set();
    });
    setEnabled(initial);
  }, [assignedLayers, preset]);

  const handleToggle = (layer: string, effect: string, checked: boolean) => {
    setEnabled(prev => {
      const layerSet = new Set(prev[layer] || []);
      if (checked) {
        layerSet.add(effect);
      } else {
        layerSet.delete(effect);
      }
      return { ...prev, [layer]: layerSet };
    });
    onToggle(layer, effect, checked);
  };

  const effects = preset.config.vfx?.effects || [];

  return (
    <div className="vfx-controls">
      <div className="controls-header">
        <h3>{preset.config.name} VFX</h3>
      </div>
      {effects.length === 0 && <p>No effects available</p>}
      {effects.map((effect: any) => (
        <div key={effect.name} className="vfx-effect-group">
          <h4>{effect.label}</h4>
          {assignedLayers.length === 0 && <p>No layers assigned</p>}
          {assignedLayers.map(layer => (
            <label key={layer} className="layer-toggle">
              <input
                type="checkbox"
                checked={enabled[layer]?.has(effect.name) || false}
                onChange={e => handleToggle(layer, effect.name, e.target.checked)}
              />
              {layer}
            </label>
          ))}
        </div>
      ))}
    </div>
  );
};

export default VFXControls;
