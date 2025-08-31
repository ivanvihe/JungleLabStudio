import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'Generative Dub',
  description: 'Generative fractals and particles that evolve forever',
  author: 'AudioVisualizer',
  version: '1.0.0',
  category: 'generative',
  tags: ['auto', 'infinite', 'dub', 'abstract', 'audio-reactive', 'fractal', 'particles'],
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
  private changeInterval = 30;

  private audioLow = 0;
  private audioMid = 0;
  private audioHigh = 0;
  private readonly audioSensitivity = 1.5;
  private readonly audioSmoothing = 0.1;

  private currentPattern = 0;
  private nextPattern = 0;
  private transitionStart = 0;
  private transitionDuration = 8;

  private static readonly PALETTES = [
    ['#0e0e0e', '#3a506b', '#5bc0be'],
    ['#000000', '#1b262c', '#0f4c75'],
    ['#000000', '#ffffff', '#88c0d0'],
    ['#0d1b2a', '#1b263b', '#415a77'],
    ['#222831', '#393e46', '#00adb5']
  ].map(p => p.map(c => new THREE.Color(c)));

  public init(): void {
    this.currentConfig = JSON.parse(JSON.stringify(this.config.defaultConfig));
    const geometry = new THREE.PlaneGeometry(10, 10);
    this.currentPattern = Math.floor(Math.random() * 10);
    this.nextPattern = this.currentPattern;
    const material = new THREE.ShaderMaterial({
      transparent: true,
      uniforms: {
        uTime: { value: 0 },
        uOpacity: { value: this.opacity },
        uParams: { value: new THREE.Vector3(Math.random() * 3 + 1, Math.random() * 5 + 1, Math.random() * 0.2 + 0.05) },
        uPatternA: { value: this.currentPattern },
        uPatternB: { value: this.nextPattern },
        uBlend: { value: 0 },
        uAudioLow: { value: 0 },
        uAudioMid: { value: 0 },
        uAudioHigh: { value: 0 },
        uColor1: { value: new THREE.Color('#0e0e0e') },
        uColor2: { value: new THREE.Color('#3a506b') },
        uColor3: { value: new THREE.Color('#5bc0be') }
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
        uniform float uPatternA;
        uniform float uPatternB;
        uniform float uBlend;
        uniform float uAudioLow;
        uniform float uAudioMid;
        uniform float uAudioHigh;
        uniform vec3 uColor1;
        uniform vec3 uColor2;
        uniform vec3 uColor3;

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

        float getPattern(float id, vec2 uv){
          if(id < 0.5){
            return fbm(uv + uTime * uParams.z);
          } else if(id < 1.5){
            vec2 p = uv;
            float ang = uTime * 0.2;
            p = vec2(cos(ang) * p.x - sin(ang) * p.y, sin(ang) * p.x + cos(ang) * p.y);
            return fbm(p * (1.0 + uAudioMid * 2.0));
          } else if(id < 2.5){
            float n = fbm(uv);
            return step(0.5 + 0.3 * sin(uTime + uAudioHigh * 5.0), n);
          } else if(id < 3.5){
            vec2 p = uv;
            p = abs(fract(p) - 0.5);
            return fbm(p * 3.0 + uTime * 0.5);
          } else if(id < 4.5){
            vec2 p = uv * 2.0 - 1.0;
            for(int i=0;i<3;i++){ p=abs(p)/dot(p,p)-vec2(0.5); }
            return length(p);
          } else if(id < 5.5){
            vec2 p = uv + noise(uv*4.0 + uTime);
            return fract(p.x + p.y);
          } else if(id < 6.5){
            vec2 p = uv*10.0;
            float n = fract(sin(dot(floor(p), vec2(12.9898,78.233)))*43758.5453);
            return step(0.98, n);
          } else if(id < 7.5){
            vec2 p = uv - 0.5;
            float r = length(p);
            float a = atan(p.y,p.x);
            return sin(6.2831*r + a*3.0 + uTime);
          } else if(id < 8.5){
            vec2 p = uv*3.0;
            p += vec2(fbm(p+uTime), fbm(p-uTime));
            return fbm(p);
          } else {
            vec2 p = uv*5.0;
            float n = fbm(p+uTime);
            return step(0.85, n);
          }
        }

        void main(){
          vec2 uv = vUv * uParams.x;
          float pA = getPattern(uPatternA, uv);
          float pB = getPattern(uPatternB, uv);
          float pattern = mix(pA, pB, uBlend);
          vec3 col = mix(uColor1, uColor2, pattern);
          col = mix(col, uColor3, pattern * pattern);
          gl_FragColor = vec4(col, uOpacity);
        }
      `
    });
    this.randomizePalette(material);
    this.mesh = new THREE.Mesh(geometry, material);
    this.scene.add(this.mesh);
    this.lastChange = 0;
  }

  private randomize(material: THREE.ShaderMaterial): void {
    material.uniforms.uParams.value.set(
      Math.random() * 3 + 1,
      Math.random() * 5 + 1,
      Math.random() * 0.2 + 0.05
    );
    this.randomizePalette(material);
    this.currentPattern = this.nextPattern;
    let newPattern = this.currentPattern;
    while (newPattern === this.currentPattern) {
      newPattern = Math.floor(Math.random() * 10);
    }
    this.nextPattern = newPattern;
    this.transitionStart = this.clock.getElapsedTime();
    this.transitionDuration = 5 + Math.random() * 5;
    material.uniforms.uPatternA.value = this.currentPattern;
    material.uniforms.uPatternB.value = this.nextPattern;
    material.uniforms.uBlend.value = 0;
  }

  public update(): void {
    const t = this.clock.getElapsedTime();
    const mat = this.mesh.material as THREE.ShaderMaterial;
    mat.uniforms.uTime.value = t;

    this.audioLow = THREE.MathUtils.lerp(
      this.audioLow,
      Math.min(this.audioData.low * this.audioSensitivity, 1),
      this.audioSmoothing
    );
    this.audioMid = THREE.MathUtils.lerp(
      this.audioMid,
      Math.min(this.audioData.mid * this.audioSensitivity, 1),
      this.audioSmoothing
    );
    this.audioHigh = THREE.MathUtils.lerp(
      this.audioHigh,
      Math.min(this.audioData.high * this.audioSensitivity, 1),
      this.audioSmoothing
    );

    mat.uniforms.uAudioLow.value = this.audioLow;
    mat.uniforms.uAudioMid.value = this.audioMid;
    mat.uniforms.uAudioHigh.value = this.audioHigh;
    mat.uniforms.uOpacity.value = this.opacity;

    if (t - this.lastChange > this.changeInterval) {
      this.randomize(mat);
      this.lastChange = t;
      this.changeInterval = 30 + Math.random() * 30;
    }

    if (this.currentPattern !== this.nextPattern) {
      const blend = Math.min((t - this.transitionStart) / this.transitionDuration, 1);
      mat.uniforms.uBlend.value = blend;
      if (blend >= 1) {
        this.currentPattern = this.nextPattern;
        this.nextPattern = this.currentPattern;
        mat.uniforms.uPatternA.value = this.currentPattern;
        mat.uniforms.uPatternB.value = this.nextPattern;
        mat.uniforms.uBlend.value = 0;
      }
    }
  }

  public updateConfig(newConfig: any): void {
    this.currentConfig = { ...this.currentConfig, ...newConfig };
    const mat = this.mesh.material as THREE.ShaderMaterial;
    if (newConfig.opacity !== undefined) {
      mat.uniforms.uOpacity.value = newConfig.opacity;
    }
  }

  private randomizePalette(material: THREE.ShaderMaterial): void {
    const palette = GenerativeDubPreset.PALETTES[
      Math.floor(Math.random() * GenerativeDubPreset.PALETTES.length)
    ];
    material.uniforms.uColor1.value.copy(palette[0]);
    material.uniforms.uColor2.value.copy(palette[1]);
    material.uniforms.uColor3.value.copy(palette[2]);
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
