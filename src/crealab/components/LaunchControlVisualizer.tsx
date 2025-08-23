import React from 'react';
import { SessionMidiController } from '../types/GeneratorTypes';
import './LaunchControlVisualizer.css';

interface Props {
  controller: SessionMidiController | null;
}

/**
 * Visual representation of the Launch Control XL state. It renders eight
 * channel strips with knobs, a fader and two buttons each.
 */
export const LaunchControlVisualizer: React.FC<Props> = ({ controller }) => {
  if (!controller) {
    return <div className="lcx-container lcx-disconnected">No controller</div>;
  }

  return (
    <div className="lcx-container">
      {controller.channelStrips.map(strip => (
        <div key={strip.stripIndex} className="lcx-strip">
          <div className="lcx-knobs">
            <div
              className="lcx-knob"
              style={{ ['--value' as any]: strip.values.knob1 }}
            />
            <div
              className="lcx-knob"
              style={{ ['--value' as any]: strip.values.knob2 }}
            />
            <div
              className="lcx-knob"
              style={{ ['--value' as any]: strip.values.knob3 }}
            />
          </div>
          <div className="lcx-fader">
            <div
              className="lcx-fader-thumb"
              style={{ ['--value' as any]: strip.values.fader }}
            />
          </div>
          <div className="lcx-buttons">
            <div
              className={`lcx-button ${strip.values.button1 ? 'active' : ''}`}
            />
            <div
              className={`lcx-button ${strip.values.button2 ? 'active' : ''}`}
            />
          </div>
        </div>
      ))}
    </div>
  );
};

export default LaunchControlVisualizer;
