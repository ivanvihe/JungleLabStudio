// MEJORA 3: AudioVisualizerEngine.ts con independencia total de layers

import * as THREE from 'three';
import { PresetLoader, LoadedPreset, AudioData } from './PresetLoader';

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

  // Compositing scene para mezclar layers
  private compositingScene: THREE.Scene;
  private compositingCamera: THREE.OrthographicCamera;
  private compositingMaterial: THREE.ShaderMaterial;
  private compositingGeometry: THREE.PlaneGeometry;
  private compositingMesh: THREE.Mesh;

  // Map layer id -> LayerState
  private layers: Map<string, LayerState> = new Map();
  private layerOrder: string[] = ['C', 'B', 'A']; // C=fondo, A=frente

  constructor(private canvas: HTMLCanvasElement, options: { glitchTextPads?: number } = {}) {
    this.camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
      preserveDrawingBuffer: false // Mejor rendimiento
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
          vec4 colorC = texture2D(layerC, vUv) * opacityC;
          vec4 colorB = texture2D(layerB, vUv) * opacityB;
          vec4 colorA = texture2D(layerA, vUv) * opacityA;
          
          // Mezcla aditiva con alpha blending correcto
          vec4 result = vec4(0.0, 0.0, 0.0, 0.0);
          
          // Layer C (fondo) - blend normal
          result = mix(result, colorC, colorC.a);
          
          // Layer B (medio) - blend normal con alpha
          result = mix(result, colorB, colorB.a);
          
          // Layer A (frente) - blend normal con alpha
          result = mix(result, colorA, colorA.a);
          
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
    scene.background = null; // Fondo transparente SIEMPRE
    
    // Crear render target para cada layer
    const renderTarget = new THREE.WebGLRenderTarget(1920, 1080, {
      format: THREE.RGBAFormat,
      type: THREE.UnsignedByteType,
      minFilter: THREE.LinearFilter,
      magFilter: THREE.LinearFilter,
      generateMipmaps: false,
      stencilBuffer: false,
      depthBuffer: true
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
    const width = rect.width;
    const height = rect.height;
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

      // Renderizar layer a su render target
      this.renderer.setRenderTarget(layer.renderTarget);
      this.renderer.clear();
      
      // Actualizar preset del layer
      this.presetLoader.updatePreset(layer.preset.id);
      
      // Renderizar scene del layer con fondo transparente
      this.renderer.render(layer.scene, this.camera);
    });

    // Volver al canvas principal
    this.renderer.setRenderTarget(null);
  }

  private compositeAndRender(): void {
    // Actualizar texturas y opacidades en el shader
    this.layers.forEach((layer, layerId) => {
      const uniformName = `layer${layerId}`;
      const opacityUniform = `opacity${layerId}`;
      
      if (layer.renderTarget && this.compositingMaterial.uniforms[uniformName]) {
        this.compositingMaterial.uniforms[uniformName].value = layer.renderTarget.texture;
        this.compositingMaterial.uniforms[opacityUniform].value = layer.isActive ? layer.opacity : 0.0;
      }
    });

    // Renderizar composición final
    this.renderer.render(this.compositingScene, this.compositingCamera);
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
        this.presetLoader.deactivatePreset(layer.preset.id);
        layer.scene.clear();
      }

      // Activar nuevo preset
      const preset = this.presetLoader.activatePreset(presetId);
      if (!preset) {
        console.error(`No se pudo activar preset ${presetId}`);
        return false;
      }

      // Configurar preset con fondo transparente
      if (preset.mesh && preset.mesh.material) {
        const material = preset.mesh.material as THREE.ShaderMaterial;
        if (material.uniforms && material.uniforms.backgroundColor) {
          material.uniforms.backgroundColor.value = new THREE.Vector4(0, 0, 0, 0); // Transparente
        }
      }

      // Asignar preset al layer
      layer.preset = preset;
      layer.isActive = true;
      
      // Agregar mesh del preset a la scene del layer
      if (preset.mesh) {
        layer.scene.add(preset.mesh);
      }

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
      this.presetLoader.deactivatePreset(layer.preset.id);
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

  public updateLayerPresetConfig(layerId: string, config: any): void {
    const layer = this.layers.get(layerId);
    if (!layer || !layer.preset) return;

    // Actualizar configuración del preset específico del layer
    this.presetLoader.updatePresetConfig(layer.preset.id, config);
  }

  public setGlobalOpacity(opacity: number): void {
    this.compositingMaterial.uniforms.globalOpacity.value = opacity;
  }

  public getAvailablePresets(): LoadedPreset[] {
    return this.presetLoader.getAllPresets();
  }

  public async updateGlitchPadCount(count: number): Promise<LoadedPreset[]> {
    return await this.presetLoader.updateGlitchPadCount(count);
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

  public dispose(): void {
    this.isRunning = false;
    
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }

    // Limpiar layers
    this.layers.forEach((layer, layerId) => {
      if (layer.preset) {
        this.presetLoader.deactivatePreset(layer.preset.id);
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