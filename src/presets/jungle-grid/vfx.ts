export function triggerClipFlash(canvas: HTMLCanvasElement): void {
  canvas.classList.add('effect-flash');
  setTimeout(() => canvas.classList.remove('effect-flash'), 300);
}
