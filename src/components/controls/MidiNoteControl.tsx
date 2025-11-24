
import React, { useEffect, useState } from 'react';
import { useMidiContext } from '../../contexts/MidiContext';

interface MidiNoteControlProps {
  value: number;
  onChange: (value: number) => void;
  label: string;
  path: string;
}

const NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];

const midiNoteToName = (note: number) => {
  if (note < 0 || note > 127) return '';
  const octave = Math.floor(note / 12) - 1;
  const name = NOTE_NAMES[note % 12];
  return `${name}${octave}`;
};

const MidiNoteControl: React.FC<MidiNoteControlProps> = ({ value, onChange, label, path }) => {
  const { startMidiLearn, cancelMidiLearn, midiLearnTarget, lastCapturedNote } = useMidiContext();
  const isLearning = midiLearnTarget === path;

  useEffect(() => {
    if (lastCapturedNote && lastCapturedNote.target === path) {
      onChange(lastCapturedNote.note);
    }
  }, [lastCapturedNote, path, onChange]);

  const handleLearnClick = () => {
    if (isLearning) {
      cancelMidiLearn();
    } else {
      startMidiLearn(path);
    }
  };

  return (
    <div className="control-row">
      <label>{label}</label>
      <div className="midi-note-control">
        <span className="note-display">{value} ({midiNoteToName(value)})</span>
        <button onClick={handleLearnClick} className={isLearning ? 'learning' : ''}>
          {isLearning ? 'Listening...' : 'REC'}
        </button>
      </div>
    </div>
  );
};

export default MidiNoteControl;
