import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'Soft Flare',
  description: 'Gentle fullscreen flare that fades quickly',
  author: 'AudioVisualizer',
  version: '1.0.0',
  category: 'one-shot',
  tags: ['flare', 'flash', 'one-shot'],
  thumbnail: 'soft_flare_thumb.png',
  note: 63,
  defaultConfig: {
    opacity: 1.0,
    duration: 1.0,
    color: '#e0f7ff'
  },
  controls: [
    { name: 'color', type: 'color', label: 'Color', default: '#e0f7ff' },
    { name: 'duration', type: 'slider', label: 'Duration', min: 0.5, max: 2, step: 0.1, default: 1.0 }
  ],
  audioMapping: {
    low: { description: 'Controls brightness', frequency: '20-250 Hz', effect: 'Intensity' },
    mid: { description: 'Modulates radius', frequency: '250-4000 Hz', effect: 'Radius' },
    high: { description: 'Adds sparkle', frequency: '4000+ Hz', effect: 'Sparkle' }
  },
  performance: { complexity: 'low', recommendedFPS: 60, gpuIntensive: false }
};

class SoftFlarePreset extends BasePreset {
  private mesh!: THREE.Mesh<THREE.PlaneGeometry, THREE.ShaderMaterial>;
  private start = 0;
  private currentConfig: any;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, cfg: PresetConfig, videoElement: HTMLVideoElement) {
    super(scene, camera, renderer, cfg, videoElement);
  }
//...
export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  cfg: PresetConfig,
  videoElement: HTMLVideoElement,
  shaderCode?: string
): BasePreset {
  return new SoftFlarePreset(scene, camera, renderer, cfg, videoElement);
}
