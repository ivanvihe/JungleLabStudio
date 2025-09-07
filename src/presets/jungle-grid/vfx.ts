import { AudioData } from '../../core/PresetLoader';

const glitches = ['effect-glitch1', 'effect-glitch2', 'effect-glitch3'];

export function triggerClipFlash(canvas: HTMLCanvasElement): void {
  if (!canvas.classList.contains('vfx-flash')) return;
  canvas.classList.add('effect-flash');
  setTimeout(() => canvas.classList.remove('effect-flash'), 300);
}

export function applyVFX(canvas: HTMLCanvasElement, audio: AudioData): void {
  if (canvas.classList.contains('vfx-glitch') && audio.high > 0.8) {
    const cls = glitches[Math.floor(Math.random() * glitches.length)];
    canvas.classList.add(cls);
    setTimeout(() => canvas.classList.remove(cls), 500);
  }
}
