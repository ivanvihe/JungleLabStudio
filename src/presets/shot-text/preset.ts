import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

// Config embebido para ROBOTICA
export const config: PresetConfig = {
  name: "ROBOTICA Text Intro",
  description: "Visualizacion de texto 'R O B O T I C A' con animacion cinematografica de aparicion letra por letra",
  author: "AudioVisualizer",
  version: "1.0.0",
  category: "text",
  tags: ["text", "intro", "robotica", "cinematic", "glow", "animation"],
  thumbnail: "robotica_intro_thumb.png",
  note: 60,
  defaultConfig: {
    opacity: 1.0,
    fadeMs: 200,
    text: {
      content: "R O B O T I C A",
      scale: 1.0,
      color: "#FFFFFF"
    },
    animation: {
      duration: 15.0,
      fadeDuration: 6.0,
      letterDelay: 0.3,
      glowIntensity: 1.2,
      pulseSpeed: 2.0,
      animationOrder: [2, 8, 4, 6, 10, 14, 12, 0] // O T B O I A C R
    },
    colors: {
      text: "#FFFFFF",
      glow: "#FFFFFF"
    },
    effects: {
      enableGlow: true,
      enablePulse: true,
      enableSparkle: true
    }
  },
  controls: [
    {
      name: "text.scale",
      type: "slider",
      label: "Escala del Texto",
      min: 0.5,
      max: 3.0,
      step: 0.1,
      default: 1.0
    },
    {
      name: "animation.fadeDuration",
      type: "slider",
      label: "Duracion de Fade",
      min: 2.0,
      max: 10.0,
      step: 0.5,
      default: 6.0
    },
    {
      name: "animation.letterDelay",
      type: "slider",
      label: "Velocidad de Animacion",
      min: 0.1,
      max: 1.0,
      step: 0.05,
      default: 0.3
    },
    {
      name: "animation.glowIntensity",
      type: "slider",
      label: "Intensidad de Brillo",
      min: 0.0,
      max: 3.0,
      step: 0.1,
      default: 1.2
    },
    {
      name: "colors.text",
      type: "color",
      label: "Color del Texto",
      default: "#FFFFFF"
    },
    {
      name: "effects.enableGlow",
      type: "checkbox",
      label: "Efectos de Brillo",
      default: true
    }
  ],
  audioMapping: {
    low: {
      description: "Controla la velocidad de animacion",
      frequency: "20-250 Hz",
      effect: "Velocidad de aparicion de letras"
    },
    mid: {
      description: "Controla el pulso y brillo",
      frequency: "250-4000 Hz",
      effect: "Intensidad de pulso y brillo"
    },
    high: {
      description: "Controla los destellos",
      frequency: "4000+ Hz",
      effect: "Destellos y efectos especiales"
    }
  },
  performance: {
    complexity: "medium",
    recommendedFPS: 60,
    gpuIntensive: false
  }
};

// Patrones de letras 5x7 (igual que en Python)
const LETTER_PATTERNS: { [key: string]: string[] } = {
  "R": [
    "11110",
    "10001",
    "10001",
    "11110",
    "10100",
    "10010",
    "10001",
  ],
  "O": [
    "01110",
    "10001",
    "10001",
    "10001",
    "10001",
    "10001",
    "01110",
  ],
  "B": [
    "11110",
    "10001",
    "10001",
    "11110",
    "10001",
    "10001",
    "11110",
  ],
  "T": [
    "11111",
    "00100",
    "00100",
    "00100",
    "00100",
    "00100",
    "00100",
  ],
  "I": [
    "11111",
    "00100",
    "00100",
    "00100",
    "00100",
    "00100",
    "11111",
  ],
  "C": [
    "01110",
    "10001",
    "10000",
    "10000",
    "10000",
    "10001",
    "01110",
  ],
  "A": [
    "01110",
    "10001",
    "10001",
    "11111",
    "10001",
    "10001",
    "10001",
  ],
};

class RoboticaLetter {
  public mesh: THREE.Group;
  public glowMesh: THREE.Group;
  public alpha: number = 0;
  public targetAlpha: number = 0;
  public startTime: number | null = null;
  public sparkleTimer: number = 0;
  public pulseOffset: number;

  constructor(char: string, position: THREE.Vector3, cellSize: number, color: THREE.Color) {
    this.mesh = new THREE.Group();
    this.glowMesh = new THREE.Group();
    this.pulseOffset = Math.random() * Math.PI * 2;

    const pattern = LETTER_PATTERNS[char];
    if (pattern) {
      this.createLetterGeometry(pattern, cellSize, color);
    }

    this.mesh.position.copy(position);
    this.glowMesh.position.copy(position);
  }

  private createLetterGeometry(pattern: string[], cellSize: number, color: THREE.Color) {
    const geometry = new THREE.BoxGeometry(cellSize * 0.9, cellSize * 0.9, cellSize * 0.1);
    
    for (let rowIdx = 0; rowIdx < pattern.length; rowIdx++) {
      for (let colIdx = 0; colIdx < pattern[rowIdx].length; colIdx++) {
        if (pattern[rowIdx][colIdx] === '1') {
          const x = colIdx * cellSize - (5 * cellSize) / 2;
          const y = (pattern.length - rowIdx - 1) * cellSize - (7 * cellSize) / 2;

          // Pixel principal
          const material = new THREE.MeshBasicMaterial({
            color: color,
            transparent: true,
            opacity: 0
          });
          const cube = new THREE.Mesh(geometry, material);
          cube.position.set(x, y, 0);
          this.mesh.add(cube);

          // Pixel de brillo
          const glowMaterial = new THREE.MeshBasicMaterial({
            color: color,
            transparent: true,
            opacity: 0
          });
          const glowCube = new THREE.Mesh(geometry, glowMaterial);
          glowCube.position.set(x, y, 0.01);
          glowCube.scale.setScalar(1.5);
          this.glowMesh.add(glowCube);
        }
      }
    }
  }

  public update(
    deltaTime: number,
    currentTime: number,
    fadeDuration: number,
    globalOpacity: number,
    config: any
  ) {
    // Animacion de fade
    if (this.startTime !== null && currentTime >= this.startTime) {
      const fadeProgress = Math.min(1.0, (currentTime - this.startTime) / fadeDuration);
      // Curva suave de fade
      this.targetAlpha = 1.0 - Math.pow(1.0 - fadeProgress, 2);
    }

    // Interpolacion suave del alpha
    this.alpha += (this.targetAlpha - this.alpha) * deltaTime * 5;

    // Efectos de pulso
    let pulse = 1.0;
    if (config.effects?.enablePulse) {
      const pulseSpeed = config.animation?.pulseSpeed ?? 2.0;
      pulse = 0.8 + 0.4 * Math.sin(currentTime * pulseSpeed + this.pulseOffset + this.alpha * 5);
    }

    // Efectos de sparkle
    let sparkle = 1.0;
    if (config.effects?.enableSparkle) {
      this.sparkleTimer += deltaTime * 0.8;
      if (this.sparkleTimer > 1 && Math.random() < 0.02) {
        this.sparkleTimer = 0;
      }
      sparkle = this.sparkleTimer < 0.2 ? 1 + Math.sin(this.sparkleTimer * Math.PI * 5) * 2 : 1.0;
    }

    const finalOpacity = this.alpha * globalOpacity * pulse * sparkle;

    // Actualizar opacidad de todos los pixels
    this.mesh.children.forEach(child => {
      if (child instanceof THREE.Mesh) {
        (child.material as THREE.MeshBasicMaterial).opacity = finalOpacity;
      }
    });

    // Actualizar brillo
    if (config.effects?.enableGlow) {
      const glowIntensity = config.animation?.glowIntensity ?? 1.2;
      const glowOpacity = this.alpha * 0.3 * globalOpacity * glowIntensity * sparkle;
      
      this.glowMesh.children.forEach(child => {
        if (child instanceof THREE.Mesh) {
          (child.material as THREE.MeshBasicMaterial).opacity = glowOpacity;
        }
      });
    } else {
      this.glowMesh.children.forEach(child => {
        if (child instanceof THREE.Mesh) {
          (child.material as THREE.MeshBasicMaterial).opacity = 0;
        }
      });
    }
  }

  public setStartTime(time: number) {
    this.startTime = time;
  }

  public resetAnimation() {
    this.alpha = 0;
    this.targetAlpha = 0;
    this.startTime = null;
    this.sparkleTimer = 0;
  }

  public updateColor(color: THREE.Color) {
    this.mesh.children.forEach(child => {
      if (child instanceof THREE.Mesh) {
        (child.material as THREE.MeshBasicMaterial).color.copy(color);
      }
    });
    
    this.glowMesh.children.forEach(child => {
      if (child instanceof THREE.Mesh) {
        (child.material as THREE.MeshBasicMaterial).color.copy(color);
      }
    });
  }
}

class RoboticaTextPreset extends BasePreset {
  private letters: RoboticaLetter[] = [];
  private animationStartTime: number | null = null;
  private currentConfig: any;
  private textGroup: THREE.Group;
  private glowGroup: THREE.Group;

  constructor(
    scene: THREE.Scene,
    camera: THREE.Camera,
    renderer: THREE.WebGLRenderer,
    config: PresetConfig,
    private shaderCode?: string
  ) {
    super(scene, camera, renderer, config);
    this.currentConfig = { ...config.defaultConfig };
    this.textGroup = new THREE.Group();
    this.glowGroup = new THREE.Group();
  }

  public init(): void {
    this.createText();
    this.scene.add(this.textGroup);
    this.scene.add(this.glowGroup);
  }

  private createText(): void {
    const text = this.currentConfig.text.content;
    const letterHeight = 0.18 * this.currentConfig.text.scale;
    const cellSize = letterHeight / 7.0;
    const letterWidth = 5 * cellSize;
    const letterSpacing = cellSize * 0.6;
    const wordSpacing = cellSize * 1.8;

    // Calcular ancho total
    let totalWidth = 0;
    for (const char of text) {
      if (char === ' ') {
        totalWidth += wordSpacing;
      } else {
        totalWidth += letterWidth + letterSpacing;
      }
    }
    totalWidth -= letterSpacing;

    const startX = -totalWidth / 2.0;
    let currentX = startX;
    const color = new THREE.Color(this.currentConfig.colors.text);

    for (let charIdx = 0; charIdx < text.length; charIdx++) {
      const char = text[charIdx];
      
      if (char === ' ') {
        currentX += wordSpacing;
        continue;
      }

      const position = new THREE.Vector3(currentX + letterWidth / 2, 0, 0);
      const letter = new RoboticaLetter(char, position, cellSize, color);
      
      this.letters.push(letter);
      this.textGroup.add(letter.mesh);
      this.glowGroup.add(letter.glowMesh);

      currentX += letterWidth + letterSpacing;
    }
  }

  private initializeAnimation() {
    if (this.animationStartTime === null) {
      this.animationStartTime = this.clock.getElapsedTime();
      
      // Configurar tiempos de inicio segun el orden de animacion
      const animationOrder = this.currentConfig.animation.animationOrder;
      const letterDelay = this.currentConfig.animation.letterDelay;

      animationOrder.forEach((letterIdx: number, orderIdx: number) => {
        // letterIdx se refiere al indice en el string completo incluyendo espacios
        // Necesitamos mapearlo al indice en el array de letters (sin espacios)
        let actualLetterIndex = 0;
        let stringIndex = 0;
        
        for (const char of this.currentConfig.text.content) {
          if (stringIndex === letterIdx) {
            if (char !== ' ') {
              const delay = orderIdx * letterDelay + (Math.random() - 0.5) * 0.1;
              const startTime = this.animationStartTime! + delay;
              this.letters[actualLetterIndex]?.setStartTime(startTime);
            }
            break;
          }
          
          if (char !== ' ') {
            actualLetterIndex++;
          }
          stringIndex++;
        }
      });
    }
  }

  public update(): void {
    const deltaTime = this.clock.getDelta();
    const currentTime = this.clock.getElapsedTime();

    this.initializeAnimation();

    // Actualizar todas las letras
    this.letters.forEach(letter => {
      letter.update(
        deltaTime,
        currentTime,
        this.currentConfig.animation.fadeDuration,
        this.opacity,
        this.currentConfig
      );
    });

    // Actualizar escala basada en audio
    const audioIntensity = (this.audioData.low + this.audioData.mid + this.audioData.high) / 3;
    const scale = this.currentConfig.text.scale * (1 + audioIntensity * 0.1);
    this.textGroup.scale.setScalar(scale);
    this.glowGroup.scale.setScalar(scale);
  }

  public updateConfig(newConfig: any): void {
    this.currentConfig = this.deepMerge(this.currentConfig, newConfig);

    if (newConfig.colors?.text) {
      const color = new THREE.Color(newConfig.colors.text);
      this.letters.forEach(letter => letter.updateColor(color));
    }

    if (newConfig.text?.scale) {
      this.recreateText();
    }
  }

  private recreateText(): void {
    // Limpiar texto existente
    this.textGroup.clear();
    this.glowGroup.clear();
    this.letters = [];
    this.animationStartTime = null;

    // Recrear texto
    this.createText();
  }

  public resetAnimation(): void {
    this.animationStartTime = null;
    this.letters.forEach(letter => letter.resetAnimation());
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
      letter.mesh.children.forEach(child => {
        if (child instanceof THREE.Mesh) {
          child.geometry.dispose();
          (child.material as THREE.Material).dispose();
        }
      });
      
      letter.glowMesh.children.forEach(child => {
        if (child instanceof THREE.Mesh) {
          child.geometry.dispose();
          (child.material as THREE.Material).dispose();
        }
      });
    });

    this.scene.remove(this.textGroup);
    this.scene.remove(this.glowGroup);
  }
}

// Exportar la funcion factory requerida
export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  config: PresetConfig,
  shaderCode?: string
): BasePreset {
  return new RoboticaTextPreset(scene, camera, renderer, config, shaderCode);
}