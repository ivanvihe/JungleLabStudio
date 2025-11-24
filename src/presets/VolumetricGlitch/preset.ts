
import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';
import { createVFX, updateVFX } from './vfx';

class VolumetricGlitchPreset extends BasePreset {
  private sceneObject: THREE.Mesh;
  private burstActive: boolean = false;
  private burstTime: number = 0;
  private palettes = {
    cyber: [new THREE.Color('#00ffff'), new THREE.Color('#ff00ff'), new THREE.Color('#ffff00')],
    nebula: [new THREE.Color('#4e00ff'), new THREE.Color('#8e00ff'), new THREE.Color('#ff00ff')],
    forest: [new THREE.Color('#00ff8a'), new THREE.Color('#45B7D1'), new THREE.Color('#96CEB4')],
  }

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
    const uniforms = {
      u_time: { value: 0.0 },
      u_resolution: { value: new THREE.Vector2(this.renderer.domElement.width, this.renderer.domElement.height) },
      u_audioLow: { value: 0.0 },
      u_audioMid: { value: 0.0 },
      u_audioHigh: { value: 0.0 },
      u_burst: { value: 0.0 },
      u_color1: { value: new THREE.Color() },
      u_color2: { value: new THREE.Color() },
      u_color3: { value: new THREE.Color() },
    };

    const material = new THREE.ShaderMaterial({
      uniforms: uniforms,
      vertexShader: `
        varying vec2 vUv;
        void main() {
          vUv = uv;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: this.shaderCode,
    });

    const geometry = new THREE.PlaneGeometry(2, 2);
    this.sceneObject = new THREE.Mesh(geometry, material);
    this.scene.add(this.sceneObject);
    this.updateColors();
    createVFX(this.scene);
  }

  public update(): void {
//...
    material.uniforms.u_audioHigh.value = this.audioData.high;
    material.uniforms.u_burst.value = this.burstActive ? this.burstTime / (this.currentConfig.midi.burstDuration / 1000) : 0.0;
    
    updateVFX(deltaTime, this.audioData);
  }

  public onMidi(note: number, velocity: number): void {
    if (note === this.currentConfig.midi.note) {
      this.burstActive = true;
      this.burstTime = 0;
    }
  }

  updateConfig(newConfig: any): void {
    super.updateConfig(newConfig);
    if (newConfig.lights?.colorPalette) {
        this.updateColors();
    }
  }

  private updateColors() {
    const paletteName = this.currentConfig.lights.colorPalette as keyof typeof this.palettes;
    const palette = this.palettes[paletteName] || this.palettes.cyber;
    const material = this.sceneObject.material as THREE.ShaderMaterial;
    material.uniforms.u_color1.value = palette[0];
    material.uniforms.u_color2.value = palette[1];
    material.uniforms.u_color3.value = palette[2];
  }

  public dispose(): void {
    this.scene.remove(this.sceneObject);
    (this.sceneObject.material as THREE.ShaderMaterial).dispose();
    this.sceneObject.geometry.dispose();
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  config: PresetConfig,
  videoElement: HTMLVideoElement,
  shaderCode: string
): BasePreset {
  return new VolumetricGlitchPreset(scene, camera, renderer, config, videoElement, shaderCode);
}
