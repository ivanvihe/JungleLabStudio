import React, { useState } from 'react';
import { useMidiDevices } from '../hooks/useMidiDevices';
import './MidiConfiguration.css';

interface DeviceSettings {
  track: boolean;
  sync: boolean;
  output: boolean;
}

interface Props {
  onClose: () => void;
}

export const MidiConfiguration: React.FC<Props> = ({ onClose }) => {
  const { inputDevices, outputDevices, refreshDevices } = useMidiDevices();
  const [globalController, setGlobalController] = useState('');
  const [settings, setSettings] = useState<Record<string, DeviceSettings>>({});

  const allDevices = [...inputDevices, ...outputDevices].filter(
    (d, i, arr) => arr.findIndex(dev => dev.id === d.id) === i
  );

  const toggle = (id: string, key: keyof DeviceSettings) => {
    setSettings(prev => ({
      ...prev,
      [id]: { ...prev[id], [key]: !prev[id]?.[key] }
    }));
  };

  return (
    <div className="midi-configuration-overlay">
      <div className="midi-configuration-modal">
        <div className="modal-header">
          <h3>MIDI Configuration</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="config-section">
          <h4>Global MIDI controller</h4>
          <select
            className="global-controller-select"
            value={globalController}
            onChange={e => setGlobalController(e.target.value)}
          >
            <option value="">Select device</option>
            {inputDevices.map(dev => (
              <option key={dev.id} value={dev.id}>{dev.name}</option>
            ))}
          </select>
        </div>

        <div className="config-section">
          <div className="section-header">
            <h4>Other MIDI devices</h4>
            <button className="refresh-btn" onClick={refreshDevices}>Refresh</button>
          </div>
          <div className="device-grid">
            <div className="device-grid-header">
              <span>Device</span>
              <span>Track</span>
              <span>Sync</span>
              <span>Output</span>
            </div>
            {allDevices.map(dev => (
              <div key={dev.id} className="device-grid-row">
                <span>{dev.name}</span>
                <input
                  type="checkbox"
                  checked={!!settings[dev.id]?.track}
                  onChange={() => toggle(dev.id, 'track')}
                />
                <input
                  type="checkbox"
                  checked={!!settings[dev.id]?.sync}
                  onChange={() => toggle(dev.id, 'sync')}
                />
                <input
                  type="checkbox"
                  checked={!!settings[dev.id]?.output}
                  onChange={() => toggle(dev.id, 'output')}
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MidiConfiguration;
