import React from 'react';
import './TopBar.css';

interface TopBarProps {
  projectName: string;
  tempo: number;
  onTempoChange: (tempo: number) => void;
  keySignature: string;
  onKeyChange: (key: string) => void;
  onSwitchToAudioVisualizer: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  projectName,
  tempo,
  onTempoChange,
  keySignature,
  onKeyChange,
  onSwitchToAudioVisualizer
}) => {
  return (
    <header className="topbar-container">
      <div className="topbar-title">
        <h1>🎼 Crea Lab</h1>
        <span className="project-name">{projectName}</span>
      </div>

      <div className="topbar-controls">
        <div className="global-settings">
          <label>
            BPM:
            <input
              type="number"
              value={tempo}
              min={60}
              max={200}
              onChange={e => onTempoChange(parseInt(e.target.value) || 0)}
            />
          </label>
          <label>
            Key:
            <select value={keySignature} onChange={e => onKeyChange(e.target.value)}>
              {['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'].map(k => (
                <option key={k} value={k}>{k}</option>
              ))}
            </select>
          </label>
        </div>

        <button onClick={onSwitchToAudioVisualizer} className="switch-app-btn">
          🎨 AudioVisualizer
        </button>
      </div>
    </header>
  );
};

export default TopBar;

