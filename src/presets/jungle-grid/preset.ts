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
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private client: AbletonRemoteClient;
  private tracks: TrackInfo[] = [];
  private lastFetch = 0;
  private blinkPhase = 0;
  private plane: THREE.Mesh;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, config: PresetConfig) {
    super(scene, camera, renderer, config);

    this.canvas = document.createElement('canvas');
    this.canvas.width = this.config.defaultConfig.width || 1920;
    this.canvas.height = this.config.defaultConfig.height || 1080;
    this.ctx = this.canvas.getContext('2d')!;
    this.client = new AbletonRemoteClient();

    const texture = new THREE.CanvasTexture(this.canvas);
    const material = new THREE.MeshBasicMaterial({ map: texture, transparent: true });
    const geometry = new THREE.PlaneGeometry(16, 9);
    this.plane = new THREE.Mesh(geometry, material);
    this.scene.add(this.plane);
  }

  init() {
    // No specific init logic needed here as constructor handles setup
  }

  async update() {
    const timeMs = performance.now();
    const dt = this.clock.getDelta() * 1000;
    this.blinkPhase = (this.blinkPhase + dt) % this.config.defaultConfig.blink.periodMs;

    await this.fetchDataIfNeeded(timeMs);
    this.renderGrid();
    (this.plane.material as THREE.MeshBasicMaterial).map.needsUpdate = true;
  }

  async fetchDataIfNeeded(timeMs: number) {
    if (timeMs - this.lastFetch >= this.config.defaultConfig.refreshMs) {
      this.lastFetch = timeMs;
      try {
        const tracks = await this.client.getTracksInfo();
        this.tracks = Array.isArray(tracks) ? tracks : [];
      } catch (error) {
        console.error("JungleGrid: Failed to fetch track info:", error);
      }
    }
  }

  renderGrid() {
    const { width, height } = this.canvas;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, width, height);

    const gridWidth = width * 0.15;
    const gridHeight = height * 0.15;
    const gridX = (width - gridWidth) / 2;
    const gridY = (height - gridHeight) / 2;

    const columns = Math.max(1, this.tracks.length);
    const rows = Math.max(1, ...this.tracks.map(t => t.clips?.length || 1));

    const cellW = gridWidth / columns;
    const cellH = gridHeight / rows;
    const margin = 2;
    const cornerRadius = 5;

    for (let c = 0; c < columns; c++) {
      for (let r = 0; r < rows; r++) {
        this.strokeRoundedRect(gridX + c * cellW + margin, gridY + r * cellH + margin, cellW - 2 * margin, cellH - 2 * margin, cornerRadius, this.config.defaultConfig.grid.stroke, this.config.defaultConfig.grid.strokeWidth, 1);
      }
    }

    const idleColor = this.config.defaultConfig.colors.clipIdle;
    const activeColor = this.config.defaultConfig.colors.clipActive;

    const t = this.blinkPhase / this.config.defaultConfig.blink.periodMs;
    const tri = t < 0.5 ? t * 2 : (1 - t) * 2;
    const blinkAlpha = this.config.defaultConfig.blink.minAlpha + tri * (this.config.defaultConfig.blink.maxAlpha - this.config.defaultConfig.blink.minAlpha);

    for (let c = 0; c < columns; c++) {
      const track = this.tracks[c];
      const clipSlots = track?.clips || [];
      for (let r = 0; r < rows; r++) {
        const slot = clipSlots[r];
        if (!slot || !slot.has_clip) continue;

        const clip = slot.clip;
        const x = gridX + c * cellW + margin;
        const y = gridY + r * cellH + margin;
        const w = cellW - 2 * margin;
        const h = cellH - 2 * margin;

        if (clip?.is_playing) {
          this.strokeRoundedRect(x, y, w, h, cornerRadius, activeColor, this.config.defaultConfig.grid.strokeWidth + 1, blinkAlpha);
        } else {
          this.strokeRoundedRect(x, y, w, h, cornerRadius, idleColor, this.config.defaultConfig.grid.strokeWidth + 1, 0.8);
        }
      }
    }
  }

  strokeRoundedRect(x: number, y: number, w: number, h: number, radius: number, color: string, lineWidth: number, alpha = 1) {
    this.ctx.save();
    this.ctx.globalAlpha = alpha;
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = lineWidth;
    this.ctx.beginPath();
    this.ctx.moveTo(x + radius, y);
    this.ctx.lineTo(x + w - radius, y);
    this.ctx.arcTo(x + w, y, x + w, y + radius, radius);
    this.ctx.lineTo(x + w, y + h - radius);
    this.ctx.arcTo(x + w, y + h, x + w - radius, y + h, radius);
    this.ctx.lineTo(x + radius, y + h);
    this.ctx.arcTo(x, y + h, x, y + h - radius, radius);
    this.ctx.lineTo(x, y + radius);
    this.ctx.arcTo(x, y, x + radius, y, radius);
    this.ctx.closePath();
    this.ctx.stroke();
    this.ctx.restore();
  }

  dispose() {
    this.scene.remove(this.plane);
    (this.plane.material as THREE.MeshBasicMaterial).map.dispose();
    this.plane.geometry.dispose();
  }
}

export function createPreset(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, config: PresetConfig): BasePreset {
  return new JungleGridPreset(scene, camera, renderer, config);
}