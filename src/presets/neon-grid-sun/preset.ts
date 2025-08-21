import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'Neon Grid Sun',
  description: 'Retro 80s grid with glowing sun',
  author: 'AudioVisualizer',
  version: '1.0.0',
  category: 'background',
  tags: ['retro','80s','grid','sun'],
  thumbnail: 'neon_grid_sun_thumb.png',
  note: 71,
  defaultConfig: {
    gridColor: '#00ffff',
    sunColor: '#ff0080'
  },
  controls: [
    { name: 'gridColor', type: 'color', label: 'Grid Color', default: '#00ffff' },
    { name: 'sunColor', type: 'color', label: 'Sun Color', default: '#ff0080' }
  ],
  audioMapping: {},
  performance: { complexity: 'low', recommendedFPS: 60, gpuIntensive: false }
};

class NeonGridSunPreset extends BasePreset {
  private grid!: THREE.GridHelper;
  private sun!: THREE.Mesh;
  private currentConfig: any;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, cfg: PresetConfig) {
    super(scene, camera, renderer, cfg);
    this.currentConfig = { ...cfg.defaultConfig };
  }

  init(): void {
    this.renderer.setClearColor(0x000000, 1);
    this.grid = new THREE.GridHelper(40, 40, this.currentConfig.gridColor, this.currentConfig.gridColor);
    (this.grid.material as THREE.Material).transparent = true;
    (this.grid.material as THREE.Material).opacity = 0.2;
    this.grid.position.y = -1;
    this.scene.add(this.grid);

    const sunGeo = new THREE.CircleGeometry(3, 64);
    const sunMat = new THREE.MeshBasicMaterial({ color: this.currentConfig.sunColor });
    this.sun = new THREE.Mesh(sunGeo, sunMat);
    this.sun.position.set(0, 5, -10);
    this.scene.add(this.sun);
  }

  update(): void {
    const delta = this.clock.getDelta();
    this.sun.position.y = 5 + Math.sin(this.clock.getElapsedTime() * 0.2);
    (this.sun.material as THREE.MeshBasicMaterial).color.offsetHSL(delta * 0.02, 0, 0);
  }

  updateConfig(newConfig: any): void {
    this.currentConfig = { ...this.currentConfig, ...newConfig };
    if (newConfig.gridColor) {
      (this.grid.material as THREE.LineBasicMaterial).color.set(newConfig.gridColor);
    }
    if (newConfig.sunColor) {
      (this.sun.material as THREE.MeshBasicMaterial).color.set(newConfig.sunColor);
    }
  }

  dispose(): void {
    this.scene.remove(this.grid);
    this.scene.remove(this.sun);
    this.grid.geometry.dispose();
    (this.grid.material as THREE.Material).dispose();
    this.sun.geometry.dispose();
    (this.sun.material as THREE.Material).dispose();
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  cfg: PresetConfig,
  shaderCode?: string
): BasePreset {
  return new NeonGridSunPreset(scene, camera, renderer, cfg);
}
