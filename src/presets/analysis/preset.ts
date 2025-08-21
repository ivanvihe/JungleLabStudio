import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'ANALYSIS',
  description: '3D audio spectrum analyzer with smooth butterfly transitions and nature-inspired visuals.',
  author: 'AudioVisualizer',
  version: '2.0.0',
  category: 'analysis',
  tags: ['spectrum', 'analysis', 'butterfly', 'grid', 'nature'],
  thumbnail: 'analysis_thumb.png',
  note: 48,
  defaultConfig: {
    radius: 8,
    butterflyCount: 50,
    colors: {
      band1: '#4A90E2',  // Azul suave
      band2: '#7ED321',  // Verde natural
      band3: '#F5A623',  // Amarillo cálido
      band4: '#D0021B',  // Rojo vibrante
      band5: '#9013FE',  // Púrpura
      band6: '#50E3C2'   // Turquesa
    }
  },
  controls: [
    { name: 'radius', type: 'slider', label: 'Camera Radius', min: 5, max: 15, step: 0.5, default: 8 },
    { name: 'butterflyCount', type: 'slider', label: 'Max Butterflies', min: 10, max: 100, step: 1, default: 50 },
    { name: 'colors.band1', type: 'color', label: 'Low Bass Color', default: '#4A90E2' },
    { name: 'colors.band2', type: 'color', label: 'High Bass Color', default: '#7ED321' },
    { name: 'colors.band3', type: 'color', label: 'Low Mid Color', default: '#F5A623' },
    { name: 'colors.band4', type: 'color', label: 'Mid Color', default: '#D0021B' },
    { name: 'colors.band5', type: 'color', label: 'High Mid Color', default: '#9013FE' },
    { name: 'colors.band6', type: 'color', label: 'Treble Color', default: '#50E3C2' }
  ],
  audioMapping: {
    band1: { description: 'Sub-bass frequencies', frequency: '40-200 Hz', effect: 'Butterfly swarm density' },
    band2: { description: 'Bass frequencies', frequency: '200-400 Hz', effect: 'Wing movement intensity' },
    band3: { description: 'Low mid frequencies', frequency: '400-600 Hz', effect: 'Flight speed variation' },
    band4: { description: 'Mid frequencies', frequency: '600-1000 Hz', effect: 'Color saturation' },
    band5: { description: 'High mid frequencies', frequency: '1000-10000 Hz', effect: 'Emergence pattern' },
    band6: { description: 'High frequencies', frequency: '10000-22000 Hz', effect: 'Sparkle effects' }
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
  life: number; // 0 = recién nacida, 1 = adulta, -1 = muriendo
  deathTimer: number;
  birthTimer: number;
  petals?: THREE.Group; // Para efecto de muerte
}

interface ButterflyRange {
  butterflies: Butterfly[];
  color: string;
  centerX: number;
  targetCount: number;
  currentCount: number;
}

type BandName = 'band1' | 'band2' | 'band3' | 'band4' | 'band5' | 'band6';

class AnalysisSpectrum extends BasePreset {
  private group!: THREE.Group;
  private butterflyGroups!: Record<BandName, ButterflyRange>;
  private gridFloor?: THREE.GridHelper;
  private gridBack?: THREE.GridHelper;
  private ambient?: THREE.AmbientLight;
  private pointLight?: THREE.PointLight;
  private currentConfig: any;
  private initialCameraPosition = this.camera.position.clone();
  private initialCameraQuaternion = this.camera.quaternion.clone();
  
  // Pool de geometrías reutilizables para optimización
  private wingGeometry!: THREE.CircleGeometry;
  private bodyGeometry!: THREE.CapsuleGeometry;
  private petalGeometry!: THREE.PlaneGeometry;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, cfg: PresetConfig) {
    super(scene, camera, renderer, cfg);
    this.currentConfig = cfg.defaultConfig;
  }

  init(): void {
    this.group = new THREE.Group();
    this.scene.add(this.group);

    // Crear geometrías reutilizables
    this.wingGeometry = new THREE.CircleGeometry(0.08, 8); // Más redondas
    this.bodyGeometry = new THREE.CapsuleGeometry(0.008, 0.06, 4, 8);
    this.petalGeometry = new THREE.PlaneGeometry(0.02, 0.03);

    // Grid helpers con aspecto más natural
    this.gridFloor = new THREE.GridHelper(12, 12, 0x444444, 0x222222);
    this.gridFloor.material.opacity = 0.3;
    this.gridFloor.material.transparent = true;
    this.scene.add(this.gridFloor);

    this.gridBack = new THREE.GridHelper(12, 12, 0x444444, 0x222222);
    this.gridBack.rotation.x = Math.PI / 2;
    this.gridBack.position.z = -6;
    this.gridBack.material.opacity = 0.2;
    this.gridBack.material.transparent = true;
    this.scene.add(this.gridBack);

    // Luces más cálidas y naturales
    this.ambient = new THREE.AmbientLight(0xffffff, 0.4);
    this.pointLight = new THREE.PointLight(0xffeaa7, 0.8);
    this.pointLight.position.set(3, 6, 4);
    this.pointLight.castShadow = true;
    this.scene.add(this.ambient);
    this.scene.add(this.pointLight);

    // Inicializar grupos de mariposas por bandas de frecuencia
    const colors = this.currentConfig.colors;
    this.butterflyGroups = {
      band1: { butterflies: [], color: colors.band1, centerX: -3.0, targetCount: 0, currentCount: 0 },
      band2: { butterflies: [], color: colors.band2, centerX: -1.8, targetCount: 0, currentCount: 0 },
      band3: { butterflies: [], color: colors.band3, centerX: -0.6, targetCount: 0, currentCount: 0 },
      band4: { butterflies: [], color: colors.band4, centerX: 0.6, targetCount: 0, currentCount: 0 },
      band5: { butterflies: [], color: colors.band5, centerX: 1.8, targetCount: 0, currentCount: 0 },
      band6: { butterflies: [], color: colors.band6, centerX: 3.0, targetCount: 0, currentCount: 0 }
    };

    // Crear mariposas iniciales
    Object.values(this.butterflyGroups).forEach(range => {
      for (let i = 0; i < 3; i++) {
        range.butterflies.push(this.createButterfly(range.color, range.centerX));
        range.currentCount++;
      }
    });
  }

  private createButterfly(colorHex: string, centerX: number): Butterfly {
    const group = new THREE.Group();
    const color = new THREE.Color(colorHex);
    
    // Alas más redondas y naturales
    const wingMaterial = new THREE.MeshLambertMaterial({ 
      color: color,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.8
    });
    
    const leftWing = new THREE.Mesh(this.wingGeometry, wingMaterial.clone());
    const rightWing = new THREE.Mesh(this.wingGeometry, wingMaterial.clone());
    
    leftWing.position.set(-0.06, 0, 0);
    rightWing.position.set(0.06, 0, 0);
    
    // Cuerpo de la mariposa
    const bodyMaterial = new THREE.MeshLambertMaterial({ color: 0x333333 });
    const body = new THREE.Mesh(this.bodyGeometry, bodyMaterial);
    body.rotation.z = Math.PI / 2;
    
    group.add(leftWing);
    group.add(rightWing);
    group.add(body);
    
    // Propiedades de vuelo más naturales
    const radius = 0.4 + Math.random() * 0.8;
    const speed = 0.3 + Math.random() * 0.4;
    const offset = Math.random() * Math.PI * 2;
    const scale = 0.7 + Math.random() * 0.6; // Mariposas más pequeñas
    
    group.scale.setScalar(scale);
    group.position.set(
      centerX + Math.cos(offset) * radius, 
      0.5 + Math.random() * 2.5, 
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
      birthTimer: 0
    };
  }

  private createDeathPetals(butterfly: Butterfly): void {
    const petalsGroup = new THREE.Group();
    const color = new THREE.Color((butterfly.wings.left.material as THREE.MeshLambertMaterial).color);
    
    // Crear 6-8 pétalos que se dispersan
    const petalCount = 6 + Math.floor(Math.random() * 3);
    
    for (let i = 0; i < petalCount; i++) {
      const petal = new THREE.Mesh(
        this.petalGeometry,
        new THREE.MeshLambertMaterial({
          color: color.clone().multiplyScalar(0.8 + Math.random() * 0.4),
          transparent: true,
          opacity: 0.7
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
          Math.cos(angle) * (0.3 + Math.random() * 0.2),
          Math.random() * 0.2 - 0.1,
          Math.sin(angle) * (0.3 + Math.random() * 0.2)
        ),
        angularVelocity: (Math.random() - 0.5) * 0.2
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
            
            // Aplicar física simple
            petal.position.add(userData.velocity.clone().multiplyScalar(deltaTime));
            userData.velocity.y -= 0.5 * deltaTime; // Gravedad
            userData.velocity.multiplyScalar(0.98); // Fricción
            
            petal.rotation.z += userData.angularVelocity * deltaTime;
            
            // Fade out
            const material = petal.material as THREE.MeshLambertMaterial;
            material.opacity -= deltaTime * 2;
            
            if (material.opacity <= 0) {
              butterfly.petals!.remove(petal);
            }
          });
          
          // Remover grupo de pétalos vacío
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
    
    // Crear nuevas mariposas gradualmente
    if (range.currentCount < target) {
      const spawnRate = 2.0; // Mariposas por segundo
      if (Math.random() < spawnRate * deltaTime) {
        const newButterfly = this.createButterfly(range.color, range.centerX);
        newButterfly.birthTimer = 1.0; // Tiempo de nacimiento
        range.butterflies.push(newButterfly);
        range.currentCount++;
      }
    }
    
    // Marcar mariposas para muerte gradual
    if (range.currentCount > target) {
      range.butterflies.forEach(butterfly => {
        if (butterfly.life > 0.8 && butterfly.deathTimer === 0 && Math.random() < 0.3 * deltaTime) {
          butterfly.deathTimer = 1.0; // Iniciar proceso de muerte
          butterfly.life = -1;
        }
      });
    }
    
    // Procesar ciclo de vida de las mariposas
    for (let i = range.butterflies.length - 1; i >= 0; i--) {
      const butterfly = range.butterflies[i];
      
      if (butterfly.birthTimer > 0) {
        // Proceso de nacimiento
        butterfly.birthTimer -= deltaTime * 2;
        const birthProgress = 1.0 - butterfly.birthTimer;
        butterfly.group.scale.setScalar(butterfly.scale * birthProgress);
        butterfly.life = Math.min(1.0, birthProgress * 2);
        
        // Efecto de aparición suave
        const opacity = Math.min(1.0, birthProgress * 1.5);
        butterfly.wings.left.material.opacity = opacity * 0.8;
        butterfly.wings.right.material.opacity = opacity * 0.8;
        
      } else if (butterfly.deathTimer > 0) {
        // Proceso de muerte
        butterfly.deathTimer -= deltaTime;
        const deathProgress = 1.0 - butterfly.deathTimer;
        
        // Ralentizar movimiento
        butterfly.speed *= (1.0 - deltaTime * 0.5);
        
        // Reducir tamaño y opacidad gradualmente
        const scale = butterfly.scale * (1.0 - deathProgress * 0.5);
        butterfly.group.scale.setScalar(scale);
        
        const opacity = (1.0 - deathProgress) * 0.8;
        butterfly.wings.left.material.opacity = opacity;
        butterfly.wings.right.material.opacity = opacity;
        
        // Crear pétalos cuando está casi muriendo
        if (deathProgress > 0.7 && !butterfly.petals) {
          this.createDeathPetals(butterfly);
        }
        
        // Remover cuando está completamente muerta
        if (butterfly.deathTimer <= 0) {
          this.group.remove(butterfly.group);
          range.butterflies.splice(i, 1);
          range.currentCount--;
        }
        
      } else {
        // Vida normal - crecimiento gradual hasta la madurez
        butterfly.life = Math.min(1.0, butterfly.life + deltaTime * 0.5);
      }
    }
  }

  update(): void {
    const time = this.clock.getElapsedTime();
    const deltaTime = this.clock.getDelta();
    const fft = this.audioData.fft;
    
    // Mejorar el análisis de frecuencias
    const sampleRate = 44100;
    const nyquist = sampleRate / 2;
    const ranges: [number, number][] = [
      [40, 200],    // Sub-bass
      [200, 400],   // Bass
      [400, 600],   // Low-mid
      [600, 1000],  // Mid
      [1000, 10000],// High-mid  
      [10000, 22000]// Treble
    ];
    
    const amps = ranges.map(([low, high]) => {
      const start = Math.floor((low / nyquist) * fft.length);
      const end = Math.floor((high / nyquist) * fft.length);
      let sum = 0;
      for (let i = start; i < end && i < fft.length; i++) {
        sum += fft[i] * fft[i]; // Usar energía (cuadrado) para mejor respuesta
      }
      return Math.sqrt(sum / Math.max(end - start, 1));
    });

    const keys: BandName[] = ['band1', 'band2', 'band3', 'band4', 'band5', 'band6'];

    keys.forEach((key, i) => {
      const range = this.butterflyGroups[key];
      const amp = Math.max(amps[i], 0);
      
      // Mejor mapeo de amplitud a cantidad de mariposas
      const sensitivity = 0.8;
      const target = Math.max(1, Math.floor((amp * sensitivity) * this.currentConfig.butterflyCount * 0.15));
      
      this.adjustButterflies(range, target, deltaTime);
      
      // Animar mariposas vivas
      range.butterflies.forEach(butterfly => {
        if (butterfly.life > 0 && butterfly.deathTimer === 0) {
          // Movimiento de vuelo más natural
          const flightTime = time * butterfly.speed + butterfly.offset;
          const x = range.centerX + Math.cos(flightTime) * butterfly.radius;
          const z = Math.sin(flightTime) * butterfly.radius;
          const y = butterfly.group.position.y + Math.sin(flightTime * 2) * 0.1 * deltaTime;
          
          butterfly.group.position.set(x, y, z);
          
          // Aleteo más realista basado en audio
          const wingBeat = Math.sin(time * 8 + butterfly.offset) * 0.4;
          const audioInfluence = amp * 0.3;
          const finalWingBeat = wingBeat + audioInfluence;
          
          butterfly.wings.left.rotation.z = finalWingBeat;
          butterfly.wings.right.rotation.z = -finalWingBeat;
          
          // Rotación corporal sutil
          butterfly.group.rotation.y = Math.sin(flightTime * 0.5) * 0.2;
        }
      });
    });

    // Actualizar pétalos en caída
    this.updatePetals(deltaTime);

    // Movimiento de cámara más fluido
    const radius = this.currentConfig.radius;
    const cameraSpeed = 0.15;
    this.camera.position.x = Math.cos(time * cameraSpeed) * radius;
    this.camera.position.z = Math.sin(time * cameraSpeed) * radius;
    this.camera.position.y = radius * 0.4 + 2.5 + Math.sin(time * 0.3) * 0.5;
    this.camera.lookAt(0, 1.5, 0);
  }

  updateConfig(newConfig: any): void {
    this.currentConfig = { ...this.currentConfig, ...newConfig };
    
    // Actualizar colores de mariposas existentes
    Object.entries(this.butterflyGroups).forEach(([key, range]) => {
      const newColor = this.currentConfig.colors[key as BandName];
      if (newColor && newColor !== range.color) {
        range.color = newColor;
        range.butterflies.forEach(butterfly => {
          butterfly.wings.left.material.color.setHex(newColor.replace('#', '0x'));
          butterfly.wings.right.material.color.setHex(newColor.replace('#', '0x'));
        });
      }
    });
  }

  dispose(): void {
    // Limpiar escena
    this.scene.remove(this.group);
    if (this.gridFloor) this.scene.remove(this.gridFloor);
    if (this.gridBack) this.scene.remove(this.gridBack);
    if (this.ambient) this.scene.remove(this.ambient);
    if (this.pointLight) this.scene.remove(this.pointLight);

    // Restaurar cámara
    this.camera.position.copy(this.initialCameraPosition);
    this.camera.quaternion.copy(this.initialCameraQuaternion);

    // Limpiar recursos
    this.group.clear();
    this.wingGeometry?.dispose();
    this.bodyGeometry?.dispose();
    this.petalGeometry?.dispose();

    // Resetear grupos
    this.butterflyGroups = {
      band1: { butterflies: [], color: '', centerX: -3.0, targetCount: 0, currentCount: 0 },
      band2: { butterflies: [], color: '', centerX: -1.8, targetCount: 0, currentCount: 0 },
      band3: { butterflies: [], color: '', centerX: -0.6, targetCount: 0, currentCount: 0 },
      band4: { butterflies: [], color: '', centerX: 0.6, targetCount: 0, currentCount: 0 },
      band5: { butterflies: [], color: '', centerX: 1.8, targetCount: 0, currentCount: 0 },
      band6: { butterflies: [], color: '', centerX: 3.0, targetCount: 0, currentCount: 0 }
    };
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