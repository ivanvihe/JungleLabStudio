import { GenerativeTrack } from '../types/CrealabTypes';
import { Note, Scale, Chord } from 'tonal';

export interface HarmonicAnalysis {
  key: string;
  scale: string;
  chords: string[];
}

/**
 * MusicalIntelligence provides advanced musical awareness features
 * used by generators to react to musical context.
 */
export class MusicalIntelligence {
  /**
   * Performs a very light-weight harmonic analysis based on the note pools
   * of all active tracks. Returns detected key, scale and possible chords.
   */
  static analyzeHarmony(tracks: GenerativeTrack[]): HarmonicAnalysis {
    const noteNumbers = tracks.flatMap(t =>
      (t.generator.parameters as any).notePool || []
    );

    const noteNames = noteNumbers
      .map(n => Note.fromMidi(n))
      .filter((n): n is string => !!n);

    const detectedScale = Scale.detect(noteNames)[0] || 'C major';
    const [detectedKey, detectedMode] = detectedScale.split(' ');
    const chords = Chord.detect(noteNames);

    return {
      key: detectedKey || 'C',
      scale: detectedMode || 'major',
      chords
    };
  }

  /**
   * Evolves generator parameters in real time. The evolution amount is read
   * from track.controls.paramC and mapped to a mutation/evolution parameter
   * if present in the generator.
   */
  static evolvePattern(track: GenerativeTrack) {
    const amount = (track.controls.paramC || 0) / 127;
    const params = track.generator.parameters as any;
    if (params.mutation != null) {
      params.mutation = amount;
    } else if (params.evolution != null) {
      params.evolution = amount;
    }
  }

  /**
   * Applies a simple cross-track influence by averaging intensities
   * between tracks so that extreme values gradually converge.
   */
  static applyCrossTrackInfluence(tracks: GenerativeTrack[]) {
    if (tracks.length === 0) return;
    const avg =
      tracks.reduce((sum, t) => sum + t.controls.intensity, 0) /
      tracks.length;
    tracks.forEach(t => {
      t.controls.intensity = Math.round((t.controls.intensity + avg) / 2);
    });
  }

  /**
   * Adjusts generator parameters to match a given genre. The mapping here is
   * intentionally simple and can be expanded with real datasets.
   */
  static applyGenreStyle(track: GenerativeTrack, genre: string) {
    const params = track.generator.parameters as any;
    switch (genre) {
      case 'ambient':
        params.density = 0.3;
        params.variation = 0.1;
        break;
      case 'techno':
        params.density = 0.8;
        params.variation = 0.5;
        break;
      case 'hiphop':
        params.density = 0.5;
        params.swing = 0.3;
        break;
      default:
        break;
    }
  }
}

