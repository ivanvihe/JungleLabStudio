import React from 'react';
import './KnobControl.css';

interface Props {
  value: number;
  onChange: (value: number) => void;
}

const KnobControl: React.FC<Props> = ({ value, onChange }) => {
  return (
    <div className="knob-control">
      <input
        type="range"
        min={0}
        max={127}
        value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="knob-range"
      />
      <div className="knob-display" style={{ ['--value' as any]: value }} />
    </div>
  );
};

export default KnobControl;
