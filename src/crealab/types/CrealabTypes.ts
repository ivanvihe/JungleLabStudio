import { SlotContent, SessionMidiController } from './GeneratorTypes';

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

export interface Track {
  id: string;
  name: string;
  color?: string; // Hex color para UI
  
  // MIDI Input/Output devices
  midiInputDevice: string;   // Para controladores como AKAI
  midiInputDeviceName?: string;
  midiOutputDevice: string;  // Para sintetizadores
  midiOutputDeviceName?: string;
  midiChannel: number;
  
  // Control settings
  volume: number;     // 0-127
  pan: number;        // -64 to +63
  mute: boolean;
  solo: boolean;
  record: boolean;
  
  // Clips híbridos (MIDI clips + generators)
  slots: SlotContent[];
  
  // Track type específico
  trackType: TrackType;
  
  // Mapping a controlador de sesión
  sessionControllerStrip?: number; // 1-8 for Launch Control XL
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
  description?: string;

  scenes?: Scene[];
  tracks?: Track[];

  globalTempo: number;
  key: string;
  scale: string;

  // Session MIDI controller
  sessionController?: SessionMidiController;
}
