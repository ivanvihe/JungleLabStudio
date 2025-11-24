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
  audioBands: { bass: number; mid: number; treble: number };
  beat: number;
  midiPulse: number;
  orientation: 'landscape' | 'portrait';
}

export interface MidiMapping {
  control: number;
  channel: number;
}
