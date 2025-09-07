import { AudioData } from '../../core/PresetLoader';

export function applyVFX(canvas: HTMLCanvasElement, audio: AudioData): void {
  const intensity = (audio.low + audio.mid + audio.high) / 3;
  if (intensity > 0.95) {
    canvas.classList.add('effect-flash');
    setTimeout(() => canvas.classList.remove('effect-flash'), 300);
  }
}
