import * as THREE from 'three';
import { PresetLoader, LoadedPreset, AudioData } from './PresetLoader';

export class AudioVisualizerEngine {
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private presetLoader: PresetLoader;
  private animationId: number | null = null;
  private isRunning = false;

  // Map layer id -> preset id
  private layerPresets: Map<string, string> = new Map();
  // Map layer id -> THREE.Scene
  private layerScenes: Map<string, THREE.Scene> = new Map();
  private layerOrder: string[] = ['C', 'B', 'A'];

  constructor(private canvas: HTMLCanvasElement) {
    this.camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    });
    this.renderer.autoClear = false;
    this.renderer.setClearColor(0x000000, 0);

    // Crear escenas para cada capa
    this.layerOrder.forEach(id => {
      const scene = new THREE.Scene();
      scene.background = null;
      scene.scale.setScalar(1);
      this.layerScenes.set(id, scene);
    });

    this.presetLoader = new PresetLoader(this.camera, this.renderer);
    this.setupScene();
    this.setupEventListeners();
  }

  private setupScene(): void {
    this.camera.position.set(0, 0, 3);
    this.camera.lookAt(0, 0, 0);
    this.updateSize();
  }

  private setupEventListeners(): void {
    window.addEventListener('resize', () => this.updateSize());
  }

  private updateSize(): void {
    const rect = this.canvas.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  }

  public async initialize(): Promise<void> {
    await this.presetLoader.loadAllPresets();
    this.startRenderLoop();
  }

  private startRenderLoop(): void {
    if (this.isRunning) return;
    this.isRunning = true;

    const animate = () => {
      if (!this.isRunning) return;

      this.animationId = requestAnimationFrame(animate);

      // Actualizar presets activos
      this.presetLoader.updateActivePresets();

      // Renderizar escenas por capas
      this.renderer.clear();
      this.layerOrder.forEach(layerId => {
        const scene = this.layerScenes.get(layerId);
        if (scene) {
          this.renderer.render(scene, this.camera);
          this.renderer.clearDepth();
        }
      });
    };

    animate();
  }

  private stopRenderLoop(): void {
    this.isRunning = false;
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }

  // Public API
  public getAvailablePresets(): LoadedPreset[] {
    return this.presetLoader.getLoadedPresets();
  }

  public activatePreset(layerId: string, presetId: string): boolean {
    const previous = this.layerPresets.get(layerId);
    if (previous) {
      this.presetLoader.deactivatePreset(layerId);
    }

    const scene = this.layerScenes.get(layerId);
    if (!scene) return false;

    const preset = this.presetLoader.activatePreset(presetId, scene, layerId);
    if (preset) {
      this.layerPresets.set(layerId, presetId);
      return true;
    }
    return false;
  }

  public deactivateLayerPreset(layerId: string): void {
    if (this.layerPresets.has(layerId)) {
      this.presetLoader.deactivatePreset(layerId);
      this.layerPresets.delete(layerId);
    }
  }

  public updateAudioData(audioData: AudioData): void {
    this.presetLoader.updateAudioData(audioData);
  }

  public setLayerOpacity(layerId: string, opacity: number): void {
    const scene = this.layerScenes.get(layerId);
    if (!scene) return;

    const preset = this.presetLoader.getActivePreset(layerId);
    preset?.setOpacity(opacity);

    scene.traverse(obj => {
      const mat: any = (obj as any).material;
      if (mat) {
        if (Array.isArray(mat)) {
          mat.forEach(m => {
            m.transparent = true;
            m.opacity = opacity;
          });
        } else {
          mat.transparent = true;
          mat.opacity = opacity;
        }
      }
    });
  }

  public updateLayerConfig(layerId: string, config: any): void {
    const scene = this.layerScenes.get(layerId);
    if (!scene) return;

    if (config.zoom !== undefined) {
      scene.scale.setScalar(config.zoom);
    }

    if (config.width !== undefined || config.height !== undefined) {
      const width = config.width !== undefined ? config.width : this.renderer.domElement.width;
      const height = config.height !== undefined ? config.height : this.renderer.domElement.height;
      this.renderer.setSize(width, height);
      this.camera.aspect = width / height;
      this.camera.updateProjectionMatrix();
    }

    const preset = this.presetLoader.getActivePreset(layerId);
    preset?.updateConfig(config);
  }

  public async reloadPresets(): Promise<void> {
    this.presetLoader.dispose();
    this.layerPresets.clear();
    await this.presetLoader.loadAllPresets();
  }

  public dispose(): void {
    this.stopRenderLoop();
    this.presetLoader.dispose();
    this.renderer.dispose();
    this.layerScenes.clear();
  }
}

