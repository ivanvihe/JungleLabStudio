import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'Soft Flare',
  description: 'Gentle fullscreen flare that fades quickly',
  author: 'AudioVisualizer',
  version: '1.0.0',
  category: 'one-shot',
  tags: ['flare', 'flash', 'one-shot'],
  thumbnail: 'soft_flare_thumb.png',
  note: 63,
  defaultConfig: {
    opacity: 1.0,
    duration: 1.0,
    color: '#e0f7ff'
  },
  controls: [
    { name: 'color', type: 'color', label: 'Color', default: '#e0f7ff' },
    { name: 'duration', type: 'slider', label: 'Duration', min: 0.5, max: 2, step: 0.1, default: 1.0 }
  ],
  audioMapping: {
    low: { description: 'Controls brightness', frequency: '20-250 Hz', effect: 'Intensity' },
    mid: { description: 'Modulates radius', frequency: '250-4000 Hz', effect: 'Radius' },
    high: { description: 'Adds sparkle', frequency: '4000+ Hz', effect: 'Sparkle' }
  },
  performance: { complexity: 'low', recommendedFPS: 60, gpuIntensive: false }
};

class SoftFlarePreset extends BasePreset {
  private mesh!: THREE.Mesh<THREE.PlaneGeometry, THREE.ShaderMaterial>;
  private start = 0;
  private currentConfig: any;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, cfg: PresetConfig, videoElement: HTMLVideoElement) {
    super(scene, camera, renderer, cfg, videoElement);
    this.currentConfig = { ...cfg.defaultConfig };
  }

  public init(): void {
    this.start = performance.now();
    const geometry = new THREE.PlaneGeometry(2, 2);
    const material = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      uniforms: {
        uColor: { value: new THREE.Color(this.currentConfig.color) },
        uDuration: { value: this.currentConfig.duration },
        uElapsed: { value: 0 },
        uOpacity: { value: this.opacity }
      },
      vertexShader: `
        varying vec2 vUv;
        void main() {
          vUv = uv;
          gl_Position = vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        varying vec2 vUv;
        uniform vec3 uColor;
        uniform float uDuration;
        uniform float uElapsed;
        uniform float uOpacity;
        void main() {
          float progress = clamp(uElapsed / max(uDuration, 0.001), 0.0, 1.0);
          float alpha = (1.0 - progress) * uOpacity;
          float dist = length(vUv - 0.5);
          float falloff = smoothstep(0.6, 0.0, dist);
          gl_FragColor = vec4(uColor * falloff, alpha * falloff);
        }
      `
    });

    this.mesh = new THREE.Mesh(geometry, material);
    this.scene.add(this.mesh);
  }

  public update(): void {
    if (!this.mesh) return;
    const material = this.mesh.material;
    const elapsed = (performance.now() - this.start) / 1000;
    material.uniforms.uElapsed.value = elapsed;
    material.uniforms.uDuration.value = this.currentConfig.duration;
    material.uniforms.uColor.value.set(this.currentConfig.color);
    material.uniforms.uOpacity.value = this.opacity * (1 + this.audioData.low * 0.5);
  }

  public dispose(): void {
    if (!this.mesh) return;
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
  videoElement: HTMLVideoElement,
  shaderCode?: string
): BasePreset {
  return new SoftFlarePreset(scene, camera, renderer, cfg, videoElement);
}
