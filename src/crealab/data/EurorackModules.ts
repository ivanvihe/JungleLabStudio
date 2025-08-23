import type { TrackType } from '../types/CrealabTypes';

export interface EurorackModule {
  id: TrackType;
  name: string;
  description: string;
  controls: [string, string, string];
}

export const EURORACK_MODULES: EurorackModule[] = [
  {
    id: 'arp',
    name: 'ARP Sequencer',
    description: 'Secuenciador rítmico/melódico para líneas repetitivas.',
    controls: ['Transpose', 'Swing', 'Humanize']
  },
  {
    id: 'lead',
    name: 'Lead Synth',
    description: 'Sintetizador monofónico para melodías principales.',
    controls: ['Transpose', 'Swing', 'Humanize']
  },
  {
    id: 'bass',
    name: 'Bass Synth',
    description: 'Generador de bajos con cuerpo y pegada.',
    controls: ['Transpose', 'Swing', 'Humanize']
  },
  {
    id: 'kick',
    name: 'Kick Drum',
    description: 'Percusión grave y corta para bombo.',
    controls: ['Transpose', 'Swing', 'Humanize']
  },
  {
    id: 'perc',
    name: 'Snare / Clap',
    description: 'Percusión media con componente de ruido.',
    controls: ['Transpose', 'Swing', 'Humanize']
  },
  {
    id: 'fx',
    name: 'FX Noise',
    description: 'Generador de ruido y efectos.',
    controls: ['Transpose', 'Swing', 'Humanize']
  },
  {
    id: 'visual',
    name: 'Visual',
    description: 'Control de parámetros visuales.',
    controls: ['Param A', 'Param B', 'Param C']
  }
];

export const MODULE_KNOB_LABELS: Record<TrackType, [string, string, string]> = EURORACK_MODULES.reduce(
  (acc, m) => {
    acc[m.id] = m.controls;
    return acc;
  },
  {} as Record<TrackType, [string, string, string]>
);

export function getModule(id: TrackType) {
  return EURORACK_MODULES.find(m => m.id === id);
}

