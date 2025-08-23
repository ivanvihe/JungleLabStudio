import React from 'react';
import './TopBar.css';

interface TopBarProps {
  projectName: string;
  tempo: number;
  onTempoChange: (tempo: number) => void;
  keySignature: string;
  onKeyChange: (key: string) => void;
  onSwitchToAudioVisualizer: () => void;
  onOpenMidiConfig: () => void;
  onOpenProjectManager: () => void;
  isPlaying: boolean;
  onPlayToggle: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  projectName,
  tempo,
  onTempoChange,
  keySignature,
  onKeyChange,
  onSwitchToAudioVisualizer,
  onOpenMidiConfig,
  onOpenProjectManager,
  isPlaying,
  onPlayToggle
}) => {
  return (
    <header className="topbar-container">
      <div className="topbar-left">
        <div className="topbar-title">
          <h1>🎼 Crea Lab</h1>
          <span className="project-name">{projectName}</span>
        </div>
        <button className="icon-btn" onClick={onOpenMidiConfig} title="MIDI Config">🎛️</button>
        <button className="icon-btn" onClick={onOpenProjectManager} title="Projects">📁</button>
      </div>

      <div className="topbar-center">
        <button className="play-btn" onClick={onPlayToggle}>{isPlaying ? '⏹️' : '▶️'}</button>
      </div>

      <div className="topbar-right">
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

          <button onClick={onSwitchToAudioVisualizer} className="switch-app-btn">🎨</button>
        </div>
      </div>
    </header>
  );
};

export default TopBar;

