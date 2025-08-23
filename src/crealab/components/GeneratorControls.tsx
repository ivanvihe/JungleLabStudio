import React from 'react';
import { GenerativeTrack } from '../types/CrealabTypes';
import { MODULE_KNOB_LABELS } from '../data/EurorackModules';
import './CreaLab.css';

interface Props {
  track: GenerativeTrack;
  onChange: (changes: Partial<GenerativeTrack['controls']>) => void;
}

export const GeneratorControls: React.FC<Props> = ({ track, onChange }) => {
  const handleNumber = (field: keyof GenerativeTrack['controls']) =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = Number(e.target.value);
      onChange({ [field]: value });
    };

  const labels = MODULE_KNOB_LABELS[track.trackType] || ['Param A', 'Param B', 'Param C'];

  return (
    <div className="generator-module">
      <div className="module-header">
        <span>{track.trackType.toUpperCase()} Module</span>
        <span className={`activity-led ${track.generator.enabled ? 'on' : ''}`} />
      </div>
      <div className="control-row">
        <label>Intensity</label>
        <input type="range" min={0} max={127} value={track.controls.intensity}
          onChange={handleNumber('intensity')} />
        <span className="control-display">{track.controls.intensity}</span>
      </div>
      <div className="control-row">
        <label>{labels[0]}</label>
        <input type="range" min={0} max={127} value={track.controls.paramA}
          onChange={handleNumber('paramA')} />
        <span className="control-display">{track.controls.paramA}</span>
      </div>
      <div className="control-row">
        <label>{labels[1]}</label>
        <input type="range" min={0} max={127} value={track.controls.paramB}
          onChange={handleNumber('paramB')} />
        <span className="control-display">{track.controls.paramB}</span>
      </div>
      <div className="control-row">
        <label>{labels[2]}</label>
        <input type="range" min={0} max={127} value={track.controls.paramC}
          onChange={handleNumber('paramC')} />
        <span className="control-display">{track.controls.paramC}</span>
      </div>
    </div>
  );
};

export default GeneratorControls;

