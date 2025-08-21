import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'ANALYSIS',
  description: '3D audio spectrum analyzer with grouped butterflies and rotating camera.',
  author: 'AudioVisualizer',
  version: '1.0.0',
  category: 'analysis',
  tags: ['spectrum', 'analysis', 'butterfly', 'grid'],
  thumbnail: 'analysis_thumb.png',
  note: 48,
  defaultConfig: {
    radius: 8,
    butterflyCount: 40,
    colors: {
      band1: '#607080',
      band2: '#708090',
      band3: '#8fa1b3',
      band4: '#a0b3c4',
      band5: '#c7d8e8',
      band6: '#e0e8f0'
    }
  },
  controls: [
    { name: 'radius', type: 'slider', label: 'Camera Radius', min: 5, max: 15, step: 0.5, default: 8 },
    { name: 'butterflyCount', type: 'slider', label: 'Max Butterflies', min: 5, max: 100, step: 1, default: 40 },
    { name: 'colors.band1', type: 'color', label: 'Band 1 Color', default: '#607080' },
    { name: 'colors.band2', type: 'color', label: 'Band 2 Color', default: '#708090' },
    { name: 'colors.band3', type: 'color', label: 'Band 3 Color', default: '#8fa1b3' },
    { name: 'colors.band4', type: 'color', label: 'Band 4 Color', default: '#a0b3c4' },
    { name: 'colors.band5', type: 'color', label: 'Band 5 Color', default: '#c7d8e8' },
    { name: 'colors.band6', type: 'color', label: 'Band 6 Color', default: '#e0e8f0' }
  ],
  audioMapping: {
    band1: { description: 'Very low frequencies', frequency: '40-200 Hz', effect: 'Butterfly density band 1' },
    band2: { description: 'Low frequencies', frequency: '200-400 Hz', effect: 'Butterfly density band 2' },
    band3: { description: 'Low mid frequencies', frequency: '400-600 Hz', effect: 'Butterfly density band 3' },
    band4: { description: 'Mid frequencies', frequency: '600-1000 Hz', effect: 'Butterfly density band 4' },
    band5: { description: 'High mid frequencies', frequency: '1000-10000 Hz', effect: 'Butterfly density band 5' },
    band6: { description: 'High frequencies', frequency: '10000-22000 Hz', effect: 'Butterfly density band 6' }
  },
  performance: { complexity: 'low', recommendedFPS: 60, gpuIntensive: false }
};

interface Butterfly {
  group: THREE.Group;
  speed: number;
  radius: number;
  offset: number;
}

interface ButterflyRange {
  butterflies: Butterfly[];
  color: string;
  centerX: number;
}

type BandName = 'band1' | 'band2' | 'band3' | 'band4' | 'band5' | 'band6';

class AnalysisSpectrum extends BasePreset {
  private group!: THREE.Group;
  private butterflyGroups!: Record<BandName, ButterflyRange>;
  private gridFloor?: THREE.GridHelper;
  private gridBack?: THREE.GridHelper;
  private ambient?: THREE.AmbientLight;
  private pointLight?: THREE.PointLight;
  private currentConfig: any;
  private initialCameraPosition = this.camera.position.clone();
  private initialCameraQuaternion = this.camera.quaternion.clone();

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, cfg: PresetConfig) {
    super(scene, camera, renderer, cfg);
    this.currentConfig = cfg.defaultConfig;
  }

  init(): void {
    this.group = new THREE.Group();
    this.scene.add(this.group);

    // Grid helpers
    this.gridFloor = new THREE.GridHelper(10, 10, 0x777777, 0x333333);
    this.scene.add(this.gridFloor);

    this.gridBack = new THREE.GridHelper(10, 10, 0x777777, 0x333333);
    this.gridBack.rotation.x = Math.PI / 2;
    this.gridBack.position.z = -5;
    this.scene.add(this.gridBack);

    // Lights
    this.ambient = new THREE.AmbientLight(0xffffff, 0.3);
    this.pointLight = new THREE.PointLight(0xffffff, 0.6);
    this.pointLight.position.set(5, 5, 5);
    this.scene.add(this.ambient);
    this.scene.add(this.pointLight);

    // Butterfly groups for six bands
    const colors = this.currentConfig.colors;
    this.butterflyGroups = {
      band1: { butterflies: [], color: colors.band1, centerX: -2.5 },
      band2: { butterflies: [], color: colors.band2, centerX: -1.5 },
      band3: { butterflies: [], color: colors.band3, centerX: -0.5 },
      band4: { butterflies: [], color: colors.band4, centerX: 0.5 },
      band5: { butterflies: [], color: colors.band5, centerX: 1.5 },
      band6: { butterflies: [], color: colors.band6, centerX: 2.5 }
    };

    Object.values(this.butterflyGroups).forEach(range => {
      for (let i = 0; i < 2; i++) {
        range.butterflies.push(this.createButterfly(range.color, range.centerX));
      }
    });
  }

  private createButterfly(color: string, centerX: number): Butterfly {
    const group = new THREE.Group();
    const geom = new THREE.PlaneGeometry(0.1, 0.075);
    const mat = new THREE.MeshBasicMaterial({ color, side: THREE.DoubleSide });
    const left = new THREE.Mesh(geom, mat);
    const right = new THREE.Mesh(geom, mat);
    left.position.x = -0.05;
    right.position.x = 0.05;
    group.add(left);
    group.add(right);
    const radius = 0.3 + Math.random() * 0.7;
    const speed = 0.5 + Math.random();
    const offset = Math.random() * Math.PI * 2;
    group.position.set(centerX + Math.cos(offset) * radius, 1 + Math.random() * 2, Math.sin(offset) * radius);
    this.group.add(group);
    return { group, speed, radius, offset };
  }

  private adjustButterflies(range: ButterflyRange, target: number): void {
    while (range.butterflies.length < target) {
      range.butterflies.push(this.createButterfly(range.color, range.centerX));
    }
    while (range.butterflies.length > target) {
      const b = range.butterflies.pop()!;
      this.group.remove(b.group);
    }
  }

  update(): void {
    const time = this.clock.getElapsedTime();
    const fft = this.audioData.fft;
    const sampleRate = 44100;
    const nyquist = sampleRate / 2;
    const ranges: [number, number][] = [
      [40, 200],
      [200, 400],
      [400, 600],
      [600, 1000],
      [1000, 10000],
      [10000, 22000]
    ];
    const amps = ranges.map(([low, high]) => {
      const start = Math.floor((low / nyquist) * fft.length);
      const end = Math.floor((high / nyquist) * fft.length);
      let sum = 0;
      for (let i = start; i < end && i < fft.length; i++) sum += fft[i];
      return sum / Math.max(end - start, 1);
    });

    const keys: BandName[] = ['band1', 'band2', 'band3', 'band4', 'band5', 'band6'];

    keys.forEach((key, i) => {
      const range = this.butterflyGroups[key];
      const amp = Math.max(amps[i], 0);
      const target = Math.max(2, Math.floor(amp * this.currentConfig.butterflyCount));
      this.adjustButterflies(range, target);
      range.butterflies.forEach(b => {
        const angle = time * b.speed + b.offset;
        b.group.position.x = range.centerX + Math.cos(angle) * b.radius;
        b.group.position.z = Math.sin(angle) * b.radius;
        const flap = Math.sin(time * 4 + b.offset) * 0.5;
        if (b.group.children[0] && b.group.children[1]) {
          b.group.children[0].rotation.z = flap;
          b.group.children[1].rotation.z = -flap;
        }
      });
    });

    const radius = this.currentConfig.radius;
    this.camera.position.x = Math.cos(time * 0.2) * radius;
    this.camera.position.z = Math.sin(time * 0.2) * radius;
    this.camera.position.y = radius * 0.3 + 2;
    this.camera.lookAt(0, 1, 0);
  }

  updateConfig(newConfig: any): void {
    this.currentConfig = { ...this.currentConfig, ...newConfig };
  }

  dispose(): void {
    this.scene.remove(this.group);
    this.scene.remove(this.gridFloor!);
    this.scene.remove(this.gridBack!);
    this.scene.remove(this.ambient!);
    this.scene.remove(this.pointLight!);

    this.camera.position.copy(this.initialCameraPosition);
    this.camera.quaternion.copy(this.initialCameraQuaternion);

    this.group.clear();
    this.butterflyGroups = {
      band1: { butterflies: [], color: '', centerX: -2.5 },
      band2: { butterflies: [], color: '', centerX: -1.5 },
      band3: { butterflies: [], color: '', centerX: -0.5 },
      band4: { butterflies: [], color: '', centerX: 0.5 },
      band5: { butterflies: [], color: '', centerX: 1.5 },
      band6: { butterflies: [], color: '', centerX: 2.5 }
    };
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  cfg: PresetConfig
): BasePreset {
  return new AnalysisSpectrum(scene, camera, renderer, cfg);
}
