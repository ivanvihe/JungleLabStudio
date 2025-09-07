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

// Cliente WebSocket mejorado para comunicación con Ableton
class AbletonRemoteClient {
  private ws: WebSocket | null = null;
  private connectionPromise: Promise<void> | null = null;
  private reconnectTimeout: number | null = null;
  private isConnecting = false;
  private connectionAttempts = 0;
  private maxReconnectAttempts = 10;
  private hasAnnouncedConnection = false;

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
    this.connectionAttempts++;
    
    this.connectionPromise = new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket('ws://127.0.0.1:9888');
        
        this.ws.onopen = () => {
          if (!this.hasAnnouncedConnection) {
            console.log('Ableton remote connected');
            this.hasAnnouncedConnection = true;
          }
          this.isConnecting = false;
          this.connectionAttempts = 0;

          if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
          }
          resolve();
        };

        this.ws.onerror = (error) => {
          console.error('JungleGrid: WebSocket error:', error);
          this.isConnecting = false;
          reject(error);
        };

        this.ws.onclose = (event) => {
          this.hasAnnouncedConnection = false;
          this.ws = null;
          this.connectionPromise = null;
          this.isConnecting = false;

          if (this.connectionAttempts < this.maxReconnectAttempts && !this.reconnectTimeout) {
            const delay = Math.min(5000 + (this.connectionAttempts * 2000), 30000);
            this.reconnectTimeout = window.setTimeout(() => {
              this.reconnectTimeout = null;
              this.connect();
            }, delay);
          } else if (this.connectionAttempts >= this.maxReconnectAttempts) {
            console.error('JungleGrid: Maximum reconnection attempts reached');
          }
        };

        this.ws.onmessage = () => {};

        // Timeout de conexión más largo
        setTimeout(() => {
          if (this.isConnecting) {
            console.error('JungleGrid: ⏱️ Timeout de conexión (15s)');
            this.isConnecting = false;
            if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
              this.ws.close();
            }
            reject(new Error('Connection timeout'));
          }
        }, 15000);

      } catch (error) {
        console.error('JungleGrid: Error creando WebSocket:', error);
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
        return [];
      }

      return new Promise((resolve) => {
        const timeout = setTimeout(() => {
          this.ws?.removeEventListener('message', onMessage);
          resolve([]);
        }, 10000);

        const onMessage = (event: MessageEvent) => {
          try {
            const data = JSON.parse(event.data);
            
            // Manejar diferentes tipos de respuesta del remote script
            if (data.status === 'ok' && 
                (data.type === 'tracks_info' || 
                 data.tracks || 
                 data.result)) {
              
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
              }
              

              
              resolve(tracks);
            } else if (data.status === 'error') {
              console.error('JungleGrid: ❌ Error del servidor:', data.message);
              clearTimeout(timeout);
              this.ws?.removeEventListener('message', onMessage);
              resolve([]);
            }
          } catch (error) {
            console.error('JungleGrid: Error parsing respuesta:', error);
            console.error('JungleGrid: Raw data:', event.data);
            clearTimeout(timeout);
            this.ws?.removeEventListener('message', onMessage);
            resolve([]);
          }
        };

        this.ws.addEventListener('message', onMessage);
        
        // Enviar múltiples formatos de solicitud
        const requests = [
          { type: 'get_tracks_info' },
          { action: 'get_tracks' },
          { command: 'tracks_info' },
          { type: 'session_info' }
        ];
        
        requests.forEach((request, index) => {
          setTimeout(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
              this.ws.send(JSON.stringify(request));
            }
          }, index * 200); // Más tiempo entre solicitudes
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

  getConnectionStatus(): string {
    if (!this.ws) return 'disconnected';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'connecting';
      case WebSocket.OPEN: return 'connected';
      case WebSocket.CLOSING: return 'closing';
      case WebSocket.CLOSED: return 'closed';
      default: return 'unknown';
    }
  }

  resetConnection(): void {
    this.connectionAttempts = 0;
    this.disconnect();
    setTimeout(() => this.connect(), 1000);
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
    this.isConnecting = false;
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
  private statusUpdateInterval: number | null = null;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, config: PresetConfig) {
    super(scene, camera, renderer, config);

    this.client = new AbletonRemoteClient();
    this.gridGroup = new THREE.Group();
    this.scene.add(this.gridGroup);
  }

  init() {
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
    
    // Status update interval
    this.statusUpdateInterval = window.setInterval(() => {
      this.updateConnectionStatus();
    }, 2000);
    
  }

  private createDebugText(): void {
    try {
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      if (!context) return;

      canvas.width = 1024;
      canvas.height = 256;
      
      context.fillStyle = 'rgba(0, 0, 0, 0.9)';
      context.fillRect(0, 0, canvas.width, canvas.height);
      
      context.fillStyle = '#ffffff';
      context.font = 'bold 32px Arial';
      context.textAlign = 'center';
      context.fillText('Jungle Grid', canvas.width / 2, 60);
      
      context.font = '24px Arial';
      context.fillStyle = '#ffaa00';
      context.fillText('Conectando a Ableton...', canvas.width / 2, 120);
      
      context.font = '18px Arial';
      context.fillStyle = '#888888';
      context.fillText('Puerto: 9888 | WebSocket', canvas.width / 2, 160);
      context.fillText('Verifica que JungleLaStudioRemote esté activo', canvas.width / 2, 190);

      const texture = new THREE.CanvasTexture(canvas);
      const material = new THREE.MeshBasicMaterial({ 
        map: texture, 
        transparent: true,
        opacity: 0.9
      });
      const geometry = new THREE.PlaneGeometry(8, 2);
      
      this.debugText = new THREE.Mesh(geometry, material);
      this.debugText.position.set(0, 4, 0);
      this.scene.add(this.debugText);
    } catch (error) {
      console.error('JungleGrid: Error creando debug text:', error);
    }
  }

  private updateDebugText(title: string, subtitle: string, details?: string): void {
    if (!this.debugText) return;
    
    try {
      const material = this.debugText.material as THREE.MeshBasicMaterial;
      const texture = material.map as THREE.CanvasTexture;
      const canvas = texture.image as HTMLCanvasElement;
      const context = canvas.getContext('2d');
      if (!context) return;

      // Clear canvas
      context.fillStyle = 'rgba(0, 0, 0, 0.9)';
      context.fillRect(0, 0, canvas.width, canvas.height);
      
      // Title
      context.fillStyle = '#ffffff';
      context.font = 'bold 32px Arial';
      context.textAlign = 'center';
      context.fillText('Jungle Grid', canvas.width / 2, 60);
      
      // Status
      const connected = this.client.isConnected();
      context.fillStyle = connected ? '#00ff00' : '#ffaa00';
      context.font = '24px Arial';
      context.fillText(title, canvas.width / 2, 120);
      
      // Details
      context.fillStyle = '#888888';
      context.font = '18px Arial';
      context.fillText(subtitle, canvas.width / 2, 160);
      
      if (details) {
        context.fillText(details, canvas.width / 2, 190);
      }
      
      // Connection status indicator
      const statusText = `Estado: ${this.client.getConnectionStatus()}`;
      context.font = '16px Arial';
      context.fillStyle = connected ? '#00ff00' : '#ff4444';
      context.fillText(statusText, canvas.width / 2, 220);
      
      texture.needsUpdate = true;
    } catch (error) {
      console.error('JungleGrid: Error actualizando debug text:', error);
    }
  }

  private updateConnectionStatus(): void {
    const connected = this.client.isConnected();
    const newStatus = connected ? 'connected' : 'disconnected';
    
    if (newStatus !== this.connectionStatus) {
      this.connectionStatus = newStatus;
      
      if (connected) {
        this.updateDebugText(
          `Conectado (${this.tracks.length} tracks)`,
          'Recibiendo datos de Ableton Live',
          'WebSocket activo en puerto 9888'
        );
      } else {
        this.updateDebugText(
          'Desconectado',
          'Intentando reconectar...',
          'Verifica JungleLaStudioRemote en Ableton'
        );
      }
    }
  }

  async update() {
    const timeMs = performance.now();
    this.blinkPhase = (this.blinkPhase + this.clock.getDelta() * 1000) % this.config.defaultConfig.blink.periodMs;
    
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
          this.tracks = Array.isArray(tracks) ? tracks : [];
          this.createGrid();
          
          this.updateDebugText(
            `${this.tracks.length} tracks detectados`,
            this.tracks.length > 0 ? 'Grid sincronizado con Ableton' : 'Esperando tracks en Ableton',
            `Última actualización: ${new Date().toLocaleTimeString()}`
          );
        }
      } catch (error) {
        console.error('JungleGrid: Error fetching data:', error);
        this.updateDebugText(
          'Error de conexión',
          'No se pudieron obtener los tracks',
          'Revisa la conexión con Ableton'
        );
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
            
            cell.material.color.setHex(parseInt(this.config.defaultConfig.colors.clipActive.replace('#', ''), 16));
            cell.material.opacity = blinkAlpha;
          } else {
            // Clip idle
            cell.material.color.setHex(parseInt(this.config.defaultConfig.colors.clipIdle.replace('#', ''), 16));
            cell.material.opacity = 0.8;
          }
        } else {
          // No clip
          cell.material.color.setHex(0x333333);
          cell.material.opacity = 0.3;
        }
      } else {
        // Grid vacío
        cell.material.color.setHex(0x222222);
        cell.material.opacity = 0.2;
      }
    });
  }

  updateConfig(newConfig: any): void {
    // Actualizar configuración si es necesario
    if (newConfig.refreshMs !== undefined) {
    }
  }

  dispose(): void {
    
    if (this.statusUpdateInterval) {
      clearInterval(this.statusUpdateInterval);
      this.statusUpdateInterval = null;
    }
    
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