import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

// Paleta de colores solicitada para el preset Analysis
const COLOR_PALETTE = [
  '#5e2577', '#702d76', '#8a3a75', '#a44875', '#ba5374', '#d36075',
  '#e86c73', '#ed7c75', '#f18c73', '#f59d70', '#f9af71', '#fdbe74',
  '#ffcd8f', '#ffdfb6'
];

export const config: PresetConfig = {
  name: 'ANALYSIS',
  description: '3D audio spectrum analyzer with smooth pastel particle transitions and frequency/dB grid.',
  author: 'AudioVisualizer',
  version: '2.1.0',
  category: 'analysis',
  tags: ['spectrum', 'analysis', 'particles', 'grid', 'nature'],
  thumbnail: 'analysis_thumb.png',
  note: 48,
  defaultConfig: {
    radius: 8,
    particleCount: 60,
    colors: {
      band1: COLOR_PALETTE[0],
      band2: COLOR_PALETTE[3],
      band3: COLOR_PALETTE[5],
      band4: COLOR_PALETTE[7],
      band5: COLOR_PALETTE[9],
      band6: COLOR_PALETTE[13]
    }
  },
  controls: [
    { name: 'radius', type: 'slider', label: 'Camera Radius', min: 5, max: 15, step: 0.5, default: 8 },
    { name: 'particleCount', type: 'slider', label: 'Max Particles', min: 20, max: 120, step: 5, default: 60 },
    { name: 'colors.band1', type: 'color', label: '40-200Hz Color', default: COLOR_PALETTE[0] },
    { name: 'colors.band2', type: 'color', label: '200-400Hz Color', default: COLOR_PALETTE[3] },
    { name: 'colors.band3', type: 'color', label: '400-600Hz Color', default: COLOR_PALETTE[5] },
    { name: 'colors.band4', type: 'color', label: '600-1000Hz Color', default: COLOR_PALETTE[7] },
    { name: 'colors.band5', type: 'color', label: '1-10kHz Color', default: COLOR_PALETTE[9] },
    { name: 'colors.band6', type: 'color', label: '10-22kHz Color', default: COLOR_PALETTE[13] }
  ],
  audioMapping: {
    band1: { description: 'Sub-bass frequencies', frequency: '40-200 Hz', effect: 'Particle density and movement in zone 1' },
    band2: { description: 'Bass frequencies', frequency: '200-400 Hz', effect: 'Particle density and movement in zone 2' },
    band3: { description: 'Low mid frequencies', frequency: '400-600 Hz', effect: 'Particle density and movement in zone 3' },
    band4: { description: 'Mid frequencies', frequency: '600-1000 Hz', effect: 'Particle density and movement in zone 4' },
    band5: { description: 'High mid frequencies', frequency: '1000-10000 Hz', effect: 'Particle density and movement in zone 5' },
    band6: { description: 'High frequencies', frequency: '10000-22000 Hz', effect: 'Particle density and movement in zone 6' }
  },
  performance: { complexity: 'medium', recommendedFPS: 60, gpuIntensive: false }
};

interface Particle {
  mesh: THREE.Mesh;
  speed: number;
  radius: number;
  offset: number;
  scale: number;
  life: number;
  deathTimer: number;
  birthTimer: number;
  basePosition: THREE.Vector3;
}

interface ParticleRange {
  particles: Particle[];
  color: string;
  centerX: number;
  targetCount: number;
  currentCount: number;
  audioLevel: number;
  smoothedLevel: number;
}

type BandName = 'band1' | 'band2' | 'band3' | 'band4' | 'band5' | 'band6';

class AnalysisSpectrum extends BasePreset {
  private group!: THREE.Group;
  private particleGroups!: Record<BandName, ParticleRange>;
  private gridFloor?: THREE.GridHelper;
  private gridBack?: THREE.GridHelper;
  private frequencyLabels?: THREE.Group;
  private dbLabels?: THREE.Group;
  private ambient?: THREE.AmbientLight;
  private pointLight?: THREE.PointLight;
  private currentConfig: any;
  private initialCameraPosition = this.camera.position.clone();
  private initialCameraQuaternion = this.camera.quaternion.clone();

  private particleGeometry!: THREE.SphereGeometry;

  private smoothingFactor = 0.85;
  private readonly BIRTH_DURATION = 0.1;
  private readonly DEATH_DURATION = 0.5;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, cfg: PresetConfig) {
    super(scene, camera, renderer, cfg);
    this.currentConfig = cfg.defaultConfig;
  }

  init(): void {
    // Reiniciar el reloj para evitar valores desfasados
    this.clock.start();

    this.group = new THREE.Group();
    this.scene.add(this.group);

    this.particleGeometry = new THREE.SphereGeometry(0.05, 16, 16);

    this.createFrequencyGrid();
    this.createDbGrid();
    this.createFrequencyLabels();
    this.createDbLabels();

    this.ambient = new THREE.AmbientLight(0x111111, 0.2);
    this.pointLight = new THREE.PointLight(0xffffff, 1.5);
    this.pointLight.position.set(0, 8, 2);
    this.pointLight.castShadow = true;

    const colorLight = new THREE.PointLight(0x4444ff, 0.8);
    colorLight.position.set(-4, 4, -2);

    this.scene.add(this.ambient);
    this.scene.add(this.pointLight);
    this.scene.add(colorLight);

    this.particleGroups = {
      band1: { particles: [], color: this.currentConfig.colors.band1, centerX: -3.2, targetCount: 0, currentCount: 0, audioLevel: 0, smoothedLevel: 0 },
      band2: { particles: [], color: this.currentConfig.colors.band2, centerX: -1.92, targetCount: 0, currentCount: 0, audioLevel: 0, smoothedLevel: 0 },
      band3: { particles: [], color: this.currentConfig.colors.band3, centerX: -0.64, targetCount: 0, currentCount: 0, audioLevel: 0, smoothedLevel: 0 },
      band4: { particles: [], color: this.currentConfig.colors.band4, centerX: 0.64, targetCount: 0, currentCount: 0, audioLevel: 0, smoothedLevel: 0 },
      band5: { particles: [], color: this.currentConfig.colors.band5, centerX: 1.92, targetCount: 0, currentCount: 0, audioLevel: 0, smoothedLevel: 0 },
      band6: { particles: [], color: this.currentConfig.colors.band6, centerX: 3.2, targetCount: 0, currentCount: 0, audioLevel: 0, smoothedLevel: 0 }
    };
  }

  private createFrequencyGrid(): void {
    this.gridFloor = new THREE.GridHelper(12, 24, 0x555555, 0x222222);
    this.gridFloor.material.opacity = 0.6;
    this.gridFloor.material.transparent = true;
    // @ts-ignore emissive exists at runtime
    this.gridFloor.material.emissive = new THREE.Color(0x111111);
    // @ts-ignore emissiveIntensity exists at runtime
    this.gridFloor.material.emissiveIntensity = 0.25;
    this.scene.add(this.gridFloor);
  }

  private createDbGrid(): void {
    this.gridBack = new THREE.GridHelper(8, 16, 0x663333, 0x331111);
    this.gridBack.rotation.x = Math.PI / 2;
    this.gridBack.position.set(0, 2, -6);
    this.gridBack.material.opacity = 0.5;
    this.gridBack.material.transparent = true;
    // @ts-ignore emissive exists at runtime
    this.gridBack.material.emissive = new THREE.Color(0x221111);
    // @ts-ignore emissiveIntensity exists at runtime
    this.gridBack.material.emissiveIntensity = 0.2;
    this.scene.add(this.gridBack);
  }

  private createFrequencyLabels(): void {
    this.frequencyLabels = new THREE.Group();
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d')!;
    canvas.width = 128;
    canvas.height = 32;

    const frequencies = ['40Hz', '200Hz', '400Hz', '600Hz', '1kHz', '10kHz', '22kHz'];
    const colors = [
      COLOR_PALETTE[0],
      COLOR_PALETTE[2],
      COLOR_PALETTE[4],
      COLOR_PALETTE[6],
      COLOR_PALETTE[9],
      COLOR_PALETTE[11],
      COLOR_PALETTE[13]
    ];
    const positions = [-3.6, -2.4, -1.2, 0, 1.2, 2.4, 3.6];

    frequencies.forEach((freq, i) => {
      context.clearRect(0, 0, 128, 32);
      context.shadowColor = colors[i];
      context.shadowBlur = 10;
      context.fillStyle = colors[i];
      context.font = 'bold 16px Arial';
      context.textAlign = 'center';
      context.fillText(freq, 64, 20);

      const texture = new THREE.CanvasTexture(canvas);
      const material = new THREE.SpriteMaterial({
        map: texture,
        transparent: true,
        opacity: 0.9
      });
      const sprite = new THREE.Sprite(material);
      sprite.position.set(positions[i], 0.15, 3);
      sprite.scale.set(1.0, 0.25, 1);

      this.frequencyLabels!.add(sprite);
    });

    this.scene.add(this.frequencyLabels);
  }

  private createDbLabels(): void {
    this.dbLabels = new THREE.Group();
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d')!;
    canvas.width = 64;
    canvas.height = 32;

    const dbLevels = ['-60dB', '-40dB', '-20dB', '0dB'];
    const yPositions = [0.5, 1.5, 2.5, 3.5];

    dbLevels.forEach((db, i) => {
      context.clearRect(0, 0, 64, 32);
      context.shadowColor = '#884C3A';
      context.shadowBlur = 8;
      context.fillStyle = '#D9B9A9';
      context.font = 'bold 14px Arial';
      context.textAlign = 'center';
      context.fillText(db, 32, 20);

      const texture = new THREE.CanvasTexture(canvas);
      const material = new THREE.SpriteMaterial({
        map: texture,
        transparent: true,
        opacity: 0.9
      });
      const sprite = new THREE.Sprite(material);
      sprite.position.set(-4.5, yPositions[i], -5.8);
      sprite.scale.set(0.8, 0.2, 1);

      this.dbLabels!.add(sprite);
    });

    this.scene.add(this.dbLabels);
  }

  private createParticle(colorHex: string, centerX: number): Particle {
    const color = new THREE.Color(colorHex);
    const material = new THREE.MeshLambertMaterial({
      color,
      emissive: color.clone().multiplyScalar(0.3),
      emissiveIntensity: 0.4,
      transparent: true,
      opacity: 0
    });

    const mesh = new THREE.Mesh(this.particleGeometry, material);

    const baseX = centerX + (Math.random() - 0.5) * 1.2;
    const baseY = 0.5 + Math.random() * 1.5;
    const baseZ = (Math.random() - 0.5) * 2;
    const radius = 0.2 + Math.random() * 0.4;
    const speed = 0.4 + Math.random() * 0.6;
    const offset = Math.random() * Math.PI * 2;
    const scale = 0.15 + Math.random() * 0.2;

    mesh.scale.setScalar(0.0001);
    mesh.position.set(baseX, baseY, baseZ);

    this.group.add(mesh);

    return {
      mesh,
      speed,
      radius,
      offset,
      scale,
      life: 0,
      deathTimer: 0,
      birthTimer: this.BIRTH_DURATION,
      basePosition: new THREE.Vector3(baseX, baseY, baseZ)
    };
  }

  private adjustParticles(range: ParticleRange, target: number, deltaTime: number): void {
    range.targetCount = target;

    if (range.currentCount < target) {
      const spawnRate = 10.0;
      if (Math.random() < spawnRate * deltaTime) {
        const newParticle = this.createParticle(range.color, range.centerX);
        range.particles.push(newParticle);
        range.currentCount++;
      }
    }

    if (range.currentCount > target) {
      range.particles.forEach(particle => {
        if (particle.life > 0.5 && particle.deathTimer === 0 && Math.random() < 0.5 * deltaTime) {
          particle.deathTimer = this.DEATH_DURATION;
          particle.life = -1;
        }
      });
    }

    for (let i = range.particles.length - 1; i >= 0; i--) {
      const particle = range.particles[i];
      const material = particle.mesh.material as THREE.MeshLambertMaterial;

      if (particle.birthTimer > 0) {
        particle.birthTimer -= deltaTime;
        const progress = 1 - particle.birthTimer / this.BIRTH_DURATION;
        particle.mesh.scale.setScalar(particle.scale * progress);
        material.opacity = progress;
        particle.life = progress;
      } else if (particle.deathTimer > 0) {
        particle.deathTimer -= deltaTime;
        const progress = 1 - particle.deathTimer / this.DEATH_DURATION;
        particle.mesh.scale.setScalar(particle.scale * (1 - progress));
        material.opacity = 1 - progress;
        if (particle.deathTimer <= 0) {
          this.group.remove(particle.mesh);
          range.particles.splice(i, 1);
          range.currentCount--;
        }
      } else {
        particle.life = Math.min(1.0, particle.life + deltaTime * 0.8);
      }
    }
  }

  update(): void {
    const time = this.clock.getElapsedTime();
    const deltaTime = this.clock.getDelta();
    const fft = this.audioData.fft;

    const sampleRate = 44100;
    const nyquist = sampleRate / 2;
    const ranges: [number, number][] = [
      [40, 200],
      [200, 400],
      [400, 600],
      [600, 1000],
      [1000, 10000],
      [10000, 22000]
    ];

    const amps = ranges.map(([low, high]) => {
      const start = Math.floor((low / nyquist) * fft.length);
      const end = Math.floor((high / nyquist) * fft.length);
      let sum = 0;
      let count = 0;

      for (let i = start; i < end && i < fft.length; i++) {
        sum += fft[i] * fft[i];
        count++;
      }

      return count > 0 ? Math.sqrt(sum / count) : 0;
    });

    const keys: BandName[] = ['band1', 'band2', 'band3', 'band4', 'band5', 'band6'];

    keys.forEach((key, i) => {
      const range = this.particleGroups[key];
      const rawAmp = Math.max(amps[i], 0);

      range.audioLevel = rawAmp;
      range.smoothedLevel = range.smoothedLevel * this.smoothingFactor + rawAmp * (1 - this.smoothingFactor);

      const sensitivity = 1.2;
      const minParticles = 5;
      const maxPerBand = Math.floor(this.currentConfig.particleCount / 6);
      const target = Math.max(minParticles,
        Math.min(maxPerBand, Math.floor(range.smoothedLevel * sensitivity * maxPerBand))
      );

      this.adjustParticles(range, target, deltaTime);

      range.particles.forEach(particle => {
        if (particle.life > 0 && particle.deathTimer === 0) {
          const flightTime = time * particle.speed + particle.offset;
          const audioInfluence = range.smoothedLevel * 1.5;
          const jitter = particle.radius + audioInfluence * 0.5;
          const x = particle.basePosition.x + Math.sin(flightTime) * jitter;
          const y = particle.basePosition.y + Math.cos(flightTime * 1.5) * jitter * 0.5 + audioInfluence * 0.3;
          const z = particle.basePosition.z + Math.cos(flightTime * 0.7) * jitter;

          particle.mesh.position.set(x, y, z);

          const material = particle.mesh.material as THREE.MeshLambertMaterial;
          const glowIntensity = 0.4 + range.audioLevel * 0.8;
          material.emissiveIntensity = glowIntensity;
        }
      });
    });

    const radius = this.currentConfig.radius;
    const cameraSpeed = 0.12;
    this.camera.position.x = Math.cos(time * cameraSpeed) * radius;
    this.camera.position.z = Math.sin(time * cameraSpeed) * radius;
    this.camera.position.y = radius * 0.4 + 2.5 + Math.sin(time * 0.25) * 0.3;
    this.camera.lookAt(0, 1.5, 0);
  }

  updateConfig(newConfig: any): void {
    this.currentConfig = { ...this.currentConfig, ...newConfig };

    Object.entries(this.particleGroups).forEach(([key, range]) => {
      const newColor = this.currentConfig.colors[key as BandName];
      if (newColor && newColor !== range.color) {
        range.color = newColor;
        range.particles.forEach(particle => {
          const color = new THREE.Color(newColor);
          const material = particle.mesh.material as THREE.MeshLambertMaterial;
          material.color.copy(color);
          material.emissive = color.clone().multiplyScalar(0.3);
        });
      }
    });
  }

  dispose(): void {
    this.scene.remove(this.group);
    if (this.gridFloor) this.scene.remove(this.gridFloor);
    if (this.gridBack) this.scene.remove(this.gridBack);
    if (this.frequencyLabels) this.scene.remove(this.frequencyLabels);
    if (this.dbLabels) this.scene.remove(this.dbLabels);
    if (this.ambient) this.scene.remove(this.ambient);
    if (this.pointLight) this.scene.remove(this.pointLight);

    this.camera.position.copy(this.initialCameraPosition);
    this.camera.quaternion.copy(this.initialCameraQuaternion);

    this.group.clear();
    this.particleGeometry?.dispose();

    Object.keys(this.particleGroups).forEach(key => {
      this.particleGroups[key as BandName] = {
        particles: [],
        color: '',
        centerX: 0,
        targetCount: 0,
        currentCount: 0,
        audioLevel: 0,
        smoothedLevel: 0
      };
    });
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  cfg: PresetConfig
): BasePreset {
  return new AnalysisSpectrum(scene, camera, renderer, cfg);
}
