import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'ARP Waves',
  description: 'Vertical bars reacting to arpeggios',
  author: 'AudioVisualizer',
  version: '1.0.0',
  category: 'audio-reactive',
  tags: ['arp', 'bars', 'audio'],
  thumbnail: 'arp_waves_thumb.png',
  note: 72,
  defaultConfig: {
    barCount: 16,
    color: '#00ffcc'
  },
  controls: [
    { name: 'barCount', type: 'slider', label: 'Bars', min: 8, max: 32, step: 1, default: 16 },
    { name: 'color', type: 'color', label: 'Color', default: '#00ffcc' }
  ],
  audioMapping: {
    fft: { description: 'FFT energy', frequency: '20-22050 Hz', effect: 'Bar height' }
  },
  performance: { complexity: 'low', recommendedFPS: 60, gpuIntensive: false }
};

class ArpWavesPreset extends BasePreset {
  private bars: THREE.Mesh[] = [];
  private currentConfig: any;
  private geometry!: THREE.BoxGeometry;
  private material!: THREE.MeshBasicMaterial;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, cfg: PresetConfig, videoElement: HTMLVideoElement) {
    super(scene, camera, renderer, cfg, videoElement);
    this.currentConfig = { ...cfg.defaultConfig };
  }

  init(): void {
    this.createBars();
  }

  private createBars(): void {
    this.dispose();

    const { barCount, color } = this.currentConfig;
    this.geometry = new THREE.BoxGeometry(0.4, 1, 0.4);
    this.material = new THREE.MeshBasicMaterial({ color });

    const spacing = 0.6;
    const totalWidth = (barCount - 1) * spacing;
    this.bars = [];

    for (let i = 0; i < barCount; i++) {
      const mesh = new THREE.Mesh(this.geometry, this.material);
      mesh.position.x = -totalWidth / 2 + i * spacing;
      mesh.position.z = -4;
      this.scene.add(mesh);
      this.bars.push(mesh);
    }
  }

  update(): void {
    const fft = this.audioData.fft || [];
    const count = this.bars.length;
    for (let i = 0; i < count; i++) {
      const energy = fft[i % fft.length] || 0;
      const scaleY = 0.5 + energy * 5;
      this.bars[i].scale.y = scaleY;
    }
  }

  dispose(): void {
    this.bars.forEach(bar => this.scene.remove(bar));
    this.bars = [];
    if (this.geometry) this.geometry.dispose();
    if (this.material) this.material.dispose();
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  cfg: PresetConfig,
  videoElement: HTMLVideoElement
): BasePreset {
  return new ArpWavesPreset(scene, camera, renderer, cfg, videoElement);
}
