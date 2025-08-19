import * as THREE from 'three';
import { PresetLoader, LoadedPreset, AudioData } from './PresetLoader';

export class AudioVisualizerEngine {
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private presetLoader: PresetLoader;
  private animationId: number | null = null;
  private isRunning = false;
  private currentPresetId: string | null = null;

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

  public activatePreset(presetId: string): boolean {
    // Desactivar preset anterior si existe
    if (this.currentPresetId) {
      this.presetLoader.deactivatePreset(this.currentPresetId);
    }

    const preset = this.presetLoader.activatePreset(presetId);
    if (preset) {
      this.currentPresetId = presetId;
      return true;
    }
    return false;
  }

  public deactivateCurrentPreset(): void {
    if (this.currentPresetId) {
      this.presetLoader.deactivatePreset(this.currentPresetId);
      this.currentPresetId = null;
    }
  }

  public updateAudioData(audioData: AudioData): void {
    this.presetLoader.updateAudioData(audioData);
  }

  public setOpacity(opacity: number): void {
    const activePresets = this.presetLoader.getActivePresets();
    activePresets.forEach(preset => preset.setOpacity(opacity));
  }

  public updatePresetConfig(config: any): void {
    const activePresets = this.presetLoader.getActivePresets();
    activePresets.forEach(preset => preset.updateConfig(config));
  }

  public async reloadPresets(): Promise<void> {
    // Limpiar presets actuales
    this.presetLoader.dispose();
    this.currentPresetId = null;

    // Recargar
    await this.presetLoader.loadAllPresets();
  }

  public dispose(): void {
    this.stopRenderLoop();
    this.presetLoader.dispose();
    this.renderer.dispose();
  }
}