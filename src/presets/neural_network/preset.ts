import * as THREE from 'three';
import { BasePreset, PresetConfig } from '../../core/PresetLoader';

export const config: PresetConfig = {
  name: 'Infinite Neural Journey',
  description: 'Endless stream of connected nodes forming a neural network starfield.',
  author: 'AudioVisualizer',
  version: '1.0.0',
  category: 'ai',
  tags: ['neural', 'network', 'infinite', 'starfield'],
  thumbnail: 'neural_network_thumb.png',
  defaultConfig: {
    speed: 5,
    nodeSize: 0.05,
    colors: {
      node: '#8e44ad',
      connection: '#3498db'
    }
  },
  controls: [
    {
      name: 'speed',
      type: 'slider',
      label: 'Travel Speed',
      min: 1,
      max: 20,
      step: 0.5,
      default: 5
    },
    {
      name: 'nodeSize',
      type: 'slider',
      label: 'Node Size',
      min: 0.02,
      max: 0.2,
      step: 0.01,
      default: 0.05
    },
    {
      name: 'colors.node',
      type: 'color',
      label: 'Node Color',
      default: '#8e44ad'
    },
    {
      name: 'colors.connection',
      type: 'color',
      label: 'Connection Color',
      default: '#3498db'
    }
  ],
  audioMapping: {
    low: {
      description: 'Controls node pulsing',
      frequency: '20-250 Hz',
      effect: 'Node scale'
    },
    mid: {
      description: 'Controls connection brightness',
      frequency: '250-4000 Hz',
      effect: 'Line opacity'
    },
    high: {
      description: 'Controls travel speed',
      frequency: '4000+ Hz',
      effect: 'Camera velocity'
    }
  },
  performance: {
    complexity: 'medium',
    recommendedFPS: 60,
    gpuIntensive: false
  }
};

class Node {
  public mesh: THREE.Mesh;
  public position: THREE.Vector3;

  constructor(position: THREE.Vector3, color: THREE.Color, size: number) {
    const geometry = new THREE.SphereGeometry(size, 8, 8);
    const material = new THREE.MeshBasicMaterial({ color });
    this.mesh = new THREE.Mesh(geometry, material);
    this.position = this.mesh.position;
    this.position.copy(position);
  }

  update(audio: number, time: number): void {
    const pulse = 1 + Math.sin(time * 5 + this.position.x) * 0.3 * audio;
    this.mesh.scale.setScalar(pulse);
  }

  setColor(color: THREE.Color): void {
    (this.mesh.material as THREE.MeshBasicMaterial).color.copy(color);
  }

  dispose(): void {
    this.mesh.geometry.dispose();
    (this.mesh.material as THREE.Material).dispose();
  }
}

class Connection {
  public line: THREE.Line;
  constructor(public a: Node, public b: Node, color: THREE.Color) {
    const geometry = new THREE.BufferGeometry().setFromPoints([a.position, b.position]);
    const material = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.7 });
    this.line = new THREE.Line(geometry, material);
  }

  update(audio: number): void {
    this.line.geometry.setFromPoints([this.a.position, this.b.position]);
    (this.line.material as THREE.LineBasicMaterial).opacity = 0.3 + audio * 0.7;
  }

  setColor(color: THREE.Color): void {
    (this.line.material as THREE.LineBasicMaterial).color.copy(color);
  }

  dispose(): void {
    this.line.geometry.dispose();
    (this.line.material as THREE.Material).dispose();
  }
}

export class InfiniteNeuralNetwork extends BasePreset {
  private nodes: Node[] = [];
  private connections: Connection[] = [];
  private currentConfig: any;
  private nextSpawnX = 0;

  constructor(scene: THREE.Scene, camera: THREE.Camera, renderer: THREE.WebGLRenderer, config: PresetConfig) {
    super(scene, camera, renderer, config);
    this.currentConfig = JSON.parse(JSON.stringify(config.defaultConfig));
  }

  init(): void {
    this.camera.position.set(0, 0, 0);
    this.camera.lookAt(1, 0, 0);
    while (this.nextSpawnX < this.camera.position.x + 50) {
      this.spawnNode();
    }
  }

  private spawnNode(): void {
    const size = this.currentConfig.nodeSize;
    const nodeColor = new THREE.Color(this.currentConfig.colors.node);
    const connColor = new THREE.Color(this.currentConfig.colors.connection);

    const x = this.nextSpawnX + Math.random() * 2 + 1;
    const y = (Math.random() - 0.5) * 4;
    const z = (Math.random() - 0.5) * 4;
    const node = new Node(new THREE.Vector3(x, y, z), nodeColor, size);
    this.scene.add(node.mesh);
    this.nodes.push(node);

    // Connect to previous nodes to ensure continuity
    if (this.nodes.length > 1) {
      const prev = this.nodes[this.nodes.length - 2];
      const connection = new Connection(prev, node, connColor);
      this.scene.add(connection.line);
      this.connections.push(connection);

      if (this.nodes.length > 2) {
        const randomIndex = Math.max(0, this.nodes.length - 3 - Math.floor(Math.random() * 10));
        const randomNode = this.nodes[randomIndex];
        const extraConn = new Connection(randomNode, node, connColor);
        this.scene.add(extraConn.line);
        this.connections.push(extraConn);
      }
    }

    this.nextSpawnX = x;
  }

  private removeNode(node: Node): void {
    this.scene.remove(node.mesh);
    node.dispose();
    this.connections = this.connections.filter(conn => {
      if (conn.a === node || conn.b === node) {
        this.scene.remove(conn.line);
        conn.dispose();
        return false;
      }
      return true;
    });
  }

  update(): void {
    const delta = this.clock.getDelta();
    const time = this.clock.getElapsedTime();
    const audioIntensity = (this.audioData.low + this.audioData.mid + this.audioData.high) / 3;

    const speed = this.currentConfig.speed * (0.5 + this.audioData.high);
    this.camera.position.x += delta * speed;
    this.camera.lookAt(this.camera.position.x + 1, 0, 0);

    while (this.nextSpawnX < this.camera.position.x + 50) {
      this.spawnNode();
    }

    while (this.nodes.length && this.nodes[0].position.x < this.camera.position.x - 20) {
      const old = this.nodes.shift()!;
      this.removeNode(old);
    }

    this.nodes.forEach(n => n.update(audioIntensity, time));
    this.connections.forEach(c => c.update(this.audioData.mid));
  }

  updateConfig(newConfig: any): void {
    this.currentConfig = this.deepMerge(this.currentConfig, newConfig);
    const nodeColor = new THREE.Color(this.currentConfig.colors.node);
    const connColor = new THREE.Color(this.currentConfig.colors.connection);
    this.nodes.forEach(n => n.setColor(nodeColor));
    this.connections.forEach(c => c.setColor(connColor));
  }

  private deepMerge(target: any, source: any): any {
    const result = { ...target };
    for (const key in source) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        result[key] = this.deepMerge(result[key] || {}, source[key]);
      } else {
        result[key] = source[key];
      }
    }
    return result;
  }

  dispose(): void {
    this.nodes.forEach(n => {
      this.scene.remove(n.mesh);
      n.dispose();
    });
    this.connections.forEach(c => {
      this.scene.remove(c.line);
      c.dispose();
    });
    this.nodes = [];
    this.connections = [];
  }
}

export function createPreset(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  config: PresetConfig
): BasePreset {
  return new InfiniteNeuralNetwork(scene, camera, renderer, config);
}

