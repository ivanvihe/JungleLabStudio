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
  camera: THREE.PerspectiveCamera;
  renderer: THREE.WebGLRenderer;
  opacity: number;
  fadeTime: number;
  isActive: boolean;
}

/**
 * Maneja la creacion, activacion y renderizado de layers.
 */
export class LayerManager {
  private layers: Map<string, LayerState> = new Map();
  private layerOrder: string[] = ['C', 'B', 'A'];

  constructor(
    private container: HTMLElement,
    private baseCamera: THREE.PerspectiveCamera,
    private presetLoader: PresetLoader
  ) {
    this.layerOrder.forEach(id => this.createLayer(id));
  }

  private createLayer(id: string): void {
    const scene = new THREE.Scene();
    scene.background = null;
    scene.overrideMaterial = null;

    const camera = this.baseCamera.clone() as THREE.PerspectiveCamera;

    const canvas = document.createElement('canvas');
    canvas.className = `layer-canvas layer-${id}`;
    canvas.style.position = 'absolute';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    const zIndex = this.layerOrder.indexOf(id) + 1;
    canvas.style.zIndex = zIndex.toString();
    canvas.style.pointerEvents = 'none';
    canvas.style.opacity = '0';
    this.container.appendChild(canvas);

    const renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
      preserveDrawingBuffer: true
    });
    renderer.autoClear = true;
    renderer.setClearColor(0x000000, 0);
    renderer.outputColorSpace = THREE.SRGBColorSpace;

    const layerState: LayerState = {
      preset: null,
      scene,
      camera,
      renderer,
      opacity: 1.0,
      fadeTime: 1000,
      isActive: false
    };

    this.layers.set(id, layerState);
    console.log(`🔧 Layer ${id} creado con canvas propio`);
  }

  public renderLayers(): void {
    this.layers.forEach(layer => {
      layer.renderer.setClearColor(0x000000, 0);
      layer.renderer.clear(true, true, true);
      if (layer.isActive && layer.preset) {
        layer.renderer.render(layer.scene, layer.camera);
      }
    });

    this.presetLoader.updateActivePresets();
  }

  public updateSize(width: number, height: number, pixelRatio: number): void {
    this.layers.forEach(layer => {
      layer.renderer.setSize(width, height, false);
      layer.renderer.setPixelRatio(pixelRatio);
      layer.camera.aspect = width / height;
      layer.camera.updateProjectionMatrix();
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
        loadedPresetConfig,
        layer.camera,
        layer.renderer
      );
      if (!presetInstance) {
        console.error(`No se pudo activar preset ${presetId}`);
        return false;
      }

      layer.preset = { ...loadedPreset, config: loadedPresetConfig };
      layer.isActive = true;
      layer.renderer.domElement.style.opacity = layer.opacity.toString();
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
    layer.renderer.clear();
    layer.renderer.domElement.style.opacity = '0';
    console.log(`🗑️ Layer ${layerId} desactivado`);
  }

  public updateLayerConfig(layerId: string, config: any): void {
    const layer = this.layers.get(layerId);
    if (!layer) return;

    if (config.opacity !== undefined) {
      layer.opacity = config.opacity / 100;
      layer.renderer.domElement.style.opacity = layer.isActive
        ? layer.opacity.toString()
        : '0';
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
          const api = (window as any).electronAPI;
          if (await api.exists(cfgPath)) {
            const content = await api.readTextFile(cfgPath);
            return JSON.parse(content);
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
          const api = (window as any).electronAPI;
          await api.createDir(dir);
          await api.writeTextFile(cfgPath, JSON.stringify(cfg, null, 2));
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

  public getLayerCanvas(layerId: string): HTMLCanvasElement | undefined {
    return this.layers.get(layerId)?.renderer.domElement;
  }

  public clearAll(): void {
    this.layers.forEach(layer => {
      layer.renderer.setClearColor(0x000000, 0);
      layer.renderer.clear(true, true, true);
    });
  }

  public updateBpm(bpm: number): void {
    this.layers.forEach((layer, layerId) => {
      if (!layer.preset) return;
      const active = this.presetLoader.getActivePreset(`${layerId}-${layer.preset.id}`);
      active?.setBpm(bpm);
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
      layer.scene.clear();
      layer.renderer.dispose();
      layer.renderer.domElement.remove();
    });
  }
}

