import { AudioEngine } from '../core/AudioEngine.js';
import { MidiEngine } from '../core/MidiEngine.js';
import { Visualizer } from '../core/VisualizerCore.js';
import { SettingsManager } from '../core/SettingsManager.js';
import { GeometricParticles } from '../visuals/GeometricParticles.js';
import { FluidParticles } from '../visuals/FluidParticles.js';
import { EvolutiveParticles } from '../visuals/EvolutiveParticles.js';
import { AbstractLines } from '../visuals/AbstractLines.js';
import { MoebiusBand } from '../visuals/MoebiusBand.js';
import { AbstractShapes } from '../visuals/AbstractShapes.js';

const canvas = document.getElementById('visualizer-canvas');

const audio = new AudioEngine();
const midi = new MidiEngine();
const settings = new SettingsManager();

const visualizer = new Visualizer(canvas, { audio, midi, settings });
visualizer.registerPreset('GeometricParticles', GeometricParticles);
visualizer.registerPreset('FluidParticles', FluidParticles);
visualizer.registerPreset('EvolutiveParticles', EvolutiveParticles);
visualizer.registerPreset('AbstractLines', AbstractLines);
visualizer.registerPreset('MoebiusBand', MoebiusBand);
visualizer.registerPreset('AbstractShapes', AbstractShapes);

window.electronAPI.on('control-change', ({ param, value }) => {
    visualizer.setParam(param, value);
});

(async () => {
    await audio.init();
    await midi.init();
    visualizer.loadPreset('GeometricParticles');
    function animate() {
        requestAnimationFrame(animate);
        visualizer.update();
    }
    animate();
})();
