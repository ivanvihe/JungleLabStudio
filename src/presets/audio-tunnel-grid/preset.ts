import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'Audio Tunnel Grid',
  description: 'Infinite tunnel with grid pattern and audio-reactive circles',
  author: 'Jungle Lab Studio',
  version: '1.0.0',
  category: 'generative',
  tags: ['tunnel', 'grid', 'audio-reactive', 'psychedelic'],
  thumbnail: 'audio_tunnel_grid_thumb.png',
  note: 72,
  defaultConfig: {
    speed: 0.5,
    tunnelColor1: '#8000cc',
    tunnelColor2: '#00ccff',
    gridSegments: 8,
    rotationSpeed: 0.1,
    bassResponse: 0.3,
    circleCount: 6
  },
  controls: [
    { name: 'speed', type: 'slider', label: 'Tunnel Speed', min: 0.1, max: 3.0, step: 0.1, default: 0.5 },
    { name: 'tunnelColor1', type: 'color', label: 'Color 1 (Purple)', default: '#8000cc' },
    { name: 'tunnelColor2', type: 'color', label: 'Color 2 (Cyan)', default: '#00ccff' },
    { name: 'gridSegments', type: 'slider', label: 'Grid Segments', min: 4, max: 16, step: 1, default: 8 },
    { name: 'rotationSpeed', type: 'slider', label: 'Rotation Speed', min: 0, max: 1, step: 0.05, default: 0.1 },
    { name: 'bassResponse', type: 'slider', label: 'Bass Response', min: 0, max: 1, step: 0.1, default: 0.3 },
    { name: 'circleCount', type: 'slider', label: 'Circle Mirrors', min: 3, max: 12, step: 1, default: 6 }
  ],
  audioMapping: {
    bass: 'bassResponse'
  },
  performance: { complexity: 'medium', recommendedFPS: 60, gpuIntensive: false }
};

class AudioTunnelGridPreset extends BasePreset {
  private tunnelGroup: THREE.Group;
  private gridLines: THREE.Line[] = [];
  private circles: THREE.Mesh[] = [];
  private currentConfig: any;
  private globalTime: number = 0;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, cfg: PresetConfig) {
    super(scene, camera, renderer, cfg);
    this.currentConfig = { ...cfg.defaultConfig };
    this.tunnelGroup = new THREE.Group();
    this.scene.add(this.tunnelGroup);
  }

  init(): void {
    // Set camera position
    if (this.camera instanceof THREE.PerspectiveCamera) {
      this.camera.position.set(0, 0, 5);
      this.camera.lookAt(0, 0, 0);
    }

    this.createTunnelGrid();
    this.createCircles();
  }

  private createTunnelGrid(): void {
    // Create grid lines in polar pattern (tunnel effect)
    const radialSegments = this.currentConfig.gridSegments * 2;
    const depthSegments = 20;
    const radius = 3;

    // Radial lines (spokes)
    for (let i = 0; i < radialSegments; i++) {
      const angle = (i / radialSegments) * Math.PI * 2;
      const points: THREE.Vector3[] = [];

      for (let d = 0; d < depthSegments; d++) {
        const depth = -d * 2;
        const x = Math.cos(angle) * radius;
        const y = Math.sin(angle) * radius;
        points.push(new THREE.Vector3(x, y, depth));
      }

      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      const material = new THREE.LineBasicMaterial({
        color: new THREE.Color(this.currentConfig.tunnelColor1),
        transparent: true,
        opacity: 0.4
      });
      const line = new THREE.Line(geometry, material);
      this.tunnelGroup.add(line);
      this.gridLines.push(line);
    }

    // Depth rings (circular grid lines)
    for (let d = 0; d < depthSegments; d++) {
      const depth = -d * 2;
      const points: THREE.Vector3[] = [];

      for (let i = 0; i <= radialSegments; i++) {
        const angle = (i / radialSegments) * Math.PI * 2;
        const x = Math.cos(angle) * radius;
        const y = Math.sin(angle) * radius;
        points.push(new THREE.Vector3(x, y, depth));
      }

      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      const material = new THREE.LineBasicMaterial({
        color: new THREE.Color(this.currentConfig.tunnelColor2),
        transparent: true,
        opacity: 0.4
      });
      const line = new THREE.Line(geometry, material);
      this.tunnelGroup.add(line);
      this.gridLines.push(line);
    }
  }

  private createCircles(): void {
    // Create kaleidoscope-style circles
    const segments = this.currentConfig.circleCount;
    const circlesPerSegment = 3;

    for (let s = 0; s < segments; s++) {
      const angle = (s / segments) * Math.PI * 2;

      for (let c = 0; c < circlesPerSegment; c++) {
        const distance = 1.5 + c * 0.7;
        const x = Math.cos(angle) * distance;
        const y = Math.sin(angle) * distance;

        const geometry = new THREE.CircleGeometry(0.3, 32);
        const material = new THREE.MeshBasicMaterial({
          color: new THREE.Color(this.currentConfig.tunnelColor1),
          transparent: true,
          opacity: 0.6,
          side: THREE.DoubleSide
        });

        const circle = new THREE.Mesh(geometry, material);
        circle.position.set(x, y, 0);
        this.tunnelGroup.add(circle);
        this.circles.push(circle);
      }
    }
  }

  update(): void {
    const delta = this.clock.getDelta();
    this.globalTime += delta;

    // Get bass intensity
    const bassIntensity = this.audioData?.bass || 0;
    const pulse = 1.0 + bassIntensity * this.currentConfig.bassResponse;

    // Animate tunnel forward motion
    this.tunnelGroup.position.z = (this.globalTime * this.currentConfig.speed) % 2;

    // Rotate tunnel
    this.tunnelGroup.rotation.z = this.globalTime * this.currentConfig.rotationSpeed;

    // Update grid line colors with gradient effect
    const color1 = new THREE.Color(this.currentConfig.tunnelColor1);
    const color2 = new THREE.Color(this.currentConfig.tunnelColor2);

    this.gridLines.forEach((line, index) => {
      const material = line.material as THREE.LineBasicMaterial;
      const t = (Math.sin(this.globalTime + index * 0.1) + 1) / 2;
      material.color.lerpColors(color1, color2, t);
      material.opacity = 0.3 + bassIntensity * 0.3;
    });

    // Animate circles with audio reactivity
    this.circles.forEach((circle, index) => {
      const material = circle.material as THREE.MeshBasicMaterial;

      // Pulsate with bass
      const scale = pulse * (1 + Math.sin(this.globalTime * 2 + index) * 0.2);
      circle.scale.setScalar(scale);

      // Color oscillation
      const t = (Math.sin(this.globalTime * 3 + index * 0.5) + 1) / 2;
      material.color.lerpColors(color1, color2, t);

      // Opacity responds to audio
      material.opacity = 0.4 + bassIntensity * 0.4;

      // Subtle rotation
      circle.rotation.z = this.globalTime + index * 0.1;
    });
  }

  updateConfig(newConfig: any): void {
    const needsRebuild =
      newConfig.gridSegments !== undefined && newConfig.gridSegments !== this.currentConfig.gridSegments ||
      newConfig.circleCount !== undefined && newConfig.circleCount !== this.currentConfig.circleCount;

    this.currentConfig = { ...this.currentConfig, ...newConfig };

    if (needsRebuild) {
      this.dispose();
      this.tunnelGroup = new THREE.Group();
      this.scene.add(this.tunnelGroup);
      this.createTunnelGrid();
      this.createCircles();
    }
  }

  dispose(): void {
    this.gridLines.forEach(line => {
      this.tunnelGroup.remove(line);
      line.geometry.dispose();
      (line.material as THREE.Material).dispose();
    });
    this.gridLines = [];

    this.circles.forEach(circle => {
      this.tunnelGroup.remove(circle);
      circle.geometry.dispose();
      (circle.material as THREE.Material).dispose();
    });
    this.circles = [];

    this.scene.remove(this.tunnelGroup);
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  cfg: PresetConfig,
  shaderCode?: string
): BasePreset {
  return new AudioTunnelGridPreset(scene, camera, renderer, cfg);
}
