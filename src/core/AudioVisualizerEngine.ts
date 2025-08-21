// AudioVisualizerEngine.ts - Corregido y completo

import * as THREE from 'three';
import { PresetLoader, LoadedPreset, AudioData } from './PresetLoader';
import fs from 'fs';
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
  private animationId: number | null = null;
  private isRunning = false;
  private multiMonitorMode = false;
  private lastFrameSent = 0;

  // Compositing scene para mezclar layers
  private compositingScene: THREE.Scene;
  private compositingCamera: THREE.OrthographicCamera;
  private compositingMaterial: THREE.ShaderMaterial;
  private compositingGeometry: THREE.PlaneGeometry;
  private compositingMesh: THREE.Mesh;

  // Map layer id -> LayerState
  private layers: Map<string, LayerState> = new Map();
  private layerOrder: string[] = ['C', 'B', 'A']; // C=fondo, A=frente
  private currentBpm: number = 120;

  constructor(private canvas: HTMLCanvasElement, options: { glitchTextPads?: number } = {}) {
    this.camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
      // Necesario para capturar frames y replicar la vista en monitores secundarios
      // cuando el modo multi-monitor está activo. Puede tener un ligero impacto en
      // el rendimiento, pero garantiza que el contenido del canvas esté disponible
      // para toBlob()/toDataURL.
      preserveDrawingBuffer: true
    });
    
    // Configuración optimizada del renderer
    this.renderer.autoClear = false;
    this.renderer.setClearColor(0x000000, 0); // Fondo transparente
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    
    // Inicializar compositing
    this.setupCompositing();
    
    // Crear estados para cada layer
    this.layerOrder.forEach(id => {
      this.createLayer(id);
    });

    this.presetLoader = new PresetLoader(this.camera, this.renderer, options.glitchTextPads ?? 1);
    this.setupScene();
    this.setupEventListeners();
  }

  private setupCompositing(): void {
    // Scene para combinar layers
    this.compositingScene = new THREE.Scene();
    this.compositingCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    
    // Material shader para mezclar layers con transparencia
    this.compositingMaterial = new THREE.ShaderMaterial({
      uniforms: {
        layerC: { value: null },
        layerB: { value: null },
        layerA: { value: null },
        opacityC: { value: 1.0 },
        opacityB: { value: 1.0 },
        opacityA: { value: 1.0 },
        globalOpacity: { value: 1.0 }
      },
      vertexShader: `
        varying vec2 vUv;
        void main() {
          vUv = uv;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform sampler2D layerC;
        uniform sampler2D layerB;
        uniform sampler2D layerA;
        uniform float opacityC;
        uniform float opacityB;
        uniform float opacityA;
        uniform float globalOpacity;
        varying vec2 vUv;

        void main() {
          vec4 colorC = texture2D(layerC, vUv);
          vec4 colorB = texture2D(layerB, vUv);
          vec4 colorA = texture2D(layerA, vUv);

          // Aplicar opacidades individuales
          colorC.a *= opacityC;
          colorB.a *= opacityB;
          colorA.a *= opacityA;

          // Blending correcto: de atrás hacia adelante (C -> B -> A)
          vec4 result = vec4(0.0, 0.0, 0.0, 0.0);

          // Layer C (fondo)
          result = mix(result, colorC, colorC.a);

          // Layer B (medio) - blend sobre el resultado anterior
          result.rgb = mix(result.rgb, colorB.rgb, colorB.a);
          result.a = max(result.a, colorB.a);

          // Layer A (frente) - blend sobre el resultado anterior  
          result.rgb = mix(result.rgb, colorA.rgb, colorA.a);
          result.a = max(result.a, colorA.a);

          // Aplicar opacidad global
          result.a *= globalOpacity;

          gl_FragColor = result;
        }
      `,
      transparent: true,
      blending: THREE.NormalBlending,
      depthTest: false,
      depthWrite: false
    });
    
    this.compositingGeometry = new THREE.PlaneGeometry(2, 2);
    this.compositingMesh = new THREE.Mesh(this.compositingGeometry, this.compositingMaterial);
    this.compositingScene.add(this.compositingMesh);
  }

  private createLayer(id: string): void {
    const scene = new THREE.Scene();
    scene.background = null; // CRÍTICO: Fondo transparente
    scene.overrideMaterial = null; // No override material

    // Crear render target con canal alpha
    const renderTarget = new THREE.WebGLRenderTarget(1920, 1080, {
      format: THREE.RGBAFormat,
      type: THREE.UnsignedByteType,
      minFilter: THREE.LinearFilter,
      magFilter: THREE.LinearFilter,
      generateMipmaps: false,
      stencilBuffer: false,
      depthBuffer: true,
      alpha: true, // IMPORTANTE: Habilitar canal alpha
      premultiplyAlpha: false // Evitar pre-multiplicación de alpha
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
    let width = rect.width;
    let height = rect.height;

    // Al ir a fullscreen el canvas puede reportar 0x0 temporalmente.
    // Evitamos propagar esos valores para no crear render targets inválidos.
    if (width === 0 || height === 0) {
      width = window.innerWidth;
      height = window.innerHeight;
    }
    const pixelRatio = Math.min(window.devicePixelRatio, 2);

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(pixelRatio);

    // Actualizar render targets de layers
    this.layers.forEach((layer, id) => {
      if (layer.renderTarget) {
        layer.renderTarget.setSize(width * pixelRatio, height * pixelRatio);
      }
    });
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

      // Limpiar canvas
      this.renderer.clear();

      // Renderizar cada layer independientemente
      this.renderLayers();

      // Componer resultado final
      this.compositeAndRender();
    };

    animate();
    console.log('🔄 Render loop started con layers independientes');
  }

  private renderLayers(): void {
    this.layers.forEach((layer, layerId) => {
      if (!layer.isActive || !layer.preset || !layer.renderTarget) return;

      // CORRECCIÓN: Asegurar clear correcto antes de renderizar layer
      this.renderer.setClearColor(0x000000, 0); // Transparente
      this.renderer.setRenderTarget(layer.renderTarget);
      this.renderer.clear(true, true, false); // Clear color y depth, no stencil
      // Renderizar layer a su render target
      this.renderer.setRenderTarget(layer.renderTarget);
      this.renderer.clear();
      
      // La scene ya contiene el preset activo, solo renderizar
      this.renderer.render(layer.scene, this.camera);
    });

    // Actualizar todos los presets activos
    this.presetLoader.updateActivePresets();

    // Volver al canvas principal
    this.renderer.setRenderTarget(null);
  }

  private compositeAndRender(): void {
    // Limpiar con alpha = 0 (transparente)
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.clear();

    // Actualizar texturas y opacidades en el shader
    this.layers.forEach((layer, layerId) => {
      const uniformName = `layer${layerId}`;
      const opacityUniform = `opacity${layerId}`;

      if (layer.renderTarget && this.compositingMaterial.uniforms[uniformName]) {
        this.compositingMaterial.uniforms[uniformName].value = layer.renderTarget.texture;
        this.compositingMaterial.uniforms[opacityUniform].value = layer.isActive ? 
          layer.opacity : 0.0;
      }
    });

    // Renderizar composición final con blending correcto
    this.renderer.render(this.compositingScene, this.compositingCamera);

    // Si estamos en modo multi-monitor, enviar frames a las ventanas clon
    if (this.multiMonitorMode && typeof window !== 'undefined') {
      const api = (window as any).electronAPI;
      const now = performance.now();
      // Throttle a ~30 FPS (33ms)
      if (api?.broadcastFrame && now - this.lastFrameSent > 33) {
        this.lastFrameSent = now;
        this.canvas.toBlob(async (blob) => {
          if (!blob) return;
          const buffer = await blob.arrayBuffer();
          api.broadcastFrame(Buffer.from(buffer));
        }, 'image/jpeg', 0.7);
      }
    }
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
      const savedConfig = this.loadLayerPresetConfig(presetId, layerId);
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

  private loadLayerPresetConfig(presetId: string, layerId: string): any {
    try {
      const cfgPath = this.getLayerConfigPath(presetId, layerId);
      if (
        typeof fs?.existsSync === 'function' &&
        typeof fs?.readFileSync === 'function' &&
        fs.existsSync(cfgPath)
      ) {
        return JSON.parse(fs.readFileSync(cfgPath, 'utf-8'));
      }
    } catch (err) {
      console.warn(`Could not load config for ${presetId} layer ${layerId}:`, err);
    }
    return {};
  }

  private saveLayerPresetConfig(presetId: string, layerId: string, cfg: any): void {
    try {
      if (
        typeof fs?.mkdirSync === 'function' &&
        typeof fs?.writeFileSync === 'function'
      ) {
        const cfgPath = this.getLayerConfigPath(presetId, layerId);
        const dir = cfgPath.substring(0, cfgPath.lastIndexOf('/'));
        fs.mkdirSync(dir, { recursive: true });
        fs.writeFileSync(cfgPath, JSON.stringify(cfg, null, 2));
      }
    } catch (err) {
      console.warn(`Could not save config for ${presetId} layer ${layerId}:`, err);
    }
  }

  public getLayerPresetConfig(layerId: string, presetId: string): any {
    const saved = this.loadLayerPresetConfig(presetId, layerId);
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
    this.saveLayerPresetConfig(layer.preset.id, layerId, layer.preset.config.defaultConfig);
  }

  public setGlobalOpacity(opacity: number): void {
    this.compositingMaterial.uniforms.globalOpacity.value = opacity;
  }

  // ✅ MÉTODOS CORREGIDOS - Compatibles con PresetLoader real
  public getAvailablePresets(): LoadedPreset[] {
    return this.presetLoader.getLoadedPresets();
  }

  public async updateGlitchPadCount(count: number): Promise<LoadedPreset[]> {
    this.presetLoader.setGlitchTextPads(count);
    await this.presetLoader.loadAllPresets();
    return this.presetLoader.getLoadedPresets();
  }

  public updateAudioData(audioData: AudioData): void {
    this.presetLoader.updateAudioData(audioData);
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

  public clearRenderer(): void {
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.clear(true, true, true);
  }

  public updateBpm(bpm: number): void {
    this.currentBpm = bpm;
    this.layers.forEach(layer => {
      layer.preset?.setBpm(bpm);
    });
  }

  public triggerBeat(): void {
    this.layers.forEach(layer => {
      layer.preset?.onBeat();
    });
  }

  public dispose(): void {
    this.isRunning = false;
    
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }

    // Limpiar layers
    this.layers.forEach((layer, layerId) => {
      if (layer.preset) {
        this.presetLoader.deactivatePreset(`${layerId}-${layer.preset.id}`);
      }
      if (layer.renderTarget) {
        layer.renderTarget.dispose();
      }
      layer.scene.clear();
    });

    // Limpiar compositing
    this.compositingGeometry.dispose();
    this.compositingMaterial.dispose();

    this.presetLoader.dispose();
    this.renderer.dispose();
    
    console.log('🧹 Engine disposed');
  }
}