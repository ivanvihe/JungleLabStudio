import React from 'react';
import { GenerativeTrack } from '../types/CrealabTypes';
import './CreaLab.css';

interface Props {
  track: GenerativeTrack;
  onKnobWheel: (
    field: keyof GenerativeTrack['controls'],
    e: React.WheelEvent
  ) => void;
}

const LaunchControlPreview: React.FC<Props> = ({ track, onKnobWheel }) => {
  return (
    <div className="launch-control-preview">
      <div className="lc-controls">
        <div className="lc-knobs">
          <div className="lc-knob" onWheel={e => onKnobWheel('paramA', e)}>
            <span className="knob-value">{track.controls.paramA}</span>
          </div>
          <div className="lc-knob" onWheel={e => onKnobWheel('paramB', e)}>
            <span className="knob-value">{track.controls.paramB}</span>
          </div>
          <div className="lc-knob" onWheel={e => onKnobWheel('paramC', e)}>
            <span className="knob-value">{track.controls.paramC}</span>
          </div>
        </div>
        <div className="lc-fader" onWheel={e => onKnobWheel('intensity', e)}>
          <div className="fader-track">
            <div
              className="fader-thumb"
              style={{ bottom: `${(track.controls.intensity / 127) * 60}px` }}
            />
          </div>
          <div className="fader-value">{track.controls.intensity}</div>
        </div>
        <div className="lc-buttons">
          <button className={`lc-button ${track.controls.mode ? 'active' : ''}`}>M</button>
        </div>
      </div>
    </div>
  );
};

export default LaunchControlPreview;
