import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'Instanced Demo',
  description: 'Simple instanced cubes showcasing InstancedMesh',
  author: 'AI',
  version: '1.0.0',
  category: 'demo',
  tags: ['instanced', 'performance'],
  thumbnail: 'instanced_demo_thumb.png',
  note: 0,
  defaultConfig: {},
  controls: [],
  audioMapping: {},
  performance: { complexity: 'low', recommendedFPS: 60, gpuIntensive: false }
};

export class InstancedDemo extends BasePreset {
  private mesh!: THREE.InstancedMesh;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, cfg: PresetConfig, videoElement: HTMLVideoElement) {
    super(scene, camera, renderer, cfg, videoElement);
  }

  init(): void {
//...
  dispose(): void {
    this.mesh.geometry.dispose();
    (this.mesh.material as THREE.Material).dispose();
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  cfg: PresetConfig,
  videoElement: HTMLVideoElement
): BasePreset {
  return new InstancedDemo(scene, camera, renderer, cfg, videoElement);
}
