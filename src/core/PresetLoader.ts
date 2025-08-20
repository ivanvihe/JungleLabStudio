import * as THREE from 'three';

export interface PresetConfig {
  name: string;
  description: string;
  author: string;
  version: string;
  category: string;
  tags: string[];
  thumbnail?: string;
  note?: number;
  defaultConfig: any;
  controls: Array<{
    name: string;
    type: 'slider' | 'color' | 'checkbox' | 'select';
    label: string;
    min?: number;
    max?: number;
    step?: number;
    default: any;
    options?: string[];
  }>;
  audioMapping: {
    low: { description: string; frequency: string; effect: string; };
    mid: { description: string; frequency: string; effect: string; };
    high: { description: string; frequency: string; effect: string; };
  };
  performance: {
    complexity: 'low' | 'medium' | 'high';
    recommendedFPS: number;
    gpuIntensive: boolean;
  };
}

export interface AudioData {
  low: number;
  mid: number;
  high: number;
  fft: number[];
}

export abstract class BasePreset {
  protected scene: THREE.Scene;
  protected camera: THREE.Camera;
  protected renderer: THREE.WebGLRenderer;
  protected config: PresetConfig;
  protected audioData: AudioData = { low: 0, mid: 0, high: 0, fft: [] };
  protected clock: THREE.Clock = new THREE.Clock();
  protected opacity: number = 1.0;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, config: PresetConfig) {
    this.scene = scene;
    this.camera = camera;
    this.renderer = renderer;
    this.config = config;
  }

  abstract init(): void;
  abstract update(): void;
  abstract dispose(): void;

  public updateAudioData(audioData: AudioData): void {
    this.audioData = audioData;
  }

  public setOpacity(opacity: number): void {
    this.opacity = opacity;
  }

  public getConfig(): PresetConfig {
    return this.config;
  }

  public updateConfig(newConfig: Partial<PresetConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }
}

export interface LoadedPreset {
  id: string;
  config: PresetConfig;
  createPreset: (scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, config: PresetConfig, shaderCode?: string) => BasePreset;
  shaderCode?: string;
  folderPath: string;
}

export class PresetLoader {
  private loadedPresets: Map<string, LoadedPreset> = new Map();
  private activePresets: Map<string, BasePreset> = new Map();

  // Registro manual de presets disponibles
  private availablePresets = [
    'neural_network',
    'abstract-lines',
    'evolutive-particles',
    'plasma-ray',
    'text-glitch'
  ];

  constructor(
    private scene: THREE.Scene,
    private camera: THREE.Camera,
    private renderer: THREE.WebGLRenderer
  ) {}

  public async loadAllPresets(): Promise<LoadedPreset[]> {
    console.log('🔍 Loading presets:', this.availablePresets);
    
    const loadPromises = this.availablePresets.map(presetId => this.loadPreset(presetId));
    const results = await Promise.allSettled(loadPromises);
    
    const loadedPresets: LoadedPreset[] = [];
    results.forEach((result, index) => {
      if (result.status === 'fulfilled' && result.value) {
        loadedPresets.push(result.value);
        console.log(`✅ Preset loaded: ${result.value.config.name}`);
      } else {
        console.error(`❌ Failed to load preset: ${this.availablePresets[index]}`, result.reason);
      }
    });

    console.log(`🎨 Loaded ${loadedPresets.length} presets total`);
    return loadedPresets;
  }

  private async loadPreset(presetId: string): Promise<LoadedPreset | null> {
    try {
      let config: PresetConfig;
      let shaderCode: string | undefined;
      let createPreset: LoadedPreset['createPreset'];

      const module = await import(`../presets/${presetId}/preset.ts`);
      config = module.config;
      createPreset = module.createPreset;

      try {
        const shaderModule = await import(`../presets/${presetId}/shader.wgsl?raw`);
        shaderCode = shaderModule.default;
      } catch {
        console.warn(`No shader found for preset ${presetId}`);
      }

      const loadedPreset: LoadedPreset = {
        id: presetId,
        config,
        createPreset,
        shaderCode,
        folderPath: `src/presets/${presetId}`
      };

      this.loadedPresets.set(presetId, loadedPreset);
      return loadedPreset;

    } catch (error) {
      console.error(`Failed to load preset from ${presetId}:`, error);
      return null;
    }
  }

  private async loadPresetModule(presetId: string): Promise<LoadedPreset['createPreset']> {
    try {
      const module = await import(`../presets/${presetId}/preset.ts`);
      return module.createPreset;
    } catch (error) {
      console.error(`Failed to load preset module for ${presetId}:`, error);
      throw error;
    }
  }

  public activatePreset(presetId: string): BasePreset | null {
    const loadedPreset = this.loadedPresets.get(presetId);
    if (!loadedPreset) {
      console.error(`Preset ${presetId} not found`);
      return null;
    }

    try {
      // Desactivar preset anterior si existe
      this.deactivatePreset(presetId);

      // Crear nueva instancia del preset
      const presetInstance = loadedPreset.createPreset(
        this.scene,
        this.camera,
        this.renderer,
        loadedPreset.config,
        loadedPreset.shaderCode
      );

      presetInstance.init();
      this.activePresets.set(presetId, presetInstance);
      
      console.log(`🎨 Activated preset: ${loadedPreset.config.name}`);
      return presetInstance;
    } catch (error) {
      console.error(`Failed to activate preset ${presetId}:`, error);
      return null;
    }
  }

  public deactivatePreset(presetId: string): void {
    const activePreset = this.activePresets.get(presetId);
    if (activePreset) {
      activePreset.dispose();
      this.activePresets.delete(presetId);
      console.log(`🗑️ Deactivated preset: ${presetId}`);
    }
  }

  public getLoadedPresets(): LoadedPreset[] {
    return Array.from(this.loadedPresets.values());
  }

  public getActivePreset(presetId: string): BasePreset | null {
    return this.activePresets.get(presetId) || null;
  }

  public getActivePresets(): BasePreset[] {
    return Array.from(this.activePresets.values());
  }

  public updateActivePresets(): void {
    this.activePresets.forEach(preset => preset.update());
  }

  public updateAudioData(audioData: AudioData): void {
    this.activePresets.forEach(preset => preset.updateAudioData(audioData));
  }

  public dispose(): void {
    this.activePresets.forEach(preset => preset.dispose());
    this.activePresets.clear();
    this.loadedPresets.clear();
  }
}