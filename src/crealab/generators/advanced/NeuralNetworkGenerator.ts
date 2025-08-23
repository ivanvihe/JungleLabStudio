import { GeneratorInstance } from '../../core/GeneratorEngine';
import { GenerativeTrack, MidiNote } from '../../types/CrealabTypes';
import { getScaleNotes } from '../../utils/MusicalMath';

export class NeuralNetworkGenerator implements GeneratorInstance {
  private weights: number[] = Array.from({ length: 12 }, () => Math.random());

  generate(
    track: GenerativeTrack,
    currentTime: number,
    globalTempo: number,
    key: string,
    scale: string
  ): MidiNote[] {
    const intensity = track.controls.intensity / 127;
    const scaleNotes = getScaleNotes(key, scale);
    const input = Math.random();
    const index = this.predict(input);
    const note = scaleNotes[index % scaleNotes.length];

    return [
      {
        note,
        time: currentTime,
        velocity: Math.floor(60 + intensity * 60),
        duration: 0.25
      }
    ];
  }

  updateParameters(track: GenerativeTrack): void {
    const lr = (track.controls.paramA || 0) / 127;
    this.weights = this.weights.map(w => w + (Math.random() - 0.5) * lr);
  }

  reset(): void {
    this.weights = Array.from({ length: 12 }, () => Math.random());
  }

  private predict(x: number): number {
    let sum = 0;
    for (let i = 0; i < this.weights.length; i++) {
      sum += this.weights[i] * Math.pow(x, i);
    }
    return Math.abs(Math.floor(sum)) % this.weights.length;
  }
}

