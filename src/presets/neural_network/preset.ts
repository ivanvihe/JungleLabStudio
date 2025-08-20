import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: "Neural Network Genesis",
  description: "Viaje interestelar a través de una red neuronal con algoritmos reales, propagación y morfología adaptativa",
  author: "AudioVisualizer Pro",
  version: "3.0.0",
  category: "ai",
  tags: ["neural", "ai", "network", "propagation", "adaptive", "professional"],
  thumbnail: "neural_network_genesis_thumb.png",
  defaultConfig: {
    opacity: 1.0,
    fadeMs: 150,
    topology: {
      layers: [16, 32, 48, 32, 16, 8],
      activationFunction: "sigmoid",
      learningRate: 0.01,
      momentum: 0.9
    },
    visualization: {
      nodeSize: 0.08,
      connectionThickness: 1.5,
      activationIntensity: 2.0,
      propagationSpeed: 2.0,
      morphologyRate: 0.6
    },
    colors: {
      input: "#A0C4FF",
      hidden: "#BDB2FF",
      output: "#FFAFCC",
      connection: "#CDB4DB",
      activation: "#FFE5EC"
    },
    performance: {
      maxConnections: 5000,
      updateFrequency: 60,
      cullingThreshold: 0.1
    }
  },
  controls: [
    {
      name: "topology.learningRate",
      type: "slider",
      label: "Tasa de Aprendizaje",
      min: 0.001,
      max: 0.1,
      step: 0.001,
      default: 0.01
    },
    {
      name: "visualization.propagationSpeed",
      type: "slider",
      label: "Velocidad de Propagación",
      min: 1.0,
      max: 15.0,
      step: 0.5,
      default: 5.0
    },
    {
      name: "visualization.morphologyRate",
      type: "slider",
      label: "Velocidad de Morfología",
      min: 0.1,
      max: 3.0,
      step: 0.1,
      default: 1.2
    }
  ],
  audioMapping: {
    low: {
      description: "Controla entrada y activación de capas input",
      frequency: "20-250 Hz",
      effect: "Señales de entrada y activación basal"
    },
    mid: {
      description: "Modula capas ocultas y propagación",
      frequency: "250-4000 Hz", 
      effect: "Procesamiento neuronal y backpropagation"
    },
    high: {
      description: "Controla capas de salida y morfología",
      frequency: "4000+ Hz",
      effect: "Salidas especializadas y adaptación estructural"
    }
  },
  performance: {
    complexity: "high",
    recommendedFPS: 60,
    gpuIntensive: true
  }
};

// Funciones de activación neuronales reales
class ActivationFunctions {
  static sigmoid(x: number): number {
    return 1 / (1 + Math.exp(-x));
  }
  
  static sigmoidDerivative(x: number): number {
    const s = this.sigmoid(x);
    return s * (1 - s);
  }
  
  static tanh(x: number): number {
    return Math.tanh(x);
  }
  
  static tanhDerivative(x: number): number {
    const t = Math.tanh(x);
    return 1 - t * t;
  }
  
  static relu(x: number): number {
    return Math.max(0, x);
  }
  
  static reluDerivative(x: number): number {
    return x > 0 ? 1 : 0;
  }
}

// Controla el movimiento de cámara simulando un viaje interestelar a través de la red
class InterstellarNavigator {
  private originalPosition: THREE.Vector3 = new THREE.Vector3();
  private startX: number;
  private endX: number;
  private speed = 1.5;

  constructor(
    private camera: THREE.Camera,
    networkWidth: number,
    private onLoop?: () => void
  ) {
    this.originalPosition.copy(camera.position);
    this.startX = -networkWidth / 2;
    this.endX = networkWidth / 2;
    // Start the camera inside the network to immediately navigate through nodes
    this.camera.position.set(0, 0, 0);
    this.camera.lookAt(1, 0, 0);
  }

  update(delta: number, intensity: number): void {
    this.camera.position.x += delta * this.speed * (0.5 + intensity);
    this.camera.lookAt(this.camera.position.x + 1, 0, 0);

    if (this.camera.position.x > this.endX) {
      this.camera.position.x = this.startX;
      this.onLoop?.();
    }
  }

  dispose(): void {
    this.camera.position.copy(this.originalPosition);
    this.camera.lookAt(0, 0, 0);
  }
}

// Neurona con comportamiento realista
class Neuron {
  public activation: number = 0;
  public rawInput: number = 0;
  public bias: number = Math.random() * 0.2 - 0.1;
  public error: number = 0;
  public position: THREE.Vector3;
  public targetPosition: THREE.Vector3;
  
  private mesh: THREE.Mesh;
  private glowMesh: THREE.Mesh;
  private material: THREE.ShaderMaterial;
  private glowMaterial: THREE.ShaderMaterial;
  
  public connections: NeuralConnection[] = [];
  public morphologyTimer: number = 0;
  public adaptationRate: number = 0.8 + Math.random() * 0.4;
  
  constructor(position: THREE.Vector3, color: THREE.Color, size: number = 0.08) {
    this.position = position.clone();
    this.targetPosition = position.clone();
    this.createVisualization(color, size);
  }
  
  private createVisualization(color: THREE.Color, size: number): void {
    // Geometría principal
    const geometry = new THREE.SphereGeometry(size, 16, 16);
    
    this.material = new THREE.ShaderMaterial({
      transparent: true,
      vertexShader: `
        varying vec3 vPosition;
        varying vec3 vNormal;
        uniform float uActivation;
        uniform float uTime;
        
        void main() {
          vPosition = position;
          vNormal = normal;
          
          vec3 pos = position;
          
          // Pulsación basada en activación
          float pulse = 1.0 + uActivation * sin(uTime * 10.0) * 0.3;
          pos *= pulse;
          
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        varying vec3 vPosition;
        varying vec3 vNormal;
        uniform vec3 uColor;
        uniform float uActivation;
        uniform float uOpacity;
        uniform float uTime;
        
        void main() {
          // Color base
          vec3 baseColor = uColor;
          
          // Intensidad basada en activación
          float intensity = 0.3 + uActivation * 1.5;
          
          // Efectos de superficie neuronal
          float surface = dot(normalize(vNormal), vec3(0.0, 0.0, 1.0));
          surface = pow(abs(surface), 0.5);
          
          // Actividad eléctrica
          float electrical = sin(vPosition.x * 20.0 + uTime * 15.0) * 
                           cos(vPosition.y * 18.0 + uTime * 12.0) * 0.1 + 0.9;
          
          vec3 finalColor = baseColor * intensity * surface * electrical;
          
          gl_FragColor = vec4(finalColor, intensity * uOpacity);
        }
      `,
      uniforms: {
        uColor: { value: color },
        uActivation: { value: 0.0 },
        uOpacity: { value: 1.0 },
        uTime: { value: 0.0 }
      }
    });
    
    this.mesh = new THREE.Mesh(geometry, this.material);
    this.mesh.position.copy(this.position);
    
    // Halo de activación
    const glowGeometry = new THREE.SphereGeometry(size * 2, 12, 12);
    this.glowMaterial = new THREE.ShaderMaterial({
      transparent: true,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      vertexShader: `
        varying float vIntensity;
        uniform float uActivation;
        
        void main() {
          vec3 vNormal = normalize(normalMatrix * normal);
          vec3 vNormel = normalize(normalMatrix * position);
          vIntensity = pow(0.7 - dot(vNormal, vNormel), 2.0) * uActivation;
          
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        varying float vIntensity;
        uniform vec3 uColor;
        uniform float uOpacity;
        
        void main() {
          vec3 glow = uColor * vIntensity;
          gl_FragColor = vec4(glow, vIntensity * 0.6 * uOpacity);
        }
      `,
      uniforms: {
        uColor: { value: color },
        uActivation: { value: 0.0 },
        uOpacity: { value: 1.0 }
      }
    });
    
    this.glowMesh = new THREE.Mesh(glowGeometry, this.glowMaterial);
    this.glowMesh.position.copy(this.position);
  }
  
  // Procesamiento neuronal real
  public processInput(inputs: number[], weights: number[]): number {
    this.rawInput = this.bias;
    
    for (let i = 0; i < inputs.length; i++) {
      this.rawInput += inputs[i] * weights[i];
    }
    
    this.activation = ActivationFunctions.sigmoid(this.rawInput);
    return this.activation;
  }
  
  // Backpropagation
  public calculateError(target?: number, nextLayerErrors?: number[], nextLayerWeights?: number[][]): void {
    if (target !== undefined) {
      // Neurona de salida
      this.error = (target - this.activation) * ActivationFunctions.sigmoidDerivative(this.rawInput);
    } else if (nextLayerErrors && nextLayerWeights) {
      // Neurona oculta
      let weightedSum = 0;
      for (let i = 0; i < nextLayerErrors.length; i++) {
        weightedSum += nextLayerErrors[i] * nextLayerWeights[i][this.connections.length];
      }
      this.error = weightedSum * ActivationFunctions.sigmoidDerivative(this.rawInput);
    }
  }
  
  // Morfología adaptativa
  public updateMorphology(deltaTime: number, audioIntensity: number, config: any): void {
    this.morphologyTimer += deltaTime * config.visualization.morphologyRate;
    
    // Adaptación posicional basada en activación
    const adaptationForce = new THREE.Vector3(
      Math.sin(this.morphologyTimer + this.activation * 5) * 0.01,
      Math.cos(this.morphologyTimer * 1.3 + this.activation * 3) * 0.01,
      Math.sin(this.morphologyTimer * 0.7) * 0.005
    );
    
    adaptationForce.multiplyScalar(this.activation * audioIntensity * this.adaptationRate);
    this.targetPosition.add(adaptationForce);
    
    // Constraint bounds
    this.targetPosition.x = Math.max(-4, Math.min(4, this.targetPosition.x));
    this.targetPosition.y = Math.max(-2, Math.min(2, this.targetPosition.y));
    this.targetPosition.z = Math.max(-1, Math.min(1, this.targetPosition.z));
    
    // Suavizado posicional
    this.position.lerp(this.targetPosition, deltaTime * 2);
    this.mesh.position.copy(this.position);
    this.glowMesh.position.copy(this.position);
  }
  
  public update(deltaTime: number, time: number, globalOpacity: number): void {
    // Actualizar uniforms
    this.material.uniforms.uActivation.value = this.activation;
    this.material.uniforms.uOpacity.value = globalOpacity;
    this.material.uniforms.uTime.value = time;
    
    this.glowMaterial.uniforms.uActivation.value = this.activation;
    this.glowMaterial.uniforms.uOpacity.value = globalOpacity;
    
    // Rotación sutil
    this.mesh.rotation.x += deltaTime * this.activation * 0.5;
    this.mesh.rotation.y += deltaTime * this.activation * 0.3;
  }
  
  public getMeshes(): THREE.Mesh[] {
    return [this.mesh, this.glowMesh];
  }
  
  public dispose(): void {
    this.mesh.geometry.dispose();
    this.material.dispose();
    this.glowMesh.geometry.dispose();
    this.glowMaterial.dispose();
  }
}

// Conexión sináptica con propagación real
class NeuralConnection {
  public weight: number;
  public deltaWeight: number = 0;
  public signalStrength: number = 0;
  public propagationProgress: number = 0;
  
  private line: THREE.Line;
  private material: THREE.ShaderMaterial;
  private signalMesh: THREE.Mesh;
  private signalMaterial: THREE.ShaderMaterial;
  
  constructor(
    public fromNeuron: Neuron,
    public toNeuron: Neuron,
    color: THREE.Color
  ) {
    this.weight = (Math.random() - 0.5) * 2;
    this.createVisualization(color);
  }
  
  private createVisualization(color: THREE.Color): void {
    // Línea de conexión
    const points = [this.fromNeuron.position, this.toNeuron.position];
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    
    this.material = new THREE.ShaderMaterial({
      transparent: true,
      vertexShader: `
        varying vec2 vUv;
        uniform float uSignalProgress;
        uniform float uWeight;
        
        void main() {
          vUv = uv;
          
          vec3 pos = position;
          
          // Grosor basado en peso
          float thickness = abs(uWeight) * 0.01;
          pos += normal * thickness;
          
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        varying vec2 vUv;
        uniform vec3 uColor;
        uniform float uSignalProgress;
        uniform float uWeight;
        uniform float uOpacity;
        uniform float uTime;
        
        void main() {
          // Color base de la conexión
          vec3 baseColor = uColor;
          
          // Intensidad basada en peso
          float intensity = abs(uWeight) * 0.5 + 0.2;
          
          // Señal propagándose
          float signal = exp(-abs(vUv.x - uSignalProgress) * 10.0) * 2.0;
          
          // Pulso eléctrico
          float pulse = sin(uTime * 8.0 + vUv.x * 20.0) * 0.2 + 0.8;
          
          vec3 finalColor = baseColor * (intensity + signal) * pulse;
          float alpha = (intensity + signal * 0.5) * uOpacity;
          
          gl_FragColor = vec4(finalColor, alpha);
        }
      `,
      uniforms: {
        uColor: { value: color },
        uSignalProgress: { value: 0.0 },
        uWeight: { value: this.weight },
        uOpacity: { value: 1.0 },
        uTime: { value: 0.0 }
      }
    });
    
    this.line = new THREE.Line(geometry, this.material);
    
    // Señal viajera
    const signalGeometry = new THREE.SphereGeometry(0.02, 8, 8);
    this.signalMaterial = new THREE.ShaderMaterial({
      transparent: true,
      blending: THREE.AdditiveBlending,
      vertexShader: `
        uniform float uIntensity;
        
        void main() {
          vec3 pos = position * (1.0 + uIntensity);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        uniform vec3 uColor;
        uniform float uIntensity;
        uniform float uOpacity;
        
        void main() {
          vec3 color = uColor * uIntensity;
          gl_FragColor = vec4(color, uIntensity * uOpacity);
        }
      `,
      uniforms: {
        uColor: { value: color },
        uIntensity: { value: 0.0 },
        uOpacity: { value: 1.0 }
      }
    });
    
    this.signalMesh = new THREE.Mesh(signalGeometry, this.signalMaterial);
  }
  
  // Propagación de señal sináptica
  public propagateSignal(inputSignal: number, propagationSpeed: number, deltaTime: number): void {
    this.signalStrength = inputSignal * Math.abs(this.weight);
    this.propagationProgress += deltaTime * propagationSpeed;
    
    if (this.propagationProgress > 1.0) {
      this.propagationProgress = 0.0;
    }
  }
  
  // Actualización de peso (aprendizaje)
  public updateWeight(learningRate: number, momentum: number): void {
    this.deltaWeight = momentum * this.deltaWeight + 
                     learningRate * this.toNeuron.error * this.fromNeuron.activation;
    this.weight += this.deltaWeight;
    
    // Constraint de peso
    this.weight = Math.max(-2, Math.min(2, this.weight));
  }
  
  public update(deltaTime: number, time: number, globalOpacity: number): void {
    // Actualizar posiciones de conexión
    const points = [this.fromNeuron.position, this.toNeuron.position];
    this.line.geometry.setFromPoints(points);
    this.line.geometry.attributes.position.needsUpdate = true;
    
    // Actualizar uniforms
    this.material.uniforms.uSignalProgress.value = this.propagationProgress;
    this.material.uniforms.uWeight.value = this.weight;
    this.material.uniforms.uOpacity.value = globalOpacity;
    this.material.uniforms.uTime.value = time;
    
    // Posición de señal viajera
    const signalPosition = new THREE.Vector3().lerpVectors(
      this.fromNeuron.position,
      this.toNeuron.position,
      this.propagationProgress
    );
    this.signalMesh.position.copy(signalPosition);
    
    this.signalMaterial.uniforms.uIntensity.value = this.signalStrength;
    this.signalMaterial.uniforms.uOpacity.value = globalOpacity;
  }
  
  public getMeshes(): THREE.Object3D[] {
    return [this.line, this.signalMesh];
  }
  
  public dispose(): void {
    this.line.geometry.dispose();
    this.material.dispose();
    this.signalMesh.geometry.dispose();
    this.signalMaterial.dispose();
  }
}

// Red neuronal completa
class NeuralNetworkGenesis extends BasePreset {
  private layers: Neuron[][] = [];
  private connections: NeuralConnection[] = [];
  private networkData: number[][] = [];
  private currentConfig: any;
  private learningPhase: number = 0;
  private frameCount: number = 0;
  private navigator: InterstellarNavigator;
  private frustum: THREE.Frustum = new THREE.Frustum();
  private viewProjectionMatrix: THREE.Matrix4 = new THREE.Matrix4();
  
  constructor(
    scene: THREE.Scene,
    camera: THREE.Camera,
    renderer: THREE.WebGLRenderer,
    config: PresetConfig
  ) {
    super(scene, camera, renderer, config);
    this.currentConfig = { ...config.defaultConfig };
    const spacing = 2.0;
    const networkWidth = this.currentConfig.topology.layers.length * spacing;
    this.navigator = new InterstellarNavigator(
      this.camera,
      networkWidth,
      () => this.regenerateNetwork()
    );
  }
  
  public init(): void {
    // Fondo completamente transparente
    this.renderer.setClearColor(0x000000, 0);
    
    this.createNetworkTopology();
    this.createConnections();
    this.addToScene();
  }
  
  private createNetworkTopology(): void {
    const topology = this.currentConfig.topology.layers;
    const colors = [
      new THREE.Color(this.currentConfig.colors.input),
      new THREE.Color(this.currentConfig.colors.hidden),
      new THREE.Color(this.currentConfig.colors.hidden),
      new THREE.Color(this.currentConfig.colors.hidden),
      new THREE.Color(this.currentConfig.colors.output)
    ];

    const spacing = 2.0;
    const radiusMul = 0.4;

    for (let layerIdx = 0; layerIdx < topology.length; layerIdx++) {
      const layer: Neuron[] = [];
      const nodeCount = topology[layerIdx];
      const color = colors[Math.min(layerIdx, colors.length - 1)];

      // Distribución espacial orgánica y aleatoria
      for (let nodeIdx = 0; nodeIdx < nodeCount; nodeIdx++) {
        let position: THREE.Vector3;

        if (nodeCount === 1) {
          position = new THREE.Vector3(
            (layerIdx - topology.length / 2) * spacing,
            0,
            0
          );
        } else {
          const angle = (nodeIdx / nodeCount) * Math.PI * 2;
          const radius = Math.sqrt(nodeCount) * radiusMul;

          position = new THREE.Vector3(
            (layerIdx - topology.length / 2) * spacing,
            Math.sin(angle) * radius,
            Math.cos(angle) * radius * 0.5
          );
        }

        position.add(new THREE.Vector3(
          (Math.random() - 0.5) * 0.5,
          (Math.random() - 0.5) * 0.5,
          (Math.random() - 0.5) * 0.5
        ));

        const neuron = new Neuron(position, color, this.currentConfig.visualization.nodeSize);
        layer.push(neuron);
      }

      this.layers.push(layer);
    }
  }
  
  private createConnections(): void {
    const connectionColor = new THREE.Color(this.currentConfig.colors.connection);
    
    for (let layerIdx = 0; layerIdx < this.layers.length - 1; layerIdx++) {
      const currentLayer = this.layers[layerIdx];
      const nextLayer = this.layers[layerIdx + 1];
      
      for (const fromNeuron of currentLayer) {
        for (const toNeuron of nextLayer) {
          const connection = new NeuralConnection(fromNeuron, toNeuron, connectionColor);
          this.connections.push(connection);
          fromNeuron.connections.push(connection);
        }
      }
    }
  }
  
  private addToScene(): void {
    // Añadir neuronas
    this.layers.flat().forEach(neuron => {
      neuron.getMeshes().forEach(mesh => this.scene.add(mesh));
    });
    
    // Añadir conexiones (limitado para performance)
    const connectionLimit = Math.min(this.connections.length, this.currentConfig.performance.maxConnections);
    for (let i = 0; i < connectionLimit; i++) {
      this.connections[i].getMeshes().forEach(mesh => this.scene.add(mesh));
    }
  }

  private regenerateNetwork(): void {
    // Reutilizar neuronas existentes para crear un viaje infinito
    const topology = this.currentConfig.topology.layers;
    const spacing = 2.0;
    const radiusMul = 0.4;

    for (let layerIdx = 0; layerIdx < topology.length; layerIdx++) {
      const layer = this.layers[layerIdx];
      const nodeCount = topology[layerIdx];

      for (let nodeIdx = 0; nodeIdx < nodeCount; nodeIdx++) {
        const neuron = layer[nodeIdx];
        let position: THREE.Vector3;

        if (nodeCount === 1) {
          position = new THREE.Vector3(
            (layerIdx - topology.length / 2) * spacing,
            0,
            0
          );
        } else {
          const angle = (nodeIdx / nodeCount) * Math.PI * 2;
          const radius = Math.sqrt(nodeCount) * radiusMul;
          position = new THREE.Vector3(
            (layerIdx - topology.length / 2) * spacing,
            Math.sin(angle) * radius,
            Math.cos(angle) * radius * 0.5
          );
        }

        position.add(
          new THREE.Vector3(
            (Math.random() - 0.5) * 0.5,
            (Math.random() - 0.5) * 0.5,
            (Math.random() - 0.5) * 0.5
          )
        );

        neuron.position.copy(position);
        neuron.targetPosition.copy(position);
        neuron.getMeshes().forEach(mesh => mesh.position.copy(position));
        neuron.bias = Math.random() * 0.2 - 0.1;
        neuron.activation = 0;
      }
    }

    // Renovar pesos de conexiones y reiniciar progreso de señal
    this.connections.forEach(conn => {
      conn.weight = (Math.random() - 0.5) * 2;
      conn.propagationProgress = 0;
      conn.signalStrength = 0;
    });
  }
  
  // Forward propagation
  private forwardPropagate(inputs: number[]): number[] {
    // Capa de entrada
    for (let i = 0; i < this.layers[0].length && i < inputs.length; i++) {
      this.layers[0][i].activation = inputs[i];
    }
    
    // Capas ocultas y salida
    for (let layerIdx = 1; layerIdx < this.layers.length; layerIdx++) {
      const currentLayer = this.layers[layerIdx];
      const prevLayer = this.layers[layerIdx - 1];
      
      for (const neuron of currentLayer) {
        const inputs = prevLayer.map(n => n.activation);
        const weights = neuron.connections.map(c => c.weight);
        neuron.processInput(inputs, weights);
      }
    }
    
    return this.layers[this.layers.length - 1].map(n => n.activation);
  }
  
  // Generar patrón de entrada desde audio
  private generateAudioInputPattern(): number[] {
    const pattern: number[] = [];
    const inputSize = this.layers[0].length;
    
    // Mapear frecuencias de audio a entradas
    for (let i = 0; i < inputSize; i++) {
      const freq = i / inputSize;
      let value = 0;
      
      if (freq < 0.3) {
        value = this.audioData.low;
      } else if (freq < 0.7) {
        value = this.audioData.mid;
      } else {
        value = this.audioData.high;
      }
      
      // Añadir ruido y variación temporal
      value += Math.sin(this.clock.getElapsedTime() * 2 + i) * 0.1;
      pattern.push(Math.max(0, Math.min(1, value)));
    }
    
    return pattern;
  }
  
  public update(): void {
    const deltaTime = this.clock.getDelta();
    const time = this.clock.getElapsedTime();
    this.frameCount++;
    
    // Generar entrada desde audio
    const audioInput = this.generateAudioInputPattern();
    
    // Forward propagation
    const output = this.forwardPropagate(audioInput);
    
    // Simular aprendizaje (target dinámico basado en audio)
    this.learningPhase += deltaTime * 0.5;
    const target = output.map((_, i) => 
      0.5 + 0.5 * Math.sin(this.learningPhase + i * Math.PI / 2)
    );
    
    // Propagación de señales
    const audioIntensity = (this.audioData.low + this.audioData.mid + this.audioData.high) / 3;
    this.navigator.update(deltaTime, audioIntensity);
    this.connections.forEach(connection => {
      connection.propagateSignal(
        connection.fromNeuron.activation,
        this.currentConfig.visualization.propagationSpeed * (0.5 + audioIntensity),
        deltaTime
      );
    });

    // Calcular visibilidad
    this.camera.updateMatrixWorld();
    this.viewProjectionMatrix.multiplyMatrices(this.camera.projectionMatrix, this.camera.matrixWorldInverse);
    this.frustum.setFromProjectionMatrix(this.viewProjectionMatrix);

    // Actualizar neuronas
    this.layers.flat().forEach(neuron => {
      neuron.updateMorphology(deltaTime, audioIntensity, this.currentConfig);
      const visible = this.frustum.containsPoint(neuron.position);
      neuron.update(deltaTime, time, this.opacity * (visible ? 1 : 0));
    });

    // Actualizar conexiones (optimizado)
    const updateStep = Math.max(1, Math.floor(this.connections.length / 60));
    for (let i = this.frameCount % updateStep; i < this.connections.length; i += updateStep) {
      const conn = this.connections[i];
      const visible = this.frustum.containsPoint(conn.fromNeuron.position) ||
                      this.frustum.containsPoint(conn.toNeuron.position);
      conn.update(deltaTime, time, this.opacity * (visible ? 1 : 0));
    }
  }
  
  public updateConfig(newConfig: any): void {
    this.currentConfig = this.deepMerge(this.currentConfig, newConfig);
    
    // Actualizar colores
    if (newConfig.colors) {
      this.updateColors();
    }
  }
  
  private updateColors(): void {
    const colors = this.currentConfig.colors;
    
    // Actualizar colores de neuronas por capa
    this.layers.forEach((layer, layerIdx) => {
      let color: THREE.Color;
      
      if (layerIdx === 0) {
        color = new THREE.Color(colors.input);
      } else if (layerIdx === this.layers.length - 1) {
        color = new THREE.Color(colors.output);
      } else {
        color = new THREE.Color(colors.hidden);
      }
      
      layer.forEach(neuron => {
        neuron.getMeshes().forEach(mesh => {
          mesh.material.uniforms.uColor.value = color;
        });
      });
    });
    
    // Actualizar colores de conexiones
    const connectionColor = new THREE.Color(colors.connection);
    this.connections.forEach(connection => {
      connection.getMeshes().forEach(mesh => {
        mesh.material.uniforms.uColor.value = connectionColor;
      });
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
    // Limpiar neuronas
    this.layers.flat().forEach(neuron => {
      neuron.getMeshes().forEach(mesh => this.scene.remove(mesh));
      neuron.dispose();
    });
    
    // Limpiar conexiones
    this.connections.forEach(connection => {
      connection.getMeshes().forEach(mesh => this.scene.remove(mesh));
      connection.dispose();
    });

    this.navigator.dispose();
    this.layers = [];
    this.connections = [];
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  config: PresetConfig,
  shaderCode?: string
): BasePreset {
  return new NeuralNetworkGenesis(scene, camera, renderer, config);
}