import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

// Interfaz para la información de tracks
interface TrackInfo {
  name: string;
  index: number;
  clips: Array<{
    name: string;
    index: number;
    isPlaying: boolean;
    color?: string;
  }>;
  color?: string;
}

// Cliente WebSocket para comunicación con Ableton
class AbletonRemoteClient {
  private ws: WebSocket | null = null;
  private connectionPromise: Promise<void> | null = null;
  private reconnectTimeout: number | null = null;
  private isConnecting = false;

  constructor() {
    this.connect();
  }

  private async connect(): Promise<void> {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return this.connectionPromise || Promise.resolve();
    }

    if (this.connectionPromise) {
      return this.connectionPromise;
    }

    this.isConnecting = true;
    this.connectionPromise = new Promise((resolve, reject) => {
      try {
        console.log('JungleGrid: Intentando conectar a Ableton Remote en ws://127.0.0.1:9888');
        this.ws = new WebSocket('ws://127.0.0.1:9888');
        
        this.ws.onopen = () => {
          console.log('JungleGrid: ✅ Conectado a Ableton Remote');
          this.isConnecting = false;
          if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
          }
          resolve();
        };

        this.ws.onerror = (error) => {
          console.error('JungleGrid: ❌ Error de conexión WebSocket:', error);
          this.isConnecting = false;
          reject(error);
        };

        this.ws.onclose = (event) => {
          console.log(`JungleGrid: 🔌 Desconectado de Ableton Remote (código: ${event.code})`);
          this.ws = null;
          this.connectionPromise = null;
          this.isConnecting = false;
          
          // Reintentar conexión en 5 segundos
          if (!this.reconnectTimeout) {
            this.reconnectTimeout = window.setTimeout(() => {
              this.reconnectTimeout = null;
              console.log('JungleGrid: 🔄 Reintentando conexión...');
              this.connect();
            }, 5000);
          }
        };

        // Timeout de conexión
        setTimeout(() => {
          if (this.isConnecting) {
            console.error('JungleGrid: ⏱️ Timeout de conexión');
            this.isConnecting = false;
            if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
              this.ws.close();
            }
            reject(new Error('Connection timeout'));
          }
        }, 10000);

      } catch (error) {
        console.error('JungleGrid: Error al crear WebSocket:', error);
        this.isConnecting = false;
        reject(error);
      }
    });

    return this.connectionPromise;
  }

  async getTracksInfo(): Promise<TrackInfo[]> {
    try {
      await this.connect();
      
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        console.warn('JungleGrid: WebSocket no está conectado');
        return [];
      }

      return new Promise((resolve) => {
        const timeout = setTimeout(() => {
          console.warn('JungleGrid: ⏱️ Timeout al obtener tracks info');
          this.ws?.removeEventListener('message', onMessage);
          resolve([]);
        }, 5000);

        const onMessage = (event: MessageEvent) => {
          try {
            const data = JSON.parse(event.data);
            console.log('JungleGrid: 📨 Mensaje recibido:', data);
            
            // Manejar diferentes tipos de respuesta del remote script
            if (data.type === 'tracks_info' || 
                data.type === 'get_tracks_info' || 
                data.action === 'tracks_data') {
              
              clearTimeout(timeout);
              this.ws?.removeEventListener('message', onMessage);
              
              // Extraer tracks de diferentes formatos de respuesta
              let tracks: TrackInfo[] = [];
              
              if (data.tracks && Array.isArray(data.tracks)) {
                tracks = data.tracks;
              } else if (data.result && Array.isArray(data.result)) {
                tracks = data.result;
              } else if (Array.isArray(data)) {
                tracks = data;
              } else if (data.data && Array.isArray(data.data)) {
                tracks = data.data;
              }
              
              console.log('JungleGrid: 🎵 Tracks obtenidos:', tracks.length);
              resolve(tracks);
            }
          } catch (error) {
            console.error('JungleGrid: Error parsing message:', error);
            clearTimeout(timeout);
            this.ws?.removeEventListener('message', onMessage);
            resolve([]);
          }
        };

        this.ws.addEventListener('message', onMessage);
        
        // Enviar solicitud usando diferentes formatos que el remote script puede entender
        const requests = [
          { type: 'get_tracks_info' },
          { action: 'get_tracks' },
          { command: 'tracks_info' },
          { type: 'session_info' }
        ];
        
        // Probar diferentes formatos de solicitud
        requests.forEach((request, index) => {
          setTimeout(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
              console.log(`JungleGrid: 📤 Enviando solicitud ${index + 1}:`, request);
              this.ws.send(JSON.stringify(request));
            }
          }, index * 100); // Espaciar las solicitudes
        });
      });

    } catch (error) {
      console.error('JungleGrid: Error obteniendo tracks info:', error);
      return [];
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connectionPromise = null;
  }
}

interface GridCell {
  mesh: THREE.Line;
  material: THREE.LineBasicMaterial;
  trackIndex: number;
  clipIndex: number;
}

class JungleGridPreset extends BasePreset {
  private client: AbletonRemoteClient;
  private tracks: TrackInfo[] = [];
  private lastFetch = 0;
  private gridGroup: THREE.Group;
  private gridCells: GridCell[] = [];
  private blinkPhase = 0;
  private connectionStatus = 'connecting';
  private debugText: THREE.Mesh | null = null;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, config: PresetConfig) {
    super(scene, camera, renderer, config);

    this.client = new AbletonRemoteClient();
    this.gridGroup = new THREE.Group();
    this.scene.add(this.gridGroup);
  }

  init() {
    console.log('JungleGrid: Inicializando preset');
    
    // Set camera position to view the grid
    if (this.camera instanceof THREE.PerspectiveCamera) {
      this.camera.position.set(0, 0, 10);
      this.camera.lookAt(0, 0, 0);
      this.camera.updateProjectionMatrix();
    }
    
    // Start with empty grid
    this.createGrid();
    
    // Crear texto de debug
    this.createDebugText();
    
    console.log('JungleGrid: ✅ Preset inicializado');
  }

  private createDebugText(): void {
    try {
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      if (!context) return;

      canvas.width = 512;
      canvas.height = 128;
      
      context.fillStyle = 'rgba(0, 0, 0, 0.8)';
      context.fillRect(0, 0, canvas.width, canvas.height);
      
      context.fillStyle = '#ffffff';
      context.font = '24px Arial';
      context.textAlign = 'center';
      context.fillText('Jungle Grid - Conectando...', canvas.width / 2, canvas.height / 2);

      const texture = new THREE.CanvasTexture(canvas);
      const material = new THREE.MeshBasicMaterial({ 
        map: texture, 
        transparent: true,
        opacity: 0.8
      });
      const geometry = new THREE.PlaneGeometry(4, 1);
      
      this.debugText = new THREE.Mesh(geometry, material);
      this.debugText.position.set(0, 4, 0);
      this.scene.add(this.debugText);
    } catch (error) {
      console.error('JungleGrid: Error creando debug text:', error);
    }
  }

  private updateDebugText(message: string): void {
    if (!this.debugText) return;
    
    try {
      const material = this.debugText.material as THREE.MeshBasicMaterial;
      const texture = material.map as THREE.CanvasTexture;
      const canvas = texture.image as HTMLCanvasElement;
      const context = canvas.getContext('2d');
      if (!context) return;

      context.fillStyle = 'rgba(0, 0, 0, 0.8)';
      context.fillRect(0, 0, canvas.width, canvas.height);
      
      context.fillStyle = '#ffffff';
      context.font = '20px Arial';
      context.textAlign = 'center';
      context.fillText(message, canvas.width / 2, canvas.height / 2);
      
      texture.needsUpdate = true;
    } catch (error) {
      console.error('JungleGrid: Error actualizando debug text:', error);
    }
  }

  async update() {
    const timeMs = performance.now();
    this.blinkPhase = (this.blinkPhase + this.clock.getDelta() * 1000) % this.config.defaultConfig.blink.periodMs;
    
    // Actualizar estado de conexión
    const connected = this.client.isConnected();
    if (connected && this.connectionStatus !== 'connected') {
      this.connectionStatus = 'connected';
      this.updateDebugText(`Jungle Grid - Conectado (${this.tracks.length} tracks)`);
    } else if (!connected && this.connectionStatus !== 'disconnected') {
      this.connectionStatus = 'disconnected';
      this.updateDebugText('Jungle Grid - Desconectado');
    }
    
    await this.fetchDataIfNeeded(timeMs);
    this.updateGrid();

    // Subtle camera oscillation
    const oscillationSpeed = 0.00005;
    const oscillationAmount = 0.3;
    this.camera.position.x = Math.sin(timeMs * oscillationSpeed) * oscillationAmount;
  }

  async fetchDataIfNeeded(timeMs: number) {
    if (timeMs - this.lastFetch >= this.config.defaultConfig.refreshMs) {
      this.lastFetch = timeMs;
      
      try {
        const tracks = await this.client.getTracksInfo();
        const tracksStr = JSON.stringify(tracks);
        const currentStr = JSON.stringify(this.tracks);
        
        if (tracksStr !== currentStr) {
          console.log('JungleGrid: 🔄 Track data actualizada', tracks);
          this.tracks = Array.isArray(tracks) ? tracks : [];
          this.createGrid();
          this.updateDebugText(`Jungle Grid - ${this.tracks.length} tracks detectados`);
        }
      } catch (error) {
        console.error('JungleGrid: Error fetching data:', error);
        this.updateDebugText('Jungle Grid - Error de conexión');
      }
    }
  }

  private createGrid(): void {
    // Limpiar grid existente
    this.gridCells.forEach(cell => {
      this.gridGroup.remove(cell.mesh);
      cell.mesh.geometry.dispose();
      cell.material.dispose();
    });
    this.gridCells = [];

    if (this.tracks.length === 0) {
      console.log('JungleGrid: No hay tracks, creando grid vacío');
      this.createEmptyGrid();
      return;
    }

    const maxTracks = Math.min(this.tracks.length, 8);
    const maxClips = 8;
    const cellWidth = 0.8;
    const cellHeight = 0.8;
    const spacing = 0.1;

    for (let trackIndex = 0; trackIndex < maxTracks; trackIndex++) {
      const track = this.tracks[trackIndex];
      
      for (let clipIndex = 0; clipIndex < maxClips; clipIndex++) {
        const x = (trackIndex - maxTracks / 2) * (cellWidth + spacing);
        const y = (clipIndex - maxClips / 2) * (cellHeight + spacing);

        // Crear cell border
        const geometry = new THREE.EdgesGeometry(new THREE.PlaneGeometry(cellWidth, cellHeight));
        const material = new THREE.LineBasicMaterial({
          color: this.config.defaultConfig.grid.stroke,
          linewidth: this.config.defaultConfig.grid.strokeWidth,
          transparent: true,
          opacity: 0.6
        });

        const mesh = new THREE.LineSegments(geometry, material);
        mesh.position.set(x, y, 0);
        this.gridGroup.add(mesh);

        this.gridCells.push({
          mesh: mesh as THREE.Line,
          material,
          trackIndex,
          clipIndex
        });
      }
    }

    console.log(`JungleGrid: ✅ Grid creado con ${this.gridCells.length} celdas`);
  }

  private createEmptyGrid(): void {
    const gridSize = 8;
    const cellWidth = 0.8;
    const cellHeight = 0.8;
    const spacing = 0.1;

    for (let x = 0; x < gridSize; x++) {
      for (let y = 0; y < gridSize; y++) {
        const posX = (x - gridSize / 2) * (cellWidth + spacing);
        const posY = (y - gridSize / 2) * (cellHeight + spacing);

        const geometry = new THREE.EdgesGeometry(new THREE.PlaneGeometry(cellWidth, cellHeight));
        const material = new THREE.LineBasicMaterial({
          color: '#333333',
          linewidth: 1,
          transparent: true,
          opacity: 0.3
        });

        const mesh = new THREE.LineSegments(geometry, material);
        mesh.position.set(posX, posY, 0);
        this.gridGroup.add(mesh);

        this.gridCells.push({
          mesh: mesh as THREE.Line,
          material,
          trackIndex: -1,
          clipIndex: -1
        });
      }
    }
  }

  private updateGrid(): void {
    this.gridCells.forEach(cell => {
      if (cell.trackIndex >= 0 && cell.trackIndex < this.tracks.length) {
        const track = this.tracks[cell.trackIndex];
        const clip = track.clips && track.clips[cell.clipIndex];
        
        if (clip) {
          if (clip.isPlaying) {
            // Clip activo - animar con blink
            const blinkAlpha = this.config.defaultConfig.blink.minAlpha + 
              (this.config.defaultConfig.blink.maxAlpha - this.config.defaultConfig.blink.minAlpha) * 
              (0.5 + 0.5 * Math.sin(this.blinkPhase * 2 * Math.PI / this.config.defaultConfig.blink.periodMs));
            
            cell.material.color.setHex(0x40a9ff);
            cell.material.opacity = blinkAlpha;
          } else {
            // Clip idle
            cell.material.color.setHex(0x0a3d66);
            cell.material.opacity = 0.8;
          }
        } else {
          // No clip
          cell.material.color.setHex(0x333333);
          cell.material.opacity = 0.3;
        }
      }
    });
  }

  updateConfig(newConfig: any): void {
    // Actualizar configuración si es necesario
  }

  dispose(): void {
    console.log('JungleGrid: Disposing preset');
    
    if (this.debugText) {
      this.scene.remove(this.debugText);
      this.debugText.geometry.dispose();
      (this.debugText.material as THREE.Material).dispose();
    }
    
    this.gridCells.forEach(cell => {
      this.gridGroup.remove(cell.mesh);
      cell.mesh.geometry.dispose();
      cell.material.dispose();
    });
    
    this.scene.remove(this.gridGroup);
    this.client.disconnect();
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  cfg: PresetConfig,
  shaderCode?: string
): BasePreset {
  return new JungleGridPreset(scene, camera, renderer, cfg);
}