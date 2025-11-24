import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';
import { applyVFX, createParticleSystem, updateParticles, triggerParticleBurst } from './vfx';

class OrganicAsciiGlitchPreset extends BasePreset {
  private videoTexture: THREE.VideoTexture;
  private sceneObject: THREE.Mesh;
  private burstActive: boolean = false;
  private burstTime: number = 0;
  private fontTexture: THREE.Texture;

  constructor(
    scene: THREE.Scene,
    camera: THREE.Camera,
    renderer: THREE.WebGLRenderer,
    config: PresetConfig,
    videoElement: HTMLVideoElement,
    private shaderCode: string
  ) {
    super(scene, camera, renderer, config, videoElement);
  }

  public init(): void {
    console.log('Initializing OrganicAsciiGlitchPreset');

    // Load font texture
    const textureLoader = new THREE.TextureLoader();
    this.fontTexture = textureLoader.load('./presets/OrganicAsciiGlitch/ascii-font.png');
    this.fontTexture.minFilter = THREE.NearestFilter;
    this.fontTexture.magFilter = THREE.NearestFilter;

    // Use the video element provided by the layer
    this.videoTexture = new THREE.VideoTexture(this.videoElement);
//...
export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  config: PresetConfig,
  videoElement: HTMLVideoElement,
  shaderCode: string
): BasePreset {
  return new OrganicAsciiGlitchPreset(scene, camera, renderer, config, videoElement, shaderCode);
}