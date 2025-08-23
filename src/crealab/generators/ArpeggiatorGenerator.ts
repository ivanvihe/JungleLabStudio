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
      const transpose = Math.round((track.controls.paramA - 64) / 64 * 12); // -12..+12
      const octaves = Math.max(1, Math.floor((track.controls.paramB / 127) * 4));
      const swing = (track.controls.paramC / 127) * 0.5; // 0..0.5 beat delay on off steps
      const noteLength = 0.1 + (track.controls.intensity / 127) * 0.4; // use fader as time

      const scaleNotes = getScaleNotes(key, scale).map(n => n + transpose);
      const sequence = this.buildSequence(scaleNotes, 'up', octaves);

      const note = sequence[this.step % sequence.length];
      const velocity = 80;
      const duration = noteLength;

      const noteTime = currentTime + (this.step % 2 === 1 ? swing : 0);
      this.step++;

      return [{ note, time: noteTime, velocity, duration }];
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
