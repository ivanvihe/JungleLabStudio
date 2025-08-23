import React, { useState } from 'react';
import { MidiClip } from '../types/CrealabTypes';
import { MidiClipGenerator } from '../core/MidiClipGenerator';
import './PianoRoll.css';

interface PianoRollProps {
  clip: MidiClip;
  projectKey: string;
  projectScale: string;
  onClipUpdate: (clip: MidiClip) => void;
  onClose: () => void;
}

const NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const OCTAVES = [7, 6, 5, 4, 3, 2, 1, 0];
const GRID_RESOLUTION = 16; // 16th notes

export const PianoRoll: React.FC<PianoRollProps> = ({
  clip,
  projectKey,
  projectScale,
  onClipUpdate,
  onClose
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const generator = MidiClipGenerator.getInstance();

  // Generate intelligent MIDI based on track type and style
  const generateIntelligentClip = (style: string) => {
    let newClip: MidiClip;

    switch (clip.trackType) {
      case 'kick':
        newClip = generator.generateKick(style as any, 4, clip.channel);
        break;
      case 'bass':
        newClip = generator.generateBass(projectKey, projectScale, style as any, 4, clip.channel);
        break;
      case 'arp':
        newClip = generator.generateArpeggio(projectKey, projectScale, style as any, 4, clip.channel);
        break;
      case 'lead':
        newClip = generator.generateMelody(projectKey, projectScale, style as any, 4, clip.channel);
        break;
      default:
        newClip = generator.generateChordProgression(projectKey, style as any, 4, clip.channel);
    }

    const updatedClip = {
      ...clip,
      notes: newClip.notes,
      name: `${clip.trackType} ${style}`
    };

    onClipUpdate(updatedClip);
  };

  const getNoteColor = (midiNote: number): string => {
    const note = NOTES[midiNote % 12];
    const scaleNotes = getScaleNotes(projectKey, projectScale);
    const isInScale = scaleNotes.includes(note);

    if (note === projectKey) return '#4CAF50'; // Root
    if (isInScale) return '#2196F3'; // Scale
    return '#757575'; // Chromatic
  };

  const getScaleNotes = (key: string, scale: string): string[] => {
    const scaleIntervals: { [key: string]: number[] } = {
      minor: [0, 2, 3, 5, 7, 8, 10],
      major: [0, 2, 4, 5, 7, 9, 11],
      dorian: [0, 2, 3, 5, 7, 9, 10],
      phrygian: [0, 1, 3, 5, 7, 8, 10],
      pentatonic: [0, 2, 5, 7, 9]
    };

    const keyIndex = NOTES.indexOf(key);
    const intervals = scaleIntervals[scale] || scaleIntervals.minor;

    return intervals.map(interval => NOTES[(keyIndex + interval) % 12]);
  };

  const handleNoteClick = (midiNote: number, time: number, velocity: number = 80) => {
    const existingNoteIndex = clip.notes.findIndex(
      n => n.note === midiNote && Math.abs(n.time - time) < 0.1
    );

    const updatedNotes = [...clip.notes];

    if (existingNoteIndex >= 0) {
      updatedNotes.splice(existingNoteIndex, 1);
    } else {
      updatedNotes.push({
        note: midiNote,
        time,
        velocity,
        duration: 0.25
      });
    }

    onClipUpdate({ ...clip, notes: updatedNotes });
  };

  const handleVelocityChange = (noteIndex: number, velocity: number) => {
    const updatedNotes = [...clip.notes];
    updatedNotes[noteIndex].velocity = velocity;
    onClipUpdate({ ...clip, notes: updatedNotes });
  };

  const getTrackTypeStyles = (): string[] => {
    switch (clip.trackType) {
      case 'kick':
        return ['minimal', 'dub', 'hypnotic', 'fourOnFloor'];
      case 'bass':
        return ['dub', 'minimal', 'hypnotic', 'octaveBass', 'psytrance'];
      case 'arp':
        return ['floating', 'ambient', 'maxCooper', 'scales', 'random'];
      case 'lead':
        return ['melody', 'ambient', 'experimental', 'hypnotic'];
      default:
        return ['dubClassic', 'minimal', 'floatingPoints', 'maxCooper'];
    }
  };

  const renderGrid = () => {
    const beats = clip.duration * 4; // 4 beats per bar
    const steps = beats * (GRID_RESOLUTION / 4); // 16th note grid
    const allMidiNotes = OCTAVES.flatMap(octave =>
      NOTES.map((note, index) => octave * 12 + index)
    );

    return (
      <div className="piano-grid">
        {/* Piano keys */}
        <div className="piano-keys">
          {allMidiNotes.map(midiNote => {
            const note = NOTES[midiNote % 12];
            const octave = Math.floor(midiNote / 12);
            const isBlackKey = note.includes('#');

            return (
              <div
                key={midiNote}
                className={`piano-key ${isBlackKey ? 'black' : 'white'}`}
                style={{ backgroundColor: getNoteColor(midiNote) }}
              >
                <span className="note-label">
                  {note}
                  {octave}
                </span>
              </div>
            );
          })}
        </div>

        {/* Grid */}
        <div className="note-grid">
          {allMidiNotes.map(midiNote => (
            <div key={midiNote} className="note-row">
              {Array.from({ length: steps }, (_, step) => {
                const time = (step / GRID_RESOLUTION) * 4;
                const existingNote = clip.notes.find(
                  n => n.note === midiNote && Math.abs(n.time - time) < 0.1
                );

                return (
                  <div
                    key={step}
                    className={`grid-cell ${existingNote ? 'has-note' : ''}`}
                    onClick={() => handleNoteClick(midiNote, time)}
                    style={{
                      backgroundColor: existingNote
                        ? `rgba(76, 175, 80, ${existingNote.velocity / 127})`
                        : undefined
                    }}
                  >
                    {existingNote && (
                      <div className="note-velocity">
                        <input
                          type="range"
                          min="1"
                          max="127"
                          value={existingNote.velocity}
                          onChange={e => {
                            const noteIndex = clip.notes.indexOf(existingNote);
                            handleVelocityChange(
                              noteIndex,
                              parseInt(e.target.value)
                            );
                          }}
                          onClick={e => e.stopPropagation()}
                        />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="piano-roll-overlay">
      <div className="piano-roll-container">
        <div className="piano-roll-header">
          <div className="clip-info">
            <input
              type="text"
              value={clip.name}
              onChange={e => onClipUpdate({ ...clip, name: e.target.value })}
              className="clip-name-input"
            />
            <span className="clip-details">
              {clip.trackType} • {projectKey} {projectScale} • Ch {clip.channel}
            </span>
          </div>

          <div className="piano-roll-controls">
            <div className="generation-buttons">
              <span className="generation-label">Generate:</span>
              {getTrackTypeStyles().map(style => (
                <button
                  key={style}
                  className="generation-btn"
                  onClick={() => generateIntelligentClip(style)}
                >
                  {style}
                </button>
              ))}
            </div>

            <div className="playback-controls">
              <button
                className={`play-btn ${isPlaying ? 'playing' : ''}`}
                onClick={() => setIsPlaying(!isPlaying)}
              >
                {isPlaying ? '⏸️' : '▶️'}
              </button>

              <button
                className="clear-btn"
                onClick={() => onClipUpdate({ ...clip, notes: [] })}
              >
                Clear
              </button>

              <button className="close-btn" onClick={onClose}>
                ✕
              </button>
            </div>
          </div>
        </div>

        <div className="piano-roll-content">{renderGrid()}</div>

        <div className="piano-roll-footer">
          <div className="scale-info">
            <span>
              Scale: {projectKey} {projectScale}
            </span>
            <div className="scale-notes">
              {getScaleNotes(projectKey, projectScale).map(note => (
                <span key={note} className="scale-note">
                  {note}
                </span>
              ))}
            </div>
          </div>

          <div className="clip-stats">
            Notes: {clip.notes.length} • Duration: {clip.duration} bars
          </div>
        </div>
      </div>
    </div>
  );
};

