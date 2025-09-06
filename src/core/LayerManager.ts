import * as THREE from 'three';
import { PresetLoader, LoadedPreset } from './PresetLoader';
import { setNestedValue } from '../utils/objectPath';

function deepMerge(target: any, source: any): any {
  const result = { ...target };
  for (const key in source) {
    if (
      source[key] &&
      typeof source[key] === 'object' &&
      !Array.isArray(source[key])
    ) {
      result[key] = deepMerge(result[key] || {}, source[key]);
    } else {
      result[key] = source[key];
    }
  }
  return result;
}

export interface LayerState {
  preset: LoadedPreset | null;
  scene: THREE.Scene;
  opacity: number;
  fadeTime: number;
  isActive: boolean;
  renderTarget?: THREE.WebGLRenderTarget;
  material?: THREE.Material;
}

/**
 * Maneja la creacion, activacion y renderizado de layers.
 */
export class LayerManager {
  private layers: Map<string, LayerState> = new Map();
  private layerOrder: string[] = ['C', 'B', 'A'];

  constructor(
    private renderer: THREE.WebGLRenderer,
    private camera: THREE.PerspectiveCamera,
    private presetLoader: PresetLoader
  ) {
    this.layerOrder.forEach(id => this.createLayer(id));
  }

  private createLayer(id: string): void {
    const scene = new THREE.Scene();
    scene.background = null;
    scene.overrideMaterial = null;

    const renderTarget = new THREE.WebGLRenderTarget(1920, 1080, {
      format: THREE.RGBAFormat,
      type: THREE.UnsignedByteType,
      minFilter: THREE.LinearFilter,
      magFilter: THREE.LinearFilter,
      generateMipmaps: false,
      stencilBuffer: false,
      depthBuffer: true,
      alpha: true,
      premultiplyAlpha: false
    });

    const layerState: LayerState = {
      preset: null,
      scene,
      opacity: 1.0,
      fadeTime: 1000,
      isActive: false,
      renderTarget
    };

    this.layers.set(id, layerState);
    console.log(`🔧 Layer ${id} creado con render target`);
  }

  public renderLayers(): void {
    this.layers.forEach(layer => {
      if (!layer.isActive || !layer.preset || !layer.renderTarget) return;

      this.renderer.setClearColor(0x000000, 0);
      this.renderer.setRenderTarget(layer.renderTarget);
      this.renderer.clearDepth(); // Clear only depth buffer
      this.renderer.clearStencil(); // Clear only stencil buffer
      // Do NOT clear the color buffer (alpha channel)
      this.renderer.render(layer.scene, this.camera);
    });

    this.presetLoader.updateActivePresets();
    this.renderer.setRenderTarget(null);
  }

  public updateSize(width: number, height: number, pixelRatio: number): void {
    this.layers.forEach(layer => {
      layer.renderTarget?.setSize(width * pixelRatio, height * pixelRatio);
    });
  }

  public async activateLayerPreset(layerId: string, presetId: string): Promise<boolean> {
    const layer = this.layers.get(layerId);
    if (!layer) {
      console.error(`Layer ${layerId} no encontrado`);
      return false;
    }

    try {
      if (layer.preset) {
        this.presetLoader.deactivatePreset(`${layerId}-${layer.preset.id}`);
        layer.scene.clear();
      }

      const loadedPreset = this.presetLoader.getLoadedPresets().find(p => p.id === presetId);
      if (!loadedPreset) {
        console.error(`Loaded preset ${presetId} no encontrado`);
        return false;
      }

        const savedConfig = await this.loadLayerPresetConfig(presetId, layerId);
        const loadedPresetConfig = JSON.parse(JSON.stringify(loadedPreset.config));
        loadedPresetConfig.defaultConfig = deepMerge(
          loadedPresetConfig.defaultConfig,
          savedConfig
        );

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
    const layer = this.layers.get(layerId);
    if (!layer) return;

    if (layer.preset) {
      this.presetLoader.deactivatePreset(`${layerId}-${layer.preset.id}`);
      layer.scene.clear();
      layer.preset = null;
    }

    layer.isActive = false;
    console.log(`🗑️ Layer ${layerId} desactivado`);
  }

  public updateLayerConfig(layerId: string, config: any): void {
    const layer = this.layers.get(layerId);
    if (!layer) return;

    if (config.opacity !== undefined) {
      layer.opacity = config.opacity / 100;
    }

    if (config.fadeTime !== undefined) {
      layer.fadeTime = config.fadeTime;
    }
  }

  private getLayerConfigPath(presetId: string, layerId: string): string {
    const loaded = this.presetLoader.getLoadedPresets().find(p => p.id === presetId);
    const folder = loaded?.folderPath ?? `${this.presetLoader.getBasePath()}/${presetId}`;
    const variantMatch = presetId.match(/-(\d+)$/);
    const variantSuffix = variantMatch ? `-${variantMatch[1]}` : '';
    return `${folder}/layers/${layerId}${variantSuffix}.json`;
  }

  private async loadLayerPresetConfig(presetId: string, layerId: string): Promise<any> {
    try {
      const cfgPath = this.getLayerConfigPath(presetId, layerId);
      if (typeof window !== 'undefined') {
        if ((window as any).__TAURI__) {
          const { exists, readTextFile } = await import(
            /* @vite-ignore */ '@tauri-apps/api/fs'
          );
          if (await exists(cfgPath)) {
            return JSON.parse(await readTextFile(cfgPath));
          }
        } else if ((window as any).electronAPI) {
          const fs = await import('fs');
          if (fs.existsSync(cfgPath)) {
            return JSON.parse(fs.readFileSync(cfgPath, 'utf-8'));
          }
        }
      }
    } catch (err) {
      console.warn(`Could not load config for ${presetId} layer ${layerId}:`, err);
    }
    return {};
  }

  private async saveLayerPresetConfig(
    presetId: string,
    layerId: string,
    cfg: any
  ): Promise<void> {
    try {
      if (typeof window !== 'undefined') {
        const cfgPath = this.getLayerConfigPath(presetId, layerId);
        const dir = cfgPath.substring(0, cfgPath.lastIndexOf('/'));
        if ((window as any).__TAURI__) {
          const { createDir, writeFile } = await import(
            /* @vite-ignore */ '@tauri-apps/api/fs'
          );
          await createDir(dir, { recursive: true });
          await writeFile({ path: cfgPath, contents: JSON.stringify(cfg, null, 2) });
        } else if ((window as any).electronAPI) {
          const fs = await import('fs');
          await fs.promises.mkdir(dir, { recursive: true });
          await fs.promises.writeFile(cfgPath, JSON.stringify(cfg, null, 2));
        }
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
      err =>
        console.warn(
          `Could not save config for ${layer.preset?.id} layer ${layerId}:`,
          err
        )
    );
  }

  public getLayerStatus(): Record<string, { active: boolean; preset: string | null }> {
    const status: Record<string, { active: boolean; preset: string | null }> = {};

    this.layers.forEach((layer, layerId) => {
      status[layerId] = {
        active: layer.isActive,
        preset: layer.preset?.id || null
      };
    });

    return status;
  }

  public getLayers(): Map<string, LayerState> {
    return this.layers;
  }

  public updateBpm(bpm: number): void {
    this.layers.forEach(layer => {
      layer.preset?.setBpm(bpm);
    });
  }

  public triggerBeat(): void {
    this.layers.forEach((layer, layerId) => {
      if (!layer.preset) return;
      const active = this.presetLoader.getActivePreset(`${layerId}-${layer.preset.id}`);
      active?.onBeat();
    });
  }

  public dispose(): void {
    this.layers.forEach((layer, layerId) => {
      if (layer.preset) {
        this.presetLoader.deactivatePreset(`${layerId}-${layer.preset.id}`);
      }
      if (layer.renderTarget) {
        layer.renderTarget.dispose();
      }
      layer.scene.clear();
    });
  }
}

