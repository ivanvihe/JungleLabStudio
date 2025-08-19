import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

// Configuración del preset Abstract Lines
export const config: PresetConfig = {
  name: "Abstract Lines",
  description: "Líneas abstractas que aparecen y desaparecen creando formas orgánicas con colores tenues",
  author: "AudioVisualizer",
  version: "1.0.0",
  category: "abstract",
  tags: ["abstract", "lines", "organic", "fluid", "minimal", "geometric"],
  thumbnail: "abstract_lines_thumb.png",
  defaultConfig: {
    opacity: 1.0,
    fadeMs: 300,
    lineCount: {
      primary: 20,
      secondary: 35,
      detail: 50
    },
    colors: {
      primary: "#E8F4F8",     // Azul muy tenue
      secondary: "#F0F8E8",   // Verde muy tenue  
      detail: "#F8F0E8",      // Naranja muy tenue
      accent: "#F8E8F0",      // Rosa muy tenue
      background: "#0A0F14"   // Azul oscuro de fondo
    },
    animation: {
      appearanceSpeed: 0.8,
      movementSpeed: 0.3,
      formationSpeed: 1.2,
      flickerIntensity: 0.4,
      morphingRate: 0.6,
      flowComplexity: 2.0
    },
    effects: {
      enableFlicker: true,
      enableMorphing: true,
      enableFormation: true,
      enableFlow: true,
      enableDepth: true
    },
    geometry: {
      maxLength: 2.5,
      minLength: 0.3,
      curvature: 0.4,
      thickness: 0.8
    }
  },
  controls: [
    {
      name: "animation.appearanceSpeed",
      type: "slider",
      label: "Velocidad de Aparición",
      min: 0.1,
      max: 3.0,
      step: 0.1,
      default: 0.8
    },
    {
      name: "animation.movementSpeed",
      type: "slider",
      label: "Velocidad de Movimiento",
      min: 0.1,
      max: 2.0,
      step: 0.1,
      default: 0.3
    },
    {
      name: "animation.formationSpeed",
      type: "slider",
      label: "Velocidad de Formación",
      min: 0.2,
      max: 4.0,
      step: 0.1,
      default: 1.2
    },
    {
      name: "animation.flickerIntensity",
      type: "slider",
      label: "Intensidad de Parpadeo",
      min: 0.0,
      max: 1.0,
      step: 0.1,
      default: 0.4
    },
    {
      name: "animation.morphingRate",
      type: "slider",
      label: "Velocidad de Transformación",
      min: 0.1,
      max: 2.0,
      step: 0.1,
      default: 0.6
    },
    {
      name: "geometry.curvature",
      type: "slider",
      label: "Curvatura de Líneas",
      min: 0.0,
      max: 1.0,
      step: 0.1,
      default: 0.4
    },
    {
      name: "geometry.thickness",
      type: "slider",
      label: "Grosor de Líneas",
      min: 0.1,
      max: 2.0,
      step: 0.1,
      default: 0.8
    },
    {
      name: "effects.enableFlicker",
      type: "checkbox",
      label: "Efecto Parpadeo",
      default: true
    },
    {
      name: "effects.enableMorphing",
      type: "checkbox",
      label: "Transformación Continua",
      default: true
    },
    {
      name: "effects.enableFormation",
      type: "checkbox",
      label: "Formación de Patrones",
      default: true
    },
    {
      name: "colors.primary",
      type: "color",
      label: "Color Primario",
      default: "#E8F4F8"
    },
    {
      name: "colors.secondary",
      type: "color",
      label: "Color Secundario",
      default: "#F0F8E8"
    },
    {
      name: "colors.detail",
      type: "color",
      label: "Color de Detalle",
      default: "#F8F0E8"
    },
    {
      name: "colors.accent",
      type: "color",
      label: "Color de Acento",
      default: "#F8E8F0"
    }
  ],
  audioMapping: {
    low: {
      description: "Controla la aparición y movimiento de líneas primarias",
      frequency: "20-250 Hz",
      effect: "Generación de líneas principales y formaciones básicas"
    },
    mid: {
      description: "Controla las líneas secundarias y transformaciones",
      frequency: "250-4000 Hz",
      effect: "Morfología y patrones intermedios"
    },
    high: {
      description: "Controla los detalles finos y efectos de parpadeo",
      frequency: "4000+ Hz",
      effect: "Líneas de detalle y efectos sutiles"
    }
  },
  performance: {
    complexity: "medium",
    recommendedFPS: 60,
    gpuIntensive: false
  }
};

class AbstractLine {
  points: THREE.Vector3[];
  targetPoints: THREE.Vector3[];
  line: THREE.Line;
  material: THREE.LineBasicMaterial;
  lifespan: number;
  maxLifespan: number;
  opacity: number = 0;
  targetOpacity: number = 0;
  flickerTimer: number = 0;
  morphProgress: number = 0;
  formationPattern: number;
  movementPhase: number;
  
  constructor(startPoint: THREE.Vector3, endPoint: THREE.Vector3, color: THREE.Color, curvature: number = 0.3) {
    this.formationPattern = Math.random() * Math.PI * 2;
    this.movementPhase = Math.random() * Math.PI * 2;
    this.maxLifespan = 3 + Math.random() * 8;
    this.lifespan = this.maxLifespan;
    
    this.points = this.generateCurvedLine(startPoint, endPoint, curvature);
    this.targetPoints = [...this.points];
    
    const geometry = new THREE.BufferGeometry().setFromPoints(this.points);
    this.material = new THREE.LineBasicMaterial({
      color: color,
      transparent: true,
      opacity: 0,
      linewidth: 1
    });
    
    this.line = new THREE.Line(geometry, this.material);
  }
  
  private generateCurvedLine(start: THREE.Vector3, end: THREE.Vector3, curvature: number): THREE.Vector3[] {
    const points: THREE.Vector3[] = [];
    const segments = Math.floor(8 + Math.random() * 12);
    
    for (let i = 0; i <= segments; i++) {
      const t = i / segments;
      const point = new THREE.Vector3().lerpVectors(start, end, t);
      
      // Añadir curvatura orgánica
      const curve1 = Math.sin(t * Math.PI * 2) * curvature;
      const curve2 = Math.sin(t * Math.PI * 3 + this.formationPattern) * curvature * 0.5;
      
      point.x += curve1 * (Math.random() - 0.5);
      point.y += curve2 * (Math.random() - 0.5);
      point.z += Math.sin(t * Math.PI + this.formationPattern) * curvature * 0.3;
      
      points.push(point);
    }
    
    return points;
  }
  
  private generateNewTarget(audioIntensity: number, config: any): void {
    const center = new THREE.Vector3(
      (Math.random() - 0.5) * 4,
      (Math.random() - 0.5) * 3,
      (Math.random() - 0.5) * 1
    );
    
    const radius = 0.5 + audioIntensity * 2;
    const angle1 = Math.random() * Math.PI * 2;
    const angle2 = angle1 + (Math.random() - 0.5) * Math.PI;
    
    const start = new THREE.Vector3(
      center.x + Math.cos(angle1) * radius,
      center.y + Math.sin(angle1) * radius,
      center.z + (Math.random() - 0.5) * 0.5
    );
    
    const end = new THREE.Vector3(
      center.x + Math.cos(angle2) * radius,
      center.y + Math.sin(angle2) * radius,
      center.z + (Math.random() - 0.5) * 0.5
    );
    
    this.targetPoints = this.generateCurvedLine(start, end, config.geometry?.curvature || 0.4);
  }
  
  update(deltaTime: number, audioData: any, globalOpacity: number, config: any, time: number): void {
    // Control de vida
    this.lifespan -= deltaTime;
    const lifeRatio = this.lifespan / this.maxLifespan;
    
    // Regenerar si es necesario
    if (this.lifespan <= 0) {
      const audioIntensity = (audioData.low + audioData.mid + audioData.high) / 3;
      this.generateNewTarget(audioIntensity, config);
      this.lifespan = this.maxLifespan;
      this.morphProgress = 0;
    }
    
    // Cálculo de opacidad objetivo
    const appearanceSpeed = config.animation?.appearanceSpeed || 0.8;
    const fadeIn = Math.min(1, (this.maxLifespan - this.lifespan) * appearanceSpeed);
    const fadeOut = Math.min(1, this.lifespan * appearanceSpeed);
    this.targetOpacity = Math.min(fadeIn, fadeOut);
    
    // Suavizado de opacidad
    this.opacity += (this.targetOpacity - this.opacity) * deltaTime * 4;
    
    // Efecto de parpadeo
    let flickerMultiplier = 1.0;
    if (config.effects?.enableFlicker) {
      this.flickerTimer += deltaTime * (config.animation?.flickerIntensity || 0.4) * 10;
      flickerMultiplier = 0.7 + 0.3 * Math.sin(this.flickerTimer + this.formationPattern);
    }
    
    // Transformación morfológica
    if (config.effects?.enableMorphing) {
      this.morphProgress += deltaTime * (config.animation?.morphingRate || 0.6);
      
      // Interpolar hacia puntos objetivo
      for (let i = 0; i < Math.min(this.points.length, this.targetPoints.length); i++) {
        const lerpFactor = Math.sin(this.morphProgress + i * 0.1) * 0.5 + 0.5;
        this.points[i].lerp(this.targetPoints[i], deltaTime * 2 * lerpFactor);
      }
    }
    
    // Movimiento orgánico
    const movementSpeed = config.animation?.movementSpeed || 0.3;
    this.movementPhase += deltaTime * movementSpeed;
    
    const flowOffset = new THREE.Vector3(
      Math.sin(this.movementPhase) * 0.1,
      Math.cos(this.movementPhase * 1.3) * 0.1,
      Math.sin(this.movementPhase * 0.7) * 0.05
    );
    
    // Aplicar movimiento a todos los puntos
    const finalPoints = this.points.map((point, index) => {
      const localOffset = flowOffset.clone().multiplyScalar(Math.sin(index * 0.3 + time));
      return point.clone().add(localOffset);
    });
    
    // Actualizar geometría
    this.line.geometry.setFromPoints(finalPoints);
    this.line.geometry.attributes.position.needsUpdate = true;
    
    // Actualizar material
    this.material.opacity = this.opacity * flickerMultiplier * globalOpacity;
    
    // Responsividad al audio
    const audioResponse = audioData.low * 0.3 + audioData.mid * 0.4 + audioData.high * 0.3;
    this.material.opacity *= 0.6 + audioResponse * 0.4;
  }
  
  setColor(color: THREE.Color): void {
    this.material.color.copy(color);
  }
  
  dispose(): void {
    this.line.geometry.dispose();
    this.material.dispose();
  }
}

class AbstractLinesPreset extends BasePreset {
  private lines: {
    primary: AbstractLine[];
    secondary: AbstractLine[];
    detail: AbstractLine[];
  };
  
  private backgroundMesh: THREE.Mesh;
  private currentConfig: any;
  private spawnTimer: number = 0;
  private colorPalette: THREE.Color[];
  
  constructor(
    scene: THREE.Scene,
    camera: THREE.Camera,
    renderer: THREE.WebGLRenderer,
    config: PresetConfig,
    private shaderCode?: string
  ) {
    super(scene, camera, renderer, config);
    
    this.lines = {
      primary: [],
      secondary: [],
      detail: []
    };
    
    this.currentConfig = { ...config.defaultConfig };
    this.initializeColorPalette();
  }
  
  private initializeColorPalette(): void {
    const colors = this.currentConfig.colors;
    this.colorPalette = [
      new THREE.Color(colors.primary),
      new THREE.Color(colors.secondary),
      new THREE.Color(colors.detail),
      new THREE.Color(colors.accent)
    ];
  }
  
  public init(): void {
    this.createBackground();
    this.createInitialLines();
  }
  
  private createBackground(): void {
    const geometry = new THREE.PlaneGeometry(20, 15);
    const material = new THREE.MeshBasicMaterial({
      color: new THREE.Color(this.currentConfig.colors.background),
      transparent: true,
      opacity: 0.95
    });
    
    this.backgroundMesh = new THREE.Mesh(geometry, material);
    this.backgroundMesh.position.z = -5;
    this.scene.add(this.backgroundMesh);
  }
  
  private createInitialLines(): void {
    const lineCount = this.currentConfig.lineCount;
    
    // Líneas primarias
    for (let i = 0; i < lineCount.primary; i++) {
      this.createRandomLine('primary');
    }
    
    // Líneas secundarias
    for (let i = 0; i < lineCount.secondary; i++) {
      this.createRandomLine('secondary');
    }
    
    // Líneas de detalle
    for (let i = 0; i < lineCount.detail; i++) {
      this.createRandomLine('detail');
    }
  }
  
  private createRandomLine(type: 'primary' | 'secondary' | 'detail'): void {
    const colors = this.colorPalette;
    const color = colors[Math.floor(Math.random() * colors.length)].clone();
    
    // Ajustar intensidad del color según el tipo
    switch (type) {
      case 'primary':
        color.multiplyScalar(0.9);
        break;
      case 'secondary':
        color.multiplyScalar(0.7);
        break;
      case 'detail':
        color.multiplyScalar(0.5);
        break;
    }
    
    const start = new THREE.Vector3(
      (Math.random() - 0.5) * 6,
      (Math.random() - 0.5) * 4,
      (Math.random() - 0.5) * 2
    );
    
    const length = this.currentConfig.geometry.minLength + 
                  Math.random() * (this.currentConfig.geometry.maxLength - this.currentConfig.geometry.minLength);
    
    const angle = Math.random() * Math.PI * 2;
    const end = new THREE.Vector3(
      start.x + Math.cos(angle) * length,
      start.y + Math.sin(angle) * length,
      start.z + (Math.random() - 0.5) * 0.5
    );
    
    const line = new AbstractLine(start, end, color, this.currentConfig.geometry.curvature);
    line.material.linewidth = this.currentConfig.geometry.thickness;
    
    this.lines[type].push(line);
    this.scene.add(line.line);
  }
  
  public update(): void {
    const deltaTime = this.clock.getDelta();
    const time = this.clock.getElapsedTime();
    
    // Actualizar todas las líneas
    Object.values(this.lines).flat().forEach(line => {
      line.update(deltaTime, this.audioData, this.opacity, this.currentConfig, time);
    });
    
    // Control de spawn dinámico basado en audio
    this.spawnTimer += deltaTime;
    const spawnRate = 0.5 + (this.audioData.low + this.audioData.mid + this.audioData.high) / 3;
    
    if (this.spawnTimer > 1 / spawnRate) {
      this.spawnTimer = 0;
      
      // Decidir qué tipo de línea crear basado en la intensidad del audio
      if (this.audioData.low > 0.6) {
        this.createRandomLine('primary');
      } else if (this.audioData.mid > 0.5) {
        this.createRandomLine('secondary');
      } else if (this.audioData.high > 0.4) {
        this.createRandomLine('detail');
      }
      
      // Limitar número máximo de líneas
      this.limitLineCount();
    }
    
    // Actualizar fondo
    if (this.backgroundMesh) {
      const material = this.backgroundMesh.material as THREE.MeshBasicMaterial;
      const audioIntensity = (this.audioData.low + this.audioData.mid + this.audioData.high) / 3;
      material.opacity = (0.95 + audioIntensity * 0.05) * this.opacity;
    }
  }
  
  private limitLineCount(): void {
    const maxCounts = {
      primary: this.currentConfig.lineCount.primary * 2,
      secondary: this.currentConfig.lineCount.secondary * 2,
      detail: this.currentConfig.lineCount.detail * 2
    };
    
    Object.entries(this.lines).forEach(([type, lines]) => {
      const maxCount = maxCounts[type as keyof typeof maxCounts];
      while (lines.length > maxCount) {
        const line = lines.shift();
        if (line) {
          this.scene.remove(line.line);
          line.dispose();
        }
      }
    });
  }
  
  public updateConfig(newConfig: any): void {
    this.currentConfig = this.deepMerge(this.currentConfig, newConfig);
    
    if (newConfig.colors) {
      this.initializeColorPalette();
      this.updateLineColors();
      
      if (newConfig.colors.background && this.backgroundMesh) {
        (this.backgroundMesh.material as THREE.MeshBasicMaterial).color.set(newConfig.colors.background);
      }
    }
    
    if (newConfig.geometry) {
      this.updateLineGeometry();
    }
  }
  
  private updateLineColors(): void {
    Object.values(this.lines).flat().forEach((line, index) => {
      const colorIndex = index % this.colorPalette.length;
      line.setColor(this.colorPalette[colorIndex]);
    });
  }
  
  private updateLineGeometry(): void {
    Object.values(this.lines).flat().forEach(line => {
      line.material.linewidth = this.currentConfig.geometry.thickness;
    });
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
    // Limpiar todas las líneas
    Object.values(this.lines).flat().forEach(line => {
      this.scene.remove(line.line);
      line.dispose();
    });
    
    // Limpiar fondo
    if (this.backgroundMesh) {
      this.scene.remove(this.backgroundMesh);
      this.backgroundMesh.geometry.dispose();
      (this.backgroundMesh.material as THREE.Material).dispose();
    }
    
    // Limpiar arrays
    this.lines.primary = [];
    this.lines.secondary = [];
    this.lines.detail = [];
  }
}

// Función factory requerida
export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  config: PresetConfig,
  shaderCode?: string
): BasePreset {
  return new AbstractLinesPreset(scene, camera, renderer, config, shaderCode);
}