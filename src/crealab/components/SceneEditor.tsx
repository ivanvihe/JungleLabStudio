import React from 'react';
import { Scene, MidiClip, TrackType } from '../types/CrealabTypes';
import { MidiClipGenerator } from '../core/MidiClipGenerator';
import { MidiExporter } from '../core/MidiExporter';
import './SceneEditor.css';

interface SceneEditorProps {
  scene: Scene;
  onUpdateScene: (updates: Partial<Scene>) => void;
  globalTempo: number;
  projectKey: string;
  projectScale: string;
}

export const SceneEditor: React.FC<SceneEditorProps> = ({
  scene,
  onUpdateScene,
  globalTempo,
  projectKey,
  projectScale
}) => {
  const clipGenerator = MidiClipGenerator.getInstance();

  const trackTypes: { type: TrackType; label: string; icon: string }[] = [
    { type: 'kick', label: 'Kick', icon: '🥁' },
    { type: 'bass', label: 'Bass', icon: '🎸' },
    { type: 'arp', label: 'Arp', icon: '🎹' },
    { type: 'lead', label: 'Lead', icon: '🎵' },
    { type: 'fx', label: 'FX/Chords', icon: '✨' },
    { type: 'perc', label: 'Perc', icon: '🔔' },
    { type: 'visual', label: 'Visual', icon: '🎨' }
  ];

  const generateClip = (trackType: TrackType) => {
    let newClip: MidiClip;
    
    switch (trackType) {
      case 'kick':
        newClip = clipGenerator.generateKick('dub', scene.duration, 10);
        break;
      case 'bass':
        newClip = clipGenerator.generateBass(projectKey, projectScale, 'dub', scene.duration, 1);
        break;
      case 'arp':
        newClip = clipGenerator.generateArpeggio(projectKey, 'dorian', 'floating', scene.duration, 2);
        break;
      case 'fx':
        newClip = clipGenerator.generateChordProgression(projectKey, 'dubClassic', scene.duration, 3);
        break;
      default:
        // Create empty clip for other types
        newClip = {
          id: `${trackType}-${Date.now()}`,
          name: `${trackType} clip`,
          trackType,
          notes: [],
          duration: scene.duration,
          channel: 4,
          enabled: true
        };
    }
    
    const updatedClips = [...scene.clips, newClip];
    onUpdateScene({ clips: updatedClips });
  };

  const removeClip = (clipId: string) => {
    const updatedClips = scene.clips.filter(clip => clip.id !== clipId);
    onUpdateScene({ clips: updatedClips });
  };

  const toggleClip = (clipId: string) => {
    const updatedClips = scene.clips.map(clip => 
      clip.id === clipId ? { ...clip, enabled: !clip.enabled } : clip
    );
    onUpdateScene({ clips: updatedClips });
  };

  const getClipsForTrackType = (trackType: TrackType) => {
    return scene.clips.filter(clip => clip.trackType === trackType);
  };

  const exportScene = () => {
    const content = MidiExporter.exportSceneToAbleton(scene);
    MidiExporter.downloadAsFile(
      content, 
      `${scene.name.replace(/[^a-zA-Z0-9]/g, '_')}_ableton.txt`
    );
  };

  const exportJSON = () => {
    const content = MidiExporter.exportSceneToText(scene);
    MidiExporter.downloadAsFile(
      content,
      `${scene.name.replace(/[^a-zA-Z0-9]/g, '_')}_midi.txt`
    );
  };

  return (
    <div className="scene-editor">
      <div className="scene-editor-header">
        <div className="scene-info">
          <h2>{scene.name}</h2>
          <div className="scene-meta">
            <span>{scene.duration} bars</span>
            <span>•</span>
            <span>{scene.tempo} BPM</span>
            <span>•</span>
            <span>{scene.clips.length} clips</span>
          </div>
        </div>
        
        <div className="scene-controls">
          <label>
            Duration:
            <input
              type="number"
              value={scene.duration}
              onChange={(e) => onUpdateScene({ duration: parseInt(e.target.value) || 8 })}
              min={1}
              max={64}
            />
            bars
          </label>
          
          <div className="export-buttons">
            <button onClick={exportJSON} className="export-btn">📄 Export Text</button>
            <button onClick={exportScene} className="export-btn primary">📤 Export for Ableton</button>
          </div>
        </div>
      </div>

      <div className="tracks-grid">
        {trackTypes.map(({ type, label, icon }) => {
          const clips = getClipsForTrackType(type);
          
          return (
            <div key={type} className="track-row">
              <div className="track-header">
                <span className="track-icon">{icon}</span>
                <span className="track-label">{label}</span>
                <button 
                  className="generate-clip-btn"
                  onClick={() => generateClip(type)}
                  title={`Generate ${label} clip`}
                >
                  +
                </button>
              </div>
              
              <div className="track-clips">
                {clips.length === 0 ? (
                  <div className="empty-track">
                    <span>No clips</span>
                  </div>
                ) : (
                  clips.map(clip => (
                    <div 
                      key={clip.id} 
                      className={`clip-item ${clip.enabled ? 'enabled' : 'disabled'}`}
                    >
                      <span className="clip-name">{clip.name}</span>
                      <div className="clip-info">
                        <span>{clip.notes.length} notes</span>
                        <span>Ch {clip.channel}</span>
                      </div>
                      <div className="clip-actions">
                        <button 
                          onClick={() => toggleClip(clip.id)}
                          className="toggle-clip-btn"
                          title={clip.enabled ? 'Disable' : 'Enable'}
                        >
                          {clip.enabled ? '👁️' : '👁️‍🗨️'}
                        </button>
                        <button 
                          onClick={() => removeClip(clip.id)}
                          className="remove-clip-btn"
                          title="Remove clip"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
      
      <div className="scene-editor-footer">
        <p className="help-text">
          Click <strong>+</strong> to generate clips, or the eye icon to enable/disable clips
        </p>
      </div>
    </div>
  );
};

