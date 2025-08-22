export type LaunchpadPreset = 'spectrum' | 'pulse' | 'wave' | 'test' | 'rainbow' | 'snake';

export const LAUNCHPAD_PRESETS: { id: LaunchpadPreset; label: string }[] = [
  { id: 'spectrum', label: 'Spectrum' },
  { id: 'pulse', label: 'Pulse' },
  { id: 'wave', label: 'Wave' },
  { id: 'test', label: 'Test Pattern' },
  { id: 'rainbow', label: 'Rainbow' },
  { id: 'snake', label: 'Snake' }
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
  if (name.includes('lppro') || name.includes('llpro') || name.includes('mk3')) return true;

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

  // Verificar que tenemos datos válidos
  if (!data.fft || data.fft.length === 0) {
    return colors; // retornar todo apagado si no hay datos
  }

  switch (preset) {
    case 'spectrum': {
      // Map FFT into 8 columns
      const cols = 8;
      for (let x = 0; x < cols; x++) {
        const idx = Math.floor((data.fft.length / cols) * x);
        const v = data.fft[idx] || 0;
        // Amplificar la señal para mejor visibilidad
        const amplified = Math.min(1, v * 3);
        const height = Math.min(8, Math.floor(amplified * 8));
        const color = Math.min(127, Math.floor(amplified * 100) + 10);
        for (let y = 0; y < height; y++) {
          if (color > 0) {
            colors[(7 - y) * 8 + x] = color;
          }
        }
      }
      break;
    }
    case 'pulse': {
      const v = Math.min(
        127,
        Math.floor(((data.low + data.mid + data.high) / 3) * 150) + 5
      );
      return colors.fill(v);
    }
    case 'wave': {
      const t = Date.now() / 150;
      for (let y = 0; y < 8; y++) {
        const v = Math.min(
          127,
          Math.floor(((Math.sin(t + y / 2) + 1) / 2) * data.mid * 100) + 10
        );
        for (let x = 0; x < 8; x++) {
          colors[y * 8 + x] = v;
        }
      }
      break;
    }
    case 'test': {
      // PRESET TEST COMPLETAMENTE INDEPENDIENTE DEL AUDIO
      const t = Date.now() / 300;
      for (let y = 0; y < 8; y++) {
        for (let x = 0; x < 8; x++) {
          // Patrón de ondas cruzadas independiente
          const wave1 = Math.sin(t + x * 0.8) * 0.5;
          const wave2 = Math.sin(t * 0.7 + y * 0.6) * 0.5;
          const combined = (wave1 + wave2 + 2) / 4;

          // Color que va de 20 a 100
          const color = Math.floor(combined * 80) + 20;
          colors[y * 8 + x] = color;
        }
      }
      break;
    }
    case 'rainbow': {
      // ARCOÍRIS ROTATIVO
      const t = Date.now() / 100;
      for (let y = 0; y < 8; y++) {
        for (let x = 0; x < 8; x++) {
          const hue = (x + y + t * 0.01) % 8;
          const colors_palette = [15, 30, 45, 60, 75, 90, 105, 120];
          const color = colors_palette[Math.floor(hue)];
          colors[y * 8 + x] = color;
        }
      }
      break;
    }
    case 'snake': {
      // EFECTO SERPIENTE MÓVIL
      const t = Date.now() / 150;
      const snakeLength = 12;

      colors.fill(0);

      for (let i = 0; i < snakeLength; i++) {
        const phase = (t + i * 0.5) % (Math.PI * 4);

        let x = Math.floor((Math.sin(phase) + 1) * 3.5);
        let y = Math.floor((Math.cos(phase * 0.7) + 1) * 3.5);

        x = Math.max(0, Math.min(7, x));
        y = Math.max(0, Math.min(7, y));

        const index = y * 8 + x;
        const intensity = Math.floor(((snakeLength - i) / snakeLength) * 100) + 20;

        if (colors[index] < intensity) {
          colors[index] = intensity;
        }
      }
      break;
    }
  }

  return colors;
}
