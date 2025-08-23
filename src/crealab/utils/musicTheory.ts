import { Scale, Chord, Note } from 'tonal';
import { ScaleTemplate } from '../types/MidiTypes';

// Escalas ideales para dub techno, ambient y experimental
export const GENRE_SCALES: Record<string, ScaleTemplate[]> = {
  dubTechno: [
    {
      name: 'Natural Minor',
      intervals: [0, 2, 3, 5, 7, 8, 10],
      mood: 'dark',
      genres: ['dub techno', 'minimal techno']
    },
    {
      name: 'Dorian',
      intervals: [0, 2, 3, 5, 7, 9, 10],
      mood: 'neutral',
      genres: ['dub techno', 'hypnotic techno']
    },
    {
      name: 'Phrygian',
      intervals: [0, 1, 3, 5, 7, 8, 10],
      mood: 'dark',
      genres: ['dark ambient', 'experimental']
    }
  ],
  ambient: [
    {
      name: 'Mixolydian',
      intervals: [0, 2, 4, 5, 7, 9, 10],
      mood: 'bright',
      genres: ['ambient techno', 'floating points style']
    },
    {
      name: 'Lydian',
      intervals: [0, 2, 4, 6, 7, 9, 11],
      mood: 'bright',
      genres: ['ambient', 'ethereal']
    }
  ],
  experimental: [
    {
      name: 'Phrygian Dominant',
      intervals: [0, 1, 4, 5, 7, 8, 10],
      mood: 'exotic',
      genres: ['experimental', 'max cooper style']
    },
    {
      name: 'Locrian',
      intervals: [0, 1, 3, 5, 6, 8, 10],
      mood: 'dark',
      genres: ['dark ambient', 'experimental']
    }
  ]
};

// Progresiones armónicas comunes por género
export const HARMONIC_PROGRESSIONS = {
  dubClassic: ['i', 'bVI', 'iv', 'v'],           // Cm - Ab - Fm - Gm
  dubMinimal: ['i', 'bvii', 'i', 'iv'],         // Cm - Bb - Cm - Fm
  floatingPoints: ['i', 'bII', 'bvii', 'i'],    // Suspended tension
  maxCooper: ['i', 'ii°', 'bVI', 'bVII'],       // Complex, diminished
  colinBenders: ['i', 'v', 'bVI', 'bvii', 'i'], // Extended loop
  ambient: ['I', 'vi', 'IV', 'V']               // Classic ambient progression
};

export class MusicTheoryUtils {
  static getScaleNotes(key: string, scaleName: string): string[] {
    return Scale.get(`${key} ${scaleName}`).notes;
  }

  static getChordFromRomanNumeral(roman: string, key: string, scale: string = 'minor'): string[] {
    const scaleNotes = this.getScaleNotes(key, scale);
    
    // Simple mapping for basic roman numerals
    const romanMap: Record<string, number> = {
      'i': 0, 'ii': 1, 'iii': 2, 'iv': 3, 'v': 4, 'vi': 5, 'vii': 6,
      'I': 0, 'II': 1, 'III': 2, 'IV': 3, 'V': 4, 'VI': 5, 'VII': 6,
      'bII': 1, 'bIII': 2, 'bVI': 5, 'bVII': 6
    };

    const rootIndex = romanMap[roman];
    if (rootIndex !== undefined) {
      const rootNote = scaleNotes[rootIndex];
      return Chord.get(`${rootNote}m`).notes; // Default to minor
    }
    
    return [];
  }

  static noteToMidi(note: string): number {
    return Note.midi(note) || 60; // Default to C4
  }
}
