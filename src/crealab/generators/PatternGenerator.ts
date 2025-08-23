import { GeneratorInstance } from '../core/GeneratorEngine';
import { GenerativeTrack, MidiNote } from '../types/CrealabTypes';
import { PatternManager } from '../core/PatternManager';

/**
 * Generator that plays a global MIDI pattern across all tracks.
 * Each track type interprets the pattern differently.
 */
export class PatternGenerator implements GeneratorInstance {
  private step: number = 0;

  generate(
    track: GenerativeTrack,
    currentTime: number,
    _globalTempo: number,
    _key: string,
    _scale: string
  ): MidiNote[] {
    const pattern = PatternManager.getInstance().getPattern().notes;
    if (pattern.length === 0) return [];

    const beatIndex = Math.floor(this.step / 4) % pattern.length;
    const baseNote = pattern[beatIndex];
    const notes: MidiNote[] = [];

    switch (track.trackType) {
      case 'lead':
        // play note each 16th
        notes.push({ note: baseNote, time: currentTime, velocity: 100, duration: 0.25 });
        break;
      case 'bass':
        // sub-bass style: trigger once per beat
        if (this.step % 4 === 0) {
          notes.push({ note: baseNote, time: currentTime, velocity: 100, duration: 1 });
        }
        break;
      default:
        // fallback: single note
        notes.push({ note: baseNote, time: currentTime, velocity: 100, duration: 0.25 });
    }

    this.step = (this.step + 1) % (pattern.length * 4);
    return notes;
  }

  updateParameters(_track: GenerativeTrack): void {}

  reset(): void {
    this.step = 0;
  }
}

export default PatternGenerator;
