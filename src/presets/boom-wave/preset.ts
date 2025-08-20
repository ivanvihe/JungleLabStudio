import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'Boom Wave',
  description: 'Circular shock waves triggered by sub-bass booms',
  author: 'AudioVisualizer',
  version: '1.0.0',
  category: 'one-shot',
  tags: ['wave', 'bass', 'one-shot'],
  thumbnail: 'boom_wave_thumb.png',
  note: 58,
  defaultConfig: {
    opacity: 1.0,
    fadeMs: 200,
    color: '#00aaff',
    maxRadius: 5,
    waveDuration: 1.5,
    threshold: 0.8,
    spawnSpread: 2
  },
  controls: [
    { name: 'color', type: 'color', label: 'Color', default: '#00aaff' },
    { name: 'maxRadius', type: 'slider', label: 'Max Radius', min: 1, max: 10, step: 0.5, default: 5 },
    { name: 'waveDuration', type: 'slider', label: 'Duration', min: 0.5, max: 3, step: 0.1, default: 1.5 },
    { name: 'threshold', type: 'slider', label: 'Trigger Threshold', min: 0, max: 1, step: 0.01, default: 0.8 },
    { name: 'spawnSpread', type: 'slider', label: 'Spawn Spread', min: 0, max: 5, step: 0.1, default: 2 }
  ],
  audioMapping: {
    low: { description: 'Triggers waves when bass peaks', frequency: '20-250 Hz', effect: 'Wave spawn' },
    mid: { description: 'Modulates color intensity', frequency: '250-4000 Hz', effect: 'Color modulation' },
    high: { description: 'Adds subtle brightness', frequency: '4000+ Hz', effect: 'Brightness' }
  },
  performance: { complexity: 'low', recommendedFPS: 60, gpuIntensive: false }
};

interface Wave {
  mesh: THREE.Mesh<THREE.PlaneGeometry, THREE.ShaderMaterial>;
  start: number;
}

class BoomWavePreset extends BasePreset {
  private waves: Wave[] = [];
  private currentConfig: any;
  private lastSpawn = 0;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, cfg: PresetConfig) {
    super(scene, camera, renderer, cfg);
  }

  public init(): void {
    this.renderer.setClearColor(0x000000, 0);
    this.currentConfig = JSON.parse(JSON.stringify(this.config.defaultConfig));
  }

  private spawnWave(): void {
    const geometry = new THREE.PlaneGeometry(1, 1);
    const material = new THREE.ShaderMaterial({
      transparent: true,
      uniforms: {
        uColor: { value: new THREE.Color(this.currentConfig.color) },
        uProgress: { value: 0 }
      },
      vertexShader: `
        varying vec2 vUv;
        void main(){
          vUv = uv;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0);
        }
      `,
      fragmentShader: `
        varying vec2 vUv;
        uniform vec3 uColor;
        uniform float uProgress;
        void main(){
          float dist = length(vUv - vec2(0.5));
          float alpha = smoothstep(uProgress, uProgress + 0.05, dist) * (1.0 - uProgress);
          gl_FragColor = vec4(uColor, alpha);
        }
      `
    });
    const mesh = new THREE.Mesh(geometry, material);
    const spread = this.currentConfig.spawnSpread || 0;
    mesh.position.set((Math.random()-0.5)*spread, (Math.random()-0.5)*spread, 0);
    this.scene.add(mesh);
    this.waves.push({ mesh, start: this.clock.getElapsedTime() });
  }

  public update(): void {
    const t = this.clock.getElapsedTime();
    const delta = this.clock.getDelta();
    if (this.audioData.low > this.currentConfig.threshold && t - this.lastSpawn > 0.1) {
      this.spawnWave();
      this.lastSpawn = t;
    }

    const duration = this.currentConfig.waveDuration;
    const maxRadius = this.currentConfig.maxRadius;

    this.waves = this.waves.filter(w => {
      const progress = (t - w.start) / duration;
      if (progress > 1) {
        this.scene.remove(w.mesh);
        w.mesh.geometry.dispose();
        w.mesh.material.dispose();
        return false;
      }
      w.mesh.scale.setScalar(progress * maxRadius);
      const mat = w.mesh.material as THREE.ShaderMaterial;
      mat.uniforms.uProgress.value = progress;
      mat.uniforms.uColor.value.set(this.currentConfig.color);
      return true;
    });
  }

  public updateConfig(newConfig: any): void {
    this.currentConfig = this.deepMerge(this.currentConfig, newConfig);
  }

  private deepMerge(target: any, source: any): any {
    const result = { ...target };
    for (const key in source) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        result[key] = this.deepMerge(result[key] || {}, source[key]);
      } else {
        result[key] = source[key];
      }
    }
    return result;
  }

  public dispose(): void {
    this.waves.forEach(w => {
      this.scene.remove(w.mesh);
      w.mesh.geometry.dispose();
      w.mesh.material.dispose();
    });
    this.waves = [];
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  cfg: PresetConfig,
  shaderCode?: string
): BasePreset {
  return new BoomWavePreset(scene, camera, renderer, cfg);
}
