import * as THREE from 'three';

export class Visualizer {
    constructor(canvas, { audio, midi, settings }) {
        this.canvas = canvas;
        this.audio = audio;
        this.midi = midi;
        this.settings = settings;

        this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.camera.position.z = 5;

        this.presets = new Map();
        this.currentPreset = null;

        window.addEventListener('resize', () => this._onResize());
    }

    registerPreset(name, presetClass) {
        this.presets.set(name, presetClass);
    }

    loadPreset(name) {
        if (this.currentPreset && this.currentPreset.dispose) {
            this.currentPreset.dispose();
        }
        this.scene.clear();
        const PresetClass = this.presets.get(name);
        if (!PresetClass) {
            console.warn(`Preset ${name} not found`);
            return;
        }
        this.currentPreset = new PresetClass(this.scene, this.audio, this.midi, this.settings);
    }

    update() {
        this.audio.update();
        if (this.currentPreset && this.currentPreset.update) {
            this.currentPreset.update();
        }
        this.renderer.render(this.scene, this.camera);
    }

    setParam(name, value) {
        if (this.currentPreset && this.currentPreset.onParamChange) {
            this.currentPreset.onParamChange(name, value);
        }
    }

    _onResize() {
        const w = window.innerWidth;
        const h = window.innerHeight;
        this.renderer.setSize(w, h);
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
    }
}

export class VisualPreset {
    constructor(scene, audio, midi, settings) {
        this.scene = scene;
        this.audio = audio;
        this.midi = midi;
        this.settings = settings;
    }
    update() {}
    dispose() {}
}
