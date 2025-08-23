import React, { useState, useEffect } from 'react';
import { GenerativeTrack, InstrumentProfile } from '../types/CrealabTypes';
import { InstrumentProfileManager } from '../core/InstrumentProfileManager';
import { SuggestionPanel } from './SuggestionPanel';
import './InstrumentSelector.css';

interface InstrumentSelectorProps {
  track: GenerativeTrack;
  onTrackUpdate: (updates: Partial<GenerativeTrack>) => void;
  genre?: string;
  allTracks?: GenerativeTrack[];
}

export const InstrumentSelector: React.FC<InstrumentSelectorProps> = ({
  track,
  onTrackUpdate,
  genre,
  allTracks
}) => {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [profiles, setProfiles] = useState<InstrumentProfile[]>([]);
  const [suggestions, setSuggestions] = useState<InstrumentProfile[]>([]);
  
  const profileManager = InstrumentProfileManager.getInstance();
  const currentProfile = track.instrumentProfile ? 
    profileManager.getProfileInfo(track.instrumentProfile) : null;

  useEffect(() => {
    // Cargar todos los perfiles
    setProfiles(profileManager.getAllProfiles());
    
    // Generar sugerencias
    const newSuggestions = profileManager.generateSuggestions(
      track,
      genre,
      allTracks
    );
    setSuggestions(newSuggestions);
  }, [track.id, genre, allTracks]);

  const handleProfileSelect = (profileId: string) => {
    const updates = profileManager.applyProfileToTrack(track, profileId);
    onTrackUpdate(updates);
    setShowSuggestions(false);
  };

  const getFilteredProfiles = () => {
    if (selectedCategory === 'all') return profiles;
    return profileManager.getProfilesByType(selectedCategory);
  };

  const categories = [
    { id: 'all', name: 'All', icon: '🎛️' },
    { id: 'bass', name: 'Bass', icon: '🎸' },
    { id: 'lead', name: 'Lead', icon: '🎹' },
    { id: 'pad', name: 'Pad', icon: '🌊' },
    { id: 'drum', name: 'Drums', icon: '🥁' },
    { id: 'experimental', name: 'Experimental', icon: '🔬' }
  ];

  return (
    <div className="instrument-selector">
      <div className="current-selection">
        <div className="selection-header">
          <span className="track-label">Track {track.trackNumber}</span>
          <button 
            className="suggestions-btn"
            onClick={() => setShowSuggestions(!showSuggestions)}
            title="Show instrument suggestions"
          >
            💡
          </button>
        </div>
        
        {currentProfile ? (
          <div className="current-instrument" style={{ borderColor: currentProfile.color }}>
            <div className="instrument-info">
              <div className="instrument-name">{currentProfile.name}</div>
              {currentProfile.brand && (
                <div className="instrument-brand">{currentProfile.brand}</div>
              )}
              <div className="instrument-type">{currentProfile.type}</div>
            </div>
            <div className="instrument-color" style={{ backgroundColor: currentProfile.color }} />
          </div>
        ) : (
          <div className="no-instrument">
            <span>No instrument selected</span>
            <button onClick={() => setShowSuggestions(true)}>
              Select Instrument
            </button>
          </div>
        )}
      </div>

      {showSuggestions && (
        <div className="suggestions-overlay">
          <div className="suggestions-modal">
            <div className="modal-header">
              <h3>Select Instrument for Track {track.trackNumber}</h3>
              <button 
                className="close-btn"
                onClick={() => setShowSuggestions(false)}
              >
                ✕
              </button>
            </div>

            {/* Sugerencias basadas en contexto */}
            {suggestions.length > 0 && (
              <SuggestionPanel
                suggestions={suggestions}
                onSelect={handleProfileSelect}
                title={`💡 Suggested for ${genre || 'this track'}`}
              />
            )}

            {/* Filtros por categoría */}
            <div className="category-filters">
              {categories.map(category => (
                <button
                  key={category.id}
                  className={`category-btn ${selectedCategory === category.id ? 'active' : ''}`}
                  onClick={() => setSelectedCategory(category.id)}
                >
                  {category.icon} {category.name}
                </button>
              ))}
            </div>

            {/* Lista de instrumentos */}
            <div className="instruments-grid">
              {getFilteredProfiles().map(profile => (
                <div
                  key={profile.id}
                  className={`instrument-card ${currentProfile?.id === profile.id ? 'selected' : ''}`}
                  onClick={() => handleProfileSelect(profile.id)}
                  style={{ borderColor: profile.color }}
                >
                  <div className="card-header">
                    <div className="instrument-color-dot" style={{ backgroundColor: profile.color }} />
                    <div className="instrument-name">{profile.name}</div>
                    {profile.brand && (
                      <div className="instrument-brand">{profile.brand}</div>
                    )}
                  </div>
                  
                  <div className="card-body">
                    <div className="instrument-description">
                      {profile.description}
                    </div>
                    
                    <div className="suggested-generators">
                      <span className="generators-label">Best for:</span>
                      <div className="generators-list">
                        {profile.suggestedGenerators.slice(0, 2).map(gen => (
                          <span key={gen} className="generator-tag">
                            {gen}
                          </span>
                        ))}
                      </div>
                    </div>
                    
                    {profile.tags && (
                      <div className="instrument-tags">
                        {profile.tags.slice(0, 3).map(tag => (
                          <span key={tag} className="tag">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  <div className="card-footer">
                    <div className="note-range">
                      Range: {profile.defaultParameters.noteRange?.[0] || 24}-{profile.defaultParameters.noteRange?.[1] || 84}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

