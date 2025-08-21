import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'ANALYSIS',
  description: '3D audio spectrum analyzer with butterflies and rotating camera.',
  author: 'AudioVisualizer',
  version: '1.0.0',
  category: 'analysis',
  tags: ['spectrum', 'analysis', 'butterfly', 'grid'],
  thumbnail: 'analysis_thumb.png',
  note: 48,
  defaultConfig: {
    radius: 8,
    butterflyCount: 12,
    colors: {
      low: '#3498db',
      mid: '#2ecc71',
      high: '#e74c3c',
      butterfly: '#ffccff'
    }
  },
  controls: [
    { name: 'radius', type: 'slider', label: 'Camera Radius', min: 5, max: 15, step: 0.5, default: 8 },
    { name: 'butterflyCount', type: 'slider', label: 'Butterflies', min: 0, max: 50, step: 1, default: 12 },
    { name: 'colors.low', type: 'color', label: 'Low Color', default: '#3498db' },
    { name: 'colors.mid', type: 'color', label: 'Mid Color', default: '#2ecc71' },
    { name: 'colors.high', type: 'color', label: 'High Color', default: '#e74c3c' },
    { name: 'colors.butterfly', type: 'color', label: 'Butterfly Color', default: '#ffccff' }
  ],
  audioMapping: {
    low: { description: 'Low frequencies', frequency: '20-250 Hz', effect: 'Low bar height' },
    mid: { description: 'Mid frequencies', frequency: '250-4000 Hz', effect: 'Mid bar height' },
    high: { description: 'High frequencies', frequency: '4000+ Hz', effect: 'High bar height' }
  },
  performance: { complexity: 'low', recommendedFPS: 60, gpuIntensive: false }
};

interface LabelData {
  sprite: THREE.Sprite;
  canvas: HTMLCanvasElement;
  ctx: CanvasRenderingContext2D;
  texture: THREE.Texture;
}

interface Bar {
  mesh: THREE.Mesh;
  label: LabelData;
}

interface Butterfly {
  group: THREE.Group;
  speed: number;
  radius: number;
  offset: number;
}

class AnalysisSpectrum extends BasePreset {
  private group!: THREE.Group;
  private bars: Bar[] = [];
  private butterflies: Butterfly[] = [];
  private grid?: THREE.GridHelper;
  private ambient?: THREE.AmbientLight;
  private pointLight?: THREE.PointLight;
  private currentConfig: any;
  private initialCameraPosition = this.camera.position.clone();
  private initialCameraQuaternion = this.camera.quaternion.clone();

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, cfg: PresetConfig) {
    super(scene, camera, renderer, cfg);
    this.currentConfig = cfg.defaultConfig;
  }

  init(): void {
    this.group = new THREE.Group();
    this.scene.add(this.group);

    // Grid helper
    this.grid = new THREE.GridHelper(10, 10, 0x444444, 0x222222);
    this.scene.add(this.grid);

    // Lights
    this.ambient = new THREE.AmbientLight(0xffffff, 0.3);
    this.pointLight = new THREE.PointLight(0xffffff, 0.6);
    this.pointLight.position.set(5, 5, 5);
    this.scene.add(this.ambient);
    this.scene.add(this.pointLight);

    // Bars for low, mid, high
    const colors = this.currentConfig.colors;
    this.bars.push(this.createBar(colors.low, -2));
    this.bars.push(this.createBar(colors.mid, 0));
    this.bars.push(this.createBar(colors.high, 2));

    // Butterflies
    for (let i = 0; i < this.currentConfig.butterflyCount; i++) {
      this.butterflies.push(this.createButterfly());
    }
  }

  private createBar(color: string, x: number): Bar {
    const geometry = new THREE.BoxGeometry(0.5, 1, 0.5);
    const material = new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.3 });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(x, 0.5, 0);
    const label = this.createLabel('0 dB');
    label.sprite.position.set(x, 1.2, 0);
    this.group.add(mesh);
    this.group.add(label.sprite);
    return { mesh, label };
  }

  private createLabel(text: string): LabelData {
    const canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 64;
    const ctx = canvas.getContext('2d')!;
    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
    const sprite = new THREE.Sprite(material);
    sprite.scale.set(1, 0.5, 1);
    const label = { sprite, canvas, ctx, texture };
    this.updateLabel(label, text);
    return label;
  }

  private updateLabel(label: LabelData, text: string): void {
    const { canvas, ctx, texture } = label;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#ffffff';
    ctx.font = '28px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, canvas.width / 2, canvas.height / 2);
    texture.needsUpdate = true;
  }

  private createButterfly(): Butterfly {
    const group = new THREE.Group();
    const geom = new THREE.PlaneGeometry(0.3, 0.2);
    const mat = new THREE.MeshBasicMaterial({ color: this.currentConfig.colors.butterfly, side: THREE.DoubleSide });
    const left = new THREE.Mesh(geom, mat);
    const right = new THREE.Mesh(geom, mat);
    left.position.x = -0.15;
    right.position.x = 0.15;
    group.add(left);
    group.add(right);
    const radius = 2 + Math.random() * 3;
    const speed = 0.5 + Math.random();
    const offset = Math.random() * Math.PI * 2;
    group.position.set(Math.cos(offset) * radius, 1 + Math.random() * 2, Math.sin(offset) * radius);
    this.group.add(group);
    return { group, speed, radius, offset };
  }

  update(): void {
    const time = this.clock.getElapsedTime();
    const bands = [this.audioData.low, this.audioData.mid, this.audioData.high];

    this.bars.forEach((bar, i) => {
      const amp = Math.max(bands[i], 0.0001);
      const target = 0.5 + amp * 5;
      bar.mesh.scale.y = THREE.MathUtils.lerp(bar.mesh.scale.y, target, 0.2);
      bar.mesh.position.y = bar.mesh.scale.y / 2;
      bar.label.sprite.position.y = bar.mesh.scale.y + 0.1;
      const db = 20 * Math.log10(amp);
      this.updateLabel(bar.label, `${db.toFixed(1)} dB`);
    });

    this.butterflies.forEach(b => {
      const angle = time * b.speed + b.offset;
      b.group.position.x = Math.cos(angle) * b.radius;
      b.group.position.z = Math.sin(angle) * b.radius;
      const flap = Math.sin(time * 4 + b.offset) * 0.5;
      if (b.group.children[0] && b.group.children[1]) {
        b.group.children[0].rotation.z = flap;
        b.group.children[1].rotation.z = -flap;
      }
    });

    const radius = this.currentConfig.radius;
    this.camera.position.x = Math.cos(time * 0.2) * radius;
    this.camera.position.z = Math.sin(time * 0.2) * radius;
    this.camera.position.y = radius * 0.3 + 2;
    this.camera.lookAt(0, 1, 0);
  }

  updateConfig(newConfig: any): void {
    this.currentConfig = { ...this.currentConfig, ...newConfig };
  }

  dispose(): void {
    this.scene.remove(this.group);
    this.scene.remove(this.grid!);
    this.scene.remove(this.ambient!);
    this.scene.remove(this.pointLight!);

    this.bars.forEach(bar => {
      bar.mesh.geometry.dispose();
      (bar.mesh.material as THREE.Material).dispose();
      bar.label.texture.dispose();
    });

    this.camera.position.copy(this.initialCameraPosition);
    this.camera.quaternion.copy(this.initialCameraQuaternion);

    this.group.clear();
    this.butterflies = [];
    this.bars = [];
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
