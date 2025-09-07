import { AudioData } from '../../core/PresetLoader';

export function applyVFX(canvas: HTMLCanvasElement, audio: AudioData): void {
  if (audio.mid > 0.85) {
    canvas.classList.add('effect-blur');
    setTimeout(() => canvas.classList.remove('effect-blur'), 400);
  }
}
