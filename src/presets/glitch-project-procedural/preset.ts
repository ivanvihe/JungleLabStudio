import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';
import { applyVFX } from './vfx';

export const config: PresetConfig = {
  name: "Procedural Complex",
  description: "Procedural geometry with evolving lines, dynamic particles and 3D point-clouds. Audio-reactive with shader-based distortions, fluid noise, raymarching and SDF shapes.",
  author: "Glitch Project",
  version: "1.0.0",
  category: "glitch-project",
  tags: ["procedural", "advanced", "shader", "raymarching", "particles", "audio-reactive", "volumetric"],
  thumbnail: "procedural_complex_thumb.png",
  note: 48,
  defaultConfig: {
    opacity: 1.0,
    fadeMs: 300,
    geometry: {
      lineCount: 80,
      pointCloudDensity: 2000,
      particleCount: 1500,
      complexityLevel: 5,
      evolutionSpeed: 0.4
    },
    shaders: {
      distortionIntensity: 0.6,
      noiseScale: 2.5,
      rayMarchSteps: 64,
      sdfSmoothing: 0.3,
      volumetricDensity: 0.8
    },
    motion: {
      flowSpeed: 0.5,
      turbulence: 0.7,
      smoothness: 0.9,
      organicMovement: 0.8
    },
    colors: {
      primary: "#0a0a0a",
      accent1: "#1a1a2e",
      accent2: "#16213e",
      highlight: "#0f3460",
      glow: "#e94560"
    },
    audioReactivity: {
      lowFreqInfluence: 0.8,
      midFreqInfluence: 0.7,
      highFreqInfluence: 0.6,
      beatPulse: 1.2
    },
    effects: {
      enableVolumetric: true,
      enableRaymarching: true,
      enableDistortion: true,
      enableGlow: true,
      quality: "high"
    }
  },
  controls: [],
  audioMapping: {
    low: {
      description: "Controls particle density and line evolution",
      frequency: "20-250 Hz",
      effect: "Geometry morphing and particle spawning"
    },
    mid: {
      description: "Modulates shader distortion and flow",
      frequency: "250-4000 Hz",
      effect: "Fluid noise and organic movement"
    },
    high: {
      description: "Affects volumetric lighting and fine details",
      frequency: "4000+ Hz",
      effect: "Glow intensity and high-frequency distortions"
    }
  },
  performance: {
    complexity: "high",
    recommendedFPS: 60,
    gpuIntensive: true
  }
};

// ============================================================================
// PROCEDURAL LINE CLASS - Evolving 3D lines with complex math
// ============================================================================
class ProceduralLine {
  private geometry: THREE.BufferGeometry;
  private material: THREE.LineBasicMaterial;
  private line: THREE.Line;
  private points: THREE.Vector3[];
  private velocities: THREE.Vector3[];
  private segments: number;
  private phase: number;

  constructor(segments: number, color: THREE.Color) {
    this.segments = segments;
    this.points = [];
    this.velocities = [];
    this.phase = Math.random() * Math.PI * 2;

    // Initialize points in a procedural pattern
    for (let i = 0; i < segments; i++) {
      const t = i / segments;
      const pos = new THREE.Vector3(
        Math.sin(t * Math.PI * 4 + this.phase) * 2,
        Math.cos(t * Math.PI * 3 + this.phase) * 2,
        Math.sin(t * Math.PI * 2) * 2
      );
      this.points.push(pos);
      this.velocities.push(new THREE.Vector3(
        (Math.random() - 0.5) * 0.01,
        (Math.random() - 0.5) * 0.01,
        (Math.random() - 0.5) * 0.01
      ));
    }

    this.geometry = new THREE.BufferGeometry().setFromPoints(this.points);
    this.material = new THREE.LineBasicMaterial({
      color,
      linewidth: 2,
      transparent: true,
      opacity: 0.6
    });
    this.line = new THREE.Line(this.geometry, this.material);
  }

  update(time: number, audioData: any, config: any) {
    const speed = config.motion.flowSpeed || 0.5;
    const turbulence = config.motion.turbulence || 0.7;
    const lowFreq = audioData?.low || 0;
    const midFreq = audioData?.mid || 0;

    // Update each point with procedural motion
    for (let i = 0; i < this.points.length; i++) {
      const t = i / this.points.length;
      const point = this.points[i];
      const vel = this.velocities[i];

      // Audio-reactive forces
      const audioForce = new THREE.Vector3(
        Math.sin(time * speed + t * Math.PI * 2) * lowFreq * 0.5,
        Math.cos(time * speed * 0.7 + t * Math.PI * 3) * midFreq * 0.5,
        Math.sin(time * speed * 0.5 + t * Math.PI * 4) * (lowFreq + midFreq) * 0.25
      );

      // Turbulent noise
      const noise = new THREE.Vector3(
        Math.sin(time * 2 + point.x * 0.5) * turbulence,
        Math.cos(time * 1.5 + point.y * 0.5) * turbulence,
        Math.sin(time * 1.8 + point.z * 0.5) * turbulence
      );

      vel.add(audioForce.multiplyScalar(0.01));
      vel.add(noise.multiplyScalar(0.005));
      vel.multiplyScalar(0.98); // Dampening

      point.add(vel);

      // Keep points within bounds with smooth wrapping
      const maxDist = 5;
      if (point.length() > maxDist) {
        point.normalize().multiplyScalar(maxDist * 0.9);
      }
    }

    this.geometry.setFromPoints(this.points);
    this.geometry.attributes.position.needsUpdate = true;
  }

  getMesh() {
    return this.line;
  }

  dispose() {
    this.geometry.dispose();
    this.material.dispose();
  }
}

// ============================================================================
// PARTICLE SYSTEM - Dynamic audio-reactive particles
// ============================================================================
class DynamicParticle {
  position: THREE.Vector3;
  velocity: THREE.Vector3;
  acceleration: THREE.Vector3;
  life: number;
  maxLife: number;
  size: number;
  phase: number;

  constructor() {
    this.position = new THREE.Vector3(
      (Math.random() - 0.5) * 6,
      (Math.random() - 0.5) * 6,
      (Math.random() - 0.5) * 6
    );
    this.velocity = new THREE.Vector3(
      (Math.random() - 0.5) * 0.02,
      (Math.random() - 0.5) * 0.02,
      (Math.random() - 0.5) * 0.02
    );
    this.acceleration = new THREE.Vector3();
    this.life = 1.0;
    this.maxLife = 5.0 + Math.random() * 5.0;
    this.size = 0.02 + Math.random() * 0.04;
    this.phase = Math.random() * Math.PI * 2;
  }

  update(delta: number, time: number, audioData: any, config: any) {
    const lowFreq = audioData?.low || 0;
    const midFreq = audioData?.mid || 0;
    const highFreq = audioData?.high || 0;

    // Audio-reactive acceleration
    const audioInfluence = new THREE.Vector3(
      Math.sin(time + this.phase) * lowFreq,
      Math.cos(time * 0.7 + this.phase) * midFreq,
      Math.sin(time * 0.5 + this.phase) * highFreq
    ).multiplyScalar(0.01);

    this.acceleration.copy(audioInfluence);

    // Orbital attraction to center
    const toCenter = this.position.clone().negate().normalize().multiplyScalar(0.001);
    this.acceleration.add(toCenter);

    // Turbulent flow
    const turbulence = config.motion?.turbulence || 0.7;
    const turbForce = new THREE.Vector3(
      Math.sin(time * 2 + this.position.x) * turbulence,
      Math.cos(time * 1.5 + this.position.y) * turbulence,
      Math.sin(time * 1.8 + this.position.z) * turbulence
    ).multiplyScalar(0.002);

    this.acceleration.add(turbForce);

    // Update physics
    this.velocity.add(this.acceleration);
    this.velocity.multiplyScalar(0.98); // Drag
    this.position.add(this.velocity);

    // Update life
    this.life -= delta / this.maxLife;

    // Respawn if dead
    if (this.life <= 0) {
      this.respawn();
    }
  }

  respawn() {
    const radius = 3 + Math.random() * 2;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.random() * Math.PI;

    this.position.set(
      radius * Math.sin(phi) * Math.cos(theta),
      radius * Math.sin(phi) * Math.sin(theta),
      radius * Math.cos(phi)
    );
    this.velocity.set(
      (Math.random() - 0.5) * 0.02,
      (Math.random() - 0.5) * 0.02,
      (Math.random() - 0.5) * 0.02
    );
    this.life = 1.0;
    this.phase = Math.random() * Math.PI * 2;
  }
}

// ============================================================================
// MAIN PRESET CLASS
// ============================================================================
export class ProceduralComplexPreset extends BasePreset {
  private lines: ProceduralLine[] = [];
  private particles: DynamicParticle[] = [];
  private particleSystem: THREE.Points | null = null;
  private pointCloud: THREE.Points | null = null;
  private time: number = 0;

  constructor(
    scene: THREE.Scene,
    camera: THREE.Camera,
    renderer: THREE.WebGLRenderer,
    config: any
  ) {
    super(scene, camera, renderer, config);
  }

  init() {
    this.initialize();
  }

  private initialize() {
    // Create procedural lines
    const lineCount = (this.config.defaultConfig as any).geometry?.lineCount || 80;
    const colors = (this.config.defaultConfig as any).colors || {};
    const lineColor = new THREE.Color(colors.accent1 || '#1a1a2e');

    for (let i = 0; i < lineCount; i++) {
      const segments = 32 + Math.floor(Math.random() * 32);
      const line = new ProceduralLine(segments, lineColor);
      this.lines.push(line);
      this.scene.add(line.getMesh());
    }

    // Create particle system
    const particleCount = (this.config.defaultConfig as any).geometry?.particleCount || 1500;
    for (let i = 0; i < particleCount; i++) {
      this.particles.push(new DynamicParticle());
    }

    const particleGeometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = this.particles[i].position.x;
      positions[i * 3 + 1] = this.particles[i].position.y;
      positions[i * 3 + 2] = this.particles[i].position.z;
      sizes[i] = this.particles[i].size;
    }

    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particleGeometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

    const particleMaterial = new THREE.PointsMaterial({
      size: 0.05,
      color: new THREE.Color(colors.glow || '#e94560'),
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending,
      sizeAttenuation: true
    });

    this.particleSystem = new THREE.Points(particleGeometry, particleMaterial);
    this.scene.add(this.particleSystem);

    // Create point cloud
    this.createPointCloud();

    // Set camera position
    if (this.camera instanceof THREE.PerspectiveCamera) {
      this.camera.position.set(0, 0, 12);
      this.camera.lookAt(0, 0, 0);
    }
  }

  private createPointCloud() {
    const density = (this.config.defaultConfig as any).geometry?.pointCloudDensity || 2000;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(density * 3);

    // Create point cloud in a complex procedural pattern
    for (let i = 0; i < density; i++) {
      const t = i / density;
      const radius = 2 + Math.sin(t * Math.PI * 8) * 1.5;
      const theta = t * Math.PI * 16;
      const phi = t * Math.PI * 4;

      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = radius * Math.cos(phi);
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({
      size: 0.02,
      color: new THREE.Color((this.config.defaultConfig as any).colors?.accent2 || '#16213e'),
      transparent: true,
      opacity: 0.3,
      blending: THREE.AdditiveBlending
    });

    this.pointCloud = new THREE.Points(geometry, material);
    this.scene.add(this.pointCloud);
  }

  update() {
    this.time = this.clock.getElapsedTime();
    const delta = this.clock.getDelta();

    // Update lines
    this.lines.forEach(line => {
      line.update(this.time, this.audioData, this.config.defaultConfig);
    });

    // Update particles
    this.particles.forEach(particle => {
      particle.update(delta, this.time, this.audioData, this.config.defaultConfig);
    });

    // Update particle system geometry
    if (this.particleSystem) {
      const positions = this.particleSystem.geometry.attributes.position;
      for (let i = 0; i < this.particles.length; i++) {
        positions.array[i * 3] = this.particles[i].position.x;
        positions.array[i * 3 + 1] = this.particles[i].position.y;
        positions.array[i * 3 + 2] = this.particles[i].position.z;
      }
      positions.needsUpdate = true;
    }

    // Rotate point cloud with audio reactivity
    if (this.pointCloud) {
      const rotationSpeed = (this.config.defaultConfig as any).motion?.flowSpeed || 0.5;
      const audioBoost = (this.audioData.low + this.audioData.mid) * 0.5;
      this.pointCloud.rotation.y += delta * rotationSpeed * (1 + audioBoost);
      this.pointCloud.rotation.x += delta * rotationSpeed * 0.5;
    }

    // Apply VFX
    if (this.config.vfx) {
      applyVFX(this, this.audioData);
    }
  }

  dispose() {
    this.lines.forEach(line => {
      this.scene.remove(line.getMesh());
      line.dispose();
    });

    if (this.particleSystem) {
      this.scene.remove(this.particleSystem);
      this.particleSystem.geometry.dispose();
      (this.particleSystem.material as THREE.Material).dispose();
    }

    if (this.pointCloud) {
      this.scene.remove(this.pointCloud);
      this.pointCloud.geometry.dispose();
      (this.pointCloud.material as THREE.Material).dispose();
    }
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  config: any
): BasePreset {
  return new ProceduralComplexPreset(scene, camera, renderer, config);
}
