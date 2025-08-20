import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'Heart Beat',
  description: 'Pulse of a grayscale electronic heart',
  author: 'AudioVisualizer',
  version: '1.0.0',
  category: 'one-shot',
  tags: ['heart', 'pulse', 'one-shot'],
  thumbnail: 'heart_beat_thumb.png',
  note: 62,
  defaultConfig: {
    opacity: 1.0,
    duration: 1.5,
    color: '#ffffff',
    scale: 1.0
  },
  controls: [
    { name: 'color', type: 'color', label: 'Color', default: '#ffffff' },
    { name: 'duration', type: 'slider', label: 'Duration', min: 0.5, max: 3, step: 0.1, default: 1.5 },
    { name: 'scale', type: 'slider', label: 'Scale', min: 0.5, max: 2, step: 0.1, default: 1.0 }
  ],
  audioMapping: {
    low: { description: 'Triggers heart beat', frequency: '20-250 Hz', effect: 'Pulse amplitude' },
    mid: { description: 'Modulates glow', frequency: '250-4000 Hz', effect: 'Glow intensity' },
    high: { description: 'Adds shimmer', frequency: '4000+ Hz', effect: 'Subtle flicker' }
  },
  performance: { complexity: 'low', recommendedFPS: 60, gpuIntensive: false }
};

class HeartBeatPreset extends BasePreset {
  private mesh!: THREE.Mesh<THREE.ShapeGeometry, THREE.MeshBasicMaterial>;
  private startTime = 0;
  private currentConfig: any;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, cfg: PresetConfig) {
    super(scene, camera, renderer, cfg);
  }

  public init(): void {
    this.renderer.setClearColor(0x000000, 0);
    this.currentConfig = JSON.parse(JSON.stringify(this.config.defaultConfig));

    const heartShape = new THREE.Shape();
    heartShape.moveTo(0, 0);
    heartShape.bezierCurveTo(0, 0, -0.5, -0.3, -1, 0);
    heartShape.bezierCurveTo(-2, 1.5, -1.5, 3, 0, 3.5);
    heartShape.bezierCurveTo(1.5, 3, 2, 1.5, 1, 0);
    heartShape.bezierCurveTo(0.5, -0.3, 0, 0, 0, 0);

    const geometry = new THREE.ShapeGeometry(heartShape);
    const material = new THREE.MeshBasicMaterial({
      color: new THREE.Color(this.currentConfig.color),
      transparent: true
    });
    this.mesh = new THREE.Mesh(geometry, material);
    this.mesh.rotation.z = Math.PI; // orient heart upright
    this.mesh.scale.setScalar(this.currentConfig.scale);
    this.scene.add(this.mesh);

    this.startTime = this.clock.getElapsedTime();
  }

  public update(): void {
    const t = this.clock.getElapsedTime() - this.startTime;
    const progress = t / this.currentConfig.duration;
    if (progress > 1) {
      this.dispose();
      return;
    }

    const beat = Math.abs(Math.sin(progress * Math.PI * 2));
    const scale = this.currentConfig.scale * (0.8 + beat * 0.4 + this.audioData.low * 0.1);
    this.mesh.scale.setScalar(scale);

    const material = this.mesh.material as THREE.MeshBasicMaterial;
    const grey = 1 - this.audioData.mid * 0.3;
    material.color.setScalar(grey);
    material.opacity = 1 - progress;
  }

  public updateConfig(newConfig: any): void {
    this.currentConfig = { ...this.currentConfig, ...newConfig };
    if (newConfig.color) {
      (this.mesh.material as THREE.MeshBasicMaterial).color.set(newConfig.color);
    }
    if (newConfig.scale) {
      this.mesh.scale.setScalar(newConfig.scale);
    }
  }

  public dispose(): void {
    this.scene.remove(this.mesh);
    this.mesh.geometry.dispose();
    this.mesh.material.dispose();
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  cfg: PresetConfig,
  shaderCode?: string
): BasePreset {
  return new HeartBeatPreset(scene, camera, renderer, cfg);
}
