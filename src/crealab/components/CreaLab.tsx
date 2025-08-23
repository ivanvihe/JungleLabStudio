import React, { useState } from 'react';
import { CreaLabProject, Track, Phase } from '../types/CrealabTypes';
import './CreaLab.css';

interface CreaLabProps {
  onSwitchToAudioVisualizer: () => void;
}

export const CreaLab: React.FC<CreaLabProps> = ({ onSwitchToAudioVisualizer }) => {
  const [project, setProject] = useState<CreaLabProject>({
    id: 'project-1',
    name: 'New Project',
    tracks: [
      { id: 'track-1', name: 'Track 1', midiDevice: '', clips: {} }
    ],
    phases: [
      { id: 'phase-1', name: 'Phase 1' }
    ],
    globalTempo: 128,
    key: 'C',
    scale: 'minor'
  });

  const addTrack = () => {
    const newTrack: Track = {
      id: `track-${Date.now()}`,
      name: `Track ${project.tracks!.length + 1}`,
      midiDevice: '',
      clips: {}
    };
    setProject(prev => ({
      ...prev,
      tracks: [...(prev.tracks || []), newTrack]
    }));
  };

  const renameTrack = (trackId: string, name: string) => {
    setProject(prev => ({
      ...prev,
      tracks: prev.tracks?.map(t => t.id === trackId ? { ...t, name } : t)
    }));
  };

  const assignMidi = (trackId: string, device: string) => {
    setProject(prev => ({
      ...prev,
      tracks: prev.tracks?.map(t => t.id === trackId ? { ...t, midiDevice: device } : t)
    }));
  };

  const addPhase = () => {
    const newPhase: Phase = {
      id: `phase-${Date.now()}`,
      name: `Phase ${project.phases!.length + 1}`
    };
    setProject(prev => ({
      ...prev,
      phases: [...(prev.phases || []), newPhase]
    }));
  };

  return (
    <div className="crealab-container">
      <header className="crealab-header">
        <div className="crealab-title">
          <h1>🎼 Crea Lab</h1>
          <span className="project-name">{project.name}</span>
        </div>

        <div className="crealab-controls">
          <div className="global-settings">
            <label>
              BPM:
              <input
                type="number"
                value={project.globalTempo}
                onChange={(e) => setProject(prev => ({
                  ...prev,
                  globalTempo: parseInt(e.target.value) || 128
                }))}
                min={60}
                max={200}
              />
            </label>
            <label>
              Key:
              <select
                value={project.key}
                onChange={(e) => setProject(prev => ({ ...prev, key: e.target.value }))}
              >
                {['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'].map(key => (
                  <option key={key} value={key}>{key}</option>
                ))}
              </select>
            </label>
          </div>

          <button onClick={onSwitchToAudioVisualizer} className="switch-app-btn">
            🎨 AudioVisualizer
          </button>
        </div>
      </header>

      <main className="crealab-workspace">
        <div className="track-view">
          <div className="section-column">
            <div className="section-header">Phases</div>
            {project.phases?.map(phase => (
              <div key={phase.id} className="section-label">{phase.name}</div>
            ))}
            <button onClick={addPhase} className="add-section">+ Phase</button>
          </div>

          {project.tracks?.map(track => (
            <div key={track.id} className="track-column">
              <div className="track-header">
                <input
                  value={track.name}
                  onChange={(e) => renameTrack(track.id, e.target.value)}
                />
                <input
                  value={track.midiDevice}
                  onChange={(e) => assignMidi(track.id, e.target.value)}
                  placeholder="MIDI Device"
                />
              </div>
              {project.phases?.map(phase => (
                <div key={phase.id} className="clip-slot">
                  {track.clips[phase.id]?.name || ''}
                </div>
              ))}
            </div>
          ))}

          <div className="add-track-column">
            <button onClick={addTrack}>+ Track</button>
          </div>
        </div>
      </main>
    </div>
  );
};
