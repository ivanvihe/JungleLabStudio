import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'Ambient Tunnel',
  description: 'Slow moving neon tunnel for drone backgrounds',
  author: 'AudioVisualizer',
  version: '1.0.0',
  category: 'background',
  tags: ['ambient','tunnel','background'],
  thumbnail: 'ambient_tunnel_thumb.png',
  note: 70,
  defaultConfig: {
    speed: 0.5,
    color: '#3366ff',
    height: 5
  },
  controls: [
    { name: 'speed', type: 'slider', label: 'Speed', min: 0.1, max: 2.0, step: 0.1, default: 0.5 },
    { name: 'color', type: 'color', label: 'Color', default: '#3366ff' },
    { name: 'height', type: 'slider', label: 'Tunnel Radius', min: 2, max: 10, step: 0.5, default: 5 }
  ],
  audioMapping: {},
  performance: { complexity: 'low', recommendedFPS: 60, gpuIntensive: false }
};

class AmbientTunnelPreset extends BasePreset {
  private rings: THREE.Mesh[] = [];
  private currentConfig: any;

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
  return new AmbientTunnelPreset(scene, camera, renderer, cfg, videoElement);
}
