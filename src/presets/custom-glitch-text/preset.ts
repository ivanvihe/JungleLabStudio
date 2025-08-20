import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'Custom Glitch Text',
  description: 'Text with configurable glitch effect',
  author: 'AudioVisualizer',
  version: '1.0.0',
  category: 'text',
  tags: ['text', 'glitch', 'one-shot'],
  thumbnail: 'custom_glitch_text_thumb.png',
  defaultConfig: {
    opacity: 1.0,
    fadeMs: 200,
    text: {
      content: 'TEXT',
      fontSize: 120,
      fontFamily: 'Arial Black, sans-serif'
    },
    glitch: {
      intensity: 0.05,
      frequency: 2.0
    },
    color: '#ffffff'
  },
  controls: [
    { name: 'text.content', type: 'text', label: 'Text', default: 'TEXT' },
    { name: 'text.fontSize', type: 'slider', label: 'Font Size', min: 40, max: 200, step: 10, default: 120 },
    { name: 'glitch.intensity', type: 'slider', label: 'Glitch Intensity', min: 0, max: 0.5, step: 0.01, default: 0.05 },
    { name: 'glitch.frequency', type: 'slider', label: 'Glitch Frequency', min: 0, max: 10, step: 0.1, default: 2.0 },
    { name: 'color', type: 'color', label: 'Color', default: '#ffffff' }
  ],
  audioMapping: {
    low: { description: 'Slight scale bump', frequency: '20-250 Hz', effect: 'Scale' },
    mid: { description: 'Glitch trigger', frequency: '250-4000 Hz', effect: 'Glitch randomness' },
    high: { description: 'Color flicker', frequency: '4000+ Hz', effect: 'Color shift' }
  },
  performance: { complexity: 'low', recommendedFPS: 60, gpuIntensive: false }
};

class CustomGlitchTextPreset extends BasePreset {
  private group!: THREE.Group;
  private mesh!: THREE.Mesh<THREE.PlaneGeometry, THREE.MeshBasicMaterial>;
  private canvas!: HTMLCanvasElement;
  private ctx!: CanvasRenderingContext2D;
  private texture!: THREE.Texture;
  private currentConfig: any;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, cfg: PresetConfig) {
    super(scene, camera, renderer, cfg);
  }

  public init(): void {
    this.currentConfig = JSON.parse(JSON.stringify(this.config.defaultConfig));
    this.group = new THREE.Group();
    this.scene.add(this.group);

    this.canvas = document.createElement('canvas');
    this.canvas.width = 1024;
    this.canvas.height = 256;
    this.ctx = this.canvas.getContext('2d')!;

    this.texture = new THREE.Texture(this.canvas);
    this.texture.needsUpdate = true;

    this.mesh = new THREE.Mesh(
      new THREE.PlaneGeometry(2, 0.5),
      new THREE.MeshBasicMaterial({ map: this.texture, transparent: true, color: new THREE.Color(this.currentConfig.color) })
    );
    this.group.add(this.mesh);

    this.updateCanvas();
  }

  private updateCanvas(): void {
    const { content, fontSize, fontFamily } = this.currentConfig.text;
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.ctx.fillStyle = '#ffffff';
    this.ctx.font = `${fontSize}px ${fontFamily}`;
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
    this.ctx.fillText(content, this.canvas.width / 2, this.canvas.height / 2);
    this.texture.needsUpdate = true;
  }

  public update(): void {
    const delta = this.clock.getDelta();
    const { intensity, frequency } = this.currentConfig.glitch;

    if (Math.random() < frequency * delta) {
      this.mesh.position.x = (Math.random() - 0.5) * intensity;
      this.mesh.position.y = (Math.random() - 0.5) * intensity;
      this.mesh.material.color.setHSL(Math.random(), 1, 0.5);
    } else {
      this.mesh.position.set(0, 0, 0);
      this.mesh.material.color.set(this.currentConfig.color);
    }

    const scaleBump = 1 + this.audioData.low * 0.1;
    this.group.scale.setScalar(scaleBump);
  }

  public updateConfig(newConfig: any): void {
    this.currentConfig = this.deepMerge(this.currentConfig, newConfig);
    if (newConfig.text) {
      this.updateCanvas();
    }
    if (newConfig.color) {
      this.mesh.material.color.set(newConfig.color);
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
    this.group.remove(this.mesh);
    this.scene.remove(this.group);
    this.mesh.geometry.dispose();
    this.mesh.material.dispose();
    this.texture.dispose();
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  cfg: PresetConfig,
  shaderCode?: string
): BasePreset {
  return new CustomGlitchTextPreset(scene, camera, renderer, cfg);
}
