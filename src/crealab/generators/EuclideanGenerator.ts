import { GeneratorInstance } from '../core/GeneratorEngine';
import { GenerativeTrack, MidiNote } from '../types/CrealabTypes';
import { getScaleNotes, euclideanRhythm } from '../utils/MusicalMath';

export class EuclideanGenerator implements GeneratorInstance {
  private pattern: boolean[] = [];
  private currentStep: number = 0;
  private lastMutationTime: number = 0;

  generate(
    track: GenerativeTrack,
    currentTime: number,
    globalTempo: number,
    key: string,
    scale: string
  ): MidiNote[] {
    const notes: MidiNote[] = [];
    const params = track.generator.parameters;
    
    // Parámetros del euclidean rhythm
    const pulses = Math.max(1, Math.floor((params.pulses || 8) * (track.controls.paramA / 127)));
    const steps = Math.max(1, Math.floor((params.steps || 16) * (track.controls.paramB / 127)));
    const offset = Math.floor((params.offset || 0) * (track.controls.paramC / 127));
    const mutationRate = (params.mutation || 0.1);
    
    // Regenerar patrón si cambió algún parámetro
    if (this.pattern.length !== steps) {
      this.pattern = euclideanRhythm(pulses, steps);
      this.rotatePattern(offset);
    }

    // Mutación evolutiva del patrón
    if (currentTime - this.lastMutationTime > 4 && Math.random() < mutationRate) {
      this.mutatePattern();
      this.lastMutationTime = currentTime;
    }

    // Verificar si hay hit en el step actual
    const stepIndex = Math.floor(currentTime * 4) % steps; // 16th notes
    if (this.pattern[stepIndex]) {
      const scaleNotes = getScaleNotes(key, scale);
      const intensity = track.controls.intensity / 127;
      
      // Aplicar probabilidad basada en intensidad
      if (Math.random() < intensity) {
        const note = this.selectNote(scaleNotes, track);
        const velocity = this.calculateVelocity(track, intensity);
        const duration = this.calculateDuration(track);

        notes.push({
          note,
          time: currentTime,
          velocity,
          duration
        });
      }
    }

    return notes;
  }

  updateParameters(track: GenerativeTrack): void {
    // Los parámetros se actualizan en tiempo real en generate()
  }

  reset(): void {
    this.pattern = [];
    this.currentStep = 0;
    this.lastMutationTime = 0;
  }

  private rotatePattern(offset: number) {
    if (offset === 0) return;
    
    const normalizedOffset = offset % this.pattern.length;
    this.pattern = [
      ...this.pattern.slice(normalizedOffset),
      ...this.pattern.slice(0, normalizedOffset)
    ];
  }

  private mutatePattern() {
    // Flip random bits with low probability
    for (let i = 0; i < this.pattern.length; i++) {
      if (Math.random() < 0.1) {
        this.pattern[i] = !this.pattern[i];
      }
    }
  }

  private selectNote(scaleNotes: number[], track: GenerativeTrack): number {
    // Selección inteligente basada en el tipo de instrumento
    const profile = track.instrumentProfile;
    let noteRange = scaleNotes;

    // Filtrar por rango del instrumento si está definido
    if (profile) {
      // Bass range: notas graves
      if (profile.includes('bass') || profile.includes('Neutron')) {
        noteRange = scaleNotes.filter(note => note < 60);
      }
      // Lead range: notas agudas
      else if (profile.includes('lead') || profile.includes('2600')) {
        noteRange = scaleNotes.filter(note => note > 60);
      }
    }

    return noteRange[Math.floor(Math.random() * noteRange.length)] || scaleNotes[0];
  }

  private calculateVelocity(track: GenerativeTrack, intensity: number): number {
    const baseVelocity = 60 + (intensity * 67); // 60-127 range
    const variation = (Math.random() - 0.5) * 20; // ±10 variation
    return Math.max(1, Math.min(127, Math.floor(baseVelocity + variation)));
  }

  private calculateDuration(track: GenerativeTrack): number {
    // Duration between 0.1 and 1.0 beats
    return 0.1 + (Math.random() * 0.9);
  }
}
