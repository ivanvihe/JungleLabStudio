import { GeneratorInstance } from '../core/GeneratorEngine';
import { GenerativeTrack, MidiNote } from '../types/CrealabTypes';
import { generateEuclideanPattern } from '../utils/euclideanPatterns';
import { getScaleNotes } from '../utils/MusicalMath';

/**
 * Simple bassline generator using predefined Euclidean patterns.
 * Supports pattern style selection and small variation amount.
 */
export class BasslineGenerator implements GeneratorInstance {
  private step = 0;
  private cachedPattern: boolean[] = [];
  private cachedStyle: string | null = null;

  /** Update internal pattern cache when parameters change */
  updateParameters(track: GenerativeTrack): void {
    const params = track.generator.parameters as any;
    const style: string = params.pattern || 'dub';
    if (style !== this.cachedStyle) {
      this.cachedPattern = generateEuclideanPattern('bass', style);
      this.cachedStyle = style;
      this.step = 0;
    }
  }

  /** Reset generator state */
  reset(): void {
    this.step = 0;
    this.cachedStyle = null;
    this.cachedPattern = [];
  }

  /** Generate bassline notes for current step */
  generate(
    track: GenerativeTrack,
    currentTime: number,
    globalTempo: number,
    key: string,
    scale: string
  ): MidiNote[] {
    if (this.cachedPattern.length === 0) {
      this.updateParameters(track);
    }

    const patternStep = this.cachedPattern[this.step % this.cachedPattern.length];
    this.step++;

    if (!patternStep) {
      return [];
    }

    const sliderVariation = (track.generator.parameters as any).variation || 0;
    const knobVariation = track.controls.paramC / 127;
    const variation = Math.min(1, sliderVariation + knobVariation);
    const scaleNotes = getScaleNotes(key, scale);
    const baseIndex = Math.floor((track.controls.paramB / 127) * (scaleNotes.length - 1));
    let note = scaleNotes[baseIndex];
    if (variation > 0) {
      const index = Math.floor(Math.random() * scaleNotes.length);
      if (Math.random() < variation) {
        note = scaleNotes[index];
      }
    }

    const velocity = Math.floor(40 + (track.controls.intensity / 127) * 87); // intensity as velocity
    const duration = 0.25 + (track.controls.paramA / 127) * 0.5; // paramA alters groove

    return [
      {
        note,
        time: currentTime,
        velocity,
        duration,
      },
    ];
  }
}
