import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';
import { applyVFX, createParticleSystem, updateParticles, triggerParticleBurst } from './vfx';
import configData from './config.json';

export const config: PresetConfig = configData as PresetConfig;

class OrganicAsciiGlitchPreset extends BasePreset {
  private videoTexture!: THREE.VideoTexture;
  private sceneObject!: THREE.Mesh;
  private burstActive: boolean = false;
  private burstTime: number = 0;
  private fontTexture!: THREE.Texture;

  constructor(
    scene: THREE.Scene,
    camera: THREE.Camera,
    renderer: THREE.WebGLRenderer,
    config: PresetConfig,
    videoElement: HTMLVideoElement,
    private shaderCode?: string
  ) {
    super(scene, camera, renderer, config, videoElement);
  }

  public init(): void {
    console.log('Initializing OrganicAsciiGlitchPreset');

    const textureLoader = new THREE.TextureLoader();
    this.fontTexture = textureLoader.load('./presets/OrganicAsciiGlitch/ascii-font.png');
    this.fontTexture.minFilter = THREE.NearestFilter;
    this.fontTexture.magFilter = THREE.NearestFilter;

    this.videoTexture = new THREE.VideoTexture(this.videoElement);
    this.videoTexture.colorSpace = THREE.SRGBColorSpace;

    const geometry = new THREE.PlaneGeometry(16, 9);
    geometry.scale(0.1, 0.1, 1);

    const material = new THREE.MeshBasicMaterial({
      map: this.videoTexture,
      transparent: true,
    });

    this.sceneObject = new THREE.Mesh(geometry, material);
    this.sceneObject.position.set(0, 0, -5);
    this.scene.add(this.sceneObject);

    createParticleSystem(this.scene);
  }

  public update(): void {
    const delta = this.clock.getDelta();
    updateParticles(delta, this.audioData, this.config.defaultConfig?.particles ?? {});

    if (this.videoTexture) {
      this.videoTexture.needsUpdate = true;
    }

    if (this.burstActive) {
      this.burstTime += delta;
      if (this.burstTime >= (this.config.defaultConfig?.midi?.burstDuration ?? 0) / 1000) {
        this.burstActive = false;
        this.burstTime = 0;
      }
    }

    applyVFX(this.renderer.domElement, this.audioData);
  }

  public onBeat(): void {
    const intensity = this.config.defaultConfig?.midi?.burstIntensity ?? 1;
    const color = this.config.defaultConfig?.particles?.color ?? '#ffffff';
    triggerParticleBurst(200, intensity, color);
    this.burstActive = true;
    this.burstTime = 0;
  }

  public dispose(): void {
    if (this.sceneObject) {
      this.scene.remove(this.sceneObject);
      (this.sceneObject.material as THREE.Material).dispose();
      this.sceneObject.geometry.dispose();
    }

    if (this.videoTexture) {
      this.videoTexture.dispose();
    }
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  config: PresetConfig,
  videoElement: HTMLVideoElement,
  shaderCode?: string
): BasePreset {
  return new OrganicAsciiGlitchPreset(scene, camera, renderer, config, videoElement, shaderCode);
}
