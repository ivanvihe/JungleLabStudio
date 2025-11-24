import { AudioData } from '../../core/PresetLoader';
import { getIntensity, triggerEffect } from '../../utils/vfx';

export function applyVFX(preset: any, audio: AudioData): void {
  const intensity = getIntensity(audio);

  // Trigger flash effect on high intensity
  if (intensity > 0.95) {
    // Note: This would need to be connected to canvas/renderer
    // triggerEffect(canvas, 'effect-flash', 300);
  }

  // Additional VFX logic can be added here
  // For now, keeping it minimal as VFX is handled by the main system
}
