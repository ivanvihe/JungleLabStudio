import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

// Configuración del preset Plasma Ray
export const config: PresetConfig = {
  name: "Plasma Ray",
  description: "Rayos de plasma energéticos con efectos eléctricos y descargas dinámicas",
  author: "AudioVisualizer",
  version: "1.0.0",
  category: "energy",
  tags: ["plasma", "energy", "electric", "lightning", "rays", "power"],
  thumbnail: "plasma_ray_thumb.png",
  defaultConfig: {
    opacity: 1.0,
    fadeMs: 150,
    raySystem: {
      primaryRays: 12,
      secondaryRays: 24,
      branches: 48,
      maxLength: 4.0,
      thickness: 0.05
    },
    colors: {
      coreEnergy: "#00FFFF",
      plasmaBlue: "#0080FF",
      electricPurple: "#8000FF",
      highVoltage: "#FF00FF",
      discharge: "#FFFFFF",
      ambient: "#001122"
    },
    energy: {
      coreIntensity: 2.5,
      pulseFrequency: 8.0,
      dischargeRate: 0.6,
      fieldStrength: 1.8,
      volatility: 0.4,
      resonance: 1.2
    },
    lightning: {
      branchProbability: 0.3,
      segmentLength: 0.1,
      randomness: 0.4,
      fadeSpeed: 2.0,
      sparkIntensity: 1.5
    },
    effects: {
      enableDischarge: true,
      enableBranching: true,
      enableGlow: true,
      enableSpark: true,
      enableField: true,
      enableResonance: true
    },
    physics: {
      electricField: 1.0,
      magneticField: 0.5,
      conductivity: 0.8,
      resistance: 0.3
    }
  },
  controls: [
    {
      name: "energy.coreIntensity",
      type: "slider",
      label: "Intensidad del Núcleo",
      min: 0.5,
      max: 5.0,
      step: 0.1,
      default: 2.5
    },
    {
      name: "energy.pulseFrequency",
      type: "slider",
      label: "Frecuencia de Pulso",
      min: 1.0,
      max: 20.0,
      step: 0.5,
      default: 8.0
    },
    {
      name: "energy.dischargeRate",
      type: "slider",
      label: "Tasa de Descarga",
      min: 0.1,
      max: 2.0,
      step: 0.1,
      default: 0.6
    },
    {
      name: "lightning.branchProbability",
      type: "slider",
      label: "Probabilidad de Ramificación",
      min: 0.0,
      max: 1.0,
      step: 0.1,
      default: 0.3
    },
    {
      name: "lightning.randomness",
      type: "slider",
      label: "Aleatoriedad del Rayo",
      min: 0.0,
      max: 1.0,
      step: 0.1,
      default: 0.4
    },
    {
      name: "physics.electricField",
      type: "slider",
      label: "Campo Eléctrico",
      min: 0.0,
      max: 3.0,
      step: 0.1,
      default: 1.0
    },
    {
      name: "physics.conductivity",
      type: "slider",
      label: "Conductividad",
      min: 0.1,
      max: 2.0,
      step: 0.1,
      default: 0.8
    },
    {
      name: "effects.enableDischarge",
      type: "checkbox",
      label: "Descargas Eléctricas",
      default: true
    },
    {
      name: "effects.enableBranching",
      type: "checkbox",
      label: "Ramificación de Rayos",
      default: true
    },
    {
      name: "effects.enableGlow",
      type: "checkbox",
      label: "Efecto de Brillo",
      default: true
    },
    {
      name: "effects.enableSpark",
      type: "checkbox",
      label: "Chispas",
      default: true
    },
    {
      name: "colors.coreEnergy",
      type: "color",
      label: "Energía del Núcleo",
      default: "#00FFFF"
    },
    {
      name: "colors.plasmaBlue",
      type: "color",
      label: "Azul Plasma",
      default: "#0080FF"
    },
    {
      name: "colors.electricPurple",
      type: "color",
      label: "Púrpura Eléctrico",
      default: "#8000FF"
    },
    {
      name: "colors.highVoltage",
      type: "color",
      label: "Alta Tensión",
      default: "#FF00FF"
    }
  ],
  audioMapping: {
    low: {
      description: "Controla la intensidad del núcleo y campo base",
      frequency: "20-250 Hz",
      effect: "Energía fundamental y campo magnético base"
    },
    mid: {
      description: "Modula las descargas y ramificaciones",
      frequency: "250-4000 Hz",
      effect: "Actividad de rayos y patrones de descarga"
    },
    high: {
      description: "Desencadena chispas y efectos de alta frecuencia",
      frequency: "4000+ Hz",
      effect: "Chispas, resonancia y efectos de alta energía"
    }
  },
  performance: {
    complexity: "high",
    recommendedFPS: 60,
    gpuIntensive: true
  }
};

class PlasmaRay {
  points: THREE.Vector3[];
  line: THREE.Line;
  glowLine: THREE.Line;
  material: THREE.LineBasicMaterial;
  glowMaterial: THREE.LineBasicMaterial;
  
  energy: number = 1.0;
  lifespan: number;
  age: number = 0;
  thickness: number;
  
  voltage: number;
  current: number;
  resistance: number;
  
  branches: PlasmaRay[] = [];
  parent: PlasmaRay | null = null;
  
  constructor(
    startPoint: THREE.Vector3,
    endPoint: THREE.Vector3,
    energy: number,
    color: THREE.Color,
    thickness: number = 0.05
  ) {
    this.energy = energy;
    this.thickness = thickness;
    this.lifespan = 0.5 + Math.random() * 2.0;
    this.voltage = energy * 100;
    this.current = energy * 10;
    this.resistance = 0.1 + Math.random() * 0.2;
    
    this.points = this.generateLightningPath(startPoint, endPoint);
    this.createMeshes(color);
  }
  
  private generateLightningPath(start: THREE.Vector3, end: THREE.Vector3): THREE.Vector3[] {
    const points: THREE.Vector3[] = [];
    const segments = Math.floor(10 + Math.random() * 20);
    
    points.push(start.clone());
    
    for (let i = 1; i < segments; i++) {
      const t = i / segments;
      const basePoint = new THREE.Vector3().lerpVectors(start, end, t);
      
      const deviation = new THREE.Vector3(
        (Math.random() - 0.5) * 0.3,
        (Math.random() - 0.5) * 0.3,
        (Math.random() - 0.5) * 0.2
      );
      
      const deviationFactor = Math.sin(t * Math.PI) * this.energy;
      deviation.multiplyScalar(deviationFactor);
      
      basePoint.add(deviation);
      points.push(basePoint);
    }
    
    points.push(end.clone());
    return points;
  }
  
  private createMeshes(color: THREE.Color): void {
    const geometry = new THREE.BufferGeometry().setFromPoints(this.points);
    
    this.material = new THREE.LineBasicMaterial({
      color: color,
      transparent: true,
      opacity: 0.9,
      linewidth: this.thickness * 10
    });
    this.line = new THREE.Line(geometry, this.material);
    
    const glowGeometry = new THREE.BufferGeometry().setFromPoints(this.points);
    this.glowMaterial = new THREE.LineBasicMaterial({
      color: color.clone().multiplyScalar(0.5),
      transparent: true,
      opacity: 0.3,
      linewidth: this.thickness * 20
    });
    this.glowLine = new THREE.Line(glowGeometry, this.glowMaterial);
  }
  
  createBranch(config: any): PlasmaRay | null {
    if (!config.effects?.enableBranching) return null;
    
    const branchPoint = this.points[Math.floor(this.points.length * (0.3 + Math.random() * 0.4))];
    const direction = new THREE.Vector3(
      (Math.random() - 0.5) * 2,
      (Math.random() - 0.5) * 2,
      (Math.random() - 0.5) * 1
    ).normalize();
    
    const branchLength = 0.5 + Math.random() * 1.5;
    const endPoint = branchPoint.clone().add(direction.multiplyScalar(branchLength));
    
    const branchEnergy = this.energy * (0.3 + Math.random() * 0.4);
    const branchColor = this.material.color.clone().multiplyScalar(0.8);
    
    const branch = new PlasmaRay(branchPoint, endPoint, branchEnergy, branchColor, this.thickness * 0.7);
    branch.parent = this;
    
    return branch;
  }
  
  update(deltaTime: number, audioData: any, config: any, time: number): void {
    this.age += deltaTime;
    
    const audioIntensity = audioData.low * 0.3 + audioData.mid * 0.5 + audioData.high * 0.2;
    
    this.updateElectricalProperties(audioIntensity, config);
    
    const pulseFreq = config.energy?.pulseFrequency || 8.0;
    const pulse = Math.sin(time * pulseFreq + this.voltage * 0.1) * 0.5 + 0.5;
    
    const baseOpacity = Math.max(0, 1 - this.age / this.lifespan);
    const energyBoost = audioIntensity * (config.energy?.coreIntensity || 1.0);
    
    this.material.opacity = baseOpacity * (0.7 + pulse * 0.3) * energyBoost;
    this.glowMaterial.opacity = baseOpacity * 0.3 * energyBoost;
    
    if (config.effects?.enableDischarge && audioData.mid > 0.6) {
      this.regeneratePath();
    }
    
    this.updatePhysics(deltaTime, config);
  }
  
  private updateElectricalProperties(audioIntensity: number, config: any): void {
    this.current = this.voltage / this.resistance;
    this.energy = this.current * this.voltage * 0.01;
    
    this.voltage *= (1 + audioIntensity * 0.5);
    this.resistance *= config.physics?.resistance || 0.3;
  }
  
  private regeneratePath(): void {
    if (this.points.length < 2) return;
    
    const start = this.points[0];
    const end = this.points[this.points.length - 1];
    this.points = this.generateLightningPath(start, end);
    
    this.line.geometry.setFromPoints(this.points);
    this.glowLine.geometry.setFromPoints(this.points);
    this.line.geometry.attributes.position.needsUpdate = true;
    this.glowLine.geometry.attributes.position.needsUpdate = true;
  }
  
  private updatePhysics(deltaTime: number, config: any): void {
    const fieldStrength = config.physics?.electricField || 1.0;
    
    this.points.forEach((point, index) => {
      if (index === 0 || index === this.points.length - 1) return;
      
      const noise = new THREE.Vector3(
        (Math.random() - 0.5) * fieldStrength * 0.01,
        (Math.random() - 0.5) * fieldStrength * 0.01,
        (Math.random() - 0.5) * fieldStrength * 0.005
      );
      
      point.add(noise);
    });
  }
  
  isDead(): boolean {
    return this.age >= this.lifespan;
  }
  
  dispose(): void {
    this.line.geometry.dispose();
    this.material.dispose();
    this.glowLine.geometry.dispose();
    this.glowMaterial.dispose();
    
    this.branches.forEach(branch => branch.dispose());
  }
}

class SparkSystem {
  sparks: THREE.Points;
  positions: Float32Array;
  colors: Float32Array;
  sizes: Float32Array;
  velocities: Float32Array;
  lifetimes: Float32Array;
  
  constructor(count: number = 200) {
    const geometry = new THREE.BufferGeometry();
    
    this.positions = new Float32Array(count * 3);
    this.colors = new Float32Array(count * 3);
    this.sizes = new Float32Array(count);
    this.velocities = new Float32Array(count * 3);
    this.lifetimes = new Float32Array(count);
    
    this.initializeSparks(count);
    
    geometry.setAttribute('position', new THREE.BufferAttribute(this.positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(this.colors, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(this.sizes, 1));
    
    const material = new THREE.PointsMaterial({
      size: 0.1,
      transparent: true,
      opacity: 0.8,
      vertexColors: true,
      blending: THREE.AdditiveBlending
    });
    
    this.sparks = new THREE.Points(geometry, material);
  }
  
  private initializeSparks(count: number): void {
    for (let i = 0; i < count; i++) {
      this.resetSpark(i);
    }
  }
  
  private resetSpark(index: number): void {
    const i3 = index * 3;
    
    this.positions[i3] = (Math.random() - 0.5) * 0.5;
    this.positions[i3 + 1] = (Math.random() - 0.5) * 0.5;
    this.positions[i3 + 2] = (Math.random() - 0.5) * 0.3;
    
    this.velocities[i3] = (Math.random() - 0.5) * 0.2;
    this.velocities[i3 + 1] = (Math.random() - 0.5) * 0.2;
    this.velocities[i3 + 2] = (Math.random() - 0.5) * 0.1;
    
    const intensity = 0.5 + Math.random() * 0.5;
    this.colors[i3] = intensity;
    this.colors[i3 + 1] = intensity * 0.8;
    this.colors[i3 + 2] = 1.0;
    
    this.sizes[index] = Math.random() * 0.1 + 0.02;
    this.lifetimes[index] = Math.random() * 2 + 0.5;
  }
  
  update(deltaTime: number, audioIntensity: number, rayPositions: THREE.Vector3[]): void {
    for (let i = 0; i < this.lifetimes.length; i++) {
      const i3 = i * 3;
      
      this.positions[i3] += this.velocities[i3] * deltaTime;
      this.positions[i3 + 1] += this.velocities[i3 + 1] * deltaTime;
      this.positions[i3 + 2] += this.velocities[i3 + 2] * deltaTime;
      
      this.velocities[i3] *= 0.98;
      this.velocities[i3 + 1] *= 0.98;
      this.velocities[i3 + 2] *= 0.98;
      
      this.lifetimes[i] -= deltaTime;
      
      if (this.lifetimes[i] <= 0 || Math.random() < audioIntensity * 0.02) {
        if (rayPositions.length > 0 && Math.random() < 0.7) {
          const rayPos = rayPositions[Math.floor(Math.random() * rayPositions.length)];
          this.positions[i3] = rayPos.x + (Math.random() - 0.5) * 0.2;
          this.positions[i3 + 1] = rayPos.y + (Math.random() - 0.5) * 0.2;
          this.positions[i3 + 2] = rayPos.z + (Math.random() - 0.5) * 0.1;
        }
        
        this.resetSpark(i);
      }
    }
    
    this.sparks.geometry.attributes.position.needsUpdate = true;
    this.sparks.geometry.attributes.color.needsUpdate = true;
  }
  
  dispose(): void {
    this.sparks.geometry.dispose();
    (this.sparks.material as THREE.Material).dispose();
  }
}

class PlasmaCore {
  mesh: THREE.Mesh;
  glowMesh: THREE.Mesh;
  energy: number = 1.0;
  pulsePhase: number = 0;
  
  constructor(position: THREE.Vector3, size: number = 0.3) {
    const coreGeometry = new THREE.SphereGeometry(size, 16, 16);
    const coreMaterial = new THREE.MeshBasicMaterial({
      color: new THREE.Color("#00FFFF"),
      transparent: true,
      opacity: 0.9
    });
    
    this.mesh = new THREE.Mesh(coreGeometry, coreMaterial);
    this.mesh.position.copy(position);
    
    const glowGeometry = new THREE.SphereGeometry(size * 2, 16, 16);
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: new THREE.Color("#0080FF"),
      transparent: true,
      opacity: 0.3,
      side: THREE.BackSide
    });
    
    this.glowMesh = new THREE.Mesh(glowGeometry, glowMaterial);
    this.glowMesh.position.copy(position);
  }
  
  update(deltaTime: number, audioData: any, config: any, time: number): void {
    const audioIntensity = (audioData.low + audioData.mid + audioData.high) / 3;
    const coreIntensity = config.energy?.coreIntensity || 2.5;
    
    this.pulsePhase += deltaTime * (config.energy?.pulseFrequency || 8.0);
    const pulse = Math.sin(this.pulsePhase) * 0.5 + 0.5;
    
    const scale = 1 + (pulse * 0.3 + audioIntensity * 0.4) * coreIntensity;
    this.mesh.scale.setScalar(scale);
    
    const glowScale = scale * 1.5 * (1 + audioIntensity * 0.5);
    this.glowMesh.scale.setScalar(glowScale);
    
    const coreMaterial = this.mesh.material as THREE.MeshBasicMaterial;
    const glowMaterial = this.glowMesh.material as THREE.MeshBasicMaterial;
    
    coreMaterial.opacity = 0.7 + pulse * 0.3 + audioIntensity * 0.2;
    glowMaterial.opacity = (0.2 + audioIntensity * 0.3) * (0.5 + pulse * 0.5);
    
    this.mesh.rotation.x += deltaTime * 2;
    this.mesh.rotation.y += deltaTime * 1.5;
    this.glowMesh.rotation.x -= deltaTime * 1;
    this.glowMesh.rotation.z += deltaTime * 0.8;
  }
  
  dispose(): void {
    this.mesh.geometry.dispose();
    (this.mesh.material as THREE.Material).dispose();
    this.glowMesh.geometry.dispose();
    (this.glowMesh.material as THREE.Material).dispose();
  }
}

class PlasmaRayPreset extends BasePreset {
  private rays: PlasmaRay[] = [];
  private sparkSystem: SparkSystem;
  private plasmaCore: PlasmaCore;
  private fieldLines: THREE.Line[] = [];
  private currentConfig: any;
  private dischargeTimer: number = 0;
  private energyBuildup: number = 0;
  
  constructor(
    scene: THREE.Scene,
    camera: THREE.Camera,
    renderer: THREE.WebGLRenderer,
    config: PresetConfig,
    private shaderCode?: string
  ) {
    super(scene, camera, renderer, config);
    
    this.currentConfig = { ...config.defaultConfig };
    this.sparkSystem = new SparkSystem(300);
    this.plasmaCore = new PlasmaCore(new THREE.Vector3(0, 0, 0), 0.2);
  }
  
  public init(): void {
    this.scene.add(this.plasmaCore.mesh);
    this.scene.add(this.plasmaCore.glowMesh);
    this.scene.add(this.sparkSystem.sparks);
    this.createInitialRays();
    this.createEnergyField();
  }
  
  private createInitialRays(): void {
    const rayCount = this.currentConfig.raySystem.primaryRays;
    
    for (let i = 0; i < rayCount; i++) {
      this.createPrimaryRay();
    }
  }
  
  private createPrimaryRay(): void {
    const angle = Math.random() * Math.PI * 2;
    const elevation = (Math.random() - 0.5) * Math.PI * 0.5;
    const distance = 2 + Math.random() * 2;
    
    const startPoint = new THREE.Vector3(0, 0, 0);
    const endPoint = new THREE.Vector3(
      Math.cos(angle) * Math.cos(elevation) * distance,
      Math.sin(elevation) * distance,
      Math.sin(angle) * Math.cos(elevation) * distance
    );
    
    const energy = 0.5 + Math.random() * 1.5;
    const color = this.getEnergyColor(energy);
    
    const ray = new PlasmaRay(startPoint, endPoint, energy, color, this.currentConfig.raySystem.thickness);
    this.rays.push(ray);
    this.scene.add(ray.line);
    
    if (this.currentConfig.effects?.enableGlow) {
      this.scene.add(ray.glowLine);
    }
  }
  
  private getEnergyColor(energy: number): THREE.Color {
    const colors = this.currentConfig.colors;
    
    if (energy < 0.3) return new THREE.Color(colors.plasmaBlue);
    if (energy < 0.6) return new THREE.Color(colors.coreEnergy);
    if (energy < 0.9) return new THREE.Color(colors.electricPurple);
    return new THREE.Color(colors.highVoltage);
  }
  
  private createEnergyField(): void {
    if (!this.currentConfig.effects?.enableField) return;
    
    const fieldPoints = 20;
    for (let i = 0; i < fieldPoints; i++) {
      const angle = (i / fieldPoints) * Math.PI * 2;
      const radius = 3 + Math.sin(i * 0.7) * 0.5;
      
      const points = [
        new THREE.Vector3(0, 0, 0),
        new THREE.Vector3(
          Math.cos(angle) * radius,
          Math.sin(angle * 1.3) * 0.5,
          Math.sin(angle) * radius
        )
      ];
      
      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      const material = new THREE.LineBasicMaterial({
        color: new THREE.Color(this.currentConfig.colors.ambient),
        transparent: true,
        opacity: 0.1
      });
      
      const fieldLine = new THREE.Line(geometry, material);
      this.fieldLines.push(fieldLine);
      this.scene.add(fieldLine);
    }
  }
  
  public update(): void {
    const deltaTime = this.clock.getDelta();
    const time = this.clock.getElapsedTime();
    
    this.plasmaCore.update(deltaTime, this.audioData, this.currentConfig, time);
    
    this.energyBuildup += this.audioData.low * 0.02 + this.audioData.mid * 0.03 + this.audioData.high * 0.01;
    
    this.dischargeTimer += deltaTime;
    const dischargeRate = this.currentConfig.energy.dischargeRate;
    
    if (this.dischargeTimer > 1 / dischargeRate || this.energyBuildup > 1.0) {
      this.triggerDischarge();
      this.dischargeTimer = 0;
      this.energyBuildup = 0;
    }
    
    this.rays.forEach(ray => {
      ray.update(deltaTime, this.audioData, this.currentConfig, time);
      
      if (this.currentConfig.effects?.enableBranching && Math.random() < this.currentConfig.lightning.branchProbability * deltaTime) {
        const branch = ray.createBranch(this.currentConfig);
        if (branch) {
          ray.branches.push(branch);
          this.scene.add(branch.line);
          if (this.currentConfig.effects?.enableGlow) {
            this.scene.add(branch.glowLine);
          }
        }
      }
    });
    
    this.rays = this.rays.filter(ray => {
      if (ray.isDead()) {
        this.scene.remove(ray.line);
        this.scene.remove(ray.glowLine);
        ray.dispose();
        return false;
      }
      return true;
    });
    
    while (this.rays.length < this.currentConfig.raySystem.primaryRays / 2) {
      this.createPrimaryRay();
    }
    
    const rayPositions = this.rays.flatMap(ray => ray.points);
    const audioIntensity = (this.audioData.low + this.audioData.mid + this.audioData.high) / 3;
    this.sparkSystem.update(deltaTime, audioIntensity, rayPositions);
    
    this.updateEnergyField(time);
  }
  
  private triggerDischarge(): void {
    if (!this.currentConfig.effects?.enableDischarge) return;
    
    const dischargeCount = 2 + Math.floor(this.audioData.high * 4);
    
    for (let i = 0; i < dischargeCount; i++) {
      this.createPrimaryRay();
    }
    
    this.rays.forEach(ray => {
      ray.energy *= 1.5;
      ray.voltage *= 2.0;
    });
  }
  
  private updateEnergyField(time: number): void {
    this.fieldLines.forEach((fieldLine, index) => {
      const material = fieldLine.material as THREE.LineBasicMaterial;
      const audioIntensity = (this.audioData.low + this.audioData.mid + this.audioData.high) / 3;
      
      const pulse = Math.sin(time * 3 + index * 0.5) * 0.5 + 0.5;
      material.opacity = (0.05 + audioIntensity * 0.15) * pulse;
      
      fieldLine.rotation.y += 0.01;
    });
  }
  
  public updateConfig(newConfig: any): void {
    this.currentConfig = this.deepMerge(this.currentConfig, newConfig);
    
    if (newConfig.colors) {
      this.updateColors();
    }
    
    if (newConfig.effects) {
      this.updateEffects();
    }
  }
  
  private updateColors(): void {
    const coreMaterial = this.plasmaCore.mesh.material as THREE.MeshBasicMaterial;
    const glowMaterial = this.plasmaCore.glowMesh.material as THREE.MeshBasicMaterial;
    
    coreMaterial.color.set(this.currentConfig.colors.coreEnergy);
    glowMaterial.color.set(this.currentConfig.colors.plasmaBlue);
    
    this.rays.forEach(ray => {
      const newColor = this.getEnergyColor(ray.energy);
      ray.material.color.copy(newColor);
      ray.glowMaterial.color.copy(newColor.clone().multiplyScalar(0.5));
    });
  }
  
  private updateEffects(): void {
    this.rays.forEach(ray => {
      if (this.currentConfig.effects.enableGlow) {
        if (!this.scene.children.includes(ray.glowLine)) {
          this.scene.add(ray.glowLine);
        }
      } else {
        this.scene.remove(ray.glowLine);
      }
    });
    
    if (this.currentConfig.effects.enableSpark) {
      if (!this.scene.children.includes(this.sparkSystem.sparks)) {
        this.scene.add(this.sparkSystem.sparks);
      }
    } else {
      this.scene.remove(this.sparkSystem.sparks);
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
    // Limpiar rayos
    this.rays.forEach(ray => {
      this.scene.remove(ray.line);
      this.scene.remove(ray.glowLine);
      ray.dispose();
    });
    
    // Limpiar núcleo
    this.scene.remove(this.plasmaCore.mesh);
    this.scene.remove(this.plasmaCore.glowMesh);
    this.plasmaCore.dispose();
    
    // Limpiar chispas
    this.scene.remove(this.sparkSystem.sparks);
    this.sparkSystem.dispose();
    
    // Limpiar campo energético
    this.fieldLines.forEach(fieldLine => {
      this.scene.remove(fieldLine);
      fieldLine.geometry.dispose();
      (fieldLine.material as THREE.Material).dispose();
    });
    
    this.rays = [];
    this.fieldLines = [];
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  config: PresetConfig,
  shaderCode?: string
): BasePreset {
  return new PlasmaRayPreset(scene, camera, renderer, config, shaderCode);
}