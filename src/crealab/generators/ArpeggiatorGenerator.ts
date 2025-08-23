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
    const params = track.generator.parameters;
    const pattern = params.pattern || 'up';
    const octaves = params.octaves || 1;
    const noteLength = params.noteLength || 0.25;

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
