import { AudioData } from '../../core/PresetLoader';

export function applyVFX(canvas: HTMLCanvasElement, audio: AudioData): void {
  if (audio.high > 0.8) {
    canvas.classList.add('effect-glitch2');
    setTimeout(() => canvas.classList.remove('effect-glitch2'), 500);
  }
}
