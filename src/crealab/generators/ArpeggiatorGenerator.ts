import { GeneratorInstance } from '../core/GeneratorEngine';
import { GenerativeTrack, MidiNote } from '../types/CrealabTypes';
import { getScaleNotes } from '../utils/MusicalMath';

export class ArpeggiatorGenerator implements GeneratorInstance {
  private step: number = 0;

  generate(
    track: GenerativeTrack,
    currentTime: number,
    globalTempo: number,
    key: string,
    scale: string
  ): MidiNote[] {
    // Map real-time controls to parameters
    const patternIndex = Math.floor((track.controls.paramA / 127) * 4);
    const pattern = ['up', 'down', 'upDown', 'random'][patternIndex] || 'up';
    const octaves = Math.max(1, Math.floor((track.controls.paramB / 127) * 4));
    const noteLength = 0.1 + (track.controls.paramC / 127) * 0.9;

    const scaleNotes = getScaleNotes(key, scale);
    const sequence = this.buildSequence(scaleNotes, pattern, octaves);

    if (!track.controls.playStop) return [];

    const note = sequence[this.step % sequence.length];
    const velocity = Math.floor(50 + (track.controls.intensity / 127) * 77);
    const duration = noteLength;

    this.step++;

    return [{ note, time: currentTime, velocity, duration }];
  }

  updateParameters(track: GenerativeTrack): void {
    // Parameters handled dynamically
  }

  reset(): void {
    this.step = 0;
  }

  private buildSequence(scaleNotes: number[], pattern: string, octaves: number): number[] {
    const base = [...scaleNotes];
    const sequence: number[] = [];

    for (let o = 0; o < octaves; o++) {
      base.forEach(n => sequence.push(n + o * 12));
    }

    switch (pattern) {
      case 'down':
        return sequence.slice().reverse();
      case 'upDown':
        return sequence.concat(sequence.slice().reverse().slice(1, -1));
      case 'random':
        return sequence.sort(() => Math.random() - 0.5);
      default:
        return sequence;
    }
  }
}
