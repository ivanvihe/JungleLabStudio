import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: "Energy Wave Ray",
  description: "Rayo horizontal de ondas de energía fluidas como la imagen",
  author: "AudioVisualizer Pro",
  version: "1.0.0",
  category: "energy",
  tags: ["energy", "wave", "flow", "horizontal", "plasma", "smooth"],
  thumbnail: "energy_wave_ray_thumb.png",
  note: 57,
  defaultConfig: {
    opacity: 1.0,
    fadeMs: 100,
    wave: {
      width: 10.0,
      height: 2.0,
      segments: 200,
      layers: 5,
      speed: 0.4,
      amplitude: 0.5,
      direction: 1.0 // 1.0 = izquierda a derecha, -1.0 = derecha a izquierda
    },
    colors: {
      hot: "#FF6B35",     // Naranja caliente
      warm: "#FF8E53",    // Naranja medio
      cool: "#4FC3F7",    // Azul cyan
      cold: "#29B6F6"     // Azul frío
    },
    flow: {
      turbulence: 0.3,
      frequency: 1.5,
      phaseShift: 0.8,
      smoothness: 0.9
    }
  },
  controls: [
    {
      name: "wave.amplitude",
      type: "slider",
      label: "Amplitud de Ondas",
      min: 0.2,
      max: 1.5,
      step: 0.1,
      default: 0.5
    },
    {
      name: "wave.speed",
      type: "slider",
      label: "Velocidad de Flujo",
      min: 0.1,
      max: 1.5,
      step: 0.1,
      default: 0.4
    },
    {
      name: "wave.direction",
      type: "slider",
      label: "Dirección (-1=Der→Izq, 1=Izq→Der)",
      min: -1.0,
      max: 1.0,
      step: 2.0,
      default: 1.0
    },
    {
      name: "flow.turbulence",
      type: "slider",
      label: "Turbulencia",
      min: 0.1,
      max: 1.0,
      step: 0.1,
      default: 0.3
    }
  ],
  audioMapping: {
    low: {
      description: "Controla amplitud y grosor del rayo",
      frequency: "20-250 Hz",
      effect: "Intensidad y anchura de las ondas"
    },
    mid: {
      description: "Modula la turbulencia y flujo",
      frequency: "250-4000 Hz",
      effect: "Variaciones en el patrón de ondas"
    },
    high: {
      description: "Controla colores calientes y efectos",
      frequency: "4000+ Hz",
      effect: "Transiciones de color y brillantez"
    }
  },
  performance: {
    complexity: "low",
    recommendedFPS: 60,
    gpuIntensive: false
  }
};

class EnergyWaveRay {
  private layers: THREE.Line[] = [];
  private materials: THREE.ShaderMaterial[] = [];
  private geometries: THREE.BufferGeometry[] = [];
  
  constructor(private config: any) {
    this.createWaveLayers();
  }
  
  private createWaveLayers(): void {
    const layerCount = this.config.wave.layers;
    
    for (let layer = 0; layer < layerCount; layer++) {
      this.createSingleWave(layer);
    }
  }
  
  private createSingleWave(layerIndex: number): void {
    const segments = this.config.wave.segments;
    const width = this.config.wave.width;
    
    // Crear geometría
    const positions = new Float32Array((segments + 1) * 3);
    const uvs = new Float32Array((segments + 1) * 2);
    
    for (let i = 0; i <= segments; i++) {
      const t = i / segments;
      const x = (t - 0.5) * width;
      
      positions[i * 3] = x;
      positions[i * 3 + 1] = 0; // Se actualizará en el shader/update
      positions[i * 3 + 2] = layerIndex * 0.01; // Separación mínima entre layers
      
      uvs[i * 2] = t;
      uvs[i * 2 + 1] = layerIndex / (this.config.wave.layers - 1);
    }
    
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
    
    // Crear material con shader
    const material = new THREE.ShaderMaterial({
      transparent: true,
      blending: THREE.AdditiveBlending,
      vertexShader: `
        varying vec2 vUv;
        varying vec3 vPosition;
        uniform float uTime;
        uniform float uLayerIndex;
        uniform float uAmplitude;
        uniform float uTurbulence;
        uniform float uSpeed;
        uniform float uDirection;
        uniform float uAudioLow;
        uniform float uAudioMid;
        uniform float uAudioHigh;
        
        // Función de ruido suave
        float noise(vec2 p) {
          return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
        }
        
        float smoothNoise(vec2 p) {
          vec2 i = floor(p);
          vec2 f = fract(p);
          f = f * f * (3.0 - 2.0 * f);
          
          return mix(
            mix(noise(i), noise(i + vec2(1.0, 0.0)), f.x),
            mix(noise(i + vec2(0.0, 1.0)), noise(i + vec2(1.0, 1.0)), f.x),
            f.y
          );
        }
        
        void main() {
          vUv = uv;
          vPosition = position;
          
          float t = uv.x;
          
          // Desplazamiento simple y lineal para crear el efecto de flujo
          float flowOffset = mod(uTime * uSpeed * uDirection * 0.1, 2.0);
          
          // Ondas FIJAS en el espacio que crean el patrón
          float wave1 = sin(t * 6.28 * 1.2 + flowOffset + uLayerIndex * 0.3) * uAmplitude;
          float wave2 = sin(t * 6.28 * 0.8 + flowOffset * 0.7 + uLayerIndex * 0.2) * uAmplitude * 0.6;
          float wave3 = cos(t * 6.28 * 1.5 + flowOffset * 1.2 + uLayerIndex * 0.4) * uAmplitude * 0.3;
          
          // Turbulencia fija
          float noiseInput = t * 4.0 + flowOffset * 0.3;
          float noiseValue = smoothNoise(vec2(noiseInput, uLayerIndex));
          float turbulenceWave = noiseValue * uTurbulence * 0.2;
          
          // Audio responsiveness simple
          float audioWave = sin(t * 6.28 * 2.0 + flowOffset * 1.5) * uAudioMid * 0.3;
          float audioAmplitude = uAudioLow * 0.2;
          
          // Combinar ondas
          float finalY = (wave1 + wave2 + wave3 + turbulenceWave + audioWave) * (0.8 + audioAmplitude);
          
          // Layer variation
          float layerOffset = uLayerIndex * 0.15;
          finalY += sin(t * 6.28 * 0.5 + flowOffset * 0.8 + layerOffset) * 0.08;
          
          vec3 pos = position;
          pos.y = finalY;
          
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        varying vec2 vUv;
        varying vec3 vPosition;
        uniform float uTime;
        uniform float uLayerIndex;
        uniform float uOpacity;
        uniform float uAudioHigh;
        uniform vec3 uHotColor;
        uniform vec3 uWarmColor;
        uniform vec3 uCoolColor;
        uniform vec3 uColdColor;
        
        void main() {
          float t = vUv.x;
          
          // Gradiente de temperatura fijo (sin desplazamiento temporal)
          float temperature = sin(t * 3.14159) * 0.4 + 0.6;
          temperature += uAudioHigh * 0.2;
          
          // Gradiente de colores basado en temperatura
          vec3 color;
          if (temperature < 0.3) {
            color = mix(uColdColor, uCoolColor, temperature * 3.33);
          } else if (temperature < 0.6) {
            color = mix(uCoolColor, uWarmColor, (temperature - 0.3) * 3.33);
          } else {
            color = mix(uWarmColor, uHotColor, (temperature - 0.6) * 2.5);
          }
          
          // Intensidad basada en la posición del layer
          float layerIntensity = 1.0 - uLayerIndex * 0.12;
          
          // Suavizado en los bordes
          float edgeFade = 1.0 - smoothstep(0.0, 0.15, abs(t - 0.5) * 2.0 - 0.7);
          
          // Pulsación muy sutil y constante
          float pulse = sin(uTime * 2.0) * 0.1 + 0.9;
          
          float finalIntensity = layerIntensity * edgeFade * pulse;
          
          gl_FragColor = vec4(color * finalIntensity, finalIntensity * uOpacity);
        }
      `,
      uniforms: {
        uTime: { value: 0.0 },
        uLayerIndex: { value: layerIndex },
        uAmplitude: { value: this.config.wave.amplitude },
        uTurbulence: { value: this.config.flow.turbulence },
        uSpeed: { value: this.config.wave.speed },
        uDirection: { value: this.config.wave.direction },
        uOpacity: { value: 1.0 },
        uAudioLow: { value: 0.0 },
        uAudioMid: { value: 0.0 },
        uAudioHigh: { value: 0.0 },
        uHotColor: { value: new THREE.Color(this.config.colors.hot) },
        uWarmColor: { value: new THREE.Color(this.config.colors.warm) },
        uCoolColor: { value: new THREE.Color(this.config.colors.cool) },
        uColdColor: { value: new THREE.Color(this.config.colors.cold) }
      }
    });
    
    const line = new THREE.Line(geometry, material);
    
    this.geometries.push(geometry);
    this.materials.push(material);
    this.layers.push(line);
  }
  
  public update(deltaTime: number, time: number, audioData: any, globalOpacity: number): void {
    // Actualizar todos los materiales
    this.materials.forEach((material, index) => {
      material.uniforms.uTime.value = time;
      material.uniforms.uAmplitude.value = this.config.wave.amplitude * (0.7 + audioData.low * 0.5);
      material.uniforms.uTurbulence.value = this.config.flow.turbulence * (0.5 + audioData.mid * 0.5);
      material.uniforms.uSpeed.value = this.config.wave.speed * (0.8 + audioData.high * 0.4);
      material.uniforms.uDirection.value = this.config.wave.direction;
      material.uniforms.uOpacity.value = globalOpacity;
      material.uniforms.uAudioLow.value = audioData.low;
      material.uniforms.uAudioMid.value = audioData.mid;
      material.uniforms.uAudioHigh.value = audioData.high;
    });
  }
  
  public getMeshes(): THREE.Line[] {
    return this.layers;
  }
  
  public updateColors(colors: any): void {
    this.materials.forEach(material => {
      material.uniforms.uHotColor.value.setHex(colors.hot.replace('#', '0x'));
      material.uniforms.uWarmColor.value.setHex(colors.warm.replace('#', '0x'));
      material.uniforms.uCoolColor.value.setHex(colors.cool.replace('#', '0x'));
      material.uniforms.uColdColor.value.setHex(colors.cold.replace('#', '0x'));
    });
  }
  
  public updateConfig(newConfig: any): void {
    this.config = newConfig;
    
    this.materials.forEach(material => {
      material.uniforms.uAmplitude.value = newConfig.wave.amplitude;
      material.uniforms.uTurbulence.value = newConfig.flow.turbulence;
      material.uniforms.uSpeed.value = newConfig.wave.speed;
      material.uniforms.uDirection.value = newConfig.wave.direction;
    });
  }
  
  public dispose(): void {
    this.geometries.forEach(geo => geo.dispose());
    this.materials.forEach(mat => mat.dispose());
  }
}

class EnergyWaveRayPreset extends BasePreset {
  private energyWave: EnergyWaveRay;
  private currentConfig: any;
  
  constructor(
    scene: THREE.Scene,
    camera: THREE.Camera,
    renderer: THREE.WebGLRenderer,
    config: PresetConfig
  ) {
    super(scene, camera, renderer, config);
    this.currentConfig = { ...config.defaultConfig };
  }
  
  public init(): void {
    // Fondo completamente transparente
    this.renderer.setClearColor(0x000000, 0);
    
    // Crear el rayo de ondas de energía
    this.energyWave = new EnergyWaveRay(this.currentConfig);
    this.energyWave.getMeshes().forEach(mesh => this.scene.add(mesh));
  }
  
  public update(): void {
    const deltaTime = this.clock.getDelta();
    const time = this.clock.getElapsedTime();
    
    // Actualizar el rayo
    this.energyWave.update(deltaTime, time, this.audioData, this.opacity);
  }
  
  public updateConfig(newConfig: any): void {
    this.currentConfig = this.deepMerge(this.currentConfig, newConfig);
    
    this.energyWave.updateConfig(this.currentConfig);
    
    if (newConfig.colors) {
      this.energyWave.updateColors(this.currentConfig.colors);
    }
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
    this.energyWave.getMeshes().forEach(mesh => this.scene.remove(mesh));
    this.energyWave.dispose();
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  config: PresetConfig,
  shaderCode?: string
): BasePreset {
  return new EnergyWaveRayPreset(scene, camera, renderer, config);
}