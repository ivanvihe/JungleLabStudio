import React from 'react';
import { ChannelStrip } from '../types/GeneratorTypes';
import './LaunchControlVisualizer.css';

interface Props {
  strip: ChannelStrip | null;
}

const LaunchControlStrip: React.FC<Props> = ({ strip }) => {
  if (!strip) {
    return <div className="lcx-strip lcx-disconnected">No strip</div>;
  }

  return (
    <div className="lcx-strip">
      <div className="lcx-knobs">
        <div className="lcx-knob" style={{ ['--value' as any]: strip.values.knob1 }} />
        <div className="lcx-knob" style={{ ['--value' as any]: strip.values.knob2 }} />
        <div className="lcx-knob" style={{ ['--value' as any]: strip.values.knob3 }} />
      </div>
      <div className="lcx-fader">
        <div
          className="lcx-fader-thumb"
          style={{ ['--value' as any]: strip.values.fader }}
        />
      </div>
      <div className="lcx-buttons">
        <div className={`lcx-button ${strip.values.button1 ? 'active' : ''}`} />
        <div className={`lcx-button ${strip.values.button2 ? 'active' : ''}`} />
      </div>
    </div>
  );
};

export default LaunchControlStrip;
