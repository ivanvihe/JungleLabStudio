import React, { useState } from 'react';
import { useMidiDevices } from '../hooks/useMidiDevices';
import './MidiConfiguration.css';

interface Props {
  onClose: () => void;
}

export const MidiConfiguration: React.FC<Props> = ({ onClose }) => {
  const { inputDevices, outputDevices, midiClock, testDevice, refreshDevices } = useMidiDevices();
  const [testing, setTesting] = useState<string | null>(null);

  const handleTest = async (id: string) => {
    setTesting(id);
    await testDevice(id);
    setTesting(null);
  };

  return (
    <div className="midi-configuration-overlay">
      <div className="midi-configuration-modal">
        <div className="modal-header">
          <h3>MIDI Configuration</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="config-section">
          <div className="section-header">
            <h4>Clock</h4>
          </div>
          <div className="clock-status">
            <div className={`status-indicator ${midiClock.isRunning ? 'running' : 'stopped'}`}></div>
            <span>{midiClock.isRunning ? 'Running' : 'Stopped'} @ {midiClock.bpm} BPM</span>
          </div>
        </div>

        <div className="config-section">
          <div className="section-header">
            <h4>Input Devices</h4>
            <button className="refresh-btn" onClick={refreshDevices}>Refresh</button>
          </div>
          <div className="devices-list">
            {inputDevices.length === 0 && (
              <div className="no-devices">No input devices</div>
            )}
            {inputDevices.map(dev => (
              <div key={dev.id} className="device-item">
                <div className="device-info">
                  <div className="device-name">{dev.name}</div>
                  <div className="device-manufacturer">{dev.manufacturer}</div>
                  <div className={`device-status ${dev.state}`}>{dev.state}</div>
                </div>
                <button
                  className={`test-btn ${testing === dev.id ? 'testing' : ''}`}
                  disabled={testing === dev.id}
                  onClick={() => handleTest(dev.id)}
                >
                  {testing === dev.id ? '...' : 'Test'}
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="config-section">
          <div className="section-header">
            <h4>Output Devices</h4>
            <button className="refresh-btn" onClick={refreshDevices}>Refresh</button>
          </div>
          <div className="devices-list">
            {outputDevices.length === 0 && (
              <div className="no-devices">No output devices</div>
            )}
            {outputDevices.map(dev => (
              <div key={dev.id} className="device-item">
                <div className="device-info">
                  <div className="device-name">{dev.name}</div>
                  <div className="device-manufacturer">{dev.manufacturer}</div>
                  <div className={`device-status ${dev.state}`}>{dev.state}</div>
                </div>
                <button
                  className={`test-btn ${testing === dev.id ? 'testing' : ''}`}
                  disabled={testing === dev.id}
                  onClick={() => handleTest(dev.id)}
                >
                  {testing === dev.id ? '...' : 'Test'}
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MidiConfiguration;
