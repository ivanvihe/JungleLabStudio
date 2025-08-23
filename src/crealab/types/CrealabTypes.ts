import { SessionMidiController } from './GeneratorTypes';

export type TrackType = 'kick' | 'bass' | 'arp' | 'lead' | 'fx' | 'visual' | 'perc';

export type MusicalContext = 'intro' | 'buildup' | 'drop' | 'breakdown' | 'outro';

export interface MidiNote {
  note: number; // MIDI note number
  time: number; // Time in beats
  velocity: number; // 0-127
  duration: number; // Duration in beats
}

// Tipos de generadores disponibles
export type GeneratorType =
  | 'euclidean'      // Ritmos euclidianos
  | 'probabilistic'  // Notas por probabilidad
  | 'markov'        // Cadenas de Markov
  | 'arpeggiator'   // Arpegiador generativo
  | 'chaos'         // Sistemas caóticos
  | 'cellular'      // Autómatas celulares
  | 'lsystem'       // L-Systems fractales
  | 'neural'        // Redes neuronales simples
  | 'off';          // Desactivado

// Parámetros base para generadores
export interface GeneratorParameters {
  [key: string]: number | boolean | string | number[];
}

// Legacy - mantener para compatibilidad temporal
export interface MidiClip {
  id: string;
  name: string;
  trackType: TrackType;
  notes: MidiNote[];
  duration: number; // Duration in bars
  channel: number; // MIDI channel
  enabled: boolean;
}

// NUEVA ESTRUCTURA: Track Generativo
export interface GenerativeTrack {
  id: string;
  name: string;
  trackNumber: number; // 1-8 (fijo)
  color: string; // Para UI (#hex)
  
  // MIDI Configuration
  outputDevice: string;     // Instrumento externo (ID del device)
  outputDeviceName?: string; // Nombre legible
  midiChannel: number;      // 1-16
  sendClock?: boolean;      // Enviar MIDI clock/start/stop
  
  inputDevice?: string;     // Controlador adicional opcional
  inputDeviceName?: string;
  inputChannel?: number;
  
  // Configuración del instrumento
  instrumentProfile?: string; // 'Neutron', 'Microfreak', etc.
  
  // Generative Settings
  generator: {
    type: GeneratorType;
    enabled: boolean;
    parameters: GeneratorParameters;
    lastNoteTime: number;
    currentStep: number;
  };
  
  // Real-time controls (mapeados al Launch Control XL)
  controls: {
    intensity: number;      // Fader (0-127) - Densidad/Volume
    paramA: number;         // Knob 1 (0-127) - Parámetro específico del generador
    paramB: number;         // Knob 2 (0-127) - Parámetro específico del generador
    paramC: number;         // Knob 3 (0-127) - Parámetro específico del generador
    playStop: boolean;      // Button 1 - Play/Stop del track
    mode: number;           // Button 2 - Modo/Tipo de generador (0-5)
  };
  
  // Launch Control XL mapping (automático basado en trackNumber)
  launchControlMapping: {
    stripNumber: number;    // 1-8
    faderCC: number;       // CC del fader
    knob1CC: number;       // CC del knob superior
    knob2CC: number;       // CC del knob medio
    knob3CC: number;       // CC del knob inferior
    button1CC: number;     // CC del botón superior
    button2CC: number;     // CC del botón inferior
  };
}

// Perfiles de instrumentos con sugerencias
export interface InstrumentProfile {
  id: string;
  name: string;
  brand?: string;
  type: 'bass' | 'lead' | 'pad' | 'drum' | 'fx' | 'experimental';
  suggestedGenerators: GeneratorType[];
  defaultParameters: {
    noteRange: [number, number]; // [min, max] MIDI notes
    preferredScale?: string;
    rhythmComplexity?: 'simple' | 'medium' | 'complex';
    [key: string]: any;
  };
  description: string;
  color: string; // Color sugerido para el track
}

// Transport state
export interface TransportState {
  isPlaying: boolean;
  isPaused: boolean;
  currentBeat: number;
  currentBar: number;
  currentStep: number;
}

// MIDI Clock configuration
export interface MidiClockConfig {
  enabled: boolean;
  source: 'internal' | 'external';
  outputDevice?: string;
  inputDevice?: string;
  ppqn: number; // Pulses per quarter note (default 24)
}

// Legacy interfaces - mantener temporalmente
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
  slots: any[]; // Temporal

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

// NUEVA ESTRUCTURA DEL PROYECTO
export interface CreaLabProject {
  id: string;
  name: string;
  description?: string;

  // 8 tracks fijos - SIEMPRE presentes, no se pueden añadir/eliminar
  tracks: [
    GenerativeTrack, // Track 1
    GenerativeTrack, // Track 2  
    GenerativeTrack, // Track 3
    GenerativeTrack, // Track 4
    GenerativeTrack, // Track 5
    GenerativeTrack, // Track 6
    GenerativeTrack, // Track 7
    GenerativeTrack  // Track 8
  ];
  
  // Global settings
  globalTempo: number;     // BPM
  key: string;            // Tónica musical
  scale: string;          // Escala musical
  genre: string;          // Género para sugerencias
  
  // Transport state
  transport: TransportState;
  
  // Launch Control XL
  launchControl: {
    connected: boolean;
    deviceId?: string;
    deviceName?: string;
  };
  
  // MIDI Clock sync
  midiClock: MidiClockConfig;
  
  // Legacy - mantener para migración
  scenes?: Scene[];
  oldTracks?: Track[];
}

// Tipos de formato para exportar proyectos
export type ProjectExportFormat = 'json' | 'preset' | 'ableton';


// === MIDI SYSTEM TYPES ===
export interface MidiDevice {
  id: string;
  name: string;
  manufacturer?: string;
  type: 'input' | 'output';
  state: 'connected' | 'disconnected';
  connection: string;
}

export interface MidiMessage {
  data: Uint8Array;
  timestamp: number;
  deviceId: string;
}

export interface MidiClockState {
  isRunning: boolean;
  bpm: number;
  currentBeat: number;
  currentStep: number;
  source: 'internal' | 'external';
}
