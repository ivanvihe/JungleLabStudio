export interface PatternTemplate {
  name: string;
  trackType: string;
  pattern: number[]; // Steps active in 16-step grid
  variations: PatternVariation[];
  musicalContext: string;
}

export interface PatternVariation {
  name: string;
  pattern: number[];
  probability: number; // 0-1
}

export interface EuclideanPattern {
  steps: number;
  pulses: number;
  offset: number;
}

export interface ScaleTemplate {
  name: string;
  intervals: number[]; // Semitone intervals
  mood: 'dark' | 'bright' | 'neutral' | 'exotic';
  genres: string[];
}
