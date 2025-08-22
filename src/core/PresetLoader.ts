import * as THREE from 'three';
import fs from 'fs';

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
    type: 'slider' | 'color' | 'checkbox' | 'select' | 'text';
    label: string;
    min?: number;
    max?: number;
    step?: number;
    default: any;
    options?: string[];
  }>;
  audioMapping: Record<string, { description: string; frequency: string; effect: string }>;
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
  protected bpm: number = 120;

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

  public setBpm(bpm: number): void {
    this.bpm = bpm;
  }

  // Hook for beat events from MIDI clock
  public onBeat(): void {
    // default no-op, can be overridden by presets
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
  private customTextContents: string[] = [];

  // Carga dinámica de presets desde el sistema de archivos
  private presetModules = import.meta.glob('../presets/*/preset.ts');
  private shaderModules = import.meta.glob('../presets/*/shader.wgsl', { as: 'raw' });
  private nextMidiNote: number = 36; // C2 como nota base

  // Listeners para cambios en presets
  private presetsChangeListeners: (() => void)[] = [];

  constructor(
    private camera: THREE.Camera,
    private renderer: THREE.WebGLRenderer,
    private glitchTextPads: number = 1
  ) {}

  public setGlitchTextPads(count: number): void {
    // Mantener compatibilidad, reutilizando textos actuales
    this.setCustomTextInstances(count, this.customTextContents);
  }

  public setCustomTextInstances(count: number, texts: string[]): void {
    const newCount = Math.max(1, Math.min(10, count));
    this.glitchTextPads = newCount;
    this.customTextContents = texts.slice(0, newCount);
    while (this.customTextContents.length < newCount) {
      this.customTextContents.push(`Text ${this.customTextContents.length + 1}`);
    }
    console.log(`🔧 Custom text instances set to: ${this.glitchTextPads}`);
    this.reloadCustomTextPresets();
  }

  public getGlitchTextPads(): number {
    return this.glitchTextPads;
  }

  private async reloadCustomTextPresets(): Promise<void> {
    // Buscar el preset custom-glitch-text base
    const customTextEntry = Object.entries(this.presetModules)
      .find(([path]) => path.includes('custom-glitch-text'));
    
    if (!customTextEntry) return;

    const [path, loader] = customTextEntry;
    const presetId = path.split('/')[2];
    
    try {
      const mod: any = await loader();
      let cfg: PresetConfig = mod.config;
      const createPreset = mod.createPreset;

      // Auto-configurar preset si es necesario
      cfg = this.autoConfigurePreset(cfg, presetId);
      
      let shaderCode: string | undefined;
      const shaderPath = `../presets/${presetId}/shader.wgsl`;
      const shaderLoader = this.shaderModules[shaderPath];
      if (shaderLoader) {
        const shaderModule: any = await (shaderLoader as any)();
        shaderCode = shaderModule.default;
      }

      // Limpiar instancias existentes de custom text
      for (const [id] of this.loadedPresets.entries()) {
        if (id.startsWith('custom-glitch-text')) {
          this.loadedPresets.delete(id);
        }
      }

      // Crear nuevas instancias
      const baseNote = cfg.note!;
      for (let i = 1; i <= this.glitchTextPads; i++) {
        const cloneConfig = JSON.parse(JSON.stringify(cfg));
        const text = this.customTextContents[i - 1] || `Text ${i}`;
        cloneConfig.name = text;

        if (cloneConfig.defaultConfig?.text?.content !== undefined) {
          cloneConfig.defaultConfig.text.content = text;
        }

        cloneConfig.note = baseNote + (i - 1);
        
        const clone: LoadedPreset = {
          id: `${presetId}-${i}`,
          config: cloneConfig,
          createPreset,
          shaderCode,
          folderPath: `src/presets/${presetId}`,
        };
        
        this.loadedPresets.set(clone.id, clone);
        console.log(`✅ Custom text instance reloaded: ${clone.config.name}`);
      }

      // Notificar cambios
      this.notifyPresetsChanged();
      
    } catch (error) {
      console.error('Error reloading custom text presets:', error);
    }
  }

  public async loadAllPresets(): Promise<LoadedPreset[]> {
    const moduleEntries = Object.entries(this.presetModules);
    console.log('🔍 Loading presets:', moduleEntries.map(([p]) => p));

    this.loadedPresets.clear();
    const loadedPresets: LoadedPreset[] = [];

    // Determinar la siguiente nota disponible
    let maxNote = 0;
    for (const [, loader] of moduleEntries) {
      const mod: any = await loader();
      const cfg: PresetConfig = mod.config;
      if (typeof cfg.note === 'number' && cfg.note > maxNote) {
        maxNote = cfg.note;
      }
    }
    let nextNote = maxNote + 1;
    this.nextMidiNote = nextNote;

    for (const [path, loader] of moduleEntries) {
      const presetId = path.split('/')[2];
      const mod: any = await loader();
      let cfg: PresetConfig = mod.config;

      // Auto-configurar preset si es necesario
      cfg = this.autoConfigurePreset(cfg, presetId);
      if (typeof cfg.note !== 'number') {
        cfg.note = nextNote++;
        await this.persistNote(presetId, cfg.note);
      }
      const createPreset = mod.createPreset;

      let shaderCode: string | undefined;
      const shaderPath = `../presets/${presetId}/shader.wgsl`;
      const shaderLoader = this.shaderModules[shaderPath];
      if (shaderLoader) {
        const shaderModule: any = await (shaderLoader as any)();
        shaderCode = shaderModule.default;
      }

      this.updateMidiNoteTracking(cfg.note);

      // Manejo especial para custom-glitch-text
      if (presetId === 'custom-glitch-text') {
        const baseNote = cfg.note!;
        
        for (let i = 1; i <= this.glitchTextPads; i++) {
          const cloneConfig = JSON.parse(JSON.stringify(cfg));
          const text = this.customTextContents[i - 1] || `Text ${i}`;
          cloneConfig.name = text;

          if (cloneConfig.defaultConfig?.text?.content !== undefined) {
            cloneConfig.defaultConfig.text.content = text;
          }

          cloneConfig.note = baseNote + (i - 1);
          
          const clone: LoadedPreset = {
            id: `${presetId}-${i}`,
            config: cloneConfig,
            createPreset,
            shaderCode,
            folderPath: `src/presets/${presetId}`,
          };
          
          this.loadedPresets.set(clone.id, clone);
          loadedPresets.push(clone);
          console.log(`✅ Preset loaded: ${clone.config.name}`);
        }
      } else {
        // Preset normal
        const loaded: LoadedPreset = {
          id: presetId,
          config: cfg,
          createPreset,
          shaderCode,
          folderPath: `src/presets/${presetId}`
        };
        
        this.loadedPresets.set(presetId, loaded);
        loadedPresets.push(loaded);
        console.log(`✅ Preset loaded: ${cfg.name}`);
      }
    }

    console.log(`🎨 Loaded ${loadedPresets.length} presets total (${this.glitchTextPads} custom text instances)`);
    return loadedPresets;
  }

  /**
   * Auto-configura presets nuevos que no tienen configuración completa
   */
  private autoConfigurePreset(config: PresetConfig, presetId: string): PresetConfig {
    const autoConfig = { ...config };

    if (!autoConfig.note) {
      autoConfig.note = this.getNextAvailableMidiNote();
      console.log(`🎵 Auto-assigned MIDI note ${autoConfig.note} to preset ${presetId}`);
    }

    if (!autoConfig.controls) {
      autoConfig.controls = [];
    }

    return autoConfig;
  }

  /**
   * Obtiene la siguiente nota MIDI disponible
   */
  private getNextAvailableMidiNote(): number {
    const note = this.nextMidiNote;
    this.nextMidiNote++;
    return note;
  }

  /**
   * Actualiza el tracking de notas MIDI
   */
  private updateMidiNoteTracking(note: number | undefined): void {
    if (note && note >= this.nextMidiNote) {
      this.nextMidiNote = note + 1;
    }
  }

  private async persistNote(presetId: string, note: number): Promise<void> {
    try {
      const path = `src/presets/${presetId}/config.json`;
      if (
        typeof fs?.existsSync === 'function' &&
        typeof fs?.readFileSync === 'function' &&
        typeof fs?.writeFileSync === 'function' &&
        fs.existsSync(path)
      ) {
        const json = JSON.parse(fs.readFileSync(path, 'utf-8'));
        json.note = note;
        fs.writeFileSync(path, JSON.stringify(json, null, 2));
      }
    } catch (err) {
      console.warn(`Could not persist note for ${presetId}:`, err);
    }
  }

  public activatePreset(
    presetId: string,
    scene: THREE.Scene,
    instanceId: string,
    configOverride?: PresetConfig
  ): BasePreset | null {
    const loadedPreset = this.loadedPresets.get(presetId);
    if (!loadedPreset) {
      console.error(`Preset ${presetId} not found`);
      return null;
    }

    try {
      this.deactivatePreset(instanceId);

      const presetInstance = loadedPreset.createPreset(
        scene,
        this.camera,
        this.renderer,
        configOverride ?? loadedPreset.config,
        loadedPreset.shaderCode
      );

      presetInstance.init();
      this.activePresets.set(instanceId, presetInstance);

      console.log(`🎨 Activated preset: ${(configOverride ?? loadedPreset.config).name}`);
      return presetInstance;
    } catch (error) {
      console.error(`Failed to activate preset ${presetId}:`, error);
      return null;
    }
  }

  public deactivatePreset(instanceId: string): void {
    const activePreset = this.activePresets.get(instanceId);
    if (activePreset) {
      activePreset.dispose();
      this.activePresets.delete(instanceId);
      console.log(`🗑️ Deactivated preset: ${instanceId}`);
    }
  }

  public getLoadedPresets(): LoadedPreset[] {
    return Array.from(this.loadedPresets.values());
  }

  public getActivePreset(instanceId: string): BasePreset | null {
    return this.activePresets.get(instanceId) || null;
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

  // Métodos para gestión de listeners de cambios en presets
  public onPresetsChanged(callback: () => void): void {
    this.presetsChangeListeners.push(callback);
  }
  
  public removePresetsChangeListener(callback: () => void): void {
    const index = this.presetsChangeListeners.indexOf(callback);
    if (index > -1) {
      this.presetsChangeListeners.splice(index, 1);
    }
  }
  
  private notifyPresetsChanged(): void {
    this.presetsChangeListeners.forEach(callback => {
      try {
        callback();
      } catch (error) {
        console.error('Error in presets change listener:', error);
      }
    });
  }

  // Métodos de utilidad para custom text
  public getCustomTextInstances(): LoadedPreset[] {
    return Array.from(this.loadedPresets.values())
      .filter(preset => preset.id.startsWith('custom-glitch-text'));
  }

  public getPresetById(id: string): LoadedPreset | undefined {
    return this.loadedPresets.get(id);
  }

  public getAllPresetIds(): string[] {
    return Array.from(this.loadedPresets.keys());
  }

  public dispose(): void {
    this.activePresets.forEach(preset => preset.dispose());
    this.activePresets.clear();
    this.loadedPresets.clear();
    this.presetsChangeListeners.length = 0;
  }
}

// Tipos para controles de configuración
export interface ControlConfig {
  name: string;
  type: 'slider' | 'color' | 'checkbox' | 'text' | 'select';
  label: string;
  [key: string]: any;
}