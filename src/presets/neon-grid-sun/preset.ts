import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'Particle Grid Sun',
  description: 'Neon particles with radial lines forming a solar grid',
  author: 'AudioVisualizer',
  version: '1.0.0',
  category: 'abstract',
  tags: ['particles', 'lines', 'sun'],
  thumbnail: 'particle_grid_sun_thumb.png',
  note: 71,
  defaultConfig: {
    particleColor: '#ffcc00',
    lineColor: '#ff00ff',
    rotationSpeed: 0.2
  },
  controls: [
    { name: 'particleColor', type: 'color', label: 'Particle Color', default: '#ffcc00' },
    { name: 'lineColor', type: 'color', label: 'Line Color', default: '#ff00ff' },
    { name: 'rotationSpeed', type: 'slider', label: 'Rotation Speed', min: 0.0, max: 1.0, step: 0.05, default: 0.2 }
  ],
  audioMapping: {
    low: { description: 'Pulses particle size', frequency: '20-250 Hz', effect: 'Particle scaling' },
    high: { description: 'Boosts line brightness', frequency: '4000+ Hz', effect: 'Line opacity' }
  },
  performance: { complexity: 'low', recommendedFPS: 60, gpuIntensive: false }
};

class ParticleGridSunPreset extends BasePreset {
  private particles!: THREE.Points;
  private lines!: THREE.LineSegments;
  private currentConfig: any;
  private particleGeometry!: THREE.BufferGeometry;
  private lineGeometry!: THREE.BufferGeometry;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, cfg: PresetConfig, videoElement: HTMLVideoElement) {
    super(scene, camera, renderer, cfg, videoElement);
    this.currentConfig = { ...cfg.defaultConfig };
  }

  public init(): void {
    const particleCount = 800;
    const positions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      const radius = 4 + Math.random() * 2;
      const angle = (i / particleCount) * Math.PI * 2;
      positions[i * 3] = Math.cos(angle) * radius;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 1.5;
      positions[i * 3 + 2] = Math.sin(angle) * radius;
    }

    this.particleGeometry = new THREE.BufferGeometry();
    this.particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const particleMaterial = new THREE.PointsMaterial({
      color: new THREE.Color(this.currentConfig.particleColor),
      size: 0.12,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });

    this.particles = new THREE.Points(this.particleGeometry, particleMaterial);
    this.scene.add(this.particles);

    const lineSegments = 60;
    const linePositions = new Float32Array(lineSegments * 2 * 3);
    for (let i = 0; i < lineSegments; i++) {
      const angle = (i / lineSegments) * Math.PI * 2;
      const x = Math.cos(angle) * 6;
      const z = Math.sin(angle) * 6;
      linePositions[i * 6] = 0;
      linePositions[i * 6 + 1] = 0;
      linePositions[i * 6 + 2] = 0;
      linePositions[i * 6 + 3] = x;
      linePositions[i * 6 + 4] = 0;
      linePositions[i * 6 + 5] = z;
    }

    this.lineGeometry = new THREE.BufferGeometry();
    this.lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));

    const lineMaterial = new THREE.LineBasicMaterial({
      color: new THREE.Color(this.currentConfig.lineColor),
      transparent: true,
      opacity: 0.25,
      depthWrite: false,
    });

    this.lines = new THREE.LineSegments(this.lineGeometry, lineMaterial);
    this.scene.add(this.lines);
  }

  public update(): void {
    const delta = this.clock.getDelta();
    const spin = (this.currentConfig.rotationSpeed + this.audioData.low * 0.5) * delta;

    if (this.particles) {
      const material = this.particles.material as THREE.PointsMaterial;
      material.color.set(this.currentConfig.particleColor);
      material.size = 0.12 + this.audioData.low * 0.3;
      this.particles.rotation.y += spin;
    }

    if (this.lines) {
      const material = this.lines.material as THREE.LineBasicMaterial;
      material.color.set(this.currentConfig.lineColor);
      material.opacity = 0.25 + this.audioData.high * 0.5;
      this.lines.rotation.y -= spin * 0.5;
    }
  }

  public dispose(): void {
    if (this.particles) {
      this.scene.remove(this.particles);
      this.particleGeometry.dispose();
      (this.particles.material as THREE.Material).dispose();
    }

    if (this.lines) {
      this.scene.remove(this.lines);
      this.lineGeometry.dispose();
      (this.lines.material as THREE.Material).dispose();
    }
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  cfg: PresetConfig,
  videoElement: HTMLVideoElement,
  shaderCode?: string
): BasePreset {
  return new ParticleGridSunPreset(scene, camera, renderer, cfg, videoElement);
}
