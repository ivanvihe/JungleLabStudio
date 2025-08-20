import * as THREE from 'three';
import { PresetLoader, LoadedPreset, AudioData } from './PresetLoader';

export class AudioVisualizerEngine {
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private presetLoader: PresetLoader;
  private animationId: number | null = null;
  private isRunning = false;
  private layerPresets: Map<string, string> = new Map();

  constructor(private canvas: HTMLCanvasElement) {
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    this.renderer = new THREE.WebGLRenderer({ 
      canvas: this.canvas,
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    });
    
    this.presetLoader = new PresetLoader(this.scene, this.camera, this.renderer);
    this.setupScene();
    this.setupEventListeners();
  }

  private setupScene(): void {
    this.scene.background = new THREE.Color(0x000000);
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
    // Cargar todos los presets
    await this.presetLoader.loadAllPresets();
    
    // Iniciar loop de renderizado
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
      
      // Renderizar escena
      this.renderer.render(this.scene, this.camera);
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
    const previousPreset = this.layerPresets.get(layerId);
    if (previousPreset) {
      this.presetLoader.deactivatePreset(previousPreset);
    }

    const preset = this.presetLoader.activatePreset(presetId);
    if (preset) {
      this.layerPresets.set(layerId, presetId);
      return true;
    }
    return false;
  }

  public deactivateLayerPreset(layerId: string): void {
    const presetId = this.layerPresets.get(layerId);
    if (presetId) {
      this.presetLoader.deactivatePreset(presetId);
      this.layerPresets.delete(layerId);
    }
  }

  public updateAudioData(audioData: AudioData): void {
    this.presetLoader.updateAudioData(audioData);
  }

  public setLayerOpacity(layerId: string, opacity: number): void {
    const presetId = this.layerPresets.get(layerId);
    if (!presetId) return;
    const preset = this.presetLoader.getActivePreset(presetId);
    preset?.setOpacity(opacity);
  }

  public updateLayerConfig(layerId: string, config: any): void {
    const presetId = this.layerPresets.get(layerId);
    if (!presetId) return;
    if (config.zoom !== undefined) {
      this.camera.zoom = config.zoom;
      this.camera.updateProjectionMatrix();
    }

    if (config.width !== undefined || config.height !== undefined) {
      const width = config.width !== undefined ? config.width : this.renderer.domElement.width;
      const height = config.height !== undefined ? config.height : this.renderer.domElement.height;
      this.renderer.setSize(width, height);
      this.camera.aspect = width / height;
      this.camera.updateProjectionMatrix();
    }

    const preset = this.presetLoader.getActivePreset(presetId);
    preset?.updateConfig(config);
  }

  public async reloadPresets(): Promise<void> {
    // Limpiar presets actuales
    this.presetLoader.dispose();
    this.layerPresets.clear();

    // Recargar
    await this.presetLoader.loadAllPresets();
  }

  public dispose(): void {
    this.stopRenderLoop();
    this.presetLoader.dispose();
    this.renderer.dispose();
  }
}