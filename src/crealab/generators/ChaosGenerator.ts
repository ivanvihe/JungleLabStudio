import { GeneratorInstance } from '../core/GeneratorEngine';
import { GenerativeTrack, MidiNote } from '../types/CrealabTypes';
import { getScaleNotes } from '../utils/MusicalMath';

export class ChaosGenerator implements GeneratorInstance {
  private x = 0.5;
  private y = 0.5;
  private z = 0.5;

  generate(
    track: GenerativeTrack,
    currentTime: number,
    globalTempo: number,
    key: string,
    scale: string
  ): MidiNote[] {
    const params = track.generator.parameters;
    const attractor = params.attractor || 'lorenz';
    const sensitivity = params.sensitivity || 0.5;
    const scaling = params.scaling || 1.0;
    const intensity = track.controls.intensity / 127;

    const scaleNotes = getScaleNotes(key, scale);

    // update chaotic system
    this.updateAttractor(attractor, sensitivity);

    if (Math.random() > intensity) return [];

    const idx = Math.floor(Math.abs(this.x) * scaling * scaleNotes.length) % scaleNotes.length;
    const note = scaleNotes[idx];
    const velocity = Math.floor(60 + intensity * 60);
    const duration = 0.25;

    return [{ note, time: currentTime, velocity, duration }];
  }

  updateParameters(track: GenerativeTrack): void {
    // handled dynamically
  }

  reset(): void {
    this.x = 0.5;
    this.y = 0.5;
    this.z = 0.5;
  }

  private updateAttractor(type: string, sensitivity: number) {
    switch (type) {
      case 'lorenz':
        const sigma = 10;
        const rho = 28;
        const beta = 8 / 3;
        const dt = 0.01 * sensitivity;
        const dx = sigma * (this.y - this.x) * dt;
        const dy = (this.x * (rho - this.z) - this.y) * dt;
        const dz = (this.x * this.y - beta * this.z) * dt;
        this.x += dx;
        this.y += dy;
        this.z += dz;
        break;
      case 'henon':
        const a = 1.4 * sensitivity + 0.2;
        const b = 0.3;
        const newX = 1 - a * this.x * this.x + this.y;
        const newY = b * this.x;
        this.x = newX;
        this.y = newY;
        break;
      default:
        // logistic map
        const r = 3.7 + sensitivity * 0.3;
        this.x = r * this.x * (1 - this.x);
    }
  }
}
