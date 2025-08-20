import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: "Text Glitch",
  description: "Texto animado con efectos glitch y aparición desordenada",
  author: "AudioVisualizer Pro",
  version: "1.0.0",
  category: "text",
  tags: ["text", "glitch", "animated", "cyberpunk"],
  thumbnail: "text_glitch_thumb.png",
  defaultConfig: {
    opacity: 1.0,
    fadeMs: 500,
    text: {
      content: "R O B O T I C A",
      fontSize: 120,
      fontFamily: "Arial Black, sans-serif",
      letterSpacing: 0.3,
      lineHeight: 1.2
    },
    animation: {
      letterDelay: 0.8,
      shuffleIntensity: 0.7,
      glitchFrequency: 2.5,
      fadeInDuration: 1.2,
      repositionSpeed: 1.5
    },
    colors: {
      primary: "#00FF88",
      secondary: "#FF0088",
      accent: "#88FF00",
      glitch1: "#FF4444",
      glitch2: "#4444FF"
    },
    effects: {
      enableGlitch: true,
      enableShuffle: true,
      enableScanlines: true,
      chromaticAberration: 0.3,
      glitchIntensity: 0.8
    }
  }
};

// Clase para manejar letras individuales con efectos
class GlitchLetter {
  private canvas: HTMLCanvasElement;
  private context: CanvasRenderingContext2D;
  private texture: THREE.Texture;
  private material: THREE.ShaderMaterial;
  private geometry: THREE.PlaneGeometry;
  private mesh: THREE.Mesh;
  
  public letter: string;
  public targetPosition: THREE.Vector3;
  public currentPosition: THREE.Vector3;
  public initialPosition: THREE.Vector3;
  public age: number = 0;
  public appearTime: number;
  public isVisible: boolean = false;
  public glitchPhase: number;
  
  constructor(
    letter: string,
    fontSize: number,
    fontFamily: string,
    appearTime: number
  ) {
    this.letter = letter;
    this.appearTime = appearTime;
    this.glitchPhase = Math.random() * Math.PI * 2;
    
    this.createCanvas(fontSize, fontFamily);
    this.createMaterial();
    this.createMesh();
    
    this.currentPosition = new THREE.Vector3();
    this.targetPosition = new THREE.Vector3();
    this.initialPosition = new THREE.Vector3();
  }

  private createCanvas(fontSize: number, fontFamily: string): void {
    this.canvas = document.createElement('canvas');
    this.canvas.width = fontSize * 2;
    this.canvas.height = fontSize * 2;
    
    this.context = this.canvas.getContext('2d')!;
    this.context.font = `${fontSize}px ${fontFamily}`;
    this.context.textAlign = 'center';
    this.context.textBaseline = 'middle';
    
    this.updateCanvasContent();
    
    this.texture = new THREE.Texture(this.canvas);
    this.texture.needsUpdate = true;
  }

  private updateCanvasContent(): void {
    this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
    
    // Dibujar letra con efecto glitch
    this.context.fillStyle = '#ffffff';
    this.context.fillText(
      this.letter,
      this.canvas.width / 2,
      this.canvas.height / 2
    );
  }

  private createMaterial(): void {
    this.material = new THREE.ShaderMaterial({
      transparent: true,
      blending: THREE.AdditiveBlending,
      uniforms: {
        uTexture: { value: this.texture },
        uTime: { value: 0.0 },
        uOpacity: { value: 0.0 },
        uGlitchIntensity: { value: 0.0 },
        uColorPrimary: { value: new THREE.Color(0x00ff88) },
        uColorGlitch1: { value: new THREE.Color(0xff4444) },
        uColorGlitch2: { value: new THREE.Color(0x4444ff) },
        uChromaticAberration: { value: 0.0 },
        uGlitchPhase: { value: this.glitchPhase },
        uDigitalNoise: { value: 0.0 }
      },
      vertexShader: `
        varying vec2 vUv;
        uniform float uTime;
        uniform float uGlitchIntensity;
        uniform float uGlitchPhase;
        
        // Función de ruido digital
        float random(vec2 st) {
          return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
        }
        
        void main() {
          vUv = uv;
          vec3 pos = position;
          
          // Efecto glitch en vértices
          float glitchTime = uTime * 10.0 + uGlitchPhase;
          float glitch = sin(glitchTime) * cos(glitchTime * 1.3) * uGlitchIntensity;
          
          // Distorsión digital aleatoria
          float noise = random(vec2(glitchTime, pos.x)) - 0.5;
          pos.x += glitch * noise * 0.1;
          pos.y += sin(glitchTime * 2.0) * uGlitchIntensity * 0.05;
          
          // Efecto de "pixelado"
          if (uGlitchIntensity > 0.5) {
            pos.x = floor(pos.x * 20.0) / 20.0;
            pos.y = floor(pos.y * 20.0) / 20.0;
          }
          
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        varying vec2 vUv;
        uniform sampler2D uTexture;
        uniform float uTime;
        uniform float uOpacity;
        uniform float uGlitchIntensity;
        uniform vec3 uColorPrimary;
        uniform vec3 uColorGlitch1;
        uniform vec3 uColorGlitch2;
        uniform float uChromaticAberration;
        uniform float uGlitchPhase;
        uniform float uDigitalNoise;
        
        // Función de ruido
        float random(vec2 st) {
          return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
        }
        
        void main() {
          vec2 uv = vUv;
          
          // Efecto de aberración cromática
          vec2 rOffset = vec2(uChromaticAberration * 0.01, 0.0);
          vec2 bOffset = vec2(-uChromaticAberration * 0.01, 0.0);
          
          float r = texture2D(uTexture, uv + rOffset).r;
          float g = texture2D(uTexture, uv).g;
          float b = texture2D(uTexture, uv + bOffset).b;
          float a = texture2D(uTexture, uv).a;
          
          // Glitch temporal
          float glitchTime = uTime * 8.0 + uGlitchPhase;
          float glitchMask = step(0.7, sin(glitchTime)) * uGlitchIntensity;
          
          // Distorsión de UV durante glitch
          if (glitchMask > 0.0) {
            float distortion = random(vec2(floor(uv.y * 20.0), floor(uTime * 10.0)));
            uv.x += (distortion - 0.5) * 0.1 * glitchMask;
            
            // Re-sample con distorsión
            r = texture2D(uTexture, uv + rOffset).r;
            g = texture2D(uTexture, uv).g;  
            b = texture2D(uTexture, uv + bOffset).b;
          }
          
          // Color base
          vec3 color = vec3(r, g, b);
          
          // Aplicar colores temáticos
          if (a > 0.1) {
            color = mix(color * uColorPrimary, color, 0.3);
            
            // Efectos glitch de color
            if (glitchMask > 0.0) {
              float colorGlitch = random(vec2(uv.x, uTime));
              if (colorGlitch > 0.7) {
                color = mix(color, uColorGlitch1, 0.6);
              } else if (colorGlitch > 0.4) {
                color = mix(color, uColorGlitch2, 0.4);
              }
            }
          }
          
          // Ruido digital
          float noise = random(uv + uTime * 0.1) * uDigitalNoise;
          color += vec3(noise);
          
          // Scanlines
          float scanline = sin(uv.y * 800.0 + uTime * 20.0) * 0.1 + 0.9;
          color *= scanline;
          
          gl_FragColor = vec4(color, a * uOpacity);
        }
      `
    });
  }

  private createMesh(): void {
    this.geometry = new THREE.PlaneGeometry(1, 1);
    this.mesh = new THREE.Mesh(this.geometry, this.material);
  }

  public setInitialPosition(x: number, y: number, z: number = 0): void {
    this.initialPosition.set(x, y, z);
    this.currentPosition.copy(this.initialPosition);
    this.mesh.position.copy(this.currentPosition);
  }

  public setTargetPosition(x: number, y: number, z: number = 0): void {
    this.targetPosition.set(x, y, z);
  }

  public update(deltaTime: number, time: number, audioData: any, config: any): void {
    this.age += deltaTime;
    
    // Controlar visibilidad basada en tiempo
    if (!this.isVisible && this.age >= this.appearTime) {
      this.isVisible = true;
    }
    
    if (this.isVisible) {
      // Fade in
      const fadeProgress = Math.min(1.0, (this.age - this.appearTime) / config.animation.fadeInDuration);
      const targetOpacity = config.opacity * fadeProgress;
      
      // Movimiento hacia posición final
      const moveSpeed = config.animation.repositionSpeed * deltaTime;
      this.currentPosition.lerp(this.targetPosition, moveSpeed);
      this.mesh.position.copy(this.currentPosition);
      
      // Actualizar uniforms
      this.material.uniforms.uTime.value = time;
      this.material.uniforms.uOpacity.value = targetOpacity;
      
      // Efectos basados en audio
      const glitchIntensity = config.effects.enableGlitch ? 
        config.effects.glitchIntensity * (0.3 + audioData.mid * 0.7) : 0.0;
      
      this.material.uniforms.uGlitchIntensity.value = glitchIntensity;
      this.material.uniforms.uChromaticAberration.value = 
        config.effects.chromaticAberration * audioData.high;
      this.material.uniforms.uDigitalNoise.value = audioData.high * 0.2;
      
      // Actualizar colores
      this.material.uniforms.uColorPrimary.value.setStyle(config.colors.primary);
      this.material.uniforms.uColorGlitch1.value.setStyle(config.colors.glitch1);
      this.material.uniforms.uColorGlitch2.value.setStyle(config.colors.glitch2);
    }
  }

  public getMesh(): THREE.Mesh {
    return this.mesh;
  }

  public dispose(): void {
    this.geometry.dispose();
    this.material.dispose();
    this.texture.dispose();
  }
}

class TextGlitchPreset extends BasePreset {
  private letters: GlitchLetter[] = [];
  private currentConfig: any;
  private shuffledIndices: number[] = [];

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
    this.renderer.setClearColor(0x000000, 0);
    this.createTextLetters();
  }

  private createTextLetters(): void {
    const text = this.currentConfig.text.content.replace(/\s+/g, ' ');
    const letters = text.split('');
    
    // Crear indices mezclados para aparición desordenada
    this.shuffledIndices = Array.from({ length: letters.length }, (_, i) => i);
    if (this.currentConfig.effects.enableShuffle) {
      for (let i = this.shuffledIndices.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [this.shuffledIndices[i], this.shuffledIndices[j]] = 
        [this.shuffledIndices[j], this.shuffledIndices[i]];
      }
    }

    // Crear letras
    letters.forEach((letter, index) => {
      if (letter.trim() !== '') {
        const shuffledIndex = this.shuffledIndices.indexOf(index);
        const appearTime = shuffledIndex * this.currentConfig.animation.letterDelay;
        
        const glitchLetter = new GlitchLetter(
          letter,
          this.currentConfig.text.fontSize,
          this.currentConfig.text.fontFamily,
          appearTime
        );

        // Posición inicial aleatoria (dispersa)
        const scatterRadius = 200;
        const initialX = (Math.random() - 0.5) * scatterRadius;
        const initialY = (Math.random() - 0.5) * scatterRadius;
        glitchLetter.setInitialPosition(initialX, initialY);

        // Posición final (formando el texto)
        const finalX = (index - letters.length / 2) * 
                      (this.currentConfig.text.fontSize * this.currentConfig.text.letterSpacing);
        const finalY = 0;
        glitchLetter.setTargetPosition(finalX, finalY);

        this.letters.push(glitchLetter);
        this.scene.add(glitchLetter.getMesh());
      }
    });
  }

  public update(): void {
    const deltaTime = this.clock.getDelta();
    const time = this.clock.getElapsedTime();

    // Actualizar todas las letras
    this.letters.forEach(letter => {
      letter.update(deltaTime, time, this.audioData, this.currentConfig);
    });
  }

  public updateConfig(newConfig: any): void {
    this.currentConfig = this.deepMerge(this.currentConfig, newConfig);
    
    // Si cambió el texto, recrear
    if (newConfig.text && newConfig.text.content) {
      this.dispose();
      this.createTextLetters();
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
    this.letters.forEach(letter => {
      this.scene.remove(letter.getMesh());
      letter.dispose();
    });
    this.letters = [];
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  config: PresetConfig,
  shaderCode?: string
): BasePreset {
  return new TextGlitchPreset(scene, camera, renderer, config);
}