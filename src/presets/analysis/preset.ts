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
    butterflyCount: 20,
    colors: {
      low: '#607080',
      mid: '#8fa1b3',
      high: '#c7d8e8'
    }
  },
  controls: [
    { name: 'radius', type: 'slider', label: 'Camera Radius', min: 5, max: 15, step: 0.5, default: 8 },
    { name: 'butterflyCount', type: 'slider', label: 'Max Butterflies', min: 5, max: 50, step: 1, default: 20 },
    { name: 'colors.low', type: 'color', label: 'Low Color', default: '#607080' },
    { name: 'colors.mid', type: 'color', label: 'Mid Color', default: '#8fa1b3' },
    { name: 'colors.high', type: 'color', label: 'High Color', default: '#c7d8e8' }
  ],
  audioMapping: {
    low: { description: 'Low frequencies', frequency: '20-250 Hz', effect: 'Low band butterfly density' },
    mid: { description: 'Mid frequencies', frequency: '250-4000 Hz', effect: 'Mid band butterfly density' },
    high: { description: 'High frequencies', frequency: '4000+ Hz', effect: 'High band butterfly density' }
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

class AnalysisSpectrum extends BasePreset {
  private group!: THREE.Group;
  private butterflyGroups!: Record<'low' | 'mid' | 'high', ButterflyRange>;
  private grid?: THREE.GridHelper;
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

    // Grid helper
    this.grid = new THREE.GridHelper(10, 10, 0x444444, 0x222222);
    this.scene.add(this.grid);

    // Lights
    this.ambient = new THREE.AmbientLight(0xffffff, 0.3);
    this.pointLight = new THREE.PointLight(0xffffff, 0.6);
    this.pointLight.position.set(5, 5, 5);
    this.scene.add(this.ambient);
    this.scene.add(this.pointLight);

    // Butterfly groups for low, mid and high bands
    const colors = this.currentConfig.colors;
    this.butterflyGroups = {
      low: { butterflies: [], color: colors.low, centerX: -2 },
      mid: { butterflies: [], color: colors.mid, centerX: 0 },
      high: { butterflies: [], color: colors.high, centerX: 2 }
    };

    Object.values(this.butterflyGroups).forEach(range => {
      for (let i = 0; i < 2; i++) {
        range.butterflies.push(this.createButterfly(range.color, range.centerX));
      }
    });
  }

  private createButterfly(color: string, centerX: number): Butterfly {
    const group = new THREE.Group();
    const geom = new THREE.PlaneGeometry(0.2, 0.15);
    const mat = new THREE.MeshBasicMaterial({ color, side: THREE.DoubleSide });
    const left = new THREE.Mesh(geom, mat);
    const right = new THREE.Mesh(geom, mat);
    left.position.x = -0.1;
    right.position.x = 0.1;
    group.add(left);
    group.add(right);
    const radius = 0.5 + Math.random();
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
    const bands = {
      low: this.audioData.low,
      mid: this.audioData.mid,
      high: this.audioData.high
    };

    (Object.keys(this.butterflyGroups) as Array<'low' | 'mid' | 'high'>).forEach(key => {
      const range = this.butterflyGroups[key];
      const amp = Math.max(bands[key], 0);
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
    this.scene.remove(this.grid!);
    this.scene.remove(this.ambient!);
    this.scene.remove(this.pointLight!);

    this.camera.position.copy(this.initialCameraPosition);
    this.camera.quaternion.copy(this.initialCameraQuaternion);

    this.group.clear();
    this.butterflyGroups = {
      low: { butterflies: [], color: '', centerX: -2 },
      mid: { butterflies: [], color: '', centerX: 0 },
      high: { butterflies: [], color: '', centerX: 2 }
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
