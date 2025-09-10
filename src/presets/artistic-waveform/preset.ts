import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: "Artistic Waveform Pro",
  description: "High-resolution waveform visualizer with Touch Designer aesthetics",
  author: "AudioVisualizer Pro",
  version: "1.0.0",
  category: "waveform",
  tags: ["waveform", "artistic", "touchdesigner", "professional", "highres"],
  thumbnail: "artistic_waveform_pro_thumb.png",
  note: 60,
  defaultConfig: {
    opacity: 1.0,
    fadeMs: 150,
    waveform: {
      resolution: 512,
      thickness: 2.5,
      smoothing: 0.8,
      amplitude: 1.2,
      frequency: 1.0,
      layers: 5,
      displacement: 0.3
    },
    visual: {
      blur: 0.4,
      glow: 0.6,
      chromatic: 0.2,
      distortion: 0.15,
      feedback: 0.3,
      particles: true
    },
    colors: {
      primary: "#00F5FF",
      secondary: "#FF1493",
      tertiary: "#FFD700",
      background: "#0A0A0F",
      accent: "#FFFFFF"
    },
    animation: {
      speed: 1.0,
      rotation: 0.2,
      scale: 1.0,
      morphing: 0.5,
      breathing: 0.3
    }
  }
};

export class ArtisticWaveformPro extends BasePreset {
  private scene!: THREE.Scene;
  private camera!: THREE.OrthographicCamera;
  private material!: THREE.ShaderMaterial;
  private mesh!: THREE.Mesh;
  private config: any;
  
  constructor(config: any) {
    super();
    this.config = config;
    this.initializeScene();
    this.createWaveformMaterial();
  }
  
  private initializeScene(): void {
    this.scene = new THREE.Scene();
    this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 1000);
    this.camera.position.z = 1;
  }
  
  private createWaveformMaterial(): void {
    const vertexShader = `
      void main() {
        gl_Position = vec4(position, 1.0);
      }
    `;
    
    const fragmentShader = `
      uniform float time;
      uniform float audio_low;
      uniform float audio_mid;
      uniform float audio_high;
      uniform float opacity;
      uniform float amplitude;
      uniform float layers;
      uniform float glow;
      uniform float distortion;
      uniform float morphing;
      uniform vec2 resolution;
      uniform vec3 primaryColor;
      uniform vec3 secondaryColor;
      uniform vec3 tertiaryColor;
      
      ${this.getShaderFunctions()}
      
      void main() {
        vec2 uv = (gl_FragCoord.xy / resolution) * 2.0 - 1.0;
        uv.x *= resolution.x / resolution.y;
        
        vec3 audioData = vec3(audio_low, audio_mid, audio_high);
        vec3 finalColor = generateArtisticWaveform(uv, time, audioData);
        
        gl_FragColor = vec4(finalColor * opacity, opacity);
      }
    `;
    
    this.material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms: {
        time: { value: 0.0 },
        audio_low: { value: 0.0 },
        audio_mid: { value: 0.0 },
        audio_high: { value: 0.0 },
        opacity: { value: 1.0 },
        amplitude: { value: this.config.waveform.amplitude },
        layers: { value: this.config.waveform.layers },
        glow: { value: this.config.visual.glow },
        distortion: { value: this.config.visual.distortion },
        morphing: { value: this.config.animation.morphing },
        resolution: { value: new THREE.Vector2(1920, 1080) },
        primaryColor: { value: new THREE.Color(this.config.colors.primary) },
        secondaryColor: { value: new THREE.Color(this.config.colors.secondary) },
        tertiaryColor: { value: new THREE.Color(this.config.colors.tertiary) }
      },
      transparent: true,
      blending: THREE.AdditiveBlending
    });
    
    const geometry = new THREE.PlaneGeometry(2, 2);
    this.mesh = new THREE.Mesh(geometry, this.material);
    this.scene.add(this.mesh);
  }
  
  private getShaderFunctions(): string {
    return `
      float hash(vec2 p) {
        return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
      }
      
      float noise(vec2 p) {
        vec2 i = floor(p);
        vec2 f = fract(p);
        vec2 u = f * f * (3.0 - 2.0 * f);
        
        return mix(
          mix(hash(i + vec2(0.0, 0.0)), hash(i + vec2(1.0, 0.0)), u.x),
          mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x),
          u.y
        );
      }
      
      float fbm(vec2 p) {
        float value = 0.0;
        float amplitude = 0.5;
        float frequency = 1.0;
        
        for (int i = 0; i < 4; i++) {
          value += amplitude * noise(p * frequency);
          amplitude *= 0.5;
          frequency *= 2.0;
        }
        
        return value;
      }
      
      vec3 generateArtisticWaveform(vec2 uv, float time, vec3 audioData) {
        vec3 finalColor = vec3(0.02, 0.05, 0.1);
        
        for (float layer = 0.0; layer < layers; layer += 1.0) {
          float frequency = 8.0 + layer * 2.0;
          float phase = time * (0.5 + layer * 0.3) + layer * 1.57;
          
          float wave = sin(uv.x * frequency + phase) * (0.3 + audioData.x * 0.7);
          wave += sin(uv.x * frequency * 1.618 + phase * 1.3) * (0.2 + audioData.y * 0.5) * 0.5;
          
          float distortionNoise = fbm(uv * 3.0 + time * 0.2) * distortion;
          wave += distortionNoise * (0.5 + audioData.x * 0.5);
          
          float thickness = 0.02 + layer * 0.01;
          thickness *= (1.0 + audioData.x * 2.0);
          float intensity = smoothstep(thickness, 0.0, abs(uv.y - wave * amplitude));
          
          vec3 color1 = primaryColor;
          vec3 color2 = secondaryColor;
          vec3 color3 = tertiaryColor;
          
          vec3 layerColor = mix(color1, color2, layer / layers);
          layerColor = mix(layerColor, color3, audioData.z * 0.7);
          
          float hdrFactor = 1.0 + intensity * 2.0 + audioData.y * 1.5;
          layerColor *= hdrFactor;
          
          finalColor += layerColor * intensity;
        }
        
        if (glow > 0.0) {
          vec3 glowColor = vec3(0.0);
          finalColor += glowColor * 0.5;
        }
        
        float particleNoise = fbm(uv * 15.0 + time * 2.0);
        float threshold = 0.8 - audio_high * 0.3;
        
        if (particleNoise > threshold) {
          float sparkle = sin(time * 10.0 + dot(uv, vec2(127.1, 311.7))) * 0.5 + 0.5;
          finalColor += vec3(1.0, 0.9, 0.7) * sparkle * (particleNoise - threshold) * 10.0 * audio_high;
        }
        
        finalColor = finalColor / (finalColor + vec3(1.0));
        float vignette = 1.0 - length(uv * 0.7);
        finalColor *= vignette;
        finalColor = pow(finalColor, vec3(0.8));
        
        return finalColor;
      }
    `;
  }
  
  public update(deltaTime: number, time: number, audioData: any, globalOpacity: number): void {
    this.material.uniforms.time.value = time * this.config.animation.speed;
    this.material.uniforms.audio_low.value = audioData.low || 0;
    this.material.uniforms.audio_mid.value = audioData.mid || 0;
    this.material.uniforms.audio_high.value = audioData.high || 0;
    this.material.uniforms.opacity.value = globalOpacity;
    this.material.uniforms.amplitude.value = this.config.waveform.amplitude;
    this.material.uniforms.layers.value = this.config.waveform.layers;
    this.material.uniforms.glow.value = this.config.visual.glow;
    this.material.uniforms.distortion.value = this.config.visual.distortion;
    this.material.uniforms.morphing.value = this.config.animation.morphing;
    
    const breathingScale = 1.0 + Math.sin(time * 2.0) * this.config.animation.breathing * 0.1;
    this.mesh.scale.setScalar(breathingScale);
    
    this.mesh.rotation.z = time * this.config.animation.rotation * 0.1;
  }
  
  public getMeshes(): THREE.Mesh[] {
    return [this.mesh];
  }
  
  public updateColors(colors: any): void {
    this.material.uniforms.primaryColor.value.setHex(colors.primary?.replace('#', '0x') || 0x00F5FF);
    this.material.uniforms.secondaryColor.value.setHex(colors.secondary?.replace('#', '0x') || 0xFF1493);
    this.material.uniforms.tertiaryColor.value.setHex(colors.tertiary?.replace('#', '0x') || 0xFFD700);
  }
  
  public updateConfig(newConfig: any): void {
    this.config = { ...this.config, ...newConfig };
    
    if (this.material?.uniforms) {
      this.material.uniforms.amplitude.value = this.config.waveform.amplitude;
      this.material.uniforms.layers.value = this.config.waveform.layers;
      this.material.uniforms.glow.value = this.config.visual.glow;
      this.material.uniforms.distortion.value = this.config.visual.distortion;
      this.material.uniforms.morphing.value = this.config.animation.morphing;
    }
  }
  
  public dispose(): void {
    if (this.material) {
      this.material.dispose();
    }
    if (this.mesh?.geometry) {
      this.mesh.geometry.dispose();
    }
  }
}

export default ArtisticWaveformPro;