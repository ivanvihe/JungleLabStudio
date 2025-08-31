import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'Generative Dub',
  description: 'Auto-evolving visuals that never repeat',
  author: 'AudioVisualizer',
  version: '1.0.0',
  category: 'generative',
  tags: ['auto', 'infinite', 'dub', 'abstract', 'audio-reactive'],
  thumbnail: 'generative_dub_thumb.png',
  defaultConfig: {
    opacity: 1.0
  },
  controls: [],
  audioMapping: {
    low: {
      description: 'Influences color warmth',
      frequency: '20-250 Hz',
      effect: 'Color shift'
    },
    mid: {
      description: 'Changes movement speed',
      frequency: '250-4000 Hz',
      effect: 'Motion intensity'
    },
    high: {
      description: 'Adds detail',
      frequency: '4000+ Hz',
      effect: 'Texture'
    }
  },
  performance: { complexity: 'medium', recommendedFPS: 60, gpuIntensive: true }
};

class GenerativeDubPreset extends BasePreset {
  private mesh!: THREE.Mesh;
  private currentConfig: any;
  private lastChange = 0;
  private changeInterval = 60;

  public init(): void {
    this.currentConfig = JSON.parse(JSON.stringify(this.config.defaultConfig));
    const geometry = new THREE.PlaneGeometry(10, 10);
    const material = new THREE.ShaderMaterial({
      transparent: true,
      uniforms: {
        uTime: { value: 0 },
        uOpacity: { value: this.opacity },
        uParams: { value: new THREE.Vector3(Math.random() * 3 + 1, Math.random() * 5 + 1, Math.random() * 0.2 + 0.05) },
        uPattern: { value: Math.floor(Math.random() * 3) },
        uAudioLow: { value: 0 },
        uAudioMid: { value: 0 },
        uAudioHigh: { value: 0 }
      },
      vertexShader: `
        varying vec2 vUv;
        void main(){
          vUv = uv;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        varying vec2 vUv;
        uniform float uTime;
        uniform float uOpacity;
        uniform vec3 uParams;
        uniform float uPattern;
        uniform float uAudioLow;
        uniform float uAudioMid;
        uniform float uAudioHigh;

        float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453123); }
        float noise(vec2 p){
          vec2 i = floor(p);
          vec2 f = fract(p);
          float a = hash(i);
          float b = hash(i + vec2(1.0, 0.0));
          float c = hash(i + vec2(0.0, 1.0));
          float d = hash(i + vec2(1.0, 1.0));
          vec2 u = f * f * (3.0 - 2.0 * f);
          return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
        }
        float fbm(vec2 p){
          float v = 0.0;
          float a = 0.5;
          for(int i = 0; i < 5; i++){
            v += a * noise(p);
            p *= 2.0;
            a *= 0.5;
          }
          return v;
        }

        void main(){
          vec2 uv = vUv * uParams.x;
          float n = fbm(uv + uTime * uParams.z);
          float pattern = n;
          if(uPattern > 0.5 && uPattern < 1.5){
            vec2 p = uv;
            float ang = uTime * 0.2;
            p = vec2(cos(ang) * p.x - sin(ang) * p.y, sin(ang) * p.x + cos(ang) * p.y);
            pattern = fbm(p * (1.0 + uAudioMid * 2.0));
          } else if(uPattern >= 1.5){
            pattern = step(0.5 + 0.3 * sin(uTime + uAudioHigh * 5.0), n);
          }
          vec3 col = 0.5 + 0.5 * sin(vec3(0.0, 2.0, 4.0) + pattern * 6.2831 + uAudioLow * 5.0);
          gl_FragColor = vec4(col, uOpacity);
        }
      `
    });
    this.mesh = new THREE.Mesh(geometry, material);
    this.scene.add(this.mesh);
    this.lastChange = 0;
  }

  private randomize(material: THREE.ShaderMaterial): void {
    material.uniforms.uParams.value.set(Math.random() * 3 + 1, Math.random() * 5 + 1, Math.random() * 0.2 + 0.05);
    material.uniforms.uPattern.value = Math.floor(Math.random() * 3);
  }

  public update(): void {
    const t = this.clock.getElapsedTime();
    const mat = this.mesh.material as THREE.ShaderMaterial;
    mat.uniforms.uTime.value = t;
    mat.uniforms.uAudioLow.value = this.audioData.low;
    mat.uniforms.uAudioMid.value = this.audioData.mid;
    mat.uniforms.uAudioHigh.value = this.audioData.high;
    mat.uniforms.uOpacity.value = this.opacity;
    if (t - this.lastChange > this.changeInterval) {
      this.randomize(mat);
      this.lastChange = t;
      this.changeInterval = 60 + Math.random() * 60;
    }
  }

  public updateConfig(newConfig: any): void {
    this.currentConfig = { ...this.currentConfig, ...newConfig };
    const mat = this.mesh.material as THREE.ShaderMaterial;
    if (newConfig.opacity !== undefined) {
      mat.uniforms.uOpacity.value = newConfig.opacity;
    }
  }

  public dispose(): void {
    this.scene.remove(this.mesh);
    this.mesh.geometry.dispose();
    (this.mesh.material as THREE.ShaderMaterial).dispose();
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  cfg: PresetConfig,
  shaderCode?: string
): BasePreset {
  return new GenerativeDubPreset(scene, camera, renderer, cfg);
}
