import { GeneratorInstance } from '../core/GeneratorEngine';
import { GenerativeTrack, MidiNote } from '../types/CrealabTypes';
import { getScaleNotes, weightedRandomChoice } from '../utils/MusicalMath';

export class ProbabilisticGenerator implements GeneratorInstance {
  private noteWeights: Map<number, number> = new Map();
  private rhythmPattern: number[] = [];
  private lastAnalysisTime: number = 0;

  generate(
    track: GenerativeTrack,
    currentTime: number,
    globalTempo: number,
    key: string,
    scale: string
  ): MidiNote[] {
    const notes: MidiNote[] = [];
    const params = track.generator.parameters;
    
    // Parámetros probabilísticos
    const density = (params.density || 0.5) * (track.controls.paramA / 127);
    const variation = (params.variation || 0.3) * (track.controls.paramB / 127);
    const swing = (params.swing || 0.1) * (track.controls.paramC / 127);
    const intensity = track.controls.intensity / 127;

    // Actualizar pesos de notas periódicamente
    if (currentTime - this.lastAnalysisTime > 8) {
      this.updateNoteWeights(key, scale, track);
      this.lastAnalysisTime = currentTime;
    }

    // Decisión probabilística de generar nota
    const shouldGenerateNote = Math.random() < (density * intensity);
    
    if (shouldGenerateNote) {
      const scaleNotes = getScaleNotes(key, scale);
      const note = this.selectWeightedNote(scaleNotes);
      const velocity = this.calculateVelocity(intensity, variation);
      const duration = this.calculateDuration(variation);
      const swingOffset = this.calculateSwingOffset(swing);

      notes.push({
        note,
        time: currentTime + swingOffset,
        velocity,
        duration
      });
    }

    return notes;
  }

  updateParameters(track: GenerativeTrack): void {
    // Parámetros se actualizan en tiempo real
  }

  reset(): void {
    this.noteWeights.clear();
    this.rhythmPattern = [];
    this.lastAnalysisTime = 0;
  }

  private updateNoteWeights(key: string, scale: string, track: GenerativeTrack) {
    const scaleNotes = getScaleNotes(key, scale);
    this.noteWeights.clear();

    // Asignar pesos basados en teoría musical y perfil del instrumento
    scaleNotes.forEach((note, index) => {
      let weight = 1.0;

      // Tónica y quinta tienen más peso
      if (index === 0) weight = 2.0; // Tónica
      if (index === 4) weight = 1.5; // Quinta

      // Ajuste por perfil de instrumento
      const profile = track.instrumentProfile;
      if (profile?.includes('bass') && note > 60) weight *= 0.5;
      if (profile?.includes('lead') && note < 60) weight *= 0.5;

      this.noteWeights.set(note, weight);
    });
  }

  private selectWeightedNote(scaleNotes: number[]): number {
    const weights = scaleNotes.map(n => this.noteWeights.get(n) || 1);
    const index = weightedRandomChoice(weights);
    return scaleNotes[index] || scaleNotes[0];
  }

  private calculateVelocity(intensity: number, variation: number): number {
    const base = 50 + intensity * 70;
    const rand = (Math.random() - 0.5) * variation * 40;
    return Math.max(1, Math.min(127, Math.floor(base + rand)));
  }

  private calculateDuration(variation: number): number {
    return 0.1 + Math.random() * (1 + variation);
  }

  private calculateSwingOffset(swing: number): number {
    return (Math.random() - 0.5) * swing * 0.1;
  }
}
