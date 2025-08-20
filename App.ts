import * as THREE from 'three';
import { PresetLoader, LoadedPreset, AudioData } from './PresetLoader';

export class AudioVisualizerApp {
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private presetLoader: PresetLoader;
  private loadedPresets: LoadedPreset[] = [];
  private currentPresetId: string | null = null;

  constructor(container: HTMLElement) {
    this.initThreeJS(container);
      this.presetLoader = new PresetLoader(this.camera, this.renderer);
    this.init();
  }

  private initThreeJS(container: HTMLElement): void {
    // Scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x000000);

    // Camera
    this.camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    this.camera.position.set(0, 0, 3);

    // Renderer
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    });
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(this.renderer.domElement);

    // Resize handler
    window.addEventListener('resize', () => this.onWindowResize());
  }

  private async init(): Promise<void> {
    try {
      console.log('🔍 Scanning for presets...');
      
      // Cargar todos los presets automáticamente
      this.loadedPresets = await this.presetLoader.loadAllPresets();
      
      console.log(`✅ Found ${this.loadedPresets.length} presets:`);
      this.loadedPresets.forEach(preset => {
        console.log(`  - ${preset.config.name} (${preset.id})`);
      });

      // Activar el primer preset por defecto
      if (this.loadedPresets.length > 0) {
        this.activatePreset(this.loadedPresets[0].id);
      }

      // Setup audio listener
      await this.setupAudioListener();

      // Start render loop
      this.startRenderLoop();

      console.log('🎨 AudioVisualizer initialized successfully!');
      
    } catch (error) {
      console.error('❌ Failed to initialize AudioVisualizer:', error);
    }
  }

  private async setupAudioListener(): Promise<void> {
    try {
      // Importar dinámicamente la API de eventos de Tauri. El comentario
      // `@vite-ignore` evita que Vite intente resolver este módulo en
      // entornos donde no está disponible (por ejemplo, Electron puro).
      const { listen } = await import(
        /* @vite-ignore */ '@tauri-apps/api/event'
      );

      await listen('audio_data', (event) => {
        const audioData = event.payload as AudioData;
        this.presetLoader.updateAudioData(audioData);
      });
      console.log('🎵 Audio listener setup complete');
    } catch (error) {
      // Si la API no está disponible simplemente registra un aviso.
      console.warn('Failed to setup audio listener:', error);
    }
  }

  private startRenderLoop(): void {
    const animate = () => {
      requestAnimationFrame(animate);
      
      // Update active presets
      this.presetLoader.updateActivePresets();
      
      // Render scene
      this.renderer.render(this.scene, this.camera);
    };

    animate();
    console.log('🔄 Render loop started');
  }

  private onWindowResize(): void {
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
  }

  // Public API methods
  
  /**
   * Obtiene la lista de presets cargados
   */
  public getAvailablePresets(): LoadedPreset[] {
    return this.loadedPresets;
  }

  /**
   * Activa un preset específico
   */
  public activatePreset(presetId: string): boolean {
    try {
      // Desactivar preset actual
      if (this.currentPresetId) {
        this.presetLoader.deactivatePreset(this.currentPresetId);
      }

      // Activar nuevo preset
      const preset = this.presetLoader.activatePreset(presetId);
      if (preset) {
        this.currentPresetId = presetId;
        console.log(`🎨 Activated preset: ${presetId}`);
        return true;
      }
      
      return false;
    } catch (error) {
      console.error(`Failed to activate preset ${presetId}:`, error);
      return false;
    }
  }

  /**
   * Desactiva el preset actual
   */
  public deactivateCurrentPreset(): void {
    if (this.currentPresetId) {
      this.presetLoader.deactivatePreset(this.currentPresetId);
      this.currentPresetId = null;
      console.log('🗑️ Deactivated current preset');
    }
  }

  /**
   * Obtiene información del preset activo
   */
  public getCurrentPreset(): LoadedPreset | null {
    if (!this.currentPresetId) return null;
    return this.loadedPresets.find(p => p.id === this.currentPresetId) || null;
  }

  /**
   * Cambia la opacidad del preset activo
   */
  public setOpacity(opacity: number): void {
    if (this.currentPresetId) {
      const activePreset = this.presetLoader.getActivePreset(this.currentPresetId);
      if (activePreset) {
        activePreset.setOpacity(opacity);
      }
    }
  }

  /**
   * Actualiza la configuración del preset activo
   */
  public updatePresetConfig(config: any): void {
    if (this.currentPresetId) {
      const activePreset = this.presetLoader.getActivePreset(this.currentPresetId);
      if (activePreset) {
        activePreset.updateConfig(config);
      }
    }
  }

  /**
   * Recarga todos los presets (útil para desarrollo)
   */
  public async reloadPresets(): Promise<void> {
    console.log('🔄 Reloading presets...');
    
    // Limpiar presets actuales
    this.presetLoader.dispose();
    this.currentPresetId = null;

    // Recargar
    this.loadedPresets = await this.presetLoader.loadAllPresets();
    
    console.log(`✅ Reloaded ${this.loadedPresets.length} presets`);
  }

  /**
   * Limpia recursos al cerrar la aplicación
   */
  public dispose(): void {
    this.presetLoader.dispose();
    this.renderer.dispose();
    console.log('🧹 App disposed');
  }
}

// Factory function para inicializar la app
export async function createAudioVisualizerApp(container: HTMLElement): Promise<AudioVisualizerApp> {
  const app = new AudioVisualizerApp(container);
  return app;
}

// UI Helper para crear controles de presets
export class PresetUI {
  private app: AudioVisualizerApp;
  private container: HTMLElement;

  constructor(app: AudioVisualizerApp, container: HTMLElement) {
    this.app = app;
    this.container = container;
    this.createUI();
  }

  private createUI(): void {
    const presets = this.app.getAvailablePresets();
    
    // Crear selector de presets
    const presetSelector = document.createElement('select');
    presetSelector.className = 'preset-selector';
    presetSelector.innerHTML = '<option value="">Seleccionar preset...</option>';
    
    presets.forEach(preset => {
      const option = document.createElement('option');
      option.value = preset.id;
      option.textContent = `${preset.config.name} - ${preset.config.description}`;
      presetSelector.appendChild(option);
    });

    presetSelector.addEventListener('change', (e) => {
      const target = e.target as HTMLSelectElement;
      if (target.value) {
        this.app.activatePreset(target.value);
        this.updateControlsForPreset(target.value);
      } else {
        this.app.deactivateCurrentPreset();
        this.clearControls();
      }
    });

    // Crear container para controles dinámicos
    const controlsContainer = document.createElement('div');
    controlsContainer.className = 'preset-controls';

    // Crear control de opacidad global
    const opacityContainer = document.createElement('div');
    opacityContainer.className = 'control-group';
    
    const opacityLabel = document.createElement('label');
    opacityLabel.textContent = 'Opacidad Global: ';
    
    const opacitySlider = document.createElement('input');
    opacitySlider.type = 'range';
    opacitySlider.min = '0';
    opacitySlider.max = '1';
    opacitySlider.step = '0.01';
    opacitySlider.value = '1';
    
    opacitySlider.addEventListener('input', (e) => {
      const target = e.target as HTMLInputElement;
      this.app.setOpacity(parseFloat(target.value));
    });

    opacityContainer.appendChild(opacityLabel);
    opacityContainer.appendChild(opacitySlider);

    // Botón de recarga (útil para desarrollo)
    const reloadButton = document.createElement('button');
    reloadButton.textContent = '🔄 Recargar Presets';
    reloadButton.addEventListener('click', () => this.app.reloadPresets());

    // Ensamblar UI
    this.container.appendChild(presetSelector);
    this.container.appendChild(opacityContainer);
    this.container.appendChild(controlsContainer);
    this.container.appendChild(reloadButton);
  }

  private updateControlsForPreset(presetId: string): void {
    const presets = this.app.getAvailablePresets();
    const preset = presets.find(p => p.id === presetId);
    
    if (!preset) return;

    const controlsContainer = this.container.querySelector('.preset-controls') as HTMLElement;
    controlsContainer.innerHTML = '';

    // Crear controles basados en la configuración del preset
    preset.config.controls.forEach(control => {
      const controlElement = this.createControl(control);
      controlsContainer.appendChild(controlElement);
    });

    // Mostrar información del preset
    const infoElement = document.createElement('div');
    infoElement.className = 'preset-info';
    infoElement.innerHTML = `
      <h3>${preset.config.name}</h3>
      <p>${preset.config.description}</p>
      <small>Autor: ${preset.config.author} | Versión: ${preset.config.version}</small>
    `;
    controlsContainer.insertBefore(infoElement, controlsContainer.firstChild);
  }

  private createControl(control: any): HTMLElement {
    const container = document.createElement('div');
    container.className = 'control-group';

    const label = document.createElement('label');
    label.textContent = control.label + ': ';

    let input: HTMLInputElement;

    switch (control.type) {
      case 'slider':
        input = document.createElement('input');
        input.type = 'range';
        input.min = control.min?.toString() || '0';
        input.max = control.max?.toString() || '1';
        input.step = control.step?.toString() || '0.01';
        input.value = control.default?.toString() || '0';
        break;

      case 'color':
        input = document.createElement('input');
        input.type = 'color';
        input.value = control.default || '#ffffff';
        break;

      case 'checkbox':
        input = document.createElement('input');
        input.type = 'checkbox';
        input.checked = control.default || false;
        break;

      default:
        input = document.createElement('input');
        input.type = 'text';
        input.value = control.default?.toString() || '';
    }

    // Añadir event listener para actualizar configuración
    input.addEventListener('input', (e) => {
      const target = e.target as HTMLInputElement;
      let value: any = target.value;
      
      if (control.type === 'slider') {
        value = parseFloat(value);
      } else if (control.type === 'checkbox') {
        value = target.checked;
      }

      // Actualizar configuración usando el path del control
      const config = this.getNestedConfig(control.name, value);
      this.app.updatePresetConfig(config);
    });

    container.appendChild(label);
    container.appendChild(input);

    return container;
  }

  private getNestedConfig(path: string, value: any): any {
    const keys = path.split('.');
    const config: any = {};
    
    let current = config;
    for (let i = 0; i < keys.length - 1; i++) {
      current[keys[i]] = {};
      current = current[keys[i]];
    }
    current[keys[keys.length - 1]] = value;
    
    return config;
  }

  private clearControls(): void {
    const controlsContainer = this.container.querySelector('.preset-controls') as HTMLElement;
    controlsContainer.innerHTML = '';
  }
}