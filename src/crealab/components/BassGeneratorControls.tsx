import React from 'react';
import { GenerativeTrack } from '../types/CrealabTypes';
import { EUCLIDEAN_PATTERNS } from '../utils/euclideanPatterns';
import './CreaLab.css';

interface Props {
  track: GenerativeTrack;
  onParametersChange: (params: Record<string, any>) => void;
}

const BassGeneratorControls: React.FC<Props> = ({ track, onParametersChange }) => {
  const patterns = Object.keys(EUCLIDEAN_PATTERNS.bass);
  const currentPattern = (track.generator.parameters as any).pattern || patterns[0];
  const variation = (track.generator.parameters as any).variation || 0;

  const handlePatternChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onParametersChange({ ...track.generator.parameters, pattern: e.target.value });
  };

  const handleVariationChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onParametersChange({ ...track.generator.parameters, variation: parseFloat(e.target.value) });
  };

  return (
    <div className="generator-controls">
      <div className="control-row">
        <label>Pattern</label>
        <select value={currentPattern} onChange={handlePatternChange}>
          {patterns.map(p => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>
      <div className="control-row">
        <label>Variation</label>
        <input type="range" min={0} max={1} step={0.01} value={variation} onChange={handleVariationChange} />
      </div>
    </div>
  );
};

export default BassGeneratorControls;
