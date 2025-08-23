import React from 'react';
import { GenerativeTrack } from '../types/CrealabTypes';
import { euclideanRhythm } from '../utils/euclideanPatterns';
import './EuclideanCirclesModule.css';

interface Props {
  track: GenerativeTrack;
  onParametersChange: (params: Record<string, any>) => void;
}

const EuclideanCirclesModule: React.FC<Props> = ({ track, onParametersChange }) => {
  const params = track.generator.parameters as any;
  const pulses = params.pulses ?? 8;
  const steps = params.steps ?? 16;
  const offset = params.offset ?? 0;

  const pattern = euclideanRhythm(pulses, steps, offset);

  const handleChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = Number(e.target.value);
    onParametersChange({ ...params, [field]: value });
  };

  return (
    <div className="euclidean-circles-module">
      <div className="circle">
        {pattern.map((hit, idx) => {
          const angle = (idx / steps) * 360;
          return (
            <div
              key={idx}
              className={`step ${hit ? 'hit' : ''}`}
              style={{ transform: `rotate(${angle}deg) translate(40px) rotate(-${angle}deg)` }}
            />
          );
        })}
      </div>
      <div className="controls">
        <label>
          Pulses
          <input type="number" min={1} max={steps} value={pulses} onChange={handleChange('pulses')} />
        </label>
        <label>
          Steps
          <input type="number" min={1} max={32} value={steps} onChange={handleChange('steps')} />
        </label>
        <label>
          Offset
          <input type="number" min={0} max={steps - 1} value={offset} onChange={handleChange('offset')} />
        </label>
      </div>
    </div>
  );
};

export default EuclideanCirclesModule;
