import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'ANALYSIS',
  description: '3D audio spectrum analyzer with smooth butterfly transitions and frequency/dB grid.',
  author: 'AudioVisualizer',
  version: '2.0.0',
  category: 'analysis',
  tags: ['spectrum', 'analysis', 'butterfly', 'grid', 'nature'],
  thumbnail: 'analysis_thumb.png',
  note: 48,
  defaultConfig: {
    radius: 8,
    butterflyCount: 60,
    colors: {
      band1: '#00FFFF',  // 40-200Hz - Cian eléctrico
      band2: '#00FF00',  // 200-400Hz - Verde neón
      band3: '#FFFF00',  // 400-600Hz - Amarillo brillante
      band4: '#FF0080',  // 600-1000Hz - Magenta vibrante
      band5: '#8000FF',  // 1000-10000Hz - Púrpura eléctrico
      band6: '#FF4000'   // 10000-22000Hz - Naranja ardiente
    }
  },
  controls: [
    { name: 'radius', type: 'slider', label: 'Camera Radius', min: 5, max: 15, step: 0.5, default: 8 },
    { name: 'butterflyCount', type: 'slider', label: 'Max Butterflies', min: 20, max: 120, step: 5, default: 60 },
    { name: 'colors.band1', type: 'color', label: '40-200Hz Color', default: '#00FFFF' },
    { name: 'colors.band2', type: 'color', label: '200-400Hz Color', default: '#00FF00' },
    { name: 'colors.band3', type: 'color', label: '400-600Hz Color', default: '#FFFF00' },
    { name: 'colors.band4', type: 'color', label: '600-1000Hz Color', default: '#FF0080' },
    { name: 'colors.band5', type: 'color', label: '1-10kHz Color', default: '#8000FF' },
    { name: 'colors.band6', type: 'color', label: '10-22kHz Color', default: '#FF4000' }
  ],
  audioMapping: {
    band1: { description: 'Sub-bass frequencies', frequency: '40-200 Hz', effect: 'Butterfly density and movement in zone 1' },
    band2: { description: 'Bass frequencies', frequency: '200-400 Hz', effect: 'Butterfly density and movement in zone 2' },
    band3: { description: 'Low mid frequencies', frequency: '400-600 Hz', effect: 'Butterfly density and movement in zone 3' },
    band4: { description: 'Mid frequencies', frequency: '600-1000 Hz', effect: 'Butterfly density and movement in zone 4' },
    band5: { description: 'High mid frequencies', frequency: '1000-10000 Hz', effect: 'Butterfly density and movement in zone 5' },
    band6: { description: 'High frequencies', frequency: '10000-22000 Hz', effect: 'Butterfly density and movement in zone 6' }
  },
  performance: { complexity: 'medium', recommendedFPS: 60, gpuIntensive: false }
};

interface Butterfly {
  group: THREE.Group;
  wings: { left: THREE.Mesh; right: THREE.Mesh; };
  body: THREE.Mesh;
  speed: number;
  radius: number;
  offset: number;
  scale: number;
  life: number;
  deathTimer: number;
  birthTimer: number;
  petals?: THREE.Group;
  baseY: number;
}

interface ButterflyRange {
  butterflies: Butterfly[];
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
  private butterflyGroups!: Record<BandName, ButterflyRange>;
  private gridFloor?: THREE.GridHelper;
  private gridBack?: THREE.GridHelper;
  private frequencyLabels?: THREE.Group;
  private dbLabels?: THREE.Group;
  private ambient?: THREE.AmbientLight;
  private pointLight?: THREE.PointLight;
  private currentConfig: any;
  private initialCameraPosition = this.camera.position.clone();
  private initialCameraQuaternion = this.camera.quaternion.clone();
  
  private wingGeometry!: THREE.CircleGeometry;
  private bodyGeometry!: THREE.CapsuleGeometry;
  private petalGeometry!: THREE.PlaneGeometry;
  
  private smoothingFactor = 0.85;
  private lastTime = 0;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, cfg: PresetConfig) {
    super(scene, camera, renderer, cfg);
    this.currentConfig = cfg.defaultConfig;
  }

  init(): void {
    this.group = new THREE.Group();
    this.scene.add(this.group);

    this.wingGeometry = new THREE.CircleGeometry(0.08, 8);
    this.bodyGeometry = new THREE.CapsuleGeometry(0.008, 0.06, 4, 8);
    this.petalGeometry = new THREE.PlaneGeometry(0.02, 0.03);

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

    const colors = this.currentConfig.colors;
    const bandCenters = [-3.0, -1.8, -0.6, 0.6, 1.8, 3.0];
    
    this.butterflyGroups = {
      band1: { butterflies: [], color: colors.band1, centerX: bandCenters[0], targetCount: 0, currentCount: 0, audioLevel: 0, smoothedLevel: 0 },
      band2: { butterflies: [], color: colors.band2, centerX: bandCenters[1], targetCount: 0, currentCount: 0, audioLevel: 0, smoothedLevel: 0 },
      band3: { butterflies: [], color: colors.band3, centerX: bandCenters[2], targetCount: 0, currentCount: 0, audioLevel: 0, smoothedLevel: 0 },
      band4: { butterflies: [], color: colors.band4, centerX: bandCenters[3], targetCount: 0, currentCount: 0, audioLevel: 0, smoothedLevel: 0 },
      band5: { butterflies: [], color: colors.band5, centerX: bandCenters[4], targetCount: 0, currentCount: 0, audioLevel: 0, smoothedLevel: 0 },
      band6: { butterflies: [], color: colors.band6, centerX: bandCenters[5], targetCount: 0, currentCount: 0, audioLevel: 0, smoothedLevel: 0 }
    };

    Object.values(this.butterflyGroups).forEach(range => {
      for (let i = 0; i < 2; i++) {
        range.butterflies.push(this.createButterfly(range.color, range.centerX));
        range.currentCount++;
      }
    });
  }

  private createFrequencyGrid(): void {
    this.gridFloor = new THREE.GridHelper(12, 24, 0x00FFAA, 0x006644);
    this.gridFloor.material.opacity = 0.8;
    this.gridFloor.material.transparent = true;
    this.gridFloor.material.emissive = new THREE.Color(0x002244);
    this.gridFloor.material.emissiveIntensity = 0.3;
    this.scene.add(this.gridFloor);
  }

  private createDbGrid(): void {
    this.gridBack = new THREE.GridHelper(8, 16, 0xFF4400, 0x884400);
    this.gridBack.rotation.x = Math.PI / 2;
    this.gridBack.position.set(0, 2, -6);
    this.gridBack.material.opacity = 0.7;
    this.gridBack.material.transparent = true;
    this.gridBack.material.emissive = new THREE.Color(0x441100);
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
    const colors = ['#00FFFF', '#00FF88', '#88FF00', '#FFFF00', '#FF8800', '#FF4400', '#FF0088'];
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
      
      this.frequencyLabels.add(sprite);
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
      context.shadowColor = '#FF6600';
      context.shadowBlur = 8;
      context.fillStyle = '#FFAA44';
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
      
      this.dbLabels.add(sprite);
    });
    
    this.scene.add(this.dbLabels);
  }

  private createButterfly(colorHex: string, centerX: number): Butterfly {
    const group = new THREE.Group();
    const color = new THREE.Color(colorHex);
    
    const wingMaterial = new THREE.MeshLambertMaterial({ 
      color: color,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.9,
      emissive: color.clone().multiplyScalar(0.3),
      emissiveIntensity: 0.4
    });
    
    const leftWing = new THREE.Mesh(this.wingGeometry, wingMaterial.clone());
    const rightWing = new THREE.Mesh(this.wingGeometry, wingMaterial.clone());
    
    leftWing.position.set(-0.06, 0, 0);
    rightWing.position.set(0.06, 0, 0);
    
    const bodyMaterial = new THREE.MeshLambertMaterial({ 
      color: 0xffffff,
      emissive: color.clone().multiplyScalar(0.2),
      emissiveIntensity: 0.3
    });
    const body = new THREE.Mesh(this.bodyGeometry, bodyMaterial);
    body.rotation.z = Math.PI / 2;
    
    group.add(leftWing);
    group.add(rightWing);
    group.add(body);
    
    const radius = 0.3 + Math.random() * 0.5;
    const speed = 0.4 + Math.random() * 0.6;
    const offset = Math.random() * Math.PI * 2;
    const scale = 0.6 + Math.random() * 0.4;
    const baseY = 0.5 + Math.random() * 1.5;
    
    group.scale.setScalar(scale);
    group.position.set(
      centerX + Math.cos(offset) * radius, 
      baseY, 
      Math.sin(offset) * radius
    );
    
    this.group.add(group);
    
    return {
      group,
      wings: { left: leftWing, right: rightWing },
      body,
      speed,
      radius,
      offset,
      scale,
      life: 0,
      deathTimer: 0,
      birthTimer: 0,
      baseY
    };
  }

  private createDeathPetals(butterfly: Butterfly): void {
    const petalsGroup = new THREE.Group();
    const color = new THREE.Color((butterfly.wings.left.material as THREE.MeshLambertMaterial).color);
    
    const petalCount = 6 + Math.floor(Math.random() * 3);
    
    for (let i = 0; i < petalCount; i++) {
      const petal = new THREE.Mesh(
        this.petalGeometry,
        new THREE.MeshLambertMaterial({
          color: color.clone().multiplyScalar(1.2),
          transparent: true,
          opacity: 0.8,
          emissive: color.clone().multiplyScalar(0.4),
          emissiveIntensity: 0.5
        })
      );
      
      const angle = (i / petalCount) * Math.PI * 2;
      petal.position.set(
        Math.cos(angle) * 0.02,
        Math.sin(angle) * 0.02,
        (Math.random() - 0.5) * 0.02
      );
      
      petal.rotation.z = Math.random() * Math.PI * 2;
      petal.userData = {
        velocity: new THREE.Vector3(
          Math.cos(angle) * (0.2 + Math.random() * 0.15),
          Math.random() * 0.1,
          Math.sin(angle) * (0.2 + Math.random() * 0.15)
        ),
        angularVelocity: (Math.random() - 0.5) * 0.15
      };
      
      petalsGroup.add(petal);
    }
    
    petalsGroup.position.copy(butterfly.group.position);
    butterfly.petals = petalsGroup;
    this.group.add(petalsGroup);
  }

  private updatePetals(deltaTime: number): void {
    Object.values(this.butterflyGroups).forEach(range => {
      range.butterflies.forEach(butterfly => {
        if (butterfly.petals) {
          butterfly.petals.children.forEach((petal: THREE.Mesh) => {
            const userData = petal.userData;
            
            petal.position.add(userData.velocity.clone().multiplyScalar(deltaTime));
            userData.velocity.y -= 0.3 * deltaTime;
            userData.velocity.multiplyScalar(0.98);
            
            petal.rotation.z += userData.angularVelocity * deltaTime;
            
            const material = petal.material as THREE.MeshLambertMaterial;
            material.opacity -= deltaTime * 1.5;
            
            if (material.opacity <= 0) {
              butterfly.petals!.remove(petal);
            }
          });
          
          if (butterfly.petals.children.length === 0) {
            this.group.remove(butterfly.petals);
            butterfly.petals = undefined;
          }
        }
      });
    });
  }

  private adjustButterflies(range: ButterflyRange, target: number, deltaTime: number): void {
    range.targetCount = target;
    
    if (range.currentCount < target) {
      const spawnRate = 3.0;
      if (Math.random() < spawnRate * deltaTime) {
        const newButterfly = this.createButterfly(range.color, range.centerX);
        newButterfly.birthTimer = 0.8;
        range.butterflies.push(newButterfly);
        range.currentCount++;
      }
    }
    
    if (range.currentCount > target) {
      range.butterflies.forEach(butterfly => {
        if (butterfly.life > 0.5 && butterfly.deathTimer === 0 && Math.random() < 0.5 * deltaTime) {
          butterfly.deathTimer = 1.2;
          butterfly.life = -1;
        }
      });
    }
    
    for (let i = range.butterflies.length - 1; i >= 0; i--) {
      const butterfly = range.butterflies[i];
      
      if (butterfly.birthTimer > 0) {
        butterfly.birthTimer -= deltaTime * 1.5;
        const birthProgress = 1.0 - butterfly.birthTimer;
        butterfly.group.scale.setScalar(butterfly.scale * birthProgress);
        butterfly.life = Math.min(1.0, birthProgress * 1.5);
        
        const opacity = Math.min(1.0, birthProgress * 2);
        butterfly.wings.left.material.opacity = opacity * 0.8;
        butterfly.wings.right.material.opacity = opacity * 0.8;
        
      } else if (butterfly.deathTimer > 0) {
        butterfly.deathTimer -= deltaTime;
        const deathProgress = 1.0 - butterfly.deathTimer;
        
        butterfly.speed *= (1.0 - deltaTime * 0.3);
        
        const scale = butterfly.scale * (1.0 - deathProgress * 0.3);
        butterfly.group.scale.setScalar(scale);
        
        const opacity = (1.0 - deathProgress) * 0.8;
        butterfly.wings.left.material.opacity = opacity;
        butterfly.wings.right.material.opacity = opacity;
        
        if (deathProgress > 0.6 && !butterfly.petals) {
          this.createDeathPetals(butterfly);
        }
        
        if (butterfly.deathTimer <= 0) {
          this.group.remove(butterfly.group);
          range.butterflies.splice(i, 1);
          range.currentCount--;
        }
        
      } else {
        butterfly.life = Math.min(1.0, butterfly.life + deltaTime * 0.8);
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
      const range = this.butterflyGroups[key];
      const rawAmp = Math.max(amps[i], 0);
      
      range.audioLevel = rawAmp;
      range.smoothedLevel = range.smoothedLevel * this.smoothingFactor + rawAmp * (1 - this.smoothingFactor);
      
      const sensitivity = 1.2;
      const minButterflies = 1;
      const maxPerBand = Math.floor(this.currentConfig.butterflyCount / 6);
      const target = Math.max(minButterflies, 
        Math.min(maxPerBand, Math.floor(range.smoothedLevel * sensitivity * maxPerBand))
      );
      
      this.adjustButterflies(range, target, deltaTime);
      
      range.butterflies.forEach(butterfly => {
        if (butterfly.life > 0 && butterfly.deathTimer === 0) {
          const flightTime = time * butterfly.speed + butterfly.offset;
          
          const audioInfluence = range.smoothedLevel * 1.5;
          const x = range.centerX + Math.cos(flightTime) * (butterfly.radius + audioInfluence * 0.2);
          const z = Math.sin(flightTime) * (butterfly.radius + audioInfluence * 0.2);
          const y = butterfly.baseY + Math.sin(flightTime * 2) * 0.1 + audioInfluence * 0.5;
          
          butterfly.group.position.set(x, y, z);
          
          const baseBeat = Math.sin(time * 6 + butterfly.offset) * 0.3;
          const audioBeat = range.audioLevel * 0.4;
          const finalBeat = baseBeat + audioBeat;
          
          butterfly.wings.left.rotation.z = finalBeat;
          butterfly.wings.right.rotation.z = -finalBeat;
          
          butterfly.group.rotation.y = Math.sin(flightTime * 0.5) * 0.15;
          
          const baseBrightness = 0.9 + range.smoothedLevel * 0.6;
          const glowIntensity = 0.4 + range.audioLevel * 0.8;
          
          butterfly.wings.left.material.opacity = Math.min(1.0, baseBrightness);
          butterfly.wings.right.material.opacity = Math.min(1.0, baseBrightness);
          
          butterfly.wings.left.material.emissiveIntensity = glowIntensity;
          butterfly.wings.right.material.emissiveIntensity = glowIntensity;
          butterfly.body.material.emissiveIntensity = glowIntensity * 0.5;
        }
      });
    });

    this.updatePetals(deltaTime);

    const radius = this.currentConfig.radius;
    const cameraSpeed = 0.12;
    this.camera.position.x = Math.cos(time * cameraSpeed) * radius;
    this.camera.position.z = Math.sin(time * cameraSpeed) * radius;
    this.camera.position.y = radius * 0.4 + 2.5 + Math.sin(time * 0.25) * 0.3;
    this.camera.lookAt(0, 1.5, 0);
  }

  updateConfig(newConfig: any): void {
    this.currentConfig = { ...this.currentConfig, ...newConfig };
    
    Object.entries(this.butterflyGroups).forEach(([key, range]) => {
      const newColor = this.currentConfig.colors[key as BandName];
      if (newColor && newColor !== range.color) {
        range.color = newColor;
        range.butterflies.forEach(butterfly => {
          const color = new THREE.Color(newColor);
          butterfly.wings.left.material.color.copy(color);
          butterfly.wings.right.material.color.copy(color);
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
    this.wingGeometry?.dispose();
    this.bodyGeometry?.dispose();
    this.petalGeometry?.dispose();

    Object.keys(this.butterflyGroups).forEach(key => {
      this.butterflyGroups[key as BandName] = {
        butterflies: [],
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