import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'Instanced Demo',
  description: 'Simple instanced cubes showcasing InstancedMesh',
  author: 'AI',
  version: '1.0.0',
  category: 'demo',
  tags: ['instanced', 'performance'],
  thumbnail: 'instanced_demo_thumb.png',
  note: 0,
  defaultConfig: {},
  controls: [],
  audioMapping: {},
  performance: { complexity: 'low', recommendedFPS: 60, gpuIntensive: false }
};

export class InstancedDemo extends BasePreset {
  private mesh!: THREE.InstancedMesh;
  private dummy = new THREE.Object3D();

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, cfg: PresetConfig, videoElement: HTMLVideoElement) {
    super(scene, camera, renderer, cfg, videoElement);
  }

  init(): void {
    const geometry = new THREE.BoxGeometry(0.4, 0.4, 0.4);
    const material = new THREE.MeshStandardMaterial({ color: 0x44aa88 });
    const count = 150;

    this.mesh = new THREE.InstancedMesh(geometry, material, count);
    this.mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);

    for (let i = 0; i < count; i++) {
      this.dummy.position.set((Math.random() - 0.5) * 6, (Math.random() - 0.5) * 6, (Math.random() - 0.5) * 6);
      this.dummy.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI);
      this.dummy.scale.setScalar(0.5 + Math.random());
      this.dummy.updateMatrix();
      this.mesh.setMatrixAt(i, this.dummy.matrix);
    }

    this.mesh.instanceMatrix.needsUpdate = true;
    this.scene.add(this.mesh);
  }

  update(): void {
    if (!this.mesh) return;
    const delta = this.clock.getDelta();
    const rotationSpeed = 0.5 + this.audioData.high * 0.5;
    this.mesh.rotation.y += delta * rotationSpeed;
    this.mesh.rotation.x += delta * 0.2;
  }

  dispose(): void {
    if (!this.mesh) return;
    this.scene.remove(this.mesh);
    this.mesh.geometry.dispose();
    (this.mesh.material as THREE.Material).dispose();
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  cfg: PresetConfig,
  videoElement: HTMLVideoElement
): BasePreset {
  return new InstancedDemo(scene, camera, renderer, cfg, videoElement);
}
