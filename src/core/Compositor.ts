import * as THREE from 'three';
import { LayerState } from './LayerManager';

/**
 * Encapsula la logica de compositing de layers.
 */
export class Compositor {
  private scene: THREE.Scene;
  private camera: THREE.OrthographicCamera;
  private material: THREE.ShaderMaterial;
  private geometry: THREE.PlaneGeometry;
  private mesh: THREE.Mesh;

  constructor(private renderer: THREE.WebGLRenderer) {
    this.scene = new THREE.Scene();
    this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    this.material = new THREE.ShaderMaterial({
      uniforms: {
        layerC: { value: null },
        layerB: { value: null },
        layerA: { value: null },
        opacityC: { value: 1.0 },
        opacityB: { value: 1.0 },
        opacityA: { value: 1.0 },
        globalOpacity: { value: 1.0 }
      },
      vertexShader: `
        varying vec2 vUv;
        void main() {
          vUv = uv;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform sampler2D layerC;
        uniform sampler2D layerB;
        uniform sampler2D layerA;
        uniform float opacityC;
        uniform float opacityB;
        uniform float opacityA;
        uniform float globalOpacity;
        varying vec2 vUv;

        void main() {
          vec4 colorC = texture2D(layerC, vUv);
          vec4 colorB = texture2D(layerB, vUv);
          vec4 colorA = texture2D(layerA, vUv);

          colorC.a *= opacityC;
          colorB.a *= opacityB;
          colorA.a *= opacityA;

          vec4 result = vec4(0.0, 0.0, 0.0, 0.0);
          result = mix(result, colorC, colorC.a);
          result.rgb = mix(result.rgb, colorB.rgb, colorB.a);
          result.a = max(result.a, colorB.a);
          result.rgb = mix(result.rgb, colorA.rgb, colorA.a);
          result.a = max(result.a, colorA.a);
          result.a *= globalOpacity;
          gl_FragColor = result;
        }
      `,
      transparent: true,
      blending: THREE.NormalBlending,
      depthTest: false,
      depthWrite: false
    });

    this.geometry = new THREE.PlaneGeometry(2, 2);
    this.mesh = new THREE.Mesh(this.geometry, this.material);
    this.scene.add(this.mesh);
  }

  /**
   * Mezcla las capas renderizadas y escribe el resultado en el renderer.
   */
  public composite(layers: Map<string, LayerState>): void {
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.clear();

    layers.forEach((layer, layerId) => {
      const uniformName = `layer${layerId}` as keyof typeof this.material.uniforms;
      const opacityUniform = `opacity${layerId}` as keyof typeof this.material.uniforms;

      if (layer.renderTarget && this.material.uniforms[uniformName]) {
        (this.material.uniforms[uniformName] as any).value = layer.renderTarget.texture;
        (this.material.uniforms[opacityUniform] as any).value = layer.isActive ? layer.opacity : 0.0;
      }
    });

    this.renderer.render(this.scene, this.camera);
  }

  public setGlobalOpacity(opacity: number): void {
    this.material.uniforms.globalOpacity.value = opacity;
  }

  public dispose(): void {
    this.geometry.dispose();
    this.material.dispose();
  }
}

