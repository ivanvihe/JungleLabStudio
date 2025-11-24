import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'ARP Waves',
  description: 'Vertical bars reacting to arpeggios',
  author: 'AudioVisualizer',
  version: '1.0.0',
  category: 'audio-reactive',
  tags: ['arp','bars','audio'],
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

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, cfg: PresetConfig, videoElement: HTMLVideoElement) {
    super(scene, camera, renderer, cfg, videoElement);
    this.currentConfig = { ...cfg.defaultConfig };
  }

  init(): void {
    this.createBars();
  }
