import p5 from 'p5';
import { VisualEngine } from '../visualEngine';
import { VisualPreset, SketchState, VisualModule, Parameter } from '../types';
import {
  allModules,
  ParticleFieldModule,
  RibbonTrailsModule,
  HolographicLinesModule,
  AsciiArtModule,
  GlitchFeedbackModule,
} from '../visuals/modules';

const buildParams = (...modules: VisualModule[]): Parameter[] => [
  { key: 'master_intensity', label: 'Master Glow', min: 0.3, max: 1.8, defaultValue: 1, step: 0.01 },
  { key: 'vhs_warp', label: 'VHS Warp', min: 0, max: 1, defaultValue: 0.35, step: 0.01 },
  { key: 'aberration', label: 'Chromatic Aberration', min: 0, max: 1, defaultValue: 0.35, step: 0.01 },
  ...modules.flatMap((m) => m.params),
];

const applyAberration = (p: p5, amount: number) => {
  if (amount <= 0) return;
  p.push();
  p.blendMode(p.ADD);
  p.tint(190, 80, 100, 0.5);
  p.image(p.get(), amount * 6, 0, p.width, p.height);
  p.tint(320, 80, 100, 0.5);
  p.image(p.get(), -amount * 6, 0, p.width, p.height);
  p.pop();
};

const createPreset = (id: string, name: string, description: string, modules: VisualModule[], modifiers: VisualModule[]): VisualPreset => ({
  id,
  name,
  description,
  parameters: buildParams(...modules, ...modifiers),
  init: (p: p5, getState: () => SketchState) => {
    let engine: VisualEngine;

    p.setup = () => {
      p.createCanvas(p.windowWidth, p.windowHeight, p.WEBGL);
      p.colorMode(p.HSB, 360, 100, 100, 1);
      engine = new VisualEngine(p, getState, modules, modifiers);
    };

    p.windowResized = () => {
      p.resizeCanvas(p.windowWidth, p.windowHeight);
      engine?.resize(p.width, p.height);
    };

    p.draw = () => {
      const state = getState();
      const aspect = state.orientation === 'portrait' ? 9 / 16 : 16 / 9;
      const targetW = state.orientation === 'portrait' ? Math.min(p.width, p.height * aspect) : p.width;
      const targetH = targetW / aspect;
      p.push();
      p.resetMatrix();
      p.translate(-p.width / 2, -p.height / 2);
      p.background(0, 0, 0, 1);
      engine.updateAndDraw();
      applyAberration(p, state.params.aberration * 0.6 + state.audioBands.treble * 0.25);
      p.pop();

      p.push();
      p.translate(p.width / 2, p.height / 2);
      p.rectMode(p.CENTER);
      p.noFill();
      p.stroke(190, 40, 100, 0.1);
      p.rect(0, 0, targetW, targetH, 8);
      p.pop();
    };
  },
});

const particleWorld = createPreset(
  'particle-field',
  'Particle Field',
  'Campo volumétrico de partículas y cintas neon con feedback y glitch.',
  [new ParticleFieldModule(), new RibbonTrailsModule(), new HolographicLinesModule(), new AsciiArtModule()],
  [new GlitchFeedbackModule()],
);

const holographicRibbons = createPreset(
  'holo-ribbons',
  'Holographic Ribbons',
  'Cintas fluidas, líneas holográficas y ASCII reactivo en modo performance.',
  [new RibbonTrailsModule(), new ParticleFieldModule(), new AsciiArtModule()],
  [new GlitchFeedbackModule(), new HolographicLinesModule()],
);

const glitchLab = createPreset(
  'glitch-lab',
  'Glitch Feedback Lab',
  'Laboratorio en vivo con feedback retro, pixelación y ráfagas de glitch.',
  [new ParticleFieldModule(), new AsciiArtModule(), new HolographicLinesModule()],
  [new GlitchFeedbackModule()],
);

export const presets: VisualPreset[] = [particleWorld, holographicRibbons, glitchLab];
export { allModules };
