import p5 from 'p5';

export interface Parameter {
  key: string;
  label: string;
  min: number;
  max: number;
  defaultValue: number;
  step?: number;
  description?: string;
}

export interface MidiMapping {
  control: number;
  channel: number;
}

export interface AudioBands {
  bass: number;
  mid: number;
  treble: number;
}

export interface VisualPreset {
  id: string;
  name: string;
  description: string;
  parameters: Parameter[];
  init: (p: p5, getState: () => SketchState) => void;
}

export interface SketchState {
  params: Record<string, number>;
  audioLevel: number;
  audioBands: AudioBands;
  beat: number;
  midiPulse: number;
  midiNote: number;
  midiVelocity: number;
  orientation: 'landscape' | 'portrait';
}

export interface VisualContext {
  p: p5;
  main: p5.Graphics;
  overlay: p5.Graphics;
  feedback: p5.Graphics;
  ascii: p5.Graphics;
  state: SketchState;
  delta: number;
}

export interface VisualModule {
  id: string;
  name: string;
  params: Parameter[];
  init(context: VisualContext): void;
  update(context: VisualContext): void;
  draw(context: VisualContext): void;
  onMidiNote?(note: number, velocity: number, channel: number, context: VisualContext): void;
  onMidiCC?(cc: number, value: number, channel: number, context: VisualContext): void;
  onAudioAnalysis?(context: VisualContext): void;
}
