import { Scale, Note } from 'tonal';

export interface MidiPattern {
  notes: number[];
}

/**
 * Simple global manager for MIDI patterns used by generators.
 * Provides a singleton instance storing the active pattern
 * and utility methods to generate new ones.
 */
export class PatternManager {
  private static instance: PatternManager;
  private current: MidiPattern = {
    // default C minor triad across one octave
    notes: [48, 57, 64, 65],
  };

  static getInstance(): PatternManager {
    if (!this.instance) {
      this.instance = new PatternManager();
    }
    return this.instance;
  }

  getPattern(): MidiPattern {
    return this.current;
  }

  setPattern(notes: number[]): void {
    this.current = { notes };
  }

  /**
   * Generate a new 4-note pattern inside a minor scale.
   * Notes are generated around C2 to keep low registers.
   */
  generatePattern(key: string = 'C', scale: string = 'minor'): MidiPattern {
    try {
      const scaleNotes: string[] = Scale.get(`${key} ${scale}`).notes;
      const pattern: number[] = [];
      for (let i = 0; i < 4; i++) {
        const name = scaleNotes[Math.floor(Math.random() * scaleNotes.length)];
        // place notes around octave 2 (C2 ~ 36)
        const midi = Note.midi(`${name}2`) ?? 36;
        pattern.push(midi);
      }
      this.current = { notes: pattern };
    } catch {
      // fallback to a static minor pattern if tonal fails
      this.current = { notes: [48, 51, 55, 60] };
    }
    return this.current;
  }
}

export default PatternManager;
