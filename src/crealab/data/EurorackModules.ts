import type { TrackType } from '../types/CrealabTypes';

export interface EurorackModule {
  id: TrackType;
  name: string;
  description: string;
  // Labels for [intensity, paramA, paramB, paramC]
  controls: [string, string, string, string];
}

export const EURORACK_MODULES: EurorackModule[] = [
    {
      id: 'arp',
      name: 'ARP Sequencer',
      description: 'Secuenciador rítmico/melódico para líneas repetitivas.',
      controls: ['Time', 'Transpose', 'Octaves', 'Swing']
    },
    {
      id: 'lead',
      name: 'Lead Synth',
      description: 'Sintetizador monofónico para melodías principales.',
      controls: ['Intensity', 'Param A', 'Param B', 'Param C']
    },
    {
      id: 'bass',
      name: 'Bass Synth',
      description: 'Generador de bajos con cuerpo y pegada.',
      controls: ['Velocity', 'Groove', 'Bass Type', 'Variation']
    },
    {
      id: 'kick',
      name: 'Kick Drum',
      description: 'Percusión grave y corta para bombo.',
      controls: ['Intensity', 'Param A', 'Param B', 'Param C']
    },
    {
      id: 'perc',
      name: 'Snare / Clap',
      description: 'Percusión media con componente de ruido.',
      controls: ['Intensity', 'Param A', 'Param B', 'Param C']
    },
    {
      id: 'fx',
      name: 'FX Noise',
      description: 'Generador de ruido y efectos.',
      controls: ['Intensity', 'Param A', 'Param B', 'Param C']
    },
    {
      id: 'visual',
      name: 'Visual',
      description: 'Control de parámetros visuales.',
      controls: ['Intensity', 'Param A', 'Param B', 'Param C']
    }
];

export const MODULE_KNOB_LABELS: Record<TrackType, [string, string, string, string]> = EURORACK_MODULES.reduce(
  (acc, m) => {
    acc[m.id] = m.controls;
    return acc;
  },
  {} as Record<TrackType, [string, string, string, string]>
);

export function getModule(id: TrackType) {
  return EURORACK_MODULES.find(m => m.id === id);
}

