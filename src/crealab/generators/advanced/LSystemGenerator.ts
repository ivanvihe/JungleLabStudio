import { GeneratorInstance } from '../../core/GeneratorEngine';
import { GenerativeTrack, MidiNote } from '../../types/CrealabTypes';
import { getScaleNotes } from '../../utils/MusicalMath';

export class LSystemGenerator implements GeneratorInstance {
  private axiom = 'A';
  private sentence = this.axiom;
  private step = 0;

  generate(
    track: GenerativeTrack,
    currentTime: number,
    globalTempo: number,
    key: string,
    scale: string
  ): MidiNote[] {
    const notes: MidiNote[] = [];
    const params = track.generator.parameters as any;
    const intensity = track.controls.intensity / 127;

    if (this.step >= this.sentence.length) {
      this.sentence = this.applyRules(this.sentence, params.rules || { A: 'AB', B: 'A' });
      this.step = 0;
    }

    const char = this.sentence[this.step++];
    const scaleNotes = getScaleNotes(key, scale);
    const index = char === 'A' ? 0 : 2;
    const note = scaleNotes[index % scaleNotes.length];

    notes.push({
      note,
      time: currentTime,
      velocity: Math.floor(60 + intensity * 60),
      duration: 0.25
    });

    return notes;
  }

  updateParameters(track: GenerativeTrack): void {
    // L-systems mainly evolve via rules string, handled in generate
  }

  reset(): void {
    this.sentence = this.axiom;
    this.step = 0;
  }

  private applyRules(sentence: string, rules: Record<string, string>): string {
    return sentence
      .split('')
      .map(ch => rules[ch] || ch)
      .join('');
  }
}

