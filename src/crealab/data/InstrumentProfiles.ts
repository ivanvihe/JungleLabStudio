import { InstrumentProfile } from '../types/CrealabTypes';

// Base de datos de perfiles de instrumentos
export const INSTRUMENT_PROFILES: InstrumentProfile[] = [
  // === BASS SYNTHESIZERS ===
  {
    id: 'neutron',
    name: 'Neutron',
    brand: 'Behringer',
    type: 'bass',
    suggestedGenerators: ['euclidean', 'probabilistic'],
    defaultParameters: {
      noteRange: [24, 48], // C1 to C3
      preferredScale: 'minor',
      rhythmComplexity: 'medium',
      density: 0.6,
      pulses: 6,
      steps: 16
    },
    description: 'Generador de bass progresivo con filtros análogos. Ideal para líneas de bajo potentes y grooves complejos.',
    color: '#ff6b35',
    tags: ['bass', 'analog', 'filter', 'progressive']
  },
  {
    id: 'minitaur',
    name: 'Minitaur',
    brand: 'Moog',
    type: 'bass',
    suggestedGenerators: ['euclidean', 'arpeggiator'],
    defaultParameters: {
      noteRange: [24, 60],
      rhythmComplexity: 'simple',
      density: 0.7,
      pulses: 4,
      steps: 8
    },
    description: 'Bass clásico Moog con sub-osciladores potentes. Perfecto para techno y house.',
    color: '#d62d20',
    tags: ['bass', 'moog', 'sub', 'classic']
  },

  // === LEAD SYNTHESIZERS ===
  {
    id: 'arp2600',
    name: 'ARP 2600',
    brand: 'ARP',
    type: 'lead',
    suggestedGenerators: ['markov', 'chaos', 'arpeggiator'],
    defaultParameters: {
      noteRange: [48, 84], // C3 to C6
      preferredScale: 'dorian',
      rhythmComplexity: 'complex',
      creativity: 0.7,
      attractor: 'lorenz',
      pattern: 'upDown'
    },
    description: 'Leads generativos modulares con carácter vintage. Ideal para solos expresivos y melodías evolutivas.',
    color: '#ffa500',
    tags: ['lead', 'modular', 'vintage', 'expressive']
  },
  {
    id: 'prophet5',
    name: 'Prophet-5',
    brand: 'Sequential',
    type: 'lead',
    suggestedGenerators: ['arpeggiator', 'markov'],
    defaultParameters: {
      noteRange: [48, 72],
      pattern: 'up',
      octaves: 2,
      creativity: 0.5
    },
    description: 'Sintetizador clásico americano. Perfecto para arpeggios y leads melódicos.',
    color: '#4a90e2',
    tags: ['lead', 'classic', 'american', 'melodic']
  },

  // === EXPERIMENTAL SYNTHESIZERS ===
  {
    id: 'microfreak',
    name: 'MicroFreak',
    brand: 'Arturia',
    type: 'experimental',
    suggestedGenerators: ['chaos', 'markov', 'probabilistic'],
    defaultParameters: {
      noteRange: [36, 96], // Rango amplio
      attractor: 'henon',
      sensitivity: 0.8,
      creativity: 0.9,
      microtonal: true
    },
    description: 'Secuencias experimentales con microtonalidad y texturas únicas. Para exploración sónica avanzada.',
    color: '#e74c3c',
    tags: ['experimental', 'microtonal', 'digital', 'unique']
  },
  {
    id: 'digitakt',
    name: 'Digitakt',
    brand: 'Elektron',
    type: 'experimental',
    suggestedGenerators: ['euclidean', 'probabilistic'],
    defaultParameters: {
      noteRange: [24, 84],
      pulses: 7,
      steps: 16,
      density: 0.4,
      mutation: 0.3
    },
    description: 'Sampler/drum machine para texturas experimentales y ritmos complejos.',
    color: '#2c3e50',
    tags: ['sampler', 'experimental', 'elektron', 'complex']
  },

  // === DRUM MACHINES ===
  {
    id: 'modelcycles',
    name: 'Model:Cycles',
    brand: 'Elektron',
    type: 'drum',
    suggestedGenerators: ['euclidean', 'probabilistic'],
    defaultParameters: {
      noteRange: [36, 60], // Drum range
      pulses: 8,
      steps: 16,
      density: 0.8,
      mutation: 0.2
    },
    description: 'Patrones de percusión euclidiana con síntesis FM. Ideal para ritmos complejos y evolución de patrones.',
    color: '#27ae60',
    tags: ['drums', 'euclidean', 'fm', 'elektron']
  },
  {
    id: 'tr808',
    name: 'TR-808',
    brand: 'Roland',
    type: 'drum',
    suggestedGenerators: ['euclidean', 'probabilistic'],
    defaultParameters: {
      noteRange: [36, 60],
      pulses: 4,
      steps: 16,
      density: 0.6
    },
    description: 'Drum machine clásica. Perfecto para patrones de hip-hop y electrónica.',
    color: '#95a5a6',
    tags: ['drums', 'classic', 'roland', 'hiphop']
  },

  // === PAD/AMBIENT SYNTHESIZERS ===
  {
    id: 'deepmind',
    name: 'DeepMind 12',
    brand: 'Behringer',
    type: 'pad',
    suggestedGenerators: ['probabilistic', 'markov', 'chaos'],
    defaultParameters: {
      noteRange: [24, 72],
      density: 0.3,
      creativity: 0.6,
      sensitivity: 0.4
    },
    description: 'Pads evolutivos y texturas ambientales. Ideal para fondos generativos y atmosferas.',
    color: '#9b59b6',
    tags: ['pad', 'ambient', 'lush', 'evolving']
  },

  // === GENERIC PROFILES ===
  {
    id: 'generic_bass',
    name: 'Generic Bass',
    brand: '',
    type: 'bass',
    suggestedGenerators: ['euclidean', 'probabilistic'],
    defaultParameters: {
      noteRange: [24, 48],
      density: 0.6,
      pulses: 6,
      steps: 16
    },
    description: 'Perfil genérico para sintetizadores de bass.',
    color: '#34495e',
    tags: ['bass', 'generic']
  },
  {
    id: 'generic_lead',
    name: 'Generic Lead',
    brand: '',
    type: 'lead',
    suggestedGenerators: ['arpeggiator', 'markov'],
    defaultParameters: {
      noteRange: [48, 84],
      pattern: 'up',
      creativity: 0.5
    },
    description: 'Perfil genérico para sintetizadores lead.',
    color: '#3498db',
    tags: ['lead', 'generic']
  }
];

// Funciones utilitarias
export function getProfilesByType(type: string): InstrumentProfile[] {
  return INSTRUMENT_PROFILES.filter(profile => profile.type === type);
}

export function getProfileById(id: string): InstrumentProfile | undefined {
  return INSTRUMENT_PROFILES.find(profile => profile.id === id);
}

export function getProfilesByTag(tag: string): InstrumentProfile[] {
  return INSTRUMENT_PROFILES.filter(profile => profile.tags?.includes(tag));
}

export function getProfilesByGenre(genre: string): InstrumentProfile[] {
  const genreProfiles: { [key: string]: string[] } = {
    'Techno': ['neutron', 'tr808', 'modelcycles', 'arp2600'],
    'House': ['minitaur', 'prophet5', 'tr808'],
    'Ambient': ['deepmind', 'microfreak', 'arp2600'],
    'Experimental': ['microfreak', 'digitakt', 'arp2600'],
    'Drum & Bass': ['neutron', 'modelcycles', 'digitakt'],
    'Dubstep': ['neutron', 'microfreak', 'modelcycles'],
    'Trance': ['prophet5', 'arp2600', 'deepmind'],
    'IDM': ['digitakt', 'microfreak', 'modelcycles']
  };

  const profileIds = genreProfiles[genre] || [];
  return profileIds.map(id => getProfileById(id)).filter(Boolean) as InstrumentProfile[];
}


