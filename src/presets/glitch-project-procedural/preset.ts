import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';
import { applyVFX } from './vfx';

export const config: PresetConfig = {
  name: "Procedural Complex",
  description: "Beat-reactive particle system with explosive kick response",
  author: "Glitch Project",
  version: "2.0.0",
  category: "glitch-project",
  tags: ["procedural", "particles", "beat-reactive", "kick-responsive"],
  thumbnail: "procedural_complex_thumb.png",
  note: 48,
  defaultConfig: {
    opacity: 1.0,
    fadeMs: 300,
    particleCount: 2000,
    kickThreshold: 0.6,
    explosionForce: 3.0,
    particleSize: 0.05,
    particleColor: "#e94560",
    attractionForce: 0.0005
  },
  controls: [
    {
      name: "particleCount",
      type: "slider",
      label: "Particle Count",
      min: 500,
      max: 5000,
      step: 100,
      default: 2000
    },
    {
      name: "kickThreshold",
      type: "slider",
      label: "Kick Sensitivity",
      min: 0.3,
      max: 0.9,
      step: 0.05,
      default: 0.6
    },
    {
      name: "explosionForce",
      type: "slider",
      label: "Explosion Force",
      min: 1.0,
      max: 8.0,
      step: 0.5,
      default: 3.0
    },
    {
      name: "particleSize",
      type: "slider",
      label: "Particle Size",
      min: 0.02,
      max: 0.15,
      step: 0.01,
      default: 0.05
    },
    {
      name: "particleColor",
      type: "color",
      label: "Particle Color",
      default: "#e94560"
    }
  ],
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

// LÍNEAS ELIMINADAS - Solo partículas reactivas al beat

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
    // Check if vertical mode
    const outputMode = localStorage.getItem('outputMode') || 'standard';
    const isVertical = outputMode === 'vertical';
    const verticalScale = isVertical ? 2.0 : 1.0; // More vertical spread
    const horizontalScale = isVertical ? 0.6 : 1.0; // Less horizontal spread

    this.position = new THREE.Vector3(
      (Math.random() - 0.5) * 6 * horizontalScale,
      (Math.random() - 0.5) * 10 * verticalScale,
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

  update(delta: number, time: number, audioData: any, config: any, explosionForce: number = 0) {
    this.acceleration.set(0, 0, 0);

    // ONLY MOVE ON EXPLOSION - Beat-reactive only!
    if (explosionForce > 0) {
      const fromCenter = this.position.clone().normalize().multiplyScalar(explosionForce * 0.5);
      this.acceleration.add(fromCenter);
    }

    // Very weak attraction to center (to bring particles back after explosion)
    const toCenter = this.position.clone().negate();
    toCenter.y *= 0.1; // Even weaker on Y-axis
    toCenter.normalize().multiplyScalar(0.0003);
    this.acceleration.add(toCenter);

    // Update physics
    this.velocity.add(this.acceleration);
    this.velocity.multiplyScalar(0.95); // Higher drag to settle faster
    this.position.add(this.velocity);

    // Update life
    this.life -= delta / this.maxLife;

    // Respawn if dead
    if (this.life <= 0) {
      this.respawn();
    }
  }

  respawn() {
    // Check if vertical mode
    const outputMode = localStorage.getItem('outputMode') || 'standard';
    const isVertical = outputMode === 'vertical';
    const verticalScale = isVertical ? 2.5 : 1.0;
    const horizontalScale = isVertical ? 0.6 : 1.0;

    const radius = 3 + Math.random() * 2;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.random() * Math.PI;

    this.position.set(
      radius * Math.sin(phi) * Math.cos(theta) * horizontalScale,
      radius * Math.sin(phi) * Math.sin(theta) * verticalScale,
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
// MAIN PRESET CLASS - Beat-reactive particles only
// ============================================================================
export class ProceduralComplexPreset extends BasePreset {
  private particles: DynamicParticle[] = [];
  private particleSystem: THREE.Points | null = null;
  private time: number = 0;
  private explosionForce: number = 0;
  private lastKickTime: number = 0;

  constructor(
    scene: THREE.Scene,
    camera: THREE.Camera,
    renderer: THREE.WebGLRenderer,
    config: any,
    videoElement: HTMLVideoElement
  ) {
    super(scene, camera, renderer, config, videoElement);
  }

  init() {
    this.initialize();
  }

  private initialize() {
    // Detect output mode for camera positioning
    const outputMode = localStorage.getItem('outputMode') || 'standard';
    const isVertical = outputMode === 'vertical';

    // Get config values
    const cfg = this.config.defaultConfig as any;
    const particleCount = cfg.particleCount || 2000;
    const particleSize = cfg.particleSize || 0.05;
    const particleColor = cfg.particleColor || '#e94560';

    // Create particle system ONLY
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
      size: particleSize,
      color: new THREE.Color(particleColor),
      transparent: true,
      opacity: 0.9,
      blending: THREE.AdditiveBlending,
      sizeAttenuation: true
    });

    this.particleSystem = new THREE.Points(particleGeometry, particleMaterial);
    this.scene.add(this.particleSystem);

    // Set camera position - adapt for vertical mode
    if (this.camera instanceof THREE.PerspectiveCamera) {
      if (isVertical) {
        this.camera.position.set(0, 0, 14);
        this.camera.fov = 85;
        this.camera.updateProjectionMatrix();
      } else {
        this.camera.position.set(0, 0, 12);
        this.camera.fov = 75;
        this.camera.updateProjectionMatrix();
      }
      this.camera.lookAt(0, 0, 0);
    }
  }

  update() {
    this.time = this.clock.getElapsedTime();
    const delta = this.clock.getDelta();

    // Get config values
    const cfg = this.config.defaultConfig as any;
    const kickThreshold = cfg.kickThreshold || 0.6;
    const explosionForce = cfg.explosionForce || 3.0;

    // Detect kick/bass hits for explosion effect - BEAT REACTIVE ONLY!
    const lowFreq = this.audioData.low;
    const timeSinceLastKick = this.time - this.lastKickTime;

    // Trigger explosion on kick
    if ((lowFreq > kickThreshold && timeSinceLastKick > 0.15)) {
      this.explosionForce = explosionForce; // Use config value
      this.lastKickTime = this.time;
      console.log('💥 KICK! Explosion Force:', explosionForce);
    }

    // Decay explosion force smoothly
    this.explosionForce *= 0.9;
    if (this.explosionForce < 0.01) {
      this.explosionForce = 0;
    }

    // Update particles with explosion force - ONLY THIS!
    this.particles.forEach(particle => {
      particle.update(delta, this.time, this.audioData, cfg, this.explosionForce);
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

    // VFX
    if (this.config.vfx) {
      applyVFX(this, this.audioData);
    }
  }

  dispose() {
    if (this.particleSystem) {
      this.scene.remove(this.particleSystem);
      this.particleSystem.geometry.dispose();
      (this.particleSystem.material as THREE.Material).dispose();
    }
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  config: any,
  videoElement: HTMLVideoElement
): BasePreset {
  return new ProceduralComplexPreset(scene, camera, renderer, config, videoElement);
}
