import { AudioData } from '../../core/PresetLoader';

export function applyVFX(canvas: HTMLCanvasElement, audio: AudioData): void {
  const intensity = (audio.low + audio.mid + audio.high) / 3;
  if (canvas.classList.contains('vfx-flash') && intensity > 0.92) {
    canvas.classList.add('effect-flash');
    setTimeout(() => canvas.classList.remove('effect-flash'), 300);
  }
  if (canvas.classList.contains('vfx-glitch') && audio.high > 0.85) {
    const glitches = ['effect-glitch1', 'effect-glitch2', 'effect-glitch3'];
    const cls = glitches[Math.floor(Math.random() * glitches.length)];
    canvas.classList.add(cls);
    setTimeout(() => canvas.classList.remove(cls), 500);
  }
}
