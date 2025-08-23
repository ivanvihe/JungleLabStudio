import { GeneratorInstance } from '../core/GeneratorEngine';
import { GenerativeTrack, MidiNote } from '../types/CrealabTypes';
import * as mm from '@magenta/music';

export class MagentaGenerator implements GeneratorInstance {
  private rnn: mm.MusicRNN;
  private loaded = false;
  private sequence: mm.INoteSequence | null = null;
  private generating = false;
  private step = 0;

  constructor() {
    this.rnn = new mm.MusicRNN(
      'https://storage.googleapis.com/magentadata/js/checkpoints/music_rnn/basic_rnn'
    );
    this.rnn.initialize().then(() => (this.loaded = true));
  }

  generate(
    track: GenerativeTrack,
    currentTime: number,
    globalTempo: number,
    key: string,
    scale: string
  ): MidiNote[] {
    if (!track.controls.playStop || !this.loaded) return [];

    const params = track.generator.parameters;
    const steps = (params.steps as number) || 32;
    const temperature = (params.temperature as number) || 1.0;

    if (!this.sequence && !this.generating) {
      this.generating = true;
      const seed: mm.INoteSequence = { notes: [], totalTime: 0 };
      this.rnn
        .continueSequence(seed, steps, temperature)
        .then(seq => {
          this.sequence = mm.sequences.quantizeNoteSequence(seq, 4);
          this.generating = false;
          this.step = 0;
        })
        .catch(() => {
          this.generating = false;
        });
      return [];
    }

    if (!this.sequence) return [];

    const notes: MidiNote[] = [];
    const quantStep = this.step;

    this.sequence.notes.forEach(n => {
      if (n.quantizedStartStep === quantStep) {
        const durationSteps = n.quantizedEndStep - n.quantizedStartStep;
        notes.push({
          note: n.pitch!,
          time: currentTime,
          velocity: n.velocity || 80,
          duration: durationSteps * 0.25,
        });
      }
    });

    this.step++;
    if (this.step >= steps) {
      this.sequence = null;
      this.step = 0;
    }

    return notes;
  }

  updateParameters(track: GenerativeTrack): void {
    // Parameters handled dynamically in generate
  }

  reset(): void {
    this.sequence = null;
    this.step = 0;
  }
}
