import { GeneratorInstance } from '../../core/GeneratorEngine';
import { GenerativeTrack, MidiNote } from '../../types/CrealabTypes';
import { getScaleNotes } from '../../utils/MusicalMath';

export class CellularAutomataGenerator implements GeneratorInstance {
  private cells: number[] = [1];
  private step = 0;

  generate(
    track: GenerativeTrack,
    currentTime: number,
    globalTempo: number,
    key: string,
    scale: string
  ): MidiNote[] {
    const notes: MidiNote[] = [];
    const intensity = track.controls.intensity / 127;
    const scaleNotes = getScaleNotes(key, scale);

    if (this.cells[this.step] === 1) {
      const note = scaleNotes[this.step % scaleNotes.length];
      notes.push({
        note,
        time: currentTime,
        velocity: Math.floor(50 + intensity * 70),
        duration: 0.25
      });
    }

    this.step++;
    if (this.step >= this.cells.length) {
      this.cells = this.evolve(this.cells);
      this.step = 0;
    }

    return notes;
  }

  updateParameters(track: GenerativeTrack): void {
    const params = track.generator.parameters as any;
    if (params.seed) {
      this.cells = params.seed;
    }
  }

  reset(): void {
    this.cells = [1];
    this.step = 0;
  }

  private evolve(cells: number[]): number[] {
    const next: number[] = [];
    for (let i = 0; i < cells.length; i++) {
      const left = cells[i - 1] || 0;
      const center = cells[i];
      const right = cells[i + 1] || 0;
      const idx = (left << 2) | (center << 1) | right;
      const rule30 = [0, 1, 1, 1, 1, 0, 0, 0];
      next[i] = rule30[idx];
    }
    next.push(0); // expand pattern over time
    return next;
  }
}

