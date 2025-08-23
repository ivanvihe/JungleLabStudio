export type TrackType = 'kick' | 'bass' | 'arp' | 'lead' | 'fx' | 'visual' | 'perc';

export type MusicalContext = 'intro' | 'buildup' | 'drop' | 'breakdown' | 'outro';

export interface MidiNote {
  note: number; // MIDI note number
  time: number; // Time in beats
  velocity: number; // 0-127
  duration: number; // Duration in beats
}

export interface MidiClip {
  id: string;
  name: string;
  trackType: TrackType;
  notes: MidiNote[];
  duration: number; // Duration in bars
  channel: number; // MIDI channel
  enabled: boolean;
}

export interface Phase {
  id: string;
  name: string;
}

export interface Track {
  id: string;
  name: string;
  midiDevice: string;
  clips: Record<string, MidiClip | null>; // phaseId -> clip
}

export interface VisualClip {
  id: string;
  presetId: string;
  triggers: VisualTrigger[];
  duration: number;
}

export interface VisualTrigger {
  time: number;
  type: 'beat' | 'note' | 'custom';
  intensity: number;
}

export interface Scene {
  id: string;
  name: string;
  duration: number; // Duration in bars
  tempo: number;
  clips: MidiClip[];
  visualConfig: VisualSceneConfig;
  musicalContext: MusicalContext;
}

export interface VisualSceneConfig {
  primaryPreset: string;
  layerPresets: Record<string, string>; // layerId -> presetId
  triggers: VisualTrigger[];
}

export interface CreaLabProject {
  id: string;
  name: string;
  scenes?: Scene[];
  phases?: Phase[];
  tracks?: Track[];
  globalTempo: number;
  key: string;
  scale: string;
}
