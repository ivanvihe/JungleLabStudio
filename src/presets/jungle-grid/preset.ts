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
    } else {
      console.warn("JungleGrid: electronAPI.tcpRequest not found. Using stub data.");
      return Promise.resolve<any>([]);
    }
  }

  getTracksInfo(): Promise<TrackInfo[]> {
    return this.request<TrackInfo[]>({ type: "get_tracks_info" });
  }
}

class JungleGridPreset extends BasePreset {
  private client: AbletonRemoteClient;
  private tracks: TrackInfo[] = [];
  private lastFetch = 0;
  private gridGroup: THREE.Group;
  private idleMaterial: THREE.LineBasicMaterial;
  private activeMaterial: THREE.LineBasicMaterial;
  private baseMaterial: THREE.LineBasicMaterial;
  private blinkPhase = 0;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, config: PresetConfig) {
    super(scene, camera, renderer, config);

    this.client = new AbletonRemoteClient();
    this.gridGroup = new THREE.Group();
    this.scene.add(this.gridGroup);

    this.idleMaterial = new THREE.LineBasicMaterial({ color: new THREE.Color(this.config.defaultConfig.colors.clipIdle) });
    this.activeMaterial = new THREE.LineBasicMaterial({ color: new THREE.Color(this.config.defaultConfig.colors.clipActive) });
    this.baseMaterial = new THREE.LineBasicMaterial({ color: new THREE.Color(this.config.defaultConfig.grid.stroke) });
  }

  init() {
    // Set camera position to view the grid filling the screen
    this.camera.position.z = 10; // Adjust as needed for desired fill
    this.camera.lookAt(0, 0, 0);
  }

  async update() {
    const timeMs = performance.now();
    this.blinkPhase = (this.blinkPhase + this.clock.getDelta() * 1000) % this.config.defaultConfig.blink.periodMs;
    await this.fetchDataIfNeeded(timeMs);
    this.updateGrid();

    // Camera oscillation
    const oscillationSpeed = 0.00005; // Adjust for desired speed
    const oscillationAmount = 0.5; // Adjust for desired movement range
    this.camera.position.x = Math.sin(timeMs * oscillationSpeed) * oscillationAmount;
  }

  async fetchDataIfNeeded(timeMs: number) {
    if (timeMs - this.lastFetch >= this.config.defaultConfig.refreshMs) {
      this.lastFetch = timeMs;
      try {
        const tracks = await this.client.getTracksInfo();
        if (JSON.stringify(tracks) !== JSON.stringify(this.tracks)) {
            this.tracks = Array.isArray(tracks) ? tracks : [];
            this.createGrid();
        }
      } catch (error) {
        console.error("JungleGrid: Failed to fetch track info:", error);
      }
    }
  }

  createGrid() {
    this.gridGroup.clear();

    const columns = Math.max(1, this.tracks.length);
    const rows = Math.max(1, ...this.tracks.map(t => t.clips?.length || 1));

    // Calculate visible width and height at camera's z position
    const aspect = this.camera.aspect;
    const fovRad = THREE.MathUtils.degToRad(this.camera.fov);
    const visibleHeight = 2 * Math.tan(fovRad / 2) * this.camera.position.z;
    const visibleWidth = visibleHeight * aspect;

    // Scale the grid to fill the visible area (e.g., 80% of visible area)
    const gridFillFactor = 0.8; 
    const gridWidth = visibleWidth * gridFillFactor;
    const gridHeight = visibleHeight * gridFillFactor;

    const cellW = gridWidth / columns;
    const cellH = gridHeight / rows;
    const margin = 0.05; // Relative margin
    const cornerRadius = 0.1; // Relative corner radius

    for (let c = 0; c < columns; c++) {
      for (let r = 0; r < rows; r++) {
        const shape = new THREE.Shape();
        const x = 0, y = 0, width = cellW - margin, height = cellH - margin, radius = cornerRadius;
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
        const cell = new THREE.Line(geometry, this.baseMaterial);

        cell.position.set(
          c * cellW - gridWidth / 2 + margin / 2,
          r * cellH - gridHeight / 2 + margin / 2,
          0
        );
        this.gridGroup.add(cell);
      }
    }
  }

  updateGrid() {
    const columns = Math.max(1, this.tracks.length);
    const rows = Math.max(1, ...this.tracks.map(t => t.clips?.length || 1));

    const t = this.blinkPhase / this.config.defaultConfig.blink.periodMs;
    const tri = t < 0.5 ? t * 2 : (1 - t) * 2;
    const blinkAlpha = this.config.defaultConfig.blink.minAlpha + tri * (this.config.defaultConfig.blink.maxAlpha - this.config.defaultConfig.blink.minAlpha);

    for (let c = 0; c < columns; c++) {
      const track = this.tracks[c];
      const clipSlots = track?.clips || [];
      for (let r = 0; r < rows; r++) {
        const slot = clipSlots[r];
        const cellIndex = c * rows + r;
        const cell = this.gridGroup.children[cellIndex] as THREE.Line;

        if (cell) {
            (cell.material as THREE.LineBasicMaterial).transparent = true;
            if (slot?.has_clip) {
                if (slot.clip?.is_playing) {
                    cell.material = this.activeMaterial;
                    (cell.material as THREE.LineBasicMaterial).opacity = blinkAlpha;
                } else {
                    cell.material = this.idleMaterial;
                    (cell.material as THREE.LineBasicMaterial).opacity = 0.8;
                }
            } else {
                cell.material = this.baseMaterial;
                (cell.material as THREE.LineBasicMaterial).opacity = 1;
            }
        }
      }
    }
  }

  dispose() {
    this.scene.remove(this.gridGroup);
  }
}

export function createPreset(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, config: PresetConfig): BasePreset {
  return new JungleGridPreset(scene, camera, renderer, config);
}
