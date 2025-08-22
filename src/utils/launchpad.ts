export type LaunchpadPreset =
  | 'spectrum'
  | 'pulse'
  | 'wave'
  | 'test'
  | 'rainbow'
  | 'snake'
  | 'canvas';

export const LAUNCHPAD_PRESETS: { id: LaunchpadPreset; label: string }[] = [
  { id: 'spectrum', label: 'Spectrum' },
  { id: 'pulse', label: 'Pulse' },
  { id: 'wave', label: 'Wave' },
  { id: 'test', label: 'Test Pattern' },
  { id: 'rainbow', label: 'Rainbow' },
  { id: 'snake', label: 'Snake' },
  { id: 'canvas', label: 'Canvas' }
];

const GRID_SIZE = 8;
const GRID_LEN = GRID_SIZE * GRID_SIZE;

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
 * Convert a 0-63 grid index (0 = top-left, 63 = bottom-right) to the
 * corresponding Launchpad MIDI note number.
 *
 * The physical Launchpad layout numbers pads from the bottom-left corner
 * with a stride of 16 between rows. For example, the bottom row spans
 * notes 0-7, the next row 16-23, and so on up to 112-119 at the top.
 */
export function gridIndexToNote(index: number): number {
  const rowFromTop = Math.floor(index / GRID_SIZE); // 0 = top row
  const col = index % GRID_SIZE;
  const rowFromBottom = GRID_SIZE - 1 - rowFromTop;
  return rowFromBottom * 16 + col;
}

/**
 * Sample the current canvas and downscale it to an 8x8 grid for the Launchpad.
 * This returns 64 brightness values (0-127) representing the canvas image.
 */
export function canvasToLaunchpadFrame(canvas: HTMLCanvasElement): number[] {
  const offscreen = document.createElement('canvas');
  offscreen.width = GRID_SIZE;
  offscreen.height = GRID_SIZE;
  const ctx = offscreen.getContext('2d', { willReadFrequently: true });
  if (!ctx) {
    return new Array(GRID_LEN).fill(0);
  }

  // Draw the source canvas scaled to 8x8
  ctx.drawImage(canvas, 0, 0, GRID_SIZE, GRID_SIZE);
  const imgData = ctx.getImageData(0, 0, GRID_SIZE, GRID_SIZE).data;

  const colors = new Array(GRID_LEN).fill(0);
  for (let i = 0; i < GRID_LEN; i++) {
    const r = imgData[i * 4];
    const g = imgData[i * 4 + 1];
    const b = imgData[i * 4 + 2];
    const a = imgData[i * 4 + 3] / 255;

    const brightness = (r + g + b) / 3 / 255;
    const value = Math.min(127, Math.floor(brightness * a * 127));
    colors[i] = value;
  }

  return colors;
}

/**
 * Build a frame of 64 color values for the Launchpad grid based on audio data.
 * Colors use the built-in palette (0-127).
 * ¡IMPORTANTE! Esta función SIEMPRE debe devolver exactamente 64 valores para el grid 8x8
 */
export function buildLaunchpadFrame(
  preset: LaunchpadPreset,
  data: { fft: number[]; low: number; mid: number; high: number }
): number[] {
  // 🔥 CRÍTICO: Siempre inicializar con exactamente 64 elementos (8x8 grid)
  const colors = new Array(GRID_LEN).fill(0);

  // Debug: verificar que tenemos datos válidos
  if (!data.fft || data.fft.length === 0) {
    console.log('⚠️ buildLaunchpadFrame: No hay datos FFT, devolviendo grid vacío');
    return colors; // retornar todo apagado si no hay datos
  }

  switch (preset) {
    case 'spectrum': {
      // Map FFT into 8 columns (grid completo 8x8)
      const cols = GRID_SIZE;
      for (let x = 0; x < cols; x++) {
        const idx = Math.floor((data.fft.length / cols) * x);
        const v = data.fft[idx] || 0;
        // Amplificar la señal para mejor visibilidad
        const amplified = Math.min(1, v * 3);
        const height = Math.min(GRID_SIZE, Math.floor(amplified * GRID_SIZE));
        const color = Math.min(127, Math.floor(amplified * 100) + 10);

        // Llenar desde abajo hacia arriba
        for (let y = 0; y < height; y++) {
          const gridIndex = (GRID_SIZE - 1 - y) * GRID_SIZE + x; // Fila (7-y) * 8 + columna x
          if (gridIndex >= 0 && gridIndex < GRID_LEN && color > 0) {
            colors[gridIndex] = color;
          }
        }
      }
      break;
    }
    case 'pulse': {
      // Pulso que llena todo el grid
      const v = Math.min(
        127,
        Math.floor(((data.low + data.mid + data.high) / 3) * 150) + 5
      );
      // Llenar todos los 64 pads con la misma intensidad
      colors.fill(v);
      break;
    }
    case 'wave': {
      // Onda que se mueve por todo el grid 8x8
      const t = Date.now() / 150;
      for (let y = 0; y < GRID_SIZE; y++) {
        for (let x = 0; x < GRID_SIZE; x++) {
          const gridIndex = y * GRID_SIZE + x;
          const wave = Math.sin(t + x * 0.5 + y * 0.3);
          const intensity = Math.min(127, Math.floor(((wave + 1) / 2) * data.mid * 100) + 10);
          colors[gridIndex] = intensity;
        }
      }
      break;
    }
    case 'test': {
      // PRESET TEST COMPLETAMENTE INDEPENDIENTE DEL AUDIO
      // Usa TODO el grid 8x8 con un patrón visible
      const t = Date.now() / 300;
      for (let y = 0; y < GRID_SIZE; y++) {
        for (let x = 0; x < GRID_SIZE; x++) {
          const gridIndex = y * GRID_SIZE + x;

          // Patrón de ondas cruzadas que cubre todo el grid
          const wave1 = Math.sin(t + x * 0.8) * 0.5;
          const wave2 = Math.sin(t * 0.7 + y * 0.6) * 0.5;
          const combined = (wave1 + wave2 + 2) / 4;

          // Color que va de 20 a 100
          const color = Math.floor(combined * 80) + 20;
          colors[gridIndex] = color;
        }
      }
      break;
    }
    case 'rainbow': {
      // ARCOÍRIS ROTATIVO que usa todo el grid 8x8
      const t = Date.now() / 100;
      for (let y = 0; y < GRID_SIZE; y++) {
        for (let x = 0; x < GRID_SIZE; x++) {
          const gridIndex = y * GRID_SIZE + x;
          const hue = (x + y + t * 0.01) % 8;
          const colors_palette = [15, 30, 45, 60, 75, 90, 105, 120];
          const color = colors_palette[Math.floor(hue)];
          colors[gridIndex] = color;
        }
      }
      break;
    }
    case 'snake': {
      // EFECTO SERPIENTE MÓVIL que usa todo el grid 8x8
      const t = Date.now() / 150;
      const snakeLength = 12;

      // Inicializar todo el grid a 0
      colors.fill(0);

      for (let i = 0; i < snakeLength; i++) {
        const phase = (t + i * 0.5) % (Math.PI * 4);

        // Calcular posición en el grid 8x8
        let x = Math.floor((Math.sin(phase) + 1) * (GRID_SIZE - 1) / 2);
        let y = Math.floor((Math.cos(phase * 0.7) + 1) * (GRID_SIZE - 1) / 2);

        // Asegurar que está dentro del grid 8x8
        x = Math.max(0, Math.min(GRID_SIZE - 1, x));
        y = Math.max(0, Math.min(GRID_SIZE - 1, y));

        const gridIndex = y * GRID_SIZE + x;
        const intensity = Math.floor(((snakeLength - i) / snakeLength) * 100) + 20;

        // Solo actualizar si el nuevo color es más brillante
        if (colors[gridIndex] < intensity) {
          colors[gridIndex] = intensity;
        }
      }
      break;
    }
    default: {
      console.warn(`Preset desconocido: ${preset}, devolviendo grid vacío`);
      break;
    }
  }

  // 🔥 VERIFICACIÓN FINAL: Asegurar que siempre devolvemos exactamente 64 elementos
  if (colors.length !== GRID_LEN) {
    console.error(`❌ ERROR CRÍTICO: buildLaunchpadFrame devuelve ${colors.length} elementos, debe ser 64!`);
    return new Array(GRID_LEN).fill(0); // Fallback seguro
  }

  // Debug: mostrar estadísticas del frame generado
  const activeCount = colors.filter(c => c > 0).length;
  const maxValue = Math.max(...colors);
  console.log(`🎹 Launchpad frame [${preset}]: ${activeCount}/64 pads activos, max=${maxValue}`);

  return colors;
}
