import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

type ClipInfo = {
  index: number;
  name?: string;
  length?: number;
  is_playing?: boolean;
  is_recording?: boolean;
  color_index?: number | null;
};

type TrackInfo = {
  index: number;
  name: string;
  is_midi: boolean;
  is_audio: boolean;
  volume: number;
  clips: { index: number; has_clip: boolean; clip?: ClipInfo | null }[];
};

class AbletonRemoteClient {
  async request<T = any>(command: object, port = 9888, host = "127.0.0.1"): Promise<T> {
    if ((window as any).electronAPI?.tcpRequest) {
      try {
        const result = await (window as any).electronAPI.tcpRequest(command, port, host);
        return result;
      } catch (error) {
        console.error("JungleGrid: TCP request failed:", error);
        return Promise.reject(error);
      }
    }

    // Fallback attempt using HTTP when running outside Electron
    try {
      const response = await fetch(`http://${host}:${port}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(command)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return (await response.json()) as T;
    } catch (error) {
      console.warn("JungleGrid: Connection failed. Using stub data:", error);
      
      // Return some stub data for testing
      if ((command as any).type === "get_tracks_info") {
        return Promise.resolve([
          {
            index: 0,
            name: "Track 1",
            is_midi: true,
            is_audio: false,
            volume: 0.8,
            clips: [
              { index: 0, has_clip: true, clip: { index: 0, name: "Clip 1", is_playing: true } },
              { index: 1, has_clip: true, clip: { index: 1, name: "Clip 2", is_playing: false } },
              { index: 2, has_clip: false }
            ]
          },
          {
            index: 1,
            name: "Track 2",
            is_midi: false,
            is_audio: true,
            volume: 0.6,
            clips: [
              { index: 0, has_clip: false },
              { index: 1, has_clip: true, clip: { index: 1, name: "Audio Clip", is_playing: false } }
            ]
          }
        ] as any);
      }
      
      return Promise.resolve([]);
    }
  }

  async getTracksInfo(): Promise<TrackInfo[]> {
    const response = await this.request<{ status?: string; result?: TrackInfo[] }>({ type: "get_tracks_info" });
    
    // Handle different response formats
    if (response && response.result && Array.isArray(response.result)) {
      return response.result;
    }
    if (Array.isArray(response)) {
      return response as TrackInfo[];
    }
    
    console.warn("JungleGrid: Unexpected response format:", response);
    return [];
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
    
    console.log("JungleGrid initialized");
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
          console.log("JungleGrid: Track data updated", tracks);
          this.tracks = Array.isArray(tracks) ? tracks : [];
          this.connectionStatus = 'connected';
          this.createGrid();
        } else if (this.connectionStatus !== 'connected') {
          this.connectionStatus = 'connected';
        }
        
      } catch (error) {
        console.error("JungleGrid: Failed to fetch track info:", error);
        this.connectionStatus = 'error';
      }
    }
  }

  createGrid() {
    // Clear existing grid
    this.gridGroup.clear();
    this.gridCells = [];

    if (this.tracks.length === 0) {
      console.log("JungleGrid: No tracks data, creating placeholder grid");
      this.createPlaceholderGrid();
      return;
    }

    const columns = this.tracks.length;
    const maxRows = Math.max(1, ...this.tracks.map(t => t.clips?.length || 1));
    
    console.log(`JungleGrid: Creating grid ${columns}x${maxRows}`);

    // Calculate grid dimensions
    const { gridWidth, gridHeight, cellW, cellH } = this.calculateGridDimensions(columns, maxRows);
    
    const margin = Math.min(cellW, cellH) * 0.05;
    const cornerRadius = Math.min(cellW, cellH) * 0.1;

    // Create cells
    for (let c = 0; c < columns; c++) {
      const track = this.tracks[c];
      const numClips = track.clips?.length || 0;
      
      for (let r = 0; r < maxRows; r++) {
        const cell = this.createGridCell(cellW - margin, cellH - margin, cornerRadius);
        
        // Position the cell
        cell.mesh.position.set(
          c * cellW - gridWidth / 2 + cellW / 2,
          r * cellH - gridHeight / 2 + cellH / 2,
          0
        );

        this.gridGroup.add(cell.mesh);
        this.gridCells.push({
          ...cell,
          trackIndex: c,
          clipIndex: r
        });
      }
    }
  }

  createPlaceholderGrid() {
    // Create a simple 4x4 grid as placeholder
    const { gridWidth, gridHeight, cellW, cellH } = this.calculateGridDimensions(4, 4);
    const margin = Math.min(cellW, cellH) * 0.05;
    const cornerRadius = Math.min(cellW, cellH) * 0.1;

    for (let c = 0; c < 4; c++) {
      for (let r = 0; r < 4; r++) {
        const cell = this.createGridCell(cellW - margin, cellH - margin, cornerRadius);
        
        cell.mesh.position.set(
          c * cellW - gridWidth / 2 + cellW / 2,
          r * cellH - gridHeight / 2 + cellH / 2,
          0
        );

        this.gridGroup.add(cell.mesh);
        this.gridCells.push({
          ...cell,
          trackIndex: c,
          clipIndex: r
        });
      }
    }
  }

  calculateGridDimensions(columns: number, rows: number) {
    // Calculate visible area at camera position
    let visibleHeight = 8; // Default fallback
    let visibleWidth = 8;
    
    if (this.camera instanceof THREE.PerspectiveCamera) {
      const fovRad = THREE.MathUtils.degToRad(this.camera.fov);
      visibleHeight = 2 * Math.tan(fovRad / 2) * this.camera.position.z;
      visibleWidth = visibleHeight * this.camera.aspect;
    }

    // Scale grid to fill most of the visible area
    const gridFillFactor = 0.8;
    const gridWidth = visibleWidth * gridFillFactor;
    const gridHeight = visibleHeight * gridFillFactor;

    const cellW = gridWidth / columns;
    const cellH = gridHeight / rows;

    return { gridWidth, gridHeight, cellW, cellH };
  }

  createGridCell(width: number, height: number, radius: number): { mesh: THREE.Line; material: THREE.LineBasicMaterial } {
    // Create rounded rectangle shape
    const shape = new THREE.Shape();
    const x = -width / 2, y = -height / 2;
    
    shape.moveTo(x, y + radius);
    shape.lineTo(x, y + height - radius);
    shape.quadraticCurveTo(x, y + height, x + radius, y + height);
    shape.lineTo(x + width - radius, y + height);
    shape.quadraticCurveTo(x + width, y + height, x + width, y + height - radius);
    shape.lineTo(x + width, y + radius);
    shape.quadraticCurveTo(x + width, y, x + width - radius, y);
    shape.lineTo(x + radius, y);
    shape.quadraticCurveTo(x, y, x, y + radius);

    const points = shape.getPoints();
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    
    // Create individual material for each cell
    const material = new THREE.LineBasicMaterial({ 
      color: new THREE.Color(this.config.defaultConfig.grid.stroke),
      transparent: true,
      opacity: 1
    });
    
    const mesh = new THREE.Line(geometry, material);

    return { mesh, material };
  }

  updateGrid() {
    if (this.gridCells.length === 0) return;

    // Calculate blink alpha
    const t = this.blinkPhase / this.config.defaultConfig.blink.periodMs;
    const tri = t < 0.5 ? t * 2 : (1 - t) * 2;
    const blinkAlpha = this.config.defaultConfig.blink.minAlpha + 
                       tri * (this.config.defaultConfig.blink.maxAlpha - this.config.defaultConfig.blink.minAlpha);

    // Update each cell
    for (const cell of this.gridCells) {
      const track = this.tracks[cell.trackIndex];
      const clipSlot = track?.clips?.[cell.clipIndex];

      if (clipSlot?.has_clip && clipSlot.clip) {
        if (clipSlot.clip.is_playing) {
          // Playing clip - use active color with blink
          cell.material.color.setHex(parseInt(this.config.defaultConfig.colors.clipActive.replace('#', '0x')));
          cell.material.opacity = blinkAlpha;
        } else {
          // Idle clip - use idle color
          cell.material.color.setHex(parseInt(this.config.defaultConfig.colors.clipIdle.replace('#', '0x')));
          cell.material.opacity = 0.8;
        }
      } else {
        // Empty slot - use base color
        cell.material.color.setHex(parseInt(this.config.defaultConfig.grid.stroke.replace('#', '0x')));
        cell.material.opacity = 0.4;
      }
    }
  }

  dispose() {
    console.log("JungleGrid disposing...");
    
    // Dispose of all materials and geometries
    for (const cell of this.gridCells) {
      if (cell.mesh.geometry) {
        cell.mesh.geometry.dispose();
      }
      if (cell.material) {
        cell.material.dispose();
      }
    }
    
    this.gridCells = [];
    this.scene.remove(this.gridGroup);
    
    console.log("JungleGrid disposed");
  }
}

export function createPreset(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, config: PresetConfig): BasePreset {
  return new JungleGridPreset(scene, camera, renderer, config);
}