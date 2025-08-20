import React from 'react';

interface DeviceOption {
  id: string;
  label: string;
}

interface GlobalSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  audioDevices: DeviceOption[];
  midiDevices: DeviceOption[];
    selectedAudioId: string | null;
    selectedMidiId: string | null;
    onSelectAudio: (id: string) => void;
    onSelectMidi: (id: string) => void;
    audioGain: number;
    onAudioGainChange: (value: number) => void;
    monitors: DeviceOption[];
    selectedMonitors: string[];
    onToggleMonitor: (id: string) => void;
    glitchTextPads: number;
    onGlitchPadChange: (value: number) => void;
  }

export const GlobalSettingsModal: React.FC<GlobalSettingsModalProps> = ({
  isOpen,
  onClose,
  audioDevices,
  midiDevices,
  selectedAudioId,
  selectedMidiId,
  onSelectAudio,
    onSelectMidi,
    audioGain,
    onAudioGainChange,
    monitors,
    selectedMonitors,
    onToggleMonitor,
    glitchTextPads,
    onGlitchPadChange
  }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Global Settings</h2>
        <div className="modal-section">
          <h3>Audio</h3>
          <label>
            Dispositivo de entrada:
            <select
              value={selectedAudioId || ''}
              onChange={(e) => onSelectAudio(e.target.value)}
            >
              <option value="">Default</option>
              {audioDevices.map(dev => (
                <option key={dev.id} value={dev.id}>{dev.label}</option>
              ))}
            </select>
          </label>
          <label>
            Ganancia de entrada:
            <input
              type="range"
              min={0}
              max={2}
              step={0.01}
              value={audioGain}
              onChange={(e) => onAudioGainChange(parseFloat(e.target.value))}
            />
          </label>
        </div>

        <div className="modal-section">
          <h3>MIDI</h3>
          <label>
            Dispositivo de entrada:
            <select
              value={selectedMidiId || ''}
              onChange={(e) => onSelectMidi(e.target.value)}
            >
              <option value="">Default</option>
              {midiDevices.map(dev => (
                <option key={dev.id} value={dev.id}>{dev.label}</option>
              ))}
            </select>
          </label>
          </div>

          <div className="modal-section">
            <h3>Full Screen Monitors</h3>
            {monitors.map(mon => (
              <label key={mon.id} className="monitor-option">
                <input
                  type="checkbox"
                  checked={selectedMonitors.includes(mon.id)}
                  onChange={() => onToggleMonitor(mon.id)}
                />
                {mon.label}
              </label>
            ))}
          </div>

          <div className="modal-section">
            <h3>Global Visual Settings</h3>
            <label>
              Glitch text pads:
              <input
                type="number"
                min={1}
                max={8}
                value={glitchTextPads}
                onChange={(e) => onGlitchPadChange(parseInt(e.target.value))}
              />
            </label>
          </div>

          <button onClick={onClose}>Cerrar</button>
        </div>
      </div>
    );
  };
