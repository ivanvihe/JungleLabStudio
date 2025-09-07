import React from 'react';
import { LoadedPreset } from '../core/PresetLoader';

interface VFXControlsProps {
  preset: LoadedPreset;
  assignedLayers: string[];
  onTrigger: (layerId: string, effect: string) => void;
}

const VFXControls: React.FC<VFXControlsProps> = ({ preset, assignedLayers, onTrigger }) => {
  return (
    <div className="vfx-controls">
      <div className="controls-header">
        <h3>{preset.config.name} VFX</h3>
      </div>
      {assignedLayers.length === 0 && <p>No layers assigned</p>}
      {assignedLayers.map(layer => (
        <button key={layer} onClick={() => onTrigger(layer, 'flash')}>
          Flash layer {layer}
        </button>
      ))}
    </div>
  );
};

export default VFXControls;
