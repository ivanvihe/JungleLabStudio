import * as THREE from 'three';
import { VisualPreset } from '../core/VisualizerCore.js';

export class GeometricParticles extends VisualPreset {
    constructor(scene, audio, midi, settings) {
        super(scene, audio, midi, settings);
        this.params = { sensitivity: 0.5 };
        const count = 1000;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(count * 3);
        for (let i = 0; i < count; i++) {
            positions[i * 3] = (Math.random() - 0.5) * 10;
            positions[i * 3 + 1] = (Math.random() - 0.5) * 10;
            positions[i * 3 + 2] = (Math.random() - 0.5) * 10;
        }
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        const material = new THREE.PointsMaterial({ color: 0xffffff, size: 0.05 });
        this.points = new THREE.Points(geometry, material);
        this.scene.add(this.points);
    }

    update() {
        const freq = this.audio.getFrequencies();
        if (!freq) return;
        const positions = this.points.geometry.attributes.position.array;
        for (let i = 0; i < freq.length && i < positions.length / 3; i++) {
            positions[i * 3 + 1] = (freq[i] / 255) * 5 * this.params.sensitivity - 2.5;
        }
        this.points.geometry.attributes.position.needsUpdate = true;
    }

    onParamChange(name, value) {
        if (name === "sensitivity") {
            this.params.sensitivity = value;
        }
    }
}
