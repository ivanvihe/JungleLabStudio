import React from 'react';
import { InstrumentProfile } from '../types/CrealabTypes';
import './SuggestionPanel.css';

interface SuggestionPanelProps {
  suggestions: InstrumentProfile[];
  onSelect: (profileId: string) => void;
  title: string;
}

export const SuggestionPanel: React.FC<SuggestionPanelProps> = ({
  suggestions,
  onSelect,
  title
}) => {
  if (suggestions.length === 0) return null;

  return (
    <div className="suggestion-panel">
      <div className="suggestion-header">
        <h4>{title}</h4>
        <span className="suggestion-count">{suggestions.length} suggestions</span>
      </div>
      
      <div className="suggestions-list">
        {suggestions.map(profile => (
          <div
            key={profile.id}
            className="suggestion-item"
            onClick={() => onSelect(profile.id)}
          >
            <div className="suggestion-color" style={{ backgroundColor: profile.color }} />
            
            <div className="suggestion-info">
              <div className="suggestion-name">{profile.name}</div>
              {profile.brand && (
                <div className="suggestion-brand">{profile.brand}</div>
              )}
              
              <div className="suggestion-generators">
                {profile.suggestedGenerators.slice(0, 2).map(gen => (
                  <span key={gen} className="gen-badge">
                    {gen}
                  </span>
                ))}
              </div>
            </div>
            
            <div className="suggestion-type">
              {profile.type}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

