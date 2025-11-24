import p5 from 'p5';
import { VisualContext, VisualModule } from '../types';

const easeAudio = (val: number) => Math.min(1, Math.pow(val, 0.8));

export class ParticleFieldModule implements VisualModule {
  id = 'particles';
  name = 'Particle Field';
  params = [
    { key: 'pf_intensity', label: 'Glow', min: 0.2, max: 1.8, defaultValue: 1, step: 0.01 },
    { key: 'pf_density', label: 'Density', min: 0.2, max: 1.5, defaultValue: 0.9, step: 0.01 },
    { key: 'pf_noise', label: 'Noise Flow', min: 0, max: 1.4, defaultValue: 0.8, step: 0.01 },
  ];
  private particles: { pos: p5.Vector; vel: p5.Vector; life: number }[] = [];

  init({ p }: VisualContext): void {
    this.particles = [];
    for (let i = 0; i < 1200; i += 1) {
      this.particles.push({ pos: p.createVector(p.random(p.width), p.random(p.height)), vel: p.createVector(), life: p.random(80, 260) });
    }
  }

  onMidiNote(_note: number, velocity: number, _channel: number, { state }: VisualContext) {
    state.params.pf_intensity = Math.min(state.params.pf_intensity + velocity * 0.6, 1.8);
    state.params.pf_density = Math.min(1.5, state.params.pf_density + velocity * 0.3);
  }

  update({ p, main, state, delta }: VisualContext): void {
    const audio = easeAudio(state.audioLevel + state.beat * 0.6 + state.midiPulse * 0.4);
    const target = Math.floor(600 * state.params.pf_density + audio * 420);
    while (this.particles.length < target)
      this.particles.push({ pos: p.createVector(p.random(p.width), p.random(p.height)), vel: p.createVector(), life: p.random(80, 260) });
    while (this.particles.length > target) this.particles.pop();

    this.particles.forEach((pt) => {
      const angle = p.noise(pt.pos.x * 0.0016, pt.pos.y * 0.0016, p.frameCount * 0.002) * p.TWO_PI * 2;
      const speed = 0.6 + state.params.pf_noise * 2.2 + audio * 1.3;
      pt.vel.set(Math.cos(angle) * speed, Math.sin(angle) * speed);
      pt.pos.add(pt.vel.mult(delta * 60));
      pt.life -= delta * 60;
      if (pt.pos.x < 0) pt.pos.x = p.width;
      if (pt.pos.y < 0) pt.pos.y = p.height;
      if (pt.pos.x > p.width) pt.pos.x = 0;
      if (pt.pos.y > p.height) pt.pos.y = 0;
      if (pt.life < 0) {
        pt.pos.set(p.random(p.width), p.random(p.height));
        pt.life = p.random(120, 260);
      }
    });
  }

  draw({ p, main, state }: VisualContext): void {
    const audio = easeAudio(state.audioLevel + state.beat * 0.6 + state.midiPulse * 0.3);
    main.push();
    main.blendMode(p.ADD);
    for (const pt of this.particles) {
      const hue = (p.noise(pt.pos.x * 0.002, pt.pos.y * 0.002, p.frameCount * 0.004) * 180 + 150) % 360;
      const alpha = (0.12 * state.params.pf_intensity + audio * 0.35) * state.params.master_intensity;
      main.noStroke();
      main.fill(hue, 80, 100, alpha);
      main.circle(pt.pos.x, pt.pos.y, 2.2 + state.params.pf_noise * 5 + audio * 6);
    }
    main.pop();
  }
}

export class RibbonTrailsModule implements VisualModule {
  id = 'ribbons';
  name = 'Ribbon Trails';
  params = [
    { key: 'rb_layers', label: 'Layers', min: 2, max: 8, defaultValue: 4, step: 1 },
    { key: 'rb_wave', label: 'Wave', min: 0.2, max: 2, defaultValue: 1, step: 0.01 },
    { key: 'rb_color', label: 'Color Drift', min: 0, max: 1, defaultValue: 0.5, step: 0.01 },
  ];

  init(): void {}

  update(): void {}

  draw({ p, main, state }: VisualContext): void {
    const time = p.millis() * 0.001;
    const layers = Math.floor(state.params.rb_layers);
    const audio = easeAudio(state.audioLevel + state.beat * 0.8 + state.midiPulse * 0.4);
    main.push();
    main.noFill();
    main.blendMode(p.SCREEN);
    for (let i = 0; i < layers; i += 1) {
      const hue = (240 + i * 30 + state.params.rb_color * 120 + audio * 80) % 360;
      main.stroke(hue, 80, 90, 0.4 * state.params.master_intensity);
      main.strokeWeight(3 - (i / layers) * 1.5);
      main.beginShape();
      for (let x = -60; x <= main.width + 60; x += 26) {
        const n = p.noise(x * 0.002 + i * 0.1, time * 0.35 + i * 0.08) - 0.5;
        const y =
          main.height * 0.5 +
          n * 260 * state.params.rb_wave +
          Math.sin(time * 0.8 + x * 0.004 + i) * 90 * (0.7 + state.params.rb_wave) -
          audio * 140 * (i / layers);
        main.curveVertex(x, y);
      }
      main.endShape();
    }
    main.pop();
  }
}

export class HolographicLinesModule implements VisualModule {
  id = 'holo-lines';
  name = 'Holographic Lines';
  params = [
    { key: 'hl_amount', label: 'Amount', min: 0, max: 1, defaultValue: 0.8, step: 0.01 },
    { key: 'hl_depth', label: 'Depth', min: 0, max: 1.4, defaultValue: 0.7, step: 0.01 },
  ];

  init(): void {}
  update(): void {}

  draw({ p, overlay, state }: VisualContext): void {
    const time = p.millis() * 0.001;
    const amount = state.params.hl_amount;
    const depth = state.params.hl_depth;
    overlay.push();
    overlay.blendMode(p.ADD);
    overlay.strokeWeight(1.2 + state.audioBands.treble * 1.2);
    overlay.stroke((240 + time * 40) % 360, 90, 90, 0.35 * amount * state.params.master_intensity);
    for (let i = 0; i < 24; i += 1) {
      const y = (i / 24) * overlay.height + Math.sin(time * 0.7 + i) * 20;
      overlay.line(0, y, overlay.width, y + Math.sin(time * 0.6 + i) * 40 * amount);
    }
    overlay.strokeWeight(2.2 + depth * 1.5);
    overlay.stroke((120 + time * 60) % 360, 80, 100, (0.25 * amount + state.audioBands.mid * 0.3) * state.params.master_intensity);
    for (let i = 0; i < 12; i += 1) {
      const x = (i / 12) * overlay.width;
      const y1 = overlay.height * 0.25 + Math.sin(time + i) * 60 * depth;
      const y2 = overlay.height * 0.75 + Math.cos(time * 0.7 + i) * 60 * depth;
      overlay.line(x, y1, overlay.width - x, y2);
    }
    overlay.pop();
  }
}

export class AsciiArtModule implements VisualModule {
  id = 'ascii';
  name = 'ASCII Art';
  params = [
    { key: 'aa_density', label: 'Density', min: 0.2, max: 1.4, defaultValue: 0.6, step: 0.02 },
    { key: 'aa_contrast', label: 'Contrast', min: 0, max: 1.2, defaultValue: 0.5, step: 0.01 },
  ];

  init(): void {}
  update(): void {}

  onMidiNote(_note: number, velocity: number, _channel: number, { state }: VisualContext) {
    state.params.aa_contrast = Math.min(1.2, state.params.aa_contrast + velocity * 0.5);
  }

  draw({ p, ascii, state }: VisualContext): void {
    const chars = '░▒▓/\\*+x=<>#%@';
    const density = Math.max(6, Math.floor(22 - state.params.aa_density * 10));
    const time = p.millis() * 0.001;
    const pulse = easeAudio(state.audioLevel + state.beat + state.midiPulse + state.midiVelocity);
    ascii.clear();
    ascii.push();
    ascii.textFont('monospace');
    ascii.textSize(density * (0.9 + pulse * 0.6));
    ascii.fill(190 + state.audioBands.mid * 120, 40, 100, 0.7 * (0.4 + state.params.aa_contrast) * state.params.master_intensity);
    ascii.noStroke();
    ascii.textAlign(p.CENTER, p.CENTER);
    for (let y = 0; y < ascii.height; y += density * 2) {
      for (let x = 0; x < ascii.width; x += density * 1.6) {
        const n = p.noise(x * 0.01, y * 0.01, time * 0.6 + pulse * 1.4);
        const idx = Math.floor(n * chars.length) % chars.length;
        ascii.text(chars[idx], x, y + Math.sin(n * p.TWO_PI) * density * 0.4 * pulse);
      }
    }
    ascii.pop();
  }
}

export class GlitchFeedbackModule implements VisualModule {
  id = 'glitch';
  name = 'Glitch / Feedback';
  params = [
    { key: 'gf_feedback', label: 'Feedback', min: 0, max: 1, defaultValue: 0.35, step: 0.01 },
    { key: 'gf_pixel', label: 'Pixelation', min: 1, max: 18, defaultValue: 6, step: 1 },
    { key: 'gf_glitch', label: 'Glitch', min: 0, max: 1, defaultValue: 0.25, step: 0.01 },
  ];

  init(): void {}
  update(): void {}

  draw({ p, main, overlay, feedback, state }: VisualContext): void {
    const pulse = easeAudio(state.beat + state.midiPulse + state.midiVelocity);
    const glitch = state.params.gf_glitch + pulse * 0.4;
    const pixel = state.params.gf_pixel;

    const snap = main.get();
    feedback.clear();
    feedback.tint(0, 0, 100, Math.max(0.1, (state.params.gf_feedback * 0.8 + state.audioBands.mid * 0.3) * state.params.master_intensity));
    feedback.image(snap, 0, 0);
    main.push();
    main.blendMode(p.LIGHTEST);
    main.tint(0, 0, 100, state.params.gf_feedback * 0.7);
    main.image(feedback, 0, 0, main.width, main.height);
    main.pop();

    const step = Math.max(1, Math.floor(pixel));
    p.push();
    p.noSmooth();
    const w = Math.max(1, Math.floor(p.width / step));
    const h = Math.max(1, Math.floor(p.height / step));
    const pixelated = p.get();
    p.image(pixelated, 0, 0, w, h);
    const px = p.get(0, 0, w, h);
    p.image(px, 0, 0, p.width, p.height);
    p.pop();

    if (glitch > 0.2) {
      p.push();
      p.tint(200, 80, 100, 0.6);
      p.image(pixelated, glitch * 8, 0, p.width, p.height);
      p.tint(320, 80, 100, 0.6);
      p.image(pixelated, -glitch * 8, 0, p.width, p.height);
      p.noTint();
      for (let i = 0; i < 8; i += 1) {
        const y = (i / 8) * p.height;
        const hStripe = (p.height / 8) * (0.7 + Math.random() * 0.6);
        const dx = (Math.random() - 0.5) * glitch * 40;
        p.copy(pixelated, 0, y, p.width, hStripe, dx, y + Math.random() * 6 - 3, p.width, hStripe);
      }
      p.pop();
    }

    overlay.push();
    overlay.noFill();
    overlay.stroke(200, 20, 100, 0.15 + glitch * 0.4);
    for (let i = 0; i < 12; i += 1) {
      const y = (i / 12) * overlay.height + Math.sin(p.frameCount * 0.03 + i) * 10;
      overlay.line(0, y, overlay.width, y + Math.sin(i) * glitch * 20);
    }
    overlay.pop();
  }
}

export const allModules: VisualModule[] = [
  new ParticleFieldModule(),
  new RibbonTrailsModule(),
  new HolographicLinesModule(),
  new AsciiArtModule(),
  new GlitchFeedbackModule(),
];
