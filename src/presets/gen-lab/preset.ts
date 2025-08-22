import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'Gen Lab',
  description: 'Generative cloud laboratory with multiple modes',
  author: 'AudioVisualizer',
  version: '1.0.0',
  category: 'generative',
  tags: ['cloud', 'vapor', 'skybox', 'noise', 'audio-reactive'],
  thumbnail: 'gen_lab_thumb.png',
  defaultConfig: {
    opacity: 1.0,
    variant: 'cloud',
    noiseScale: 1.5,
    speed: 0.2,
    color1: '#ff8a00',
    color2: '#4e00ff',
    radialBlur: 0.4,
    uvDistort: 0.2
  },
  controls: [
    { name: 'variant', type: 'select', label: 'Variant', options: ['cloud', 'vapor', 'skybox'], default: 'cloud' },
    { name: 'noiseScale', type: 'slider', label: 'Noise Scale', min: 0.5, max: 5.0, step: 0.1, default: 1.5 },
    { name: 'speed', type: 'slider', label: 'Speed', min: 0.0, max: 2.0, step: 0.01, default: 0.2 },
    { name: 'color1', type: 'color', label: 'Color 1', default: '#ff8a00' },
    { name: 'color2', type: 'color', label: 'Color 2', default: '#4e00ff' },
    { name: 'radialBlur', type: 'slider', label: 'Radial Blur', min: 0.0, max: 1.0, step: 0.01, default: 0.4 },
    { name: 'uvDistort', type: 'slider', label: 'UV Distortion', min: 0.0, max: 1.0, step: 0.01, default: 0.2 }
  ],
  audioMapping: {
    low: { description: 'Modula densidad del ruido', frequency: '20-250 Hz', effect: 'Noise density' },
    mid: { description: 'Desplazamiento UV y profundidad', frequency: '250-4000 Hz', effect: 'Distortion & depth' },
    high: { description: 'Remolinos y cambio de color', frequency: '4000+ Hz', effect: 'Color swirl' }
  },
  performance: { complexity: 'medium', recommendedFPS: 60, gpuIntensive: false }
};

class GenLabPreset extends BasePreset {
  private mesh!: THREE.Mesh<THREE.PlaneGeometry, THREE.ShaderMaterial>;
  private currentConfig: any;

  public init(): void {
    this.renderer.setClearColor(0x000000, 0);
    this.currentConfig = JSON.parse(JSON.stringify(this.config.defaultConfig));

    const geometry = new THREE.PlaneGeometry(2, 2);
    const material = new THREE.ShaderMaterial({
      transparent: true,
      uniforms: {
        uTime: { value: 0 },
        uColor1: { value: new THREE.Color(this.currentConfig.color1) },
        uColor2: { value: new THREE.Color(this.currentConfig.color2) },
        uNoiseScale: { value: this.currentConfig.noiseScale },
        uSpeed: { value: this.currentConfig.speed },
        uVariant: { value: 0 },
        uRadialBlur: { value: this.currentConfig.radialBlur },
        uUvDistort: { value: this.currentConfig.uvDistort },
        uAudioLow: { value: 0 },
        uAudioMid: { value: 0 },
        uAudioHigh: { value: 0 },
        uOpacity: { value: 1 }
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
        uniform float uTime;
        uniform vec3 uColor1;
        uniform vec3 uColor2;
        uniform float uNoiseScale;
        uniform float uSpeed;
        uniform int uVariant;
        uniform float uRadialBlur;
        uniform float uUvDistort;
        uniform float uAudioLow;
        uniform float uAudioMid;
        uniform float uAudioHigh;
        uniform float uOpacity;

        float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453123); }
        float noise(vec2 p){
          vec2 i=floor(p), f=fract(p);
          float a=hash(i), b=hash(i+vec2(1.,0.));
          float c=hash(i+vec2(0.,1.)), d=hash(i+vec2(1.,1.));
          vec2 u=f*f*(3.-2.*f);
          return mix(a,b,u.x)+(c-a)*u.y*(1.-u.x)+(d-b)*u.x*u.y;
        }
        float fbm(vec2 p){
          float v=0.; float a=.5;
          for(int i=0;i<5;i++){ v+=a*noise(p); p*=2.; a*=.5; }
          return v;
        }

        void main(){
          vec2 uv=vUv;
          if(uVariant==1){
            uv.x += uTime*0.2;
            uv.y += sin(uv.x*10.0 + uTime)*0.02;
          } else if(uVariant==2){
            vec2 p = uv*2.0 - 1.0;
            float r = length(p);
            float theta = atan(p.y,p.x);
            uv = vec2(theta/6.28318 + 0.5, r);
          }
          uv += (uv-0.5)*uAudioMid*uUvDistort;
          float t = uTime*uSpeed;
          float n = fbm(uv*uNoiseScale + t);
          float r = length(uv-0.5);
          n *= 1.0 - r*uRadialBlur*(1.0 + uAudioLow);
          vec3 col = mix(uColor1, uColor2, n + uAudioHigh*0.2);
          gl_FragColor = vec4(col, n*uOpacity);
        }
      `
    });

    this.mesh = new THREE.Mesh(geometry, material);
    this.scene.add(this.mesh);
  }

  public update(): void {
    const t = this.clock.getElapsedTime();
    const mat = this.mesh.material as THREE.ShaderMaterial;
    mat.uniforms.uTime.value = t;
    mat.uniforms.uAudioLow.value = this.audioData.low;
    mat.uniforms.uAudioMid.value = this.audioData.mid;
    mat.uniforms.uAudioHigh.value = this.audioData.high;
    mat.uniforms.uOpacity.value = this.opacity;
    const variant = this.currentConfig.variant;
    let idx = 0;
    if (variant === 'vapor') idx = 1; else if (variant === 'skybox') idx = 2;
    mat.uniforms.uVariant.value = idx;
  }

  public updateConfig(newConfig: any): void {
    this.currentConfig = { ...this.currentConfig, ...newConfig };
    const mat = this.mesh.material as THREE.ShaderMaterial;
    if (newConfig.color1) mat.uniforms.uColor1.value = new THREE.Color(newConfig.color1);
    if (newConfig.color2) mat.uniforms.uColor2.value = new THREE.Color(newConfig.color2);
    if (newConfig.noiseScale !== undefined) mat.uniforms.uNoiseScale.value = newConfig.noiseScale;
    if (newConfig.speed !== undefined) mat.uniforms.uSpeed.value = newConfig.speed;
    if (newConfig.radialBlur !== undefined) mat.uniforms.uRadialBlur.value = newConfig.radialBlur;
    if (newConfig.uvDistort !== undefined) mat.uniforms.uUvDistort.value = newConfig.uvDistort;
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
  return new GenLabPreset(scene, camera, renderer, cfg);
}
