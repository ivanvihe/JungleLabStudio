import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'Boom Wave',
  description: 'Expanding ring pulse',
  author: 'AudioVisualizer',
  version: '1.0.0',
  category: 'one-shot',
  tags: ['ring', 'pulse', 'one-shot'],
  thumbnail: 'boom_wave_thumb.png',
  note: 58,
  defaultConfig: {
    opacity: 1.0,
    duration: 1.5,
    color: '#00aaff',
    maxRadius: 5
  },
  controls: [
    { name: 'color', type: 'color', label: 'Color', default: '#00aaff' },
    { name: 'maxRadius', type: 'slider', label: 'Max Radius', min: 1, max: 10, step: 0.5, default: 5 },
    { name: 'duration', type: 'slider', label: 'Duration', min: 0.5, max: 3, step: 0.1, default: 1.5 }
  ],
  audioMapping: {
    low: { description: 'Slight expansion', frequency: '20-250 Hz', effect: 'Radius' },
    mid: { description: 'Color modulation', frequency: '250-4000 Hz', effect: 'Hue' },
    high: { description: 'Adds subtle brightness', frequency: '4000+ Hz', effect: 'Brightness' }
  },
  performance: { complexity: 'low', recommendedFPS: 60, gpuIntensive: false }
};

class BoomWavePreset extends BasePreset {
  private mesh!: THREE.Mesh<THREE.PlaneGeometry, THREE.ShaderMaterial>;
  private start = 0;
  private currentConfig: any;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, cfg: PresetConfig) {
    super(scene, camera, renderer, cfg);
  }

  public init(): void {
    this.renderer.setClearColor(0x000000, 0);
    this.currentConfig = JSON.parse(JSON.stringify(this.config.defaultConfig));
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
          float ring = smoothstep(uProgress, uProgress + 0.02, dist);
          float alpha = (1.0 - uProgress) * (1.0 - ring);
          gl_FragColor = vec4(uColor, alpha);
        }
      `
    });
    this.mesh = new THREE.Mesh(geometry, material);
    this.scene.add(this.mesh);
    this.start = this.clock.getElapsedTime();
  }

  public update(): void {
    const t = this.clock.getElapsedTime();
    const progress = (t - this.start) / this.currentConfig.duration;
    const mat = this.mesh.material as THREE.ShaderMaterial;
    mat.uniforms.uProgress.value = progress;
    this.mesh.scale.setScalar(progress * this.currentConfig.maxRadius);
    mat.uniforms.uColor.value.set(this.currentConfig.color);
    if (progress > 1) {
      this.dispose();
    }
  }

  public updateConfig(newConfig: any): void {
    this.currentConfig = { ...this.currentConfig, ...newConfig };
    const mat = this.mesh?.material as THREE.ShaderMaterial;
    if (newConfig.color && mat) {
      mat.uniforms.uColor.value = new THREE.Color(newConfig.color);
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
  return new BoomWavePreset(scene, camera, renderer, cfg);
}
