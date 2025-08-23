import React, { useState } from 'react';
import { CreaLabProject, Scene } from '../types/CrealabTypes';
import './CreaLab.css';

interface CreaLabProps {
  onSwitchToAudioVisualizer: () => void;
}

export const CreaLab: React.FC<CreaLabProps> = ({ onSwitchToAudioVisualizer }) => {
  const [project, setProject] = useState<CreaLabProject>({
    id: 'project-1',
    name: 'New Project',
    scenes: [],
    globalTempo: 128,
    key: 'C',
    scale: 'minor'
  });

  const [selectedScene, setSelectedScene] = useState<string | null>(null);

  const createNewScene = () => {
    const newScene: Scene = {
      id: `scene-${Date.now()}`,
      name: `Scene ${project.scenes.length + 1}`,
      duration: 8,
      tempo: project.globalTempo,
      clips: [],
      visualConfig: {
        primaryPreset: '',
        layerPresets: {},
        triggers: []
      },
      musicalContext: 'intro'
    };
    
    setProject(prev => ({
      ...prev,
      scenes: [...prev.scenes, newScene]
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
        <div className="scenes-panel">
          <div className="scenes-header">
            <h3>Scenes</h3>
            <button onClick={createNewScene} className="add-scene-btn">+ Add Scene</button>
          </div>
          
          <div className="scenes-list">
            {project.scenes.map(scene => (
              <div 
                key={scene.id}
                className={`scene-item ${selectedScene === scene.id ? 'selected' : ''}`}
                onClick={() => setSelectedScene(scene.id)}
              >
                <span className="scene-name">{scene.name}</span>
                <span className="scene-info">{scene.duration} bars</span>
              </div>
            ))}
            
            {project.scenes.length === 0 && (
              <div className="no-scenes">
                <p>No scenes yet</p>
                <p>Create your first scene to start composing</p>
              </div>
            )}
          </div>
        </div>

        <div className="main-workspace">
          {selectedScene ? (
            <div className="scene-editor">
              <h2>Scene Editor</h2>
              <p>Selected scene: {project.scenes.find(s => s.id === selectedScene)?.name}</p>
              <p className="coming-soon">MIDI Grid and clip editor coming soon...</p>
            </div>
          ) : (
            <div className="no-scene-selected">
              <div className="welcome-message">
                <h2>Welcome to Crea Lab</h2>
                <p>Your MIDI generation and creative assistant</p>
                <div className="quick-actions">
                  <button onClick={createNewScene} className="primary-btn">
                    Create First Scene
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
