export type LaunchpadPreset = 'spectrum' | 'pulse' | 'wave' | 'test';

export const LAUNCHPAD_PRESETS: { id: LaunchpadPreset; label: string }[] = [
  { id: 'spectrum', label: 'Spectrum' },
  { id: 'pulse', label: 'Pulse' },
  { id: 'wave', label: 'Wave' },
  { id: 'test', label: 'Test' }
];

/**
 * Determine whether a given MIDI port belongs to a Novation Launchpad.
 * Some Launchpad models expose names like "LPPRO MIDI" or "LPX Standalone Port",
 * so we check both the manufacturer and common LP prefixes.
 */
export function isLaunchpadDevice(device: any): boolean {
  const name = (device?.name || '').toLowerCase();
  const manufacturer = (device?.manufacturer || '').toLowerCase();

  if (name.includes('launchpad')) return true;

  const fromNovation = manufacturer.includes('novation');
  return fromNovation && /^lp/.test(name);
}

/**
 * Build a frame of 64 color values for the Launchpad grid based on audio data.
 * Colors use the built-in palette (0-127).
 */
export function buildLaunchpadFrame(
  preset: LaunchpadPreset,
  data: { fft: number[]; low: number; mid: number; high: number }
): number[] {
  const colors = new Array(64).fill(0);

  switch (preset) {
    case 'spectrum': {
      // Map FFT into 8 columns
      const cols = 8;
      for (let x = 0; x < cols; x++) {
        const idx = Math.floor((data.fft.length / cols) * x);
        const v = data.fft[idx] || 0;
        const height = Math.min(8, Math.floor(v * 8));
        const color = Math.min(127, Math.floor(v * 127));
        for (let y = 0; y < height; y++) {
          colors[(7 - y) * 8 + x] = color;
        }
      }
      break;
    }
    case 'pulse': {
      const v = Math.min(
        127,
        Math.floor(((data.low + data.mid + data.high) / 3) * 127)
      );
      return colors.fill(v);
    }
    case 'wave': {
      const t = Date.now() / 150;
      for (let y = 0; y < 8; y++) {
        const v = Math.min(
          127,
          Math.floor(((Math.sin(t + y / 2) + 1) / 2) * data.mid * 127)
        );
        for (let x = 0; x < 8; x++) {
          colors[y * 8 + x] = v;
        }
      }
      break;
    }
    case 'test': {
      const t = Date.now() / 200;
      for (let y = 0; y < 8; y++) {
        for (let x = 0; x < 8; x++) {
          const fftIndex = (x + y * 8) % data.fft.length;
          const v = data.fft[fftIndex] || 0;
          const wave = (Math.sin(t + x / 2 + y / 3) + 1) / 2;
          const color = Math.min(127, Math.floor(v * wave * 127));
          colors[y * 8 + x] = color;
        }
      }
      break;
    }
  }

  return colors;
}
