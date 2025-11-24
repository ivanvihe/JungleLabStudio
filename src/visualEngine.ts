import p5 from 'p5';
import { AudioBands, SketchState, VisualContext, VisualModule } from './types';

export class VisualEngine {
  private p: p5;
  private modules: VisualModule[];
  private modifiers: VisualModule[];
  private main: p5.Graphics;
  private overlay: p5.Graphics;
  private feedback: p5.Graphics;
  private ascii: p5.Graphics;
  private lastTime = 0;
  private getState: () => SketchState;

  constructor(p: p5, getState: () => SketchState, modules: VisualModule[], modifiers: VisualModule[] = []) {
    this.p = p;
    this.getState = getState;
    this.modules = modules;
    this.modifiers = modifiers;
    this.main = p.createGraphics(p.width, p.height);
    this.overlay = p.createGraphics(p.width, p.height);
    this.feedback = p.createGraphics(p.width, p.height);
    this.ascii = p.createGraphics(p.width, p.height);
    this.configureLayer(this.main);
    this.configureLayer(this.overlay);
    this.configureLayer(this.feedback);
    this.configureLayer(this.ascii);
    const ctx = this.buildContext(0);
    this.modules.forEach((m) => m.init(ctx));
    this.modifiers.forEach((m) => m.init(ctx));
  }

  private configureLayer(layer: p5.Graphics) {
    layer.colorMode(this.p.HSB, 360, 100, 100, 1);
    layer.noiseSeed(Math.random() * 10000);
  }

  private buildContext(delta: number): VisualContext {
    return {
      p: this.p,
      main: this.main,
      overlay: this.overlay,
      feedback: this.feedback,
      ascii: this.ascii,
      state: this.getState(),
      delta,
    };
  }

  resize(width: number, height: number) {
    this.main.resizeCanvas(width, height);
    this.overlay.resizeCanvas(width, height);
    this.feedback.resizeCanvas(width, height);
    this.ascii.resizeCanvas(width, height);
  }

  onMidiNote(note: number, velocity: number, channel: number) {
    const ctx = this.buildContext(0);
    this.modules.forEach((m) => m.onMidiNote?.(note, velocity, channel, ctx));
    this.modifiers.forEach((m) => m.onMidiNote?.(note, velocity, channel, ctx));
  }

  onMidiCC(cc: number, value: number, channel: number) {
    const ctx = this.buildContext(0);
    this.modules.forEach((m) => m.onMidiCC?.(cc, value, channel, ctx));
    this.modifiers.forEach((m) => m.onMidiCC?.(cc, value, channel, ctx));
  }

  onAudio(data: { level: number; bands: AudioBands; beat: number }) {
    const ctx = this.buildContext(0);
    ctx.state.audioBands = data.bands;
    ctx.state.audioLevel = data.level;
    ctx.state.beat = data.beat;
    this.modules.forEach((m) => m.onAudioAnalysis?.(ctx));
    this.modifiers.forEach((m) => m.onAudioAnalysis?.(ctx));
  }

  updateAndDraw() {
    const now = this.p.millis() * 0.001;
    const delta = Math.min(0.05, Math.max(0.016, now - this.lastTime));
    this.lastTime = now;
    const ctx = this.buildContext(delta);

    this.main.clear();
    this.overlay.clear();
    this.ascii.clear();

    this.modules.forEach((m) => m.update(ctx));
    this.modules.forEach((m) => m.draw(ctx));
    this.modifiers.forEach((m) => m.update(ctx));
    this.modifiers.forEach((m) => m.draw(ctx));

    this.p.push();
    this.p.clear();
    this.p.image(this.main, 0, 0, this.p.width, this.p.height);
    this.p.blendMode(this.p.ADD);
    this.p.image(this.overlay, 0, 0, this.p.width, this.p.height);
    this.p.image(this.ascii, 0, 0, this.p.width, this.p.height);
    this.applyVhsWarp(ctx.state.params.vhs_warp + ctx.state.audioBands.bass * 0.2);
    this.p.pop();
  }

  private applyVhsWarp(amount: number) {
    if (amount <= 0) return;
    const slices = 12;
    const jitter = amount * 12;
    for (let i = 0; i < slices; i += 1) {
      const sy = (i / slices) * this.p.height;
      const sh = (this.p.height / slices) * (0.7 + Math.random() * 0.4);
      const dx = (Math.random() - 0.5) * jitter;
      this.p.copy(0, sy, this.p.width, sh, dx, sy + Math.sin(this.p.frameCount * 0.02 + i) * amount * 6, this.p.width, sh);
    }
  }
}
