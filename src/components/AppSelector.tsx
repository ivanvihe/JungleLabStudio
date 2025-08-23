import React from 'react';
import './AppSelector.css';

export type AppMode = 'audiovisualizer' | 'crealab';

interface AppSelectorProps {
  onSelectApp: (app: AppMode) => void;
}

export const AppSelector: React.FC<AppSelectorProps> = ({ onSelectApp }) => {
  return (
    <div className="app-selector-overlay">
      <div className="app-selector-modal">
        <div className="app-selector-header">
          <h1>🌿 Jungle Lab Studio</h1>
          <p>Choose your creative workspace</p>
        </div>
        
        <div className="app-selector-options">
          <div 
            className="app-option audiovisualizer"
            onClick={() => onSelectApp('audiovisualizer')}
          >
            <div className="app-icon">🎨</div>
            <h2>AudioVisualizer</h2>
            <p>Real-time audio visualization engine</p>
            <div className="app-features">
              <span>• Live MIDI control</span>
              <span>• Visual presets</span>
              <span>• Multi-layer composition</span>
              <span>• Real-time effects</span>
            </div>
            <button className="app-button av-button">
              Open AudioVisualizer
            </button>
          </div>

          <div 
            className="app-option crealab"
            onClick={() => onSelectApp('crealab')}
          >
            <div className="app-icon">🎼</div>
            <h2>Crea Lab</h2>
            <p>MIDI generation & creative assistant</p>
            <div className="app-features">
              <span>• Euclidean rhythm generation</span>
              <span>• Scale-based composition</span>
              <span>• Scene management</span>
              <span>• Ableton integration</span>
            </div>
            <button className="app-button cl-button">
              Open Crea Lab
            </button>
          </div>
        </div>
        
        <div className="app-selector-footer">
          <p>You can switch between apps at any time</p>
        </div>
      </div>
    </div>
  );
};
