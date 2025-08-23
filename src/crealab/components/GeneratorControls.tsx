import React from 'react';
import { GenerativeTrack } from '../types/CrealabTypes';
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

  return (
    <div className="generator-controls">
      <div className="control-row">
        <label>Intensity</label>
        <input type="range" min={0} max={127} value={track.controls.intensity}
          onChange={handleNumber('intensity')} />
      </div>
      <div className="control-row">
        <label>Param A</label>
        <input type="range" min={0} max={127} value={track.controls.paramA}
          onChange={handleNumber('paramA')} />
      </div>
      <div className="control-row">
        <label>Param B</label>
        <input type="range" min={0} max={127} value={track.controls.paramB}
          onChange={handleNumber('paramB')} />
      </div>
      <div className="control-row">
        <label>Param C</label>
        <input type="range" min={0} max={127} value={track.controls.paramC}
          onChange={handleNumber('paramC')} />
      </div>
      <div className="control-row buttons">
        <button onClick={() => onChange({ playStop: !track.controls.playStop })}>
          {track.controls.playStop ? 'Stop' : 'Play'}
        </button>
        <button onClick={() => onChange({ mode: (track.controls.mode + 1) % 6 })}>
          Cycle Generator
        </button>
      </div>
    </div>
  );
};

export default GeneratorControls;

