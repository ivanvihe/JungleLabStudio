import React, { useState } from 'react';
import { Note } from 'tonal';
import PatternManager from '../../crealab/core/PatternManager';

export const PatternSettings: React.FC = () => {
  const manager = PatternManager.getInstance();
  const [notes, setNotes] = useState<number[]>(manager.getPattern().notes);

  const handleGenerate = () => {
    const pattern = manager.generatePattern();
    setNotes([...pattern.notes]);
  };

  return (
    <div className="settings-section">
      <h3>🎹 MIDI Pattern</h3>
      <div className="setting-group">
        <label className="setting-label">
          <span>Active Pattern</span>
          <div className="pattern-display">
            {notes.map(n => Note.fromMidi(n)).join(', ')}
          </div>
        </label>
      </div>
      <div className="setting-group">
        <button className="primary-button" onClick={handleGenerate}>
          Generate Pattern
        </button>
      </div>
    </div>
  );
};

export default PatternSettings;
