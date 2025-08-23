import React, { useEffect, useState } from 'react';
import { GenerativeTrack } from '../types/CrealabTypes';
import { MODULE_KNOB_LABELS } from '../data/EurorackModules';
import './CreaLab.css';
import KnobControl from './KnobControl';

interface Props {
  track: GenerativeTrack;
  onChange: (changes: Partial<GenerativeTrack['controls']>) => void;
  mappingMode?: boolean;
}

export const GeneratorControls: React.FC<Props> = ({ track, onChange, mappingMode }) => {
  const handleNumber = (field: keyof GenerativeTrack['controls']) =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = Number(e.target.value);
      onChange({ [field]: value });
    };

  const handleMap = (field: keyof GenerativeTrack['controls']) => () => {
    if (!mappingMode) return;
    console.log(`MIDI mapping for ${field} not implemented`);
  };

    const labels = MODULE_KNOB_LABELS[track.trackType] || ['Intensity', 'Param A', 'Param B', 'Param C'];

  const [noteActive, setNoteActive] = useState(false);

  useEffect(() => {
    const handler = (e: any) => {
      if (e.detail.trackId === track.id) {
        setNoteActive(true);
        setTimeout(() => setNoteActive(false), 100);
      }
    };
    window.addEventListener('generatorNote', handler);
    return () => window.removeEventListener('generatorNote', handler);
  }, [track.id]);

  return (
    <div className={`generator-module${mappingMode ? ' mapping-mode' : ''}`}>
      <div className="module-header">
        <span>{track.trackType.toUpperCase()} Module</span>
        <span className={`activity-led ${noteActive ? 'on' : ''}`} />
      </div>
        <div className="control-row" onClick={handleMap('intensity')}>
          <label>{labels[0]}</label>
          <KnobControl value={track.controls.intensity} onChange={handleNumber('intensity')} />
        </div>
        <div className="control-row" onClick={handleMap('paramA')}>
          <label>{labels[1]}</label>
          <KnobControl value={track.controls.paramA} onChange={handleNumber('paramA')} />
        </div>
        <div className="control-row" onClick={handleMap('paramB')}>
          <label>{labels[2]}</label>
          <KnobControl value={track.controls.paramB} onChange={handleNumber('paramB')} />
        </div>
        <div className="control-row" onClick={handleMap('paramC')}>
          <label>{labels[3]}</label>
          <KnobControl value={track.controls.paramC} onChange={handleNumber('paramC')} />
        </div>
    </div>
  );
};

export default GeneratorControls;

