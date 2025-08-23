import { GeneratorInstance } from '../core/GeneratorEngine';
import { GenerativeTrack, MidiNote } from '../types/CrealabTypes';
// Magenta is loaded dynamically to avoid bundling heavy dependencies.
// Declare lightweight type aliases so the build can succeed even if the
// library isn't installed locally.
type MagentaModule = typeof import('@magenta/music');
type MusicRNN = import('@magenta/music').MusicRNN;
type NoteSequence = import('@magenta/music').INoteSequence;

export class MagentaGenerator implements GeneratorInstance {
  private mm: MagentaModule | null = null;
  private rnn: MusicRNN | null = null;
  private loaded = false;
  private sequence: NoteSequence | null = null;
  private generating = false;
  private step = 0;

  constructor() {
    import('@magenta/music').then(mod => {
      this.mm = mod;
      this.rnn = new mod.MusicRNN(
        'https://storage.googleapis.com/magentadata/js/checkpoints/music_rnn/basic_rnn'
      );
      this.rnn.initialize().then(() => (this.loaded = true));
    });
  }

  generate(
    track: GenerativeTrack,
    currentTime: number,
    globalTempo: number,
    key: string,
    scale: string
  ): MidiNote[] {
    if (!track.controls.playStop || !this.loaded || !this.rnn || !this.mm)
      return [];

    const steps = Math.max(1, Math.floor((track.controls.paramA / 127) * 64));
    const temperature = 0.1 + (track.controls.paramB / 127) * 1.9;
    const density = track.controls.paramC / 127;

    if (!this.sequence && !this.generating) {
        this.generating = true;
        const seed: NoteSequence = { notes: [], totalTime: 0 };
        this.rnn
          .continueSequence(seed, steps, temperature)
        .then(seq => {
          this.sequence = this.mm!.sequences.quantizeNoteSequence(seq, 4);
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
      if (n.quantizedStartStep === quantStep && Math.random() < density) {
        const durationSteps = n.quantizedEndStep - n.quantizedStartStep;
        const velocity = Math.max(
          1,
          Math.floor((n.velocity || 80) * (track.controls.intensity / 127))
        );
        notes.push({
          note: n.pitch!,
          time: currentTime,
          velocity,
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
