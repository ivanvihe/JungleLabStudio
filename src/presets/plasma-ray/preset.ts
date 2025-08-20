import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: "Plasma Ray Genesis",
  description: "Sistema de plasma procedural con física real y efectos HDR",
  author: "AudioVisualizer Pro",
  version: "3.0.0",
  category: "energy",
  tags: ["plasma", "procedural", "physics", "hdr", "energy", "professional"],
  thumbnail: "plasma_ray_genesis_thumb.png",
  defaultConfig: {
    opacity: 1.0,
    fadeMs: 100,
    plasma: {
      coreIntensity: 3.5,
      fieldStrength: 2.0,
      volatility: 0.6,
      coherence: 0.8,
      temperature: 5000.0 // Kelvin
    },
    emission: {
      rayCount: 8,
      branchProbability: 0.4,
      energyDecay: 0.95,
      propagationSpeed: 15.0,
      maxBranches: 3
    },
    physics: {
      magneticField: 1.2,
      electricField: 2.5,
      conductivity: 0.85,
      permeability: 0.7,
      resistance: 0.3
    },
    colors: {
      coreTemperature: "#FFFFFF",
      hotPlasma: "#00FFFF", 
      mediumPlasma: "#0080FF",
      coolPlasma: "#8000FF",
      discharge: "#FF00FF"
    },
    quality: {
      segments: 128,
      particleCount: 2000,
      fieldResolution: 64,
      updateRate: 60
    }
  },
  controls: [
    {
      name: "plasma.coreIntensity",
      type: "slider",
      label: "Intensidad del Núcleo",
      min: 1.0,
      max: 10.0,
      step: 0.1,
      default: 3.5
    },
    {
      name: "plasma.temperature",
      type: "slider", 
      label: "Temperatura (K)",
      min: 2000.0,
      max: 15000.0,
      step: 100.0,
      default: 5000.0
    },
    {
      name: "emission.propagationSpeed",
      type: "slider",
      label: "Velocidad de Propagación",
      min: 5.0,
      max: 50.0,
      step: 1.0,
      default: 15.0
    },
    {
      name: "physics.magneticField",
      type: "slider",
      label: "Campo Magnético",
      min: 0.0,
      max: 3.0,
      step: 0.1,
      default: 1.2
    }
  ],
  audioMapping: {
    low: {
      description: "Controla la generación de plasma y campo base",
      frequency: "20-250 Hz",
      effect: "Intensidad del núcleo y generación de energía"
    },
    mid: {
      description: "Modula propagación y ramificación",
      frequency: "250-4000 Hz", 
      effect: "Velocidad de rayos y patrones de descarga"
    },
    high: {
      description: "Efectos de alta energía y descargas",
      frequency: "4000+ Hz",
      effect: "Chispas, resonancia y efectos especiales"
    }
  },
  performance: {
    complexity: "high",
    recommendedFPS: 60,
    gpuIntensive: true
  }
};

// Simulación física de plasma con ecuaciones Maxwell simplificadas
class PlasmaPhysics {
  public electricField: THREE.Vector3 = new THREE.Vector3();
  public magneticField: THREE.Vector3 = new THREE.Vector3();
  public temperature: number = 5000.0;
  public density: number = 1.0;
  
  constructor(
    private fieldStrength: number,
    private magneticStrength: number,
    private conductivity: number
  ) {}

  // Calcular campo electromagnético en un punto
  public getFieldAt(position: THREE.Vector3, time: number): {
    electric: THREE.Vector3,
    magnetic: THREE.Vector3,
    potential: number
  } {
    const r = position.length();
    const theta = Math.atan2(position.y, position.x);
    const phi = Math.acos(position.z / Math.max(r, 0.001));
    
    // Campo eléctrico radial con perturbaciones
    const electricMagnitude = this.fieldStrength / (r * r + 0.1) * 
      (1 + 0.3 * Math.sin(time * 5 + theta * 3));
    
    const electric = position.clone().normalize().multiplyScalar(electricMagnitude);
    
    // Campo magnético tangencial (Ley de Ampère)
    const magneticMagnitude = this.magneticStrength * this.conductivity / (r + 0.1);
    const magnetic = new THREE.Vector3(-Math.sin(theta), Math.cos(theta), 0)
      .multiplyScalar(magneticMagnitude);
    
    // Potencial escalar
    const potential = this.fieldStrength / (r + 0.1) * 
      Math.exp(-r * 0.5) * (1 + 0.2 * Math.sin(time * 3));
    
    return { electric, magnetic, potential };
  }

  // Temperatura basada en densidad de energía
  public getTemperatureAt(position: THREE.Vector3, energyDensity: number): number {
    const baseTemp = this.temperature;
    const distance = position.length();
    const tempGradient = Math.exp(-distance * 0.8);
    
    return baseTemp * tempGradient * (0.5 + energyDensity * 1.5);
  }

  // Color basado en temperatura (Planck's law aproximada)
  public getColorFromTemperature(temp: number): THREE.Color {
    const normalizedTemp = Math.max(0, Math.min(1, (temp - 2000) / 13000));
    
    if (normalizedTemp < 0.25) {
      // Rojo-Púrpura (frío)
      return new THREE.Color().setHSL(0.75, 0.8, 0.3 + normalizedTemp * 0.4);
    } else if (normalizedTemp < 0.5) {
      // Azul (medio)
      return new THREE.Color().setHSL(0.6, 0.9, 0.4 + normalizedTemp * 0.4);
    } else if (normalizedTemp < 0.75) {
      // Cyan (caliente)
      return new THREE.Color().setHSL(0.5, 1.0, 0.5 + normalizedTemp * 0.3);
    } else {
      // Blanco (muy caliente)
      return new THREE.Color().setHSL(0.0, 0.0, 0.8 + normalizedTemp * 0.2);
    }
  }
}

// Rayo de plasma con física real
class PlasmaRay {
  public points: THREE.Vector3[] = [];
  public energies: number[] = [];
  public temperatures: number[] = [];
  public mesh: THREE.Line;
  private material: THREE.ShaderMaterial;
  
  public age: number = 0;
  public lifespan: number;
  public totalEnergy: number;
  private branches: PlasmaRay[] = [];
  
  constructor(
    private physics: PlasmaPhysics,
    startPoint: THREE.Vector3,
    direction: THREE.Vector3,
    initialEnergy: number,
    segments: number
  ) {
    this.lifespan = 1.5 + Math.random() * 2.0;
    this.totalEnergy = initialEnergy;
    
    this.generatePath(startPoint, direction, segments);
    this.createMaterial();
    this.createMesh();
  }

  private generatePath(start: THREE.Vector3, direction: THREE.Vector3, segments: number): void {
    this.points = [start.clone()];
    this.energies = [this.totalEnergy];
    this.temperatures = [this.physics.temperature];
    
    let currentPos = start.clone();
    let currentDir = direction.clone().normalize();
    let currentEnergy = this.totalEnergy;
    
    const segmentLength = 0.1;
    
    for (let i = 1; i < segments; i++) {
      // Propagar según campos electromagnéticos
      const fields = this.physics.getFieldAt(currentPos, 0);
      
      // Deflexión por campo eléctrico
      const electricForce = fields.electric.clone().multiplyScalar(0.01);
      currentDir.add(electricForce);
      
      // Curvatura por campo magnético (Fuerza de Lorentz)
      const magneticForce = currentDir.clone().cross(fields.magnetic).multiplyScalar(0.005);
      currentDir.add(magneticForce);
      
      // Ruido cuántico
      const quantumNoise = new THREE.Vector3(
        (Math.random() - 0.5) * 0.02,
        (Math.random() - 0.5) * 0.02,
        (Math.random() - 0.5) * 0.01
      );
      currentDir.add(quantumNoise);
      
      currentDir.normalize();
      
      // Avanzar posición
      currentPos.add(currentDir.clone().multiplyScalar(segmentLength));
      
      // Decaimiento energético
      currentEnergy *= 0.98 + Math.random() * 0.02;
      
      this.points.push(currentPos.clone());
      this.energies.push(currentEnergy);
      
      // Calcular temperatura local
      const temp = this.physics.getTemperatureAt(currentPos, currentEnergy);
      this.temperatures.push(temp);
      
      // Condición de terminación
      if (currentEnergy < 0.1 || currentPos.length() > 5) break;
    }
  }

  private createMaterial(): void {
    this.material = new THREE.ShaderMaterial({
      transparent: true,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
      vertexShader: `
        attribute float aEnergy;
        attribute float aTemperature;
        varying float vEnergy;
        varying float vTemperature;
        varying vec3 vPosition;
        uniform float uTime;
        uniform float uGlobalIntensity;
        
        void main() {
          vEnergy = aEnergy;
          vTemperature = aTemperature;
          vPosition = position;
          
          vec3 pos = position;
          
          // Fluctuaciones cuánticas
          float quantum = sin(uTime * 20.0 + position.x * 10.0) * 0.001 * aEnergy;
          pos += normal * quantum;
          
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        varying float vEnergy;
        varying float vTemperature;
        varying vec3 vPosition;
        uniform float uTime;
        uniform float uOpacity;
        uniform float uGlobalIntensity;
        
        // Función para color por temperatura (Planck)
        vec3 temperatureToColor(float temp) {
          float normalized = clamp((temp - 2000.0) / 13000.0, 0.0, 1.0);
          
          if (normalized < 0.25) {
            return mix(vec3(0.5, 0.0, 1.0), vec3(0.0, 0.0, 1.0), normalized * 4.0);
          } else if (normalized < 0.5) {
            return mix(vec3(0.0, 0.0, 1.0), vec3(0.0, 1.0, 1.0), (normalized - 0.25) * 4.0);
          } else if (normalized < 0.75) {
            return mix(vec3(0.0, 1.0, 1.0), vec3(1.0, 1.0, 1.0), (normalized - 0.5) * 4.0);
          } else {
            return vec3(1.0, 1.0, 1.0);
          }
        }
        
        void main() {
          // Color basado en temperatura física
          vec3 baseColor = temperatureToColor(vTemperature);
          
          // Intensidad basada en energía
          float intensity = vEnergy * uGlobalIntensity;
          
          // Efectos de plasma: fluctuaciones de alta frecuencia
          float plasmaFlicker = sin(uTime * 50.0 + vPosition.x * 20.0) * 0.1 + 0.9;
          intensity *= plasmaFlicker;
          
          // Emisión HDR
          vec3 emission = baseColor * intensity * 2.0;
          
          // Glow core
          float coreGlow = exp(-length(vPosition) * 2.0) * intensity;
          emission += vec3(1.0, 1.0, 1.0) * coreGlow * 0.5;
          
          gl_FragColor = vec4(emission, min(1.0, intensity) * uOpacity);
        }
      `,
      uniforms: {
        uTime: { value: 0.0 },
        uOpacity: { value: 1.0 },
        uGlobalIntensity: { value: 1.0 }
      }
    });
  }

  private createMesh(): void {
    const geometry = new THREE.BufferGeometry();
    
    const positions = new Float32Array(this.points.length * 3);
    const energies = new Float32Array(this.points.length);
    const temperatures = new Float32Array(this.points.length);
    
    for (let i = 0; i < this.points.length; i++) {
      positions[i * 3] = this.points[i].x;
      positions[i * 3 + 1] = this.points[i].y;
      positions[i * 3 + 2] = this.points[i].z;
      
      energies[i] = this.energies[i];
      temperatures[i] = this.temperatures[i];
    }
    
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('aEnergy', new THREE.BufferAttribute(energies, 1));
    geometry.setAttribute('aTemperature', new THREE.BufferAttribute(temperatures, 1));
    
    this.mesh = new THREE.Line(geometry, this.material);
  }

  public update(deltaTime: number, time: number, audioIntensity: number): void {
    this.age += deltaTime;
    
    // Actualizar uniforms
    this.material.uniforms.uTime.value = time;
    this.material.uniforms.uGlobalIntensity.value = 0.5 + audioIntensity * 1.5;
    this.material.uniforms.uOpacity.value = Math.max(0, 1 - this.age / this.lifespan);
    
    // Evolución temporal del rayo
    if (this.age < this.lifespan * 0.5) {
      this.evolvePath(time, audioIntensity);
    }
  }

  private evolvePath(time: number, audioIntensity: number): void {
    const positions = this.mesh.geometry.attributes.position.array as Float32Array;
    
    for (let i = 1; i < this.points.length - 1; i++) {
      // Perturbaciones electromagnéticas
      const fields = this.physics.getFieldAt(this.points[i], time);
      const perturbation = fields.electric.clone().multiplyScalar(0.001 * audioIntensity);
      
      positions[i * 3] += perturbation.x;
      positions[i * 3 + 1] += perturbation.y;
      positions[i * 3 + 2] += perturbation.z;
    }
    
    this.mesh.geometry.attributes.position.needsUpdate = true;
  }

  public createBranch(config: any): PlasmaRay | null {
    if (this.branches.length >= config.emission.maxBranches) return null;
    if (Math.random() > config.emission.branchProbability) return null;
    
    const branchPoint = Math.floor(this.points.length * (0.3 + Math.random() * 0.4));
    const startPoint = this.points[branchPoint];
    const branchEnergy = this.energies[branchPoint] * 0.6;
    
    const direction = new THREE.Vector3(
      (Math.random() - 0.5) * 2,
      (Math.random() - 0.5) * 2,
      (Math.random() - 0.5) * 1
    ).normalize();
    
    const branch = new PlasmaRay(
      this.physics,
      startPoint,
      direction,
      branchEnergy,
      Math.floor(config.quality.segments * 0.6)
    );
    
    this.branches.push(branch);
    return branch;
  }

  public isDead(): boolean {
    return this.age >= this.lifespan;
  }

  public dispose(): void {
    this.mesh.geometry.dispose();
    this.material.dispose();
    this.branches.forEach(branch => branch.dispose());
  }
}

// Sistema de partículas para chispas y efectos
class PlasmaParticleSystem {
  private particles: THREE.Points;
  private particleCount: number;
  private positions: Float32Array;
  private velocities: Float32Array;
  private energies: Float32Array;
  private lifetimes: Float32Array;
  private material: THREE.ShaderMaterial;

  constructor(count: number) {
    this.particleCount = count;
    this.initializeBuffers();
    this.createMaterial();
    this.createMesh();
  }

  private initializeBuffers(): void {
    this.positions = new Float32Array(this.particleCount * 3);
    this.velocities = new Float32Array(this.particleCount * 3);
    this.energies = new Float32Array(this.particleCount);
    this.lifetimes = new Float32Array(this.particleCount);

    for (let i = 0; i < this.particleCount; i++) {
      this.resetParticle(i);
    }
  }

  private createMaterial(): void {
    this.material = new THREE.ShaderMaterial({
      transparent: true,
      blending: THREE.AdditiveBlending,
      vertexShader: `
        attribute float aEnergy;
        attribute float aLifetime;
        varying float vEnergy;
        varying float vLifetime;
        uniform float uTime;
        uniform float uSize;
        
        void main() {
          vEnergy = aEnergy;
          vLifetime = aLifetime;
          
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          gl_Position = projectionMatrix * mvPosition;
          
          // Tamaño basado en energía y distancia
          float size = uSize * aEnergy * (1.0 + sin(uTime * 10.0 + position.x * 5.0) * 0.3);
          gl_PointSize = size * (300.0 / -mvPosition.z);
        }
      `,
      fragmentShader: `
        varying float vEnergy;
        varying float vLifetime;
        uniform float uTime;
        uniform float uOpacity;
        
        void main() {
          // Círculo suave
          vec2 center = gl_PointCoord - 0.5;
          float dist = length(center);
          if (dist > 0.5) discard;
          
          float alpha = 1.0 - smoothstep(0.3, 0.5, dist);
          
          // Color energético
          vec3 color = mix(
            vec3(1.0, 0.0, 1.0),  // Magenta
            vec3(1.0, 1.0, 1.0),  // Blanco
            vEnergy
          );
          
          // Sparkle effect
          float sparkle = sin(uTime * 20.0 + gl_PointCoord.x * 10.0) * 0.5 + 0.5;
          color *= 1.0 + sparkle * vEnergy;
          
          gl_FragColor = vec4(color, alpha * vEnergy * uOpacity);
        }
      `,
      uniforms: {
        uTime: { value: 0.0 },
        uSize: { value: 20.0 },
        uOpacity: { value: 1.0 }
      }
    });
  }

  private createMesh(): void {
    const geometry = new THREE.BufferGeometry();
    
    geometry.setAttribute('position', new THREE.BufferAttribute(this.positions, 3));
    geometry.setAttribute('aEnergy', new THREE.BufferAttribute(this.energies, 1));
    geometry.setAttribute('aLifetime', new THREE.BufferAttribute(this.lifetimes, 1));
    
    this.particles = new THREE.Points(geometry, this.material);
  }

  private resetParticle(index: number): void {
    const i3 = index * 3;
    
    // Posición inicial cerca del origen con dispersión
    const radius = Math.random() * 0.5;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.random() * Math.PI;
    
    this.positions[i3] = radius * Math.sin(phi) * Math.cos(theta);
    this.positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
    this.positions[i3 + 2] = radius * Math.cos(phi);
    
    // Velocidad radial con componente aleatoria
    const speed = 0.5 + Math.random() * 1.5;
    this.velocities[i3] = (Math.random() - 0.5) * speed;
    this.velocities[i3 + 1] = (Math.random() - 0.5) * speed;
    this.velocities[i3 + 2] = (Math.random() - 0.5) * speed * 0.5;
    
    this.energies[index] = 0.3 + Math.random() * 0.7;
    this.lifetimes[index] = 1.0 + Math.random() * 2.0;
  }

  public update(deltaTime: number, time: number, audioIntensity: number, plasmaSources: THREE.Vector3[]): void {
    this.material.uniforms.uTime.value = time;
    this.material.uniforms.uOpacity.value = 0.7 + audioIntensity * 0.3;
    
    for (let i = 0; i < this.particleCount; i++) {
      const i3 = i * 3;
      
      // Actualizar posición
      this.positions[i3] += this.velocities[i3] * deltaTime;
      this.positions[i3 + 1] += this.velocities[i3 + 1] * deltaTime;
      this.positions[i3 + 2] += this.velocities[i3 + 2] * deltaTime;
      
      // Decaimiento de energía y tiempo
      this.energies[i] *= 0.99;
      this.lifetimes[i] -= deltaTime;
      
      // Respawn si es necesario
      if (this.lifetimes[i] <= 0 || this.energies[i] < 0.1) {
        if (plasmaSources.length > 0 && Math.random() < 0.3) {
          // Spawn desde fuente de plasma
          const source = plasmaSources[Math.floor(Math.random() * plasmaSources.length)];
          this.positions[i3] = source.x + (Math.random() - 0.5) * 0.2;
          this.positions[i3 + 1] = source.y + (Math.random() - 0.5) * 0.2;
          this.positions[i3 + 2] = source.z + (Math.random() - 0.5) * 0.1;
        }
        this.resetParticle(i);
      }
    }
    
    this.particles.geometry.attributes.position.needsUpdate = true;
    this.particles.geometry.attributes.aEnergy.needsUpdate = true;
  }

  public getMesh(): THREE.Points {
    return this.particles;
  }

  public dispose(): void {
    this.particles.geometry.dispose();
    this.material.dispose();
  }
}

// Núcleo de plasma principal
class PlasmaCore {
  private mesh: THREE.Mesh;
  private glowMesh: THREE.Mesh;
  private material: THREE.ShaderMaterial;
  private glowMaterial: THREE.ShaderMaterial;
  public energy: number = 1.0;

  constructor(radius: number = 0.3) {
    this.createCore(radius);
    this.createGlow(radius * 2);
  }

  private createCore(radius: number): void {
    const geometry = new THREE.SphereGeometry(radius, 32, 32);
    
    this.material = new THREE.ShaderMaterial({
      transparent: true,
      blending: THREE.AdditiveBlending,
      vertexShader: `
        varying vec3 vPosition;
        varying vec3 vNormal;
        uniform float uTime;
        uniform float uEnergy;
        
        void main() {
          vPosition = position;
          vNormal = normal;
          
          vec3 pos = position;
          
          // Pulsación del núcleo
          float pulse = sin(uTime * 8.0) * 0.1 + 1.0;
          pos *= pulse * (1.0 + uEnergy * 0.2);
          
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        varying vec3 vPosition;
        varying vec3 vNormal;
        uniform float uTime;
        uniform float uEnergy;
        uniform float uTemperature;
        uniform float uOpacity;
        
        vec3 blackbodyColor(float temp) {
          float t = temp / 15000.0;
          
          if (t < 0.3) {
            return mix(vec3(1.0, 0.0, 0.0), vec3(1.0, 0.5, 0.0), t / 0.3);
          } else if (t < 0.6) {
            return mix(vec3(1.0, 0.5, 0.0), vec3(1.0, 1.0, 0.8), (t - 0.3) / 0.3);
          } else {
            return mix(vec3(1.0, 1.0, 0.8), vec3(0.8, 0.9, 1.0), (t - 0.6) / 0.4);
          }
        }
        
        void main() {
          vec3 color = blackbodyColor(uTemperature);
          
          // Efectos de turbulencia interna
          float turbulence = sin(vPosition.x * 10.0 + uTime * 5.0) *
                           cos(vPosition.y * 8.0 + uTime * 3.0) *
                           sin(vPosition.z * 12.0 + uTime * 4.0);
          
          float intensity = uEnergy * (1.0 + turbulence * 0.3);
          
          // Fresnel para el borde
          float fresnel = 1.0 - dot(normalize(vNormal), vec3(0.0, 0.0, 1.0));
          intensity *= 0.5 + fresnel * 1.5;
          
          gl_FragColor = vec4(color * intensity, intensity * uOpacity);
        }
      `,
      uniforms: {
        uTime: { value: 0.0 },
        uEnergy: { value: 1.0 },
        uTemperature: { value: 5000.0 },
        uOpacity: { value: 1.0 }
      }
    });
    
    this.mesh = new THREE.Mesh(geometry, this.material);
  }

  private createGlow(radius: number): void {
    const geometry = new THREE.SphereGeometry(radius, 16, 16);
    
    this.glowMaterial = new THREE.ShaderMaterial({
      transparent: true,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      vertexShader: `
        varying float vIntensity;
        uniform float uTime;
        
        void main() {
          vec3 vNormal = normalize(normalMatrix * normal);
          vec3 vNormel = normalize(normalMatrix * position);
          vIntensity = pow(0.6 - dot(vNormal, vNormel), 2.0);
          
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        varying float vIntensity;
        uniform float uEnergy;
        uniform float uOpacity;
        
        void main() {
          vec3 glow = vec3(0.0, 0.8, 1.0) * vIntensity * uEnergy;
          gl_FragColor = vec4(glow, vIntensity * 0.3 * uOpacity);
        }
      `,
      uniforms: {
        uEnergy: { value: 1.0 },
        uOpacity: { value: 1.0 }
      }
    });
    
    this.glowMesh = new THREE.Mesh(geometry, this.glowMaterial);
  }

  public update(deltaTime: number, time: number, audioData: any, config: any): void {
    const audioIntensity = (audioData.low + audioData.mid + audioData.high) / 3;
    this.energy = 0.5 + audioIntensity * 2.0;
    
    // Actualizar uniforms
    this.material.uniforms.uTime.value = time;
    this.material.uniforms.uEnergy.value = this.energy * config.plasma.coreIntensity;
    this.material.uniforms.uTemperature.value = config.plasma.temperature * (0.8 + audioIntensity * 0.4);
    
    this.glowMaterial.uniforms.uEnergy.value = this.energy;
    
    // Rotación del núcleo
    this.mesh.rotation.x += deltaTime * 0.5;
    this.mesh.rotation.y += deltaTime * 0.3;
    this.glowMesh.rotation.x -= deltaTime * 0.2;
    this.glowMesh.rotation.z += deltaTime * 0.4;
  }

  public getMeshes(): THREE.Mesh[] {
    return [this.mesh, this.glowMesh];
  }

  public getPosition(): THREE.Vector3 {
    return this.mesh.position;
  }

  public dispose(): void {
    this.mesh.geometry.dispose();
    this.material.dispose();
    this.glowMesh.geometry.dispose();
    this.glowMaterial.dispose();
  }
}

class PlasmaRayGenesisPreset extends BasePreset {
  private physics: PlasmaPhysics;
  private core: PlasmaCore;
  private rays: PlasmaRay[] = [];
  private particleSystem: PlasmaParticleSystem;
  private currentConfig: any;
  private spawnTimer: number = 0;
  private frameCount: number = 0;

  constructor(
    scene: THREE.Scene,
    camera: THREE.Camera,
    renderer: THREE.WebGLRenderer,
    config: PresetConfig
  ) {
    super(scene, camera, renderer, config);
    
    this.currentConfig = { ...config.defaultConfig };
    
    this.physics = new PlasmaPhysics(
      this.currentConfig.physics.electricField,
      this.currentConfig.physics.magneticField,
      this.currentConfig.physics.conductivity
    );
    
    this.core = new PlasmaCore(0.2);
    this.particleSystem = new PlasmaParticleSystem(this.currentConfig.quality.particleCount);
  }

  public init(): void {
    // Fondo completamente transparente
    this.renderer.setClearColor(0x000000, 0);
    
    // Añadir núcleo
    this.core.getMeshes().forEach(mesh => this.scene.add(mesh));
    
    // Añadir sistema de partículas
    this.scene.add(this.particleSystem.getMesh());
    
    // Crear rayos iniciales
    for (let i = 0; i < 6; i++) {
      this.createRay();
    }
  }

  private createRay(): void {
    const angle = Math.random() * Math.PI * 2;
    const elevation = (Math.random() - 0.5) * Math.PI * 0.5;
    
    const direction = new THREE.Vector3(
      Math.cos(angle) * Math.cos(elevation),
      Math.sin(elevation),
      Math.sin(angle) * Math.cos(elevation)
    );
    
    const energy = 0.8 + Math.random() * 1.2;
    const ray = new PlasmaRay(
      this.physics,
      this.core.getPosition(),
      direction,
      energy,
      this.currentConfig.quality.segments
    );
    
    this.rays.push(ray);
    this.scene.add(ray.mesh);
  }

  public update(): void {
    const deltaTime = this.clock.getDelta();
    const time = this.clock.getElapsedTime();
    this.frameCount++;
    
    const audioIntensity = (this.audioData.low + this.audioData.mid + this.audioData.high) / 3;
    
    // Actualizar núcleo
    this.core.update(deltaTime, time, this.audioData, this.currentConfig);
    
    // Spawn control
    this.spawnTimer += deltaTime;
    const spawnRate = this.currentConfig.emission.propagationSpeed * (0.1 + this.audioData.mid * 0.4);
    
    if (this.spawnTimer > 60 / spawnRate && this.rays.length < this.currentConfig.emission.rayCount) {
      this.createRay();
      this.spawnTimer = 0;
    }
    
    // Actualizar rayos
    for (let i = this.rays.length - 1; i >= 0; i--) {
      const ray = this.rays[i];
      ray.update(deltaTime, time, audioIntensity);
      
      // Crear ramas
      if (Math.random() < this.currentConfig.emission.branchProbability * deltaTime && 
          this.audioData.mid > 0.5) {
        const branch = ray.createBranch(this.currentConfig);
        if (branch) {
          this.scene.add(branch.mesh);
          this.rays.push(branch);
        }
      }
      
      // Remover rayos muertos
      if (ray.isDead()) {
        this.scene.remove(ray.mesh);
        ray.dispose();
        this.rays.splice(i, 1);
      }
    }
    
    // Actualizar partículas
    const plasmaSources = [this.core.getPosition(), ...this.rays.map(r => r.points[0])];
    this.particleSystem.update(deltaTime, time, audioIntensity, plasmaSources);
    
    // Actualizar opacidad global
    this.core.getMeshes().forEach(mesh => {
      mesh.material.uniforms.uOpacity.value = this.opacity;
    });
    
    this.particleSystem.getMesh().material.uniforms.uOpacity.value = this.opacity;
  }

  public updateConfig(newConfig: any): void {
    this.currentConfig = this.deepMerge(this.currentConfig, newConfig);
    
    // Actualizar física
    if (newConfig.physics) {
      this.physics = new PlasmaPhysics(
        this.currentConfig.physics.electricField,
        this.currentConfig.physics.magneticField,
        this.currentConfig.physics.conductivity
      );
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
      this.scene.remove(ray.mesh);
      ray.dispose();
    });
    
    // Limpiar núcleo
    this.core.getMeshes().forEach(mesh => this.scene.remove(mesh));
    this.core.dispose();
    
    // Limpiar partículas
    this.scene.remove(this.particleSystem.getMesh());
    this.particleSystem.dispose();
    
    this.rays = [];
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  config: PresetConfig,
  shaderCode?: string
): BasePreset {
  return new PlasmaRayGenesisPreset(scene, camera, renderer, config);
}