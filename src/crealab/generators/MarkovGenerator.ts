import { GeneratorInstance } from '../core/GeneratorEngine';
import { GenerativeTrack, MidiNote } from '../types/CrealabTypes';
import { getScaleNotes, weightedRandomChoice } from '../utils/MusicalMath';

interface TransitionMap {
  [note: number]: Map<number, number>;
}

export class MarkovGenerator implements GeneratorInstance {
  private transitions: TransitionMap = {};
  private context: number[] = [];

  generate(
    track: GenerativeTrack,
    currentTime: number,
    globalTempo: number,
    key: string,
    scale: string
  ): MidiNote[] {
    const notes: MidiNote[] = [];
    const order = Math.max(1, Math.floor((track.controls.paramA / 127) * 4));
    const creativity = track.controls.paramB / 127;
    const density = track.controls.paramC / 127;
    const intensity = track.controls.intensity / 127;

    const scaleNotes = getScaleNotes(key, scale);

    // Build transitions if empty
    if (Object.keys(this.transitions).length === 0) {
      this.train(scaleNotes);
    }

    // Probability to trigger based on intensity and density
    if (Math.random() > intensity * density) {
      return notes;
    }

    const nextNote = this.generateNextNote(scaleNotes, order, creativity);
    const velocity = Math.floor(60 + intensity * 60);
    const duration = 0.25;

    notes.push({ note: nextNote, time: currentTime, velocity, duration });
    this.context.push(nextNote);
    if (this.context.length > order) this.context.shift();

    return notes;
  }

  updateParameters(track: GenerativeTrack): void {
    // Parameters are reactive in generate
  }

  reset(): void {
    this.transitions = {};
    this.context = [];
  }

  private train(scaleNotes: number[]) {
    // Simple circular transitions
    for (let i = 0; i < scaleNotes.length; i++) {
      const current = scaleNotes[i];
      const next = scaleNotes[(i + 1) % scaleNotes.length];
      if (!this.transitions[current]) {
        this.transitions[current] = new Map();
      }
      const map = this.transitions[current];
      map.set(next, (map.get(next) || 0) + 1);
    }
  }

  private generateNextNote(scaleNotes: number[], order: number, creativity: number): number {
    // Use last note to get probabilities
    const last = this.context[this.context.length - 1];
    let candidates: number[] = [];
    let weights: number[] = [];

    if (last != null && this.transitions[last]) {
      const map = this.transitions[last];
      candidates = Array.from(map.keys());
      weights = Array.from(map.values());
    }

    if (candidates.length === 0 || Math.random() < creativity) {
      // pick random from scale
      return scaleNotes[Math.floor(Math.random() * scaleNotes.length)];
    }

    const index = weightedRandomChoice(weights);
    return candidates[index];
  }
}
