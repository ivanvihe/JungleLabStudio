import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'Particle Grid Sun',
  description: 'Neon particles with radial lines forming a solar grid',
  author: 'AudioVisualizer',
  version: '1.0.0',
  category: 'abstract',
  tags: ['particles', 'lines', 'sun'],
  thumbnail: 'particle_grid_sun_thumb.png',
  note: 71,
  defaultConfig: {
    particleColor: '#ffcc00',
    lineColor: '#ff00ff',
    rotationSpeed: 0.2
  },
  controls: [
    { name: 'particleColor', type: 'color', label: 'Particle Color', default: '#ffcc00' },
    { name: 'lineColor', type: 'color', label: 'Line Color', default: '#ff00ff' },
    { name: 'rotationSpeed', type: 'slider', label: 'Rotation Speed', min: 0.0, max: 1.0, step: 0.05, default: 0.2 }
  ],
  audioMapping: {
    low: { description: 'Pulses particle size', frequency: '20-250 Hz', effect: 'Particle scaling' },
    high: { description: 'Boosts line brightness', frequency: '4000+ Hz', effect: 'Line opacity' }
  },
  performance: { complexity: 'low', recommendedFPS: 60, gpuIntensive: false }
};

class ParticleGridSunPreset extends BasePreset {
  private particles!: THREE.Points;
  private lines!: THREE.LineSegments;
  private currentConfig: any;
  private particleGeometry!: THREE.BufferGeometry;
  private lineGeometry!: THREE.BufferGeometry;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, cfg: PresetConfig, videoElement: HTMLVideoElement) {
    super(scene, camera, renderer, cfg, videoElement);
    this.currentConfig = { ...cfg.defaultConfig };
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
  return new ParticleGridSunPreset(scene, camera, renderer, cfg, videoElement);
}
