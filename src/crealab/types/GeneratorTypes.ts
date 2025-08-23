import { MidiNote } from './CrealabTypes';

export type GeneratorType =
  | 'euclidean'        // Patrones euclidianos dinámicos
  | 'euclidean-circles' // Euclidean Circles v2
  | 'markov'          // Cadenas de Markov
  | 'probabilistic'   // Notas por probabilidad
  | 'arpeggiator'     // Arpegiador generativo
  | 'sequencer'       // Secuenciador con variaciones
    | 'chaos'           // Sistemas caóticos
    | 'cellular'        // Autómatas celulares
    | 'lsystem'        // L-Systems fractales
    | 'neural'        // Redes neuronales simples
    | 'magenta'       // Generador basado en Magenta.js
    | 'bassline';     // Generador específico de bajos

export interface MidiGenerator {
  id: string;
  name: string;
  type: GeneratorType;
  isActive: boolean;
  isPlaying: boolean;
  parameters: GeneratorParameters;
  lastNoteTime: number;
  currentStep: number;
  generatedNotes: MidiNote[];
  
  // Control en tiempo real
  realTimeControls: {
    density: number;      // 0-1: Densidad de notas
    probability: number;  // 0-1: Probabilidad de trigger
    velocity: number;     // 0-1: Velocity multiplier
    octave: number;       // -3 to +3: Octave shift
    chaos: number;        // 0-1: Randomness amount
    evolution: number;    // 0-1: Pattern evolution rate
    swing: number;        // 0-1: Timing swing
    filter: number;       // 0-1: Note filtering
  };
  
  // MIDI mapping para controladores
  midiMapping?: {
    controllerId: string;
    channelStrip: number; // 1-8 for Launch Control XL
    ccMappings: {
      [control: string]: number; // CC number
    };
  };
}

export interface GeneratorParameters {
  // Parámetros base
  scale: string;
  key: string;
  notePool: number[];
  tempo: number;
  
  // Parámetros específicos por tipo
  euclidean?: EuclideanParams;
  markov?: MarkovParams;
  probabilistic?: ProbabilisticParams;
  arpeggiator?: ArpeggiatorParams;
  chaos?: ChaosParams;
}

export interface EuclideanParams {
  pulses: number;        // Número de hits
  steps: number;         // Longitud del patrón
  offset: number;        // Rotación del patrón
  mutationRate: number;  // Tasa de evolución
  polyrhythm: boolean;   // Habilitar polirritmia
}

export interface MarkovParams {
  order: number;         // N-gram order (1-4)
  creativity: number;    // 0-1: Balance entre repetición y novedad
  trainingClips: string[]; // IDs de clips para entrenar
  contextLength: number; // Longitud del contexto
}

export interface ProbabilisticParams {
  noteWeights: { [note: number]: number }; // Peso por nota
  rhythmPattern: number[]; // Patrón rítmico base
  variation: number;     // Variación rítmica
}

export interface ArpeggiatorParams {
  pattern: 'up' | 'down' | 'upDown' | 'random' | 'custom';
  octaveRange: number;   // Rango de octavas
  noteLength: number;    // Duración de notas
  swing: number;         // Swing amount
  customPattern?: number[]; // Patrón personalizado
}

export interface ChaosParams {
  attractor: 'lorenz' | 'henon' | 'rossler';
  sensitivity: number;   // Sensibilidad al caos
  scaling: number;       // Escalado de valores
  dimensions: 2 | 3;     // Dimensiones del atractor
}

// Tipos para control de slots híbridos
export type SlotContentType = 'empty' | 'midiClip' | 'generator' | 'hybrid';

export interface SlotContent {
  id: string;
  type: SlotContentType;
  name: string;
  slotIndex: number;
  
  // Contenido específico
  midiClip?: any; // MidiClip existente
  generator?: MidiGenerator;
  hybrid?: HybridContent;
  
  // Control
  isActive: boolean;
  volume: number; // 0-1
  probability: number; // 0-1
}

export interface HybridContent {
  staticClip: any; // MidiClip base
  generator: MidiGenerator;
  blendMode: 'add' | 'multiply' | 'replace' | 'interleave';
  generatorInfluence: number; // 0-1
}

// Interfaces para controladores MIDI
export interface SessionMidiController {
  id: string;
  name: string;
  type: 'launchControl' | 'akai' | 'oxygen' | 'generic';
  isConnected: boolean;
  
  // Mapping de controles
  channelStrips: ChannelStrip[];
  globalControls: GlobalMidiControl[];
  
  // Estado actual
  currentValues: { [ccNumber: number]: number };
}

export interface ChannelStrip {
  stripIndex: number; // 1-8 for Launch Control XL
  trackId?: string;   // Track asignado
  
  controls: {
    fader: number;      // CC para fader principal
    knob1: number;      // CC para knob 1 (density)
    knob2: number;      // CC para knob 2 (probability)
    knob3: number;      // CC para knob 3 (velocity)
    button1: number;    // CC para botón 1 (play/stop)
    button2: number;    // CC para botón 2 (record)
  };
  
  // Estado actual
  values: {
    fader: number;      // 0-127
    knob1: number;      // 0-127
    knob2: number;      // 0-127
    knob3: number;      // 0-127
    button1: boolean;   // pressed
    button2: boolean;   // pressed
  };
}

export interface GlobalMidiControl {
  name: string;
  ccNumber: number;
  value: number;
  function: 'masterTempo' | 'globalVolume' | 'sceneSelect' | 'transport';
}

// Templates de generadores
export interface GeneratorTemplate {
  id: string;
  name: string;
  description: string;
  type: GeneratorType;
  bestFor: string[]; // ['kick', 'bass', etc.]
  defaultParameters: GeneratorParameters;
  previewPattern?: boolean[]; // Preview del patrón
}

