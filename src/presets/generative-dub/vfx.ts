import { AudioData } from '../../core/PresetLoader';

export function applyVFX(canvas: HTMLCanvasElement, audio: AudioData): void {
  if (audio.high > 0.9) {
    canvas.classList.add('effect-glitch1');
    setTimeout(() => canvas.classList.remove('effect-glitch1'), 500);
  }
}
