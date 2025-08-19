import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

// Config embebido mejorado con controles de animación
export const config: PresetConfig = {
  name: "Neural Network",
  description: "Red neuronal dinámica con crecimiento orgánico, brillos y destellos para shows audiovisuales",
  author: "AudioVisualizer",
  version: "2.0.0",
  category: "abstract",
  tags: ["neural", "network", "ai", "organic", "growth", "glow", "particles"],
  thumbnail: "neural_network_thumb.png",
  defaultConfig: {
    opacity: 1.0,
    fadeMs: 200,
    nodeCount: {
      input: 6,
      hidden1: 12,
      hidden2: 8,
      output: 4
    },
    colors: {
      input: "#00FFFF",     // Cyan
      hidden1: "#FF6B6B",   // Coral
      hidden2: "#4ECDC4",   // Turquoise
      output: "#FFE66D",    // Yellow
      connections: "#64B5F6",
      particles: "#FFFFFF"
    },
    animation: {
      growthSpeed: 1.0,
      pulseIntensity: 2.0,
      sparkleFrequency: 0.8,
      connectionFlow: 1.5,
      networkExpansion: 0.5,
      glowIntensity: 1.2
    },
    effects: {
      enableGlow: true,
      enableSparkles: true,
      enableGrowth: true,
      enablePulse: true,
      enableFlow: true
    }
  },
  controls: [
    {
      name: "animation.growthSpeed",
      type: "slider",
      label: "Velocidad de Crecimiento",
      min: 0.1,
      max: 3.0,
      step: 0.1,
      default: 1.0
    },
    {
      name: "animation.pulseIntensity",
      type: "slider",
      label: "Intensidad de Pulso",
      min: 0.5,
      max: 5.0,
      step: 0.1,
      default: 2.0
    },
    {
      name: "animation.sparkleFrequency",
      type: "slider",
      label: "Frecuencia de Destellos",
      min: 0.1,
      max: 2.0,
      step: 0.1,
      default: 0.8
    },
    {
      name: "animation.connectionFlow",
      type: "slider",
      label: "Flujo de Conexiones",
      min: 0.2,
      max: 4.0,
      step: 0.1,
      default: 1.5
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
      name: "effects.enableGlow",
      type: "checkbox",
      label: "Efectos de Brillo",
      default: true
    },
    {
      name: "effects.enableSparkles",
      type: "checkbox",
      label: "Destellos",
      default: true
    },
    {
      name: "effects.enableGrowth",
      type: "checkbox",
      label: "Crecimiento Dinámico",
      default: true
    },
    {
      name: "colors.input",
      type: "color",
      label: "Color Nodos Entrada",
      default: "#00FFFF"
    },
    {
      name: "colors.hidden1",
      type: "color",
      label: "Color Capa Oculta 1",
      default: "#FF6B6B"
    },
    {
      name: "colors.hidden2",
      type: "color",
      label: "Color Capa Oculta 2",
      default: "#4ECDC4"
    },
    {
      name: "colors.output",
      type: "color",
      label: "Color Nodos Salida",
      default: "#FFE66D"
    }
  ],
  audioMapping: {
    low: {
      description: "Controla el crecimiento de la red y nodos de entrada",
      frequency: "20-250 Hz",
      effect: "Activación y expansión de nodos de entrada"
    },
    mid: {
      description: "Controla las capas ocultas y flujo de conexiones",
      frequency: "250-4000 Hz",
      effect: "Intensidad de procesamiento neuronal"
    },
    high: {
      description: "Controla destellos, brillos y nodos de salida",
      frequency: "4000+ Hz",
      effect: "Efectos visuales y activación de salida"
    }
  },
  performance: {
    complexity: "high",
    recommendedFPS: 60,
    gpuIntensive: true
  }
};

class NeuralNode {
  position: THREE.Vector3;
  targetPosition: THREE.Vector3;
  mesh: THREE.Mesh;
  glowMesh: THREE.Mesh;
  originalScale: number;
  activity: number = 0;
  targetActivity: number = 0;
  growthFactor: number = 0;
  sparkleTimer: number = 0;
  pulseOffset: number;

  constructor(position: THREE.Vector3, color: THREE.Color, size: number = 0.05) {
    this.targetPosition = position.clone();
    this.position = position.clone();
    this.originalScale = size;
    this.pulseOffset = Math.random() * Math.PI * 2;

    // Nodo principal
    const geometry = new THREE.SphereGeometry(size, 16, 16);
    const material = new THREE.MeshBasicMaterial({
      color: color,
      transparent: true,
      opacity: 0.8
    });
    this.mesh = new THREE.Mesh(geometry, material);
    this.mesh.position.copy(position);

    // Halo de brillo
    const glowGeometry = new THREE.SphereGeometry(size * 2, 16, 16);
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: color,
      transparent: true,
      opacity: 0.2,
      side: THREE.BackSide
    });
    this.glowMesh = new THREE.Mesh(glowGeometry, glowMaterial);
    this.glowMesh.position.copy(position);
    this.glowMesh.scale.setScalar(0);
  }

  update(
    deltaTime: number,
    targetActivity: number,
    audioIntensity: number,
    globalOpacity: number,
    config: any,
    time: number
  ) {
    this.targetActivity = targetActivity * audioIntensity;
    this.activity += (this.targetActivity - this.activity) * deltaTime * 5;

    // Crecimiento orgánico
    if (config.effects?.enableGrowth) {
      this.growthFactor += deltaTime * (config.animation?.growthSpeed ?? 1.0) * audioIntensity;
      this.growthFactor = Math.min(this.growthFactor, 1);
    } else {
      this.growthFactor = 1;
    }

    // Pulso base
    const pulseSpeed = config.animation?.pulseIntensity ?? 2.0;
    const pulse = config.effects?.enablePulse
      ? 0.8 + 0.4 * Math.sin(time * pulseSpeed + this.pulseOffset + this.activity * 5)
      : 1.0;

    // Escala con crecimiento y pulso
    const scale = this.originalScale * this.growthFactor * (1 + this.activity * 0.6) * pulse;
    this.mesh.scale.setScalar(scale);

    // Destellos aleatorios
    let sparkle = 1.0;
    if (config.effects?.enableSparkles) {
      this.sparkleTimer += deltaTime * (config.animation?.sparkleFrequency ?? 0.8);
      if (this.sparkleTimer > 1 && Math.random() < 0.02) {
        this.sparkleTimer = 0;
      }
      sparkle = this.sparkleTimer < 0.2 ? 1 + Math.sin(this.sparkleTimer * Math.PI * 5) * 2 : 1.0;
    }

    // Material principal
    (this.mesh.material as THREE.MeshBasicMaterial).opacity =
      (0.6 + this.activity * 0.4) * globalOpacity * sparkle;

    // Halo de brillo
    if (config.effects?.enableGlow) {
      const glowIntensity = config.animation?.glowIntensity ?? 1.2;
      const glowScale = scale * 1.5 * (1 + this.activity * glowIntensity);
      this.glowMesh.scale.setScalar(glowScale);
      (this.glowMesh.material as THREE.MeshBasicMaterial).opacity =
        this.activity * 0.3 * globalOpacity * sparkle;
    } else {
      this.glowMesh.scale.setScalar(0);
    }

    // Movimiento orgánico sutil
    const offset = new THREE.Vector3(
      Math.sin(time * 0.5 + this.pulseOffset) * 0.02,
      Math.cos(time * 0.7 + this.pulseOffset) * 0.02,
      Math.sin(time * 0.3 + this.pulseOffset) * 0.01
    );

    this.mesh.position.copy(this.targetPosition).add(offset.multiplyScalar(this.activity));
    this.glowMesh.position.copy(this.mesh.position);
  }
}

class NeuralConnection {
  line: THREE.Line;
  material: THREE.LineBasicMaterial;
  startNode: NeuralNode;
  endNode: NeuralNode;
  strength: number = 0;
  targetStrength: number = 0;
  flowOffset: number;
  growthProgress: number = 0;
  pulseTrail: number[] = [];

  constructor(startNode: NeuralNode, endNode: NeuralNode, color: THREE.Color) {
    this.startNode = startNode;
    this.endNode = endNode;
    this.flowOffset = Math.random() * Math.PI * 2;

    // Crear línea con múltiples puntos para efectos de flujo
    const points = this.createCurvedPath(startNode.position, endNode.position);
    const geometry = new THREE.BufferGeometry().setFromPoints(points);

    this.material = new THREE.LineBasicMaterial({
      color: color,
      transparent: true,
      opacity: 0.3,
      linewidth: 2
    });

    this.line = new THREE.Line(geometry, this.material);

    // Inicializar trail de pulsos
    this.pulseTrail = new Array(10).fill(0);
  }

  private createCurvedPath(start: THREE.Vector3, end: THREE.Vector3): THREE.Vector3[] {
    const points: THREE.Vector3[] = [];
    const segments = 20;

    // Crear curva ligeramente ondulada
    for (let i = 0; i <= segments; i++) {
      const t = i / segments;
      const point = new THREE.Vector3().lerpVectors(start, end, t);

      // Añadir ondulación sutil
      const bend = Math.sin(t * Math.PI) * 0.1;
      point.y += bend * (Math.random() - 0.5) * 0.2;
      point.z += bend * (Math.random() - 0.5) * 0.1;

      points.push(point);
    }

    return points;
  }

  update(deltaTime: number, audioIntensity: number, globalOpacity: number, config: any, time: number) {
    this.targetStrength = audioIntensity * (0.3 + 0.7 * Math.sin(time * 0.5 + this.flowOffset));
    this.strength += (this.targetStrength - this.strength) * deltaTime * 3;

    // Crecimiento de conexión
    if (config.effects?.enableGrowth) {
      this.growthProgress += deltaTime * (config.animation?.growthSpeed ?? 1.0) * 0.5;
      this.growthProgress = Math.min(this.growthProgress, 1);
    } else {
      this.growthProgress = 1;
    }

    // Flujo de datos
    let flowIntensity = 1.0;
    if (config.effects?.enableFlow) {
      const flowSpeed = config.animation?.connectionFlow ?? 1.5;
      const flow = Math.sin(time * flowSpeed + this.flowOffset) * 0.5 + 0.5;
      flowIntensity = 0.4 + 0.6 * flow;

      // Actualizar trail de pulsos
      for (let i = this.pulseTrail.length - 1; i > 0; i--) {
        this.pulseTrail[i] = this.pulseTrail[i - 1];
      }
      this.pulseTrail[0] = flow > 0.8 ? 1.0 : 0.0;
    }

    // Opacidad final
    const finalOpacity = this.strength * this.growthProgress * flowIntensity * globalOpacity;
    this.material.opacity = Math.max(0.1, finalOpacity);

    // Color pulsante
    const pulseColor = new THREE.Color().copy(this.material.color);
    pulseColor.multiplyScalar(1 + this.strength * 0.5);
    this.material.color.copy(pulseColor);
  }
}

class ParticleSystem {
  particles: THREE.Points;
  positions: Float32Array;
  colors: Float32Array;
  sizes: Float32Array;
  velocities: Float32Array;
  lifetimes: Float32Array;

  constructor(count: number = 100) {
    const geometry = new THREE.BufferGeometry();

    this.positions = new Float32Array(count * 3);
    this.colors = new Float32Array(count * 3);
    this.sizes = new Float32Array(count);
    this.velocities = new Float32Array(count * 3);
    this.lifetimes = new Float32Array(count);

    // Inicializar partículas
    for (let i = 0; i < count; i++) {
      this.resetParticle(i);
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(this.positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(this.colors, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(this.sizes, 1));

    const material = new THREE.PointsMaterial({
      size: 0.05,
      transparent: true,
      opacity: 0.8,
      vertexColors: true,
      blending: THREE.AdditiveBlending
    });

    this.particles = new THREE.Points(geometry, material);
  }

  private resetParticle(index: number) {
    const i3 = index * 3;

    // Posición aleatoria
    this.positions[i3] = (Math.random() - 0.5) * 6;
    this.positions[i3 + 1] = (Math.random() - 0.5) * 4;
    this.positions[i3 + 2] = (Math.random() - 0.5) * 2;

    // Velocidad aleatoria
    this.velocities[i3] = (Math.random() - 0.5) * 0.02;
    this.velocities[i3 + 1] = (Math.random() - 0.5) * 0.02;
    this.velocities[i3 + 2] = (Math.random() - 0.5) * 0.01;

    // Color aleatorio
    const hue = Math.random();
    const color = new THREE.Color().setHSL(hue, 0.8, 0.6);
    this.colors[i3] = color.r;
    this.colors[i3 + 1] = color.g;
    this.colors[i3 + 2] = color.b;

    // Tamaño y vida
    this.sizes[index] = Math.random() * 0.05 + 0.01;
    this.lifetimes[index] = Math.random() * 5 + 2;
  }

  update(deltaTime: number, audioIntensity: number) {
    for (let i = 0; i < this.lifetimes.length; i++) {
      const i3 = i * 3;

      // Actualizar posición
      this.positions[i3] += this.velocities[i3] * audioIntensity;
      this.positions[i3 + 1] += this.velocities[i3 + 1] * audioIntensity;
      this.positions[i3 + 2] += this.velocities[i3 + 2] * audioIntensity;

      // Actualizar vida
      this.lifetimes[i] -= deltaTime;

      if (this.lifetimes[i] <= 0) {
        this.resetParticle(i);
      }
    }

    // Actualizar atributos
    this.particles.geometry.attributes.position.needsUpdate = true;
    this.particles.geometry.attributes.color.needsUpdate = true;
  }
}

class NeuralNetworkPreset extends BasePreset {
  private nodes: {
    input: NeuralNode[];
    hidden1: NeuralNode[];
    hidden2: NeuralNode[];
    output: NeuralNode[];
  };

  private connections: {
    inputToHidden1: NeuralConnection[];
    hidden1ToHidden2: NeuralConnection[];
    hidden2ToOutput: NeuralConnection[];
  };

  private particleSystem: ParticleSystem;
  private gridHelper!: THREE.GridHelper;
  private currentConfig: any;

  constructor(
    scene: THREE.Scene,
    camera: THREE.Camera,
    renderer: THREE.WebGLRenderer,
    config: PresetConfig,
    private shaderCode?: string
  ) {
    super(scene, camera, renderer, config);

    this.nodes = {
      input: [],
      hidden1: [],
      hidden2: [],
      output: []
    };

    this.connections = {
      inputToHidden1: [],
      hidden1ToHidden2: [],
      hidden2ToOutput: []
    };

    this.currentConfig = { ...config.defaultConfig };
    this.particleSystem = new ParticleSystem(150);
  }

  public init(): void {
    this.createNodes();
    this.createConnections();
    this.addParticleSystem();
    this.addGridBackground();
  }

  private createNodes(): void {
    const nodeConfig = this.currentConfig.nodeCount;
    const colors = this.currentConfig.colors;

    // Input layer - disposición más orgánica
    for (let i = 0; i < nodeConfig.input; i++) {
      const angle = (i / nodeConfig.input) * Math.PI * 2;
      const radius = 0.3;
      const x = -2.5 + Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius;
      const z = (Math.random() - 0.5) * 0.2;

      const node = new NeuralNode(
        new THREE.Vector3(x, y, z),
        new THREE.Color(colors.input),
        0.06
      );
      this.nodes.input.push(node);
      this.scene.add(node.mesh);
      this.scene.add(node.glowMesh);
    }

    // Hidden layer 1 - formación más densa
    for (let i = 0; i < nodeConfig.hidden1; i++) {
      const rows = Math.ceil(Math.sqrt(nodeConfig.hidden1));
      const row = Math.floor(i / rows);
      const col = i % rows;
      const x = -0.8;
      const y = (row - (rows - 1) / 2) * 0.4 + (Math.random() - 0.5) * 0.1;
      const z = (col - (rows - 1) / 2) * 0.3 + (Math.random() - 0.5) * 0.1;

      const node = new NeuralNode(
        new THREE.Vector3(x, y, z),
        new THREE.Color(colors.hidden1),
        0.05
      );
      this.nodes.hidden1.push(node);
      this.scene.add(node.mesh);
      this.scene.add(node.glowMesh);
    }

    // Hidden layer 2
    for (let i = 0; i < nodeConfig.hidden2; i++) {
      const y = (i - (nodeConfig.hidden2 - 1) / 2) * 0.35 + (Math.random() - 0.5) * 0.1;
      const z = (Math.random() - 0.5) * 0.3;

      const node = new NeuralNode(
        new THREE.Vector3(0.8, y, z),
        new THREE.Color(colors.hidden2),
        0.055
      );
      this.nodes.hidden2.push(node);
      this.scene.add(node.mesh);
      this.scene.add(node.glowMesh);
    }

    // Output layer - formación en estrella
    for (let i = 0; i < nodeConfig.output; i++) {
      const angle = (i / nodeConfig.output) * Math.PI * 2;
      const radius = 0.25;
      const x = 2.5 + Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius;
      const z = (Math.random() - 0.5) * 0.15;

      const node = new NeuralNode(
        new THREE.Vector3(x, y, z),
        new THREE.Color(colors.output),
        0.07
      );
      this.nodes.output.push(node);
      this.scene.add(node.mesh);
      this.scene.add(node.glowMesh);
    }
  }

  private createConnections(): void {
    const colors = this.currentConfig.colors;

    // Input to Hidden1
    this.nodes.input.forEach(inputNode => {
      this.nodes.hidden1.forEach(hidden1Node => {
        const connection = new NeuralConnection(
          inputNode,
          hidden1Node,
          new THREE.Color(colors.connections)
        );
        this.connections.inputToHidden1.push(connection);
        this.scene.add(connection.line);
      });
    });

    // Hidden1 to Hidden2
    this.nodes.hidden1.forEach(hidden1Node => {
      this.nodes.hidden2.forEach(hidden2Node => {
        const connection = new NeuralConnection(
          hidden1Node,
          hidden2Node,
          new THREE.Color(colors.connections)
        );
        this.connections.hidden1ToHidden2.push(connection);
        this.scene.add(connection.line);
      });
    });

    // Hidden2 to Output
    this.nodes.hidden2.forEach(hidden2Node => {
      this.nodes.output.forEach(outputNode => {
        const connection = new NeuralConnection(
          hidden2Node,
          outputNode,
          new THREE.Color(colors.connections)
        );
        this.connections.hidden2ToOutput.push(connection);
        this.scene.add(connection.line);
      });
    });
  }

  private addParticleSystem(): void {
    this.scene.add(this.particleSystem.particles);
  }

  private addGridBackground(): void {
    this.gridHelper = new THREE.GridHelper(8, 16, 0x333333, 0x333333) as THREE.GridHelper;
    this.gridHelper.rotateX(Math.PI / 2);
    (this.gridHelper.material as THREE.Material & { opacity: number; transparent: boolean }).opacity = 0.05;
    (this.gridHelper.material as THREE.Material & { opacity: number; transparent: boolean }).transparent = true;
    this.scene.add(this.gridHelper);
  }

  public update(): void {
    const deltaTime = this.clock.getDelta();
    const time = this.clock.getElapsedTime();

    // Intensidad de audio promedio
    const overallAudio = (this.audioData.low + this.audioData.mid + this.audioData.high) / 3;

    // Update input nodes
    this.nodes.input.forEach((node, index) => {
      const baseActivity = 0.3 + 0.7 * Math.sin(time * 1.5 + index * 0.5);
      node.update(deltaTime, baseActivity, this.audioData.low * 2, this.opacity, this.currentConfig, time);
    });

    // Update hidden1 nodes
    this.nodes.hidden1.forEach((node, index) => {
      const baseActivity = 0.2 + 0.8 * Math.sin(time * 1.2 + index * 0.3);
      node.update(deltaTime, baseActivity, this.audioData.mid * 1.5, this.opacity, this.currentConfig, time);
    });

    // Update hidden2 nodes
    this.nodes.hidden2.forEach((node, index) => {
      const baseActivity = 0.25 + 0.75 * Math.sin(time * 1.8 + index * 0.4);
      node.update(deltaTime, baseActivity, this.audioData.mid * 1.8, this.opacity, this.currentConfig, time);
    });

    // Update output nodes
    this.nodes.output.forEach((node, index) => {
      const baseActivity = 0.4 + 0.6 * Math.sin(time * 2.2 + index * 0.6);
      node.update(deltaTime, baseActivity, this.audioData.high * 2.5, this.opacity, this.currentConfig, time);
    });

    // Update connections
    this.connections.inputToHidden1.forEach(connection => {
      connection.update(deltaTime, this.audioData.low * 1.5, this.opacity, this.currentConfig, time);
    });

    this.connections.hidden1ToHidden2.forEach(connection => {
      connection.update(deltaTime, this.audioData.mid * 1.8, this.opacity, this.currentConfig, time);
    });

    this.connections.hidden2ToOutput.forEach(connection => {
      connection.update(deltaTime, this.audioData.high * 2.0, this.opacity, this.currentConfig, time);
    });

    // Update particle system
    this.particleSystem.update(deltaTime, overallAudio * 2);

    // Update grid
    if (this.gridHelper) {
      (this.gridHelper.material as THREE.Material & { opacity: number }).opacity = (0.05 + overallAudio * 0.1) * this.opacity;
    }
  }

  public updateConfig(newConfig: any): void {
    this.currentConfig = this.deepMerge(this.currentConfig, newConfig);

    if (newConfig.colors) {
      this.updateColors(newConfig.colors);
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

  private updateColors(colors: any): void {
    // Update node colors
    if (colors.input) {
      this.nodes.input.forEach(node => {
        const color = new THREE.Color(colors.input);
        (node.mesh.material as THREE.MeshBasicMaterial).color.copy(color);
        (node.glowMesh.material as THREE.MeshBasicMaterial).color.copy(color);
      });
    }

    if (colors.hidden1) {
      this.nodes.hidden1.forEach(node => {
        const color = new THREE.Color(colors.hidden1);
        (node.mesh.material as THREE.MeshBasicMaterial).color.copy(color);
        (node.glowMesh.material as THREE.MeshBasicMaterial).color.copy(color);
      });
    }

    if (colors.hidden2) {
      this.nodes.hidden2.forEach(node => {
        const color = new THREE.Color(colors.hidden2);
        (node.mesh.material as THREE.MeshBasicMaterial).color.copy(color);
        (node.glowMesh.material as THREE.MeshBasicMaterial).color.copy(color);
      });
    }

    if (colors.output) {
      this.nodes.output.forEach(node => {
        const color = new THREE.Color(colors.output);
        (node.mesh.material as THREE.MeshBasicMaterial).color.copy(color);
        (node.glowMesh.material as THREE.MeshBasicMaterial).color.copy(color);
      });
    }

    if (colors.connections) {
      [
        ...this.connections.inputToHidden1,
        ...this.connections.hidden1ToHidden2,
        ...this.connections.hidden2ToOutput,
      ].forEach(connection => {
        connection.material.color.set(colors.connections);
      });
    }
  }

  public dispose(): void {
    // Remove nodes and glow effects
    [
      ...this.nodes.input,
      ...this.nodes.hidden1,
      ...this.nodes.hidden2,
      ...this.nodes.output
    ].forEach(node => {
      this.scene.remove(node.mesh);
      this.scene.remove(node.glowMesh);

      node.mesh.geometry.dispose();
      (node.mesh.material as THREE.Material).dispose();

      node.glowMesh.geometry.dispose();
      (node.glowMesh.material as THREE.Material).dispose();
    });

    // Remove connections
    [
      ...this.connections.inputToHidden1,
      ...this.connections.hidden1ToHidden2,
      ...this.connections.hidden2ToOutput
    ].forEach(connection => {
      this.scene.remove(connection.line);
      connection.line.geometry.dispose();
      connection.material.dispose();
    });

    // Remove particles
    if (this.particleSystem?.particles) {
      this.scene.remove(this.particleSystem.particles);
      this.particleSystem.particles.geometry.dispose();
      (this.particleSystem.particles.material as THREE.Material).dispose();
    }

    // Remove grid
    if (this.gridHelper) {
      this.scene.remove(this.gridHelper);
      this.gridHelper.geometry.dispose();
      (this.gridHelper.material as THREE.Material).dispose();
    }
  }
}

// Exportar la función factory requerida
export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  config: PresetConfig,
  shaderCode?: string
): BasePreset {
  return new NeuralNetworkPreset(scene, camera, renderer, config, shaderCode);
}
