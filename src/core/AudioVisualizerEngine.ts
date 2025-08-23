import * as THREE from 'three';
import { PresetLoader, LoadedPreset, AudioData } from './PresetLoader';
import { LayerManager } from './LayerManager';
import { Compositor } from './Compositor';

export class AudioVisualizerEngine {
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private presetLoader: PresetLoader;
  private layerManager: LayerManager;
  private compositor: Compositor;
  private animationId: number | null = null;
  private isRunning = false;
  private multiMonitorMode = false;
  private currentBpm: number = 120;

  constructor(private canvas: HTMLCanvasElement, options: { glitchTextPads?: number } = {}) {
    this.camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
      preserveDrawingBuffer: true
    });

    this.renderer.autoClear = false;
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;

    this.presetLoader = new PresetLoader(this.camera, this.renderer, options.glitchTextPads ?? 1);
    this.layerManager = new LayerManager(this.renderer, this.camera, this.presetLoader);
    this.compositor = new Compositor(this.renderer);

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
    const width = 1920;
    const height = 1080;
    const pixelRatio = Math.min(window.devicePixelRatio, 2);
    const visualScale = parseFloat(localStorage.getItem('visualScale') || '1');
    const scaledWidth = width * visualScale;
    const scaledHeight = height * visualScale;

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();

    this.renderer.setSize(scaledWidth, scaledHeight, false);
    this.renderer.domElement.style.width = '100%';
    this.renderer.domElement.style.height = '100%';
    this.renderer.setPixelRatio(pixelRatio);

    this.layerManager.updateSize(scaledWidth, scaledHeight, pixelRatio);
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

      this.renderer.clear();
      this.layerManager.renderLayers();
      this.compositor.composite(this.layerManager.getLayers());
    };

    animate();
    console.log('🔄 Render loop started con layers independientes');
  }

  public setMultiMonitorMode(active: boolean): void {
    this.multiMonitorMode = active;
  }

  public async activateLayerPreset(layerId: string, presetId: string): Promise<boolean> {
    return this.layerManager.activateLayerPreset(layerId, presetId);
  }

  public deactivateLayerPreset(layerId: string): void {
    this.layerManager.deactivateLayerPreset(layerId);
  }

  public updateLayerConfig(layerId: string, config: any): void {
    this.layerManager.updateLayerConfig(layerId, config);
  }

  public getLayerPresetConfig(layerId: string, presetId: string): any {
    return this.layerManager.getLayerPresetConfig(layerId, presetId);
  }

  public updateLayerPresetConfig(layerId: string, pathKey: string, value: any): void {
    this.layerManager.updateLayerPresetConfig(layerId, pathKey, value);
  }

  public setGlobalOpacity(opacity: number): void {
    this.compositor.setGlobalOpacity(opacity);
  }

  public getAvailablePresets(): LoadedPreset[] {
    return this.presetLoader.getLoadedPresets();
  }

  public async updateGlitchPadCount(count: number): Promise<LoadedPreset[]> {
    this.presetLoader.setGlitchTextPads(count);
    await this.presetLoader.loadAllPresets();
    return this.presetLoader.getLoadedPresets();
  }

  public async updateCustomTextTemplates(count: number, texts: string[]): Promise<LoadedPreset[]> {
    this.presetLoader.setCustomTextInstances(count, texts);
    await this.presetLoader.loadAllPresets();
    return this.presetLoader.getLoadedPresets();
  }

  public async updateGenLabPresets(presets: { name: string; config: any }[]): Promise<LoadedPreset[]> {
    this.presetLoader.setGenLabPresets(presets);
    await this.presetLoader.loadAllPresets();
    return this.presetLoader.getLoadedPresets();
  }

  public getGenLabBasePreset(): LoadedPreset | null {
    return this.presetLoader.getGenLabBasePreset();
  }

  public updateAudioData(audioData: AudioData): void {
    this.presetLoader.updateAudioData(audioData);
  }

  public getLayerStatus(): Record<string, { active: boolean; preset: string | null }> {
    return this.layerManager.getLayerStatus();
  }

  public clearRenderer(): void {
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.clear(true, true, true);
  }

  public updateBpm(bpm: number): void {
    this.currentBpm = bpm;
    this.layerManager.updateBpm(bpm);
  }

  public triggerBeat(): void {
    this.layerManager.triggerBeat();
  }

  public dispose(): void {
    this.isRunning = false;

    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }

    this.layerManager.dispose();
    this.compositor.dispose();
    this.presetLoader.dispose();
    this.renderer.dispose();

    console.log('🧹 Engine disposed');
  }
}

