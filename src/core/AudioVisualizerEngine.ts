import * as THREE from 'three';
import { PresetLoader, LoadedPreset, AudioData } from './PresetLoader';
import { LayerManager } from './LayerManager';
import { Compositor } from './Compositor';
// Using simple path helpers instead of Node's `path` module which is not
// available in the browser runtime. Node's `path.join` was causing errors
// after bundling (e.g. `TypeError: Bi.join is not a function`).
// For our use case we only need basic string concatenation to build and
// inspect paths, so we implement lightweight helpers below.
import { setNestedValue } from '../utils/objectPath';

interface LayerState {
  preset: LoadedPreset | null;
  scene: THREE.Scene;
  opacity: number;
  fadeTime: number;
  isActive: boolean;
  renderTarget?: THREE.WebGLRenderTarget;
  material?: THREE.Material;
}


export class AudioVisualizerEngine {
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private presetLoader: PresetLoader;
  private layerManager: LayerManager;
  private layers: Map<string, LayerState>;
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
    this.layers = this.layerManager.getLayers();
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
    const layer = this.layers.get(layerId);
    if (!layer) {
      console.error(`Layer ${layerId} no encontrado`);
      return false;
    }

    try {
      // Desactivar preset anterior del layer si existe
      if (layer.preset) {
        this.presetLoader.deactivatePreset(`${layerId}-${layer.preset.id}`);
        layer.scene.clear();
      }

      // Buscar preset cargado
      const loadedPreset = this.presetLoader.getLoadedPresets().find(p => p.id === presetId);
      if (!loadedPreset) {
        console.error(`Loaded preset ${presetId} no encontrado`);
        return false;
      }

      // Cargar configuración guardada específica para el layer y clonar config base
      const savedConfig = await this.loadLayerPresetConfig(presetId, layerId);
      const loadedPresetConfig = JSON.parse(JSON.stringify(loadedPreset.config));
      loadedPresetConfig.defaultConfig = {
        ...loadedPresetConfig.defaultConfig,
        ...savedConfig
      };

      // Activar nuevo preset con config específica del layer
      const presetInstance = this.presetLoader.activatePreset(
        presetId,
        layer.scene,
        `${layerId}-${presetId}`,
        loadedPresetConfig
      );
      if (!presetInstance) {
        console.error(`No se pudo activar preset ${presetId}`);
        return false;
      }

      // Asignar preset clonado con config al layer
      layer.preset = { ...loadedPreset, config: loadedPresetConfig };
      layer.isActive = true;

      console.log(`✅ Layer ${layerId} activado con preset ${presetId}`);
      return true;
    } catch (error) {
      console.error(`Error activando preset ${presetId} en layer ${layerId}:`, error);
      return false;
    }

  }

  public deactivateLayerPreset(layerId: string): void {
    this.layerManager.deactivateLayerPreset(layerId);
  }

  public updateLayerConfig(layerId: string, config: any): void {
    const layer = this.layers.get(layerId);
    if (!layer) return;

    if (config.opacity !== undefined) {
      layer.opacity = config.opacity / 100; // Convertir de 0-100 a 0-1
    }
    
    if (config.fadeTime !== undefined) {
      layer.fadeTime = config.fadeTime;
    }
  }

  // Build the path to the config file for a given layer preset. We keep the
  // configs inside the original preset folder and append the clone index (if
  // any) to the filename so each pad has its own file. Using Node's `path`
  // utilities is avoided to stay compatible with the browser/Tauri runtime.
  private getLayerConfigPath(presetId: string, layerId: string): string {
    const loaded = this.presetLoader.getLoadedPresets().find(p => p.id === presetId);
    const folder = loaded?.folderPath ?? `src/presets/${presetId}`;
    const variantMatch = presetId.match(/-(\d+)$/);
    const variantSuffix = variantMatch ? `-${variantMatch[1]}` : '';
    return `${folder}/layers/${layerId}${variantSuffix}.json`;
  }

  private async loadLayerPresetConfig(presetId: string, layerId: string): Promise<any> {
    try {
      const cfgPath = this.getLayerConfigPath(presetId, layerId);
      if (typeof window !== 'undefined' && (window as any).__TAURI__) {
        const { exists, readTextFile } = await import(
          /* @vite-ignore */ '@tauri-apps/api/fs'
        );
        if (await exists(cfgPath)) {
          return JSON.parse(await readTextFile(cfgPath));
        }
      }
    } catch (err) {
      console.warn(`Could not load config for ${presetId} layer ${layerId}:`, err);
    }
    return {};
  }

  private async saveLayerPresetConfig(presetId: string, layerId: string, cfg: any): Promise<void> {
    try {
      if (typeof window !== 'undefined' && (window as any).__TAURI__) {
        const { createDir, writeFile } = await import(
          /* @vite-ignore */ '@tauri-apps/api/fs'
        );
        const cfgPath = this.getLayerConfigPath(presetId, layerId);
        const dir = cfgPath.substring(0, cfgPath.lastIndexOf('/'));
        await createDir(dir, { recursive: true });
        await writeFile({ path: cfgPath, contents: JSON.stringify(cfg, null, 2) });
      }
    } catch (err) {
      console.warn(`Could not save config for ${presetId} layer ${layerId}:`, err);
    }
  }

  public async getLayerPresetConfig(layerId: string, presetId: string): Promise<any> {
    const saved = await this.loadLayerPresetConfig(presetId, layerId);
    if (Object.keys(saved).length > 0) return saved;
    const loaded = this.presetLoader.getLoadedPresets().find(p => p.id === presetId);
    return loaded ? JSON.parse(JSON.stringify(loaded.config.defaultConfig)) : {};
  }

  public updateLayerPresetConfig(layerId: string, pathKey: string, value: any): void {
    const layer = this.layers.get(layerId);
    if (!layer || !layer.preset) return;

    setNestedValue(layer.preset.config.defaultConfig, pathKey, value);

    const activePreset = this.presetLoader.getActivePreset(`${layerId}-${layer.preset.id}`);
    if (activePreset && activePreset.updateConfig) {
      activePreset.updateConfig(layer.preset.config.defaultConfig);
    }
    this.saveLayerPresetConfig(layer.preset.id, layerId, layer.preset.config.defaultConfig).catch(
      err => console.warn(`Could not save config for ${layer.preset?.id}:`, err)
    );
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

