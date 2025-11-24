import p5 from 'p5';
import { SketchState, VisualPreset } from '../types';

interface FlowParticle {
  pos: p5.Vector;
  vel: p5.Vector;
  life: number;
}

const createNebulaBloom = (): VisualPreset => ({
  id: 'nebula-bloom',
  name: 'Nebula Bloom',
  description:
    'Niebla volumétrica neón con partículas aditivas, cintas luminosas y gradientes holográficos influenciados por audio.',
  parameters: [
    {
      key: 'intensity',
      label: 'Intensidad / Glow',
      min: 0.2,
      max: 1.6,
      defaultValue: 0.9,
      step: 0.01,
      description: 'Controla el brillo global, halos y bloom simulado.',
    },
    {
      key: 'turbulence',
      label: 'Turbulencia',
      min: 0,
      max: 1.2,
      defaultValue: 0.45,
      step: 0.01,
      description: 'Cantidad de deformación procedural y movimiento fluido.',
    },
    {
      key: 'particleDensity',
      label: 'Densidad de partículas',
      min: 0.2,
      max: 1.4,
      defaultValue: 0.8,
      step: 0.05,
      description: 'Cantidad de micro partículas y polvo flotante.',
    },
    {
      key: 'ribbonTwist',
      label: 'Cintas / Parallax',
      min: 0,
      max: 1,
      defaultValue: 0.5,
      step: 0.01,
      description: 'Ondulación y parallax de las cintas holográficas.',
    },
    {
      key: 'hueShift',
      label: 'Desplazamiento cromático',
      min: 0,
      max: 1,
      defaultValue: 0.35,
      step: 0.01,
      description: 'Mezcla los gradientes entre cyan, turquesa, magenta y púrpura.',
    },
  ],
  init: (p: p5, getState: () => SketchState) => {
    const particles: FlowParticle[] = [];
    const spawnParticle = () => {
      const pos = p.createVector(p.random(p.width), p.random(p.height));
      const vel = p.createVector(0, 0);
      return { pos, vel, life: p.random(120, 320) } as FlowParticle;
    };

    const seedParticles = (count: number) => {
      particles.length = 0;
      for (let i = 0; i < count; i += 1) particles.push(spawnParticle());
    };

    p.setup = () => {
      p.createCanvas(p.windowWidth, p.windowHeight);
      p.colorMode(p.HSB, 360, 100, 100, 1);
      p.noStroke();
      seedParticles(800);
    };

    p.windowResized = () => {
      p.resizeCanvas(p.windowWidth, p.windowHeight);
    };

    const drawGradient = (hueShift: number, intensity: number) => {
      const ctx = p.drawingContext as CanvasRenderingContext2D;
      const gradient = ctx.createRadialGradient(p.width * 0.3, p.height * 0.35, 120, p.width * 0.5, p.height * 0.5, p.width);
      const c1 = p.color((200 + hueShift * 80) % 360, 80, 50, 0.5 * intensity);
      const c2 = p.color((310 + hueShift * 120) % 360, 90, 65, 0.45 * intensity);
      const c3 = p.color((150 + hueShift * 40) % 360, 75, 55, 0.35 * intensity);
      gradient.addColorStop(0, c1.toString());
      gradient.addColorStop(0.45, c2.toString());
      gradient.addColorStop(1, c3.toString());
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, p.width, p.height);
    };

    const drawRibbons = (time: number, twist: number, intensity: number, audio: number) => {
      p.push();
      p.blendMode(p.ADD);
      p.noFill();
      const layers = 3;
      for (let l = 0; l < layers; l += 1) {
        const hue = (190 + l * 55 + twist * 120) % 360;
        p.stroke(hue, 80, 90, 0.35 * intensity);
        p.strokeWeight(2.5 + l * 0.4);
        p.beginShape();
        for (let x = 0; x < p.width; x += 30) {
          const y =
            p.height * 0.35 +
            p.sin((x * 0.002 + time * (0.6 + l * 0.15)) + l * 0.8) * 60 * (1 + twist * 0.8) +
            p.noise(x * 0.003, time * 0.2 + l * 0.1) * 120 * twist +
            audio * 90;
          p.curveVertex(x, y + l * 40 * (0.5 + twist));
        }
        p.endShape();
      }
      p.pop();
    };

    const drawFog = (time: number, intensity: number, hueShift: number) => {
      p.push();
      p.blendMode(p.SCREEN);
      for (let i = 0; i < 3; i += 1) {
        const alpha = 0.05 * intensity;
        const radius = p.width * (0.35 + i * 0.15);
        const cx = p.width * (0.3 + 0.25 * i + p.sin(time * 0.12 + i) * 0.05);
        const cy = p.height * (0.45 + p.cos(time * 0.08 + i * 0.6) * 0.08);
        const grad = (p.drawingContext as CanvasRenderingContext2D).createRadialGradient(
          cx,
          cy,
          radius * 0.2,
          cx,
          cy,
          radius,
        );
        const baseHue = (220 + hueShift * 100 + i * 20) % 360;
        grad.addColorStop(0, p.color(baseHue, 70, 90, alpha).toString());
        grad.addColorStop(1, p.color(baseHue + 60, 60, 30, 0).toString());
        (p.drawingContext as CanvasRenderingContext2D).fillStyle = grad;
        p.rect(0, 0, p.width, p.height);
      }
      p.pop();
    };

    const updateParticles = (time: number, turbulence: number, intensity: number, audio: number) => {
      const targetCount = Math.floor(600 * intensity * 0.8 + 400 * turbulence);
      if (targetCount !== particles.length) seedParticles(targetCount);

      p.push();
      p.blendMode(p.ADD);
      for (const particle of particles) {
        const angle = p.noise(particle.pos.x * 0.0015, particle.pos.y * 0.0015, time * 0.2) * p.TWO_PI * 2;
        particle.vel.x = p.cos(angle) * (0.6 + turbulence * 2.4 + audio * 1.4);
        particle.vel.y = p.sin(angle) * (0.6 + turbulence * 2.4 + audio * 1.4);
        particle.pos.add(particle.vel);
        particle.life -= 1;

        if (particle.pos.x < 0 || particle.pos.x > p.width || particle.pos.y < 0 || particle.pos.y > p.height || particle.life <= 0) {
          particle.pos.set(p.random(p.width), p.random(p.height));
          particle.life = p.random(120, 320);
        }

        const hue = (p.noise(particle.pos.x * 0.002, time * 0.1) * 180 + 160) % 360;
        const alpha = 0.15 * intensity + audio * 0.25;
        p.fill(hue, 80, 100, alpha);
        p.circle(particle.pos.x, particle.pos.y, 2 + turbulence * 4 + audio * 4);
      }
      p.pop();
    };

    p.draw = () => {
      const { params, audioLevel } = getState();
      const time = p.millis() * 0.001;
      const smoothAudio = p.lerp(0, audioLevel, 0.8);

      p.clear();
      drawGradient(params.hueShift, params.intensity);
      drawFog(time, params.intensity + smoothAudio * 0.8, params.hueShift);
      drawRibbons(time, params.ribbonTwist, params.intensity, smoothAudio);
      updateParticles(time, params.turbulence, params.particleDensity, smoothAudio);

      p.push();
      p.noStroke();
      p.fill(0, 0, 0, 0.2);
      p.rect(0, 0, p.width, p.height);
      p.pop();
    };
  },
});

const createChromaticCurrents = (): VisualPreset => ({
  id: 'chromatic-currents',
  name: 'Chromatic Currents',
  description: 'Cintas líquidas, halos volumétricos y partículas orbitando con desfase de profundidad.',
  parameters: [
    {
      key: 'waveStrength',
      label: 'Ondulación',
      min: 0.2,
      max: 2,
      defaultValue: 1,
      step: 0.01,
      description: 'Deformación de las cintas y el fluido.',
    },
    {
      key: 'ribbonCount',
      label: 'Capas de cintas',
      min: 2,
      max: 8,
      defaultValue: 4,
      step: 1,
      description: 'Cantidad de capas con parallax y glow.',
    },
    {
      key: 'colorDrift',
      label: 'Deriva cromática',
      min: 0,
      max: 1,
      defaultValue: 0.5,
      step: 0.01,
      description: 'Cuánto se desplazan los gradientes a lo largo del tiempo.',
    },
    {
      key: 'particleShimmer',
      label: 'Brillo de partículas',
      min: 0,
      max: 1.2,
      defaultValue: 0.7,
      step: 0.01,
      description: 'Intensidad del brillo y trails.',
    },
    {
      key: 'depth',
      label: 'Profundidad',
      min: 0.4,
      max: 1.4,
      defaultValue: 0.9,
      step: 0.01,
      description: 'Separación espacial y neblina de fondo.',
    },
  ],
  init: (p: p5, getState: () => SketchState) => {
    const ribbons: { points: p5.Vector[]; offset: number }[] = [];
    const particles: FlowParticle[] = [];

    const seed = (width: number, height: number) => {
      ribbons.length = 0;
      particles.length = 0;
      for (let i = 0; i < 10; i += 1) particles.push({ pos: p.createVector(p.random(width), p.random(height)), vel: p.createVector(), life: p.random(160, 320) });
    };

    p.setup = () => {
      p.createCanvas(p.windowWidth, p.windowHeight);
      p.colorMode(p.HSB, 360, 100, 100, 1);
      p.noFill();
      seed(p.width, p.height);
    };

    p.windowResized = () => {
      p.resizeCanvas(p.windowWidth, p.windowHeight);
      seed(p.width, p.height);
    };

    const updateParticles = (time: number, shimmer: number, depth: number, audio: number) => {
      const target = Math.floor(150 + shimmer * 180);
      while (particles.length < target) particles.push({ pos: p.createVector(p.random(p.width), p.random(p.height)), vel: p.createVector(), life: p.random(160, 320) });
      while (particles.length > target) particles.pop();

      p.push();
      p.blendMode(p.ADD);
      for (const pt of particles) {
        const angle = p.noise(pt.pos.x * 0.002, pt.pos.y * 0.002, time * 0.25) * p.TWO_PI * 2;
        const speed = 0.8 + shimmer * 1.2 + audio * 1.4;
        pt.vel.set(p.cos(angle) * speed, p.sin(angle) * speed);
        pt.pos.add(pt.vel);
        pt.life -= 1;
        if (pt.pos.x < 0) pt.pos.x = p.width;
        if (pt.pos.x > p.width) pt.pos.x = 0;
        if (pt.pos.y < 0) pt.pos.y = p.height;
        if (pt.pos.y > p.height) pt.pos.y = 0;
        if (pt.life < 0) {
          pt.life = p.random(200, 320);
        }

        const hue = (p.noise(pt.pos.x * 0.003, time * 0.15) * 220 + 90) % 360;
        p.stroke(hue, 80, 100, 0.35 + shimmer * 0.4);
        p.strokeWeight(1.5 + shimmer * 2.5);
        p.point(pt.pos.x + (Math.random() - 0.5) * 2 * depth, pt.pos.y + (Math.random() - 0.5) * 2 * depth);
      }
      p.pop();
    };

    const drawRibbons = (time: number, count: number, wave: number, drift: number, depth: number, audio: number) => {
      p.push();
      p.blendMode(p.SCREEN);
      for (let i = 0; i < count; i += 1) {
        const parallax = (i / count) * depth;
        const hue = (260 + i * 30 + drift * 120) % 360;
        p.stroke(hue, 80, 90, 0.4);
        p.strokeWeight(3.5 - (i / count) * 1.8);
        p.beginShape();
        for (let x = -40; x <= p.width + 40; x += 28) {
          const noiseY = p.noise(x * 0.002 + i * 0.08, time * 0.35 + i * 0.05) - 0.5;
          const y =
            p.height * 0.5 +
            noiseY * 280 * wave +
            p.sin(time * 0.6 + x * 0.004 + i) * 80 * (0.6 + wave) +
            parallax * 160 -
            audio * 120 * (0.4 + parallax);
          p.curveVertex(x, y);
        }
        p.endShape();
      }
      p.pop();
    };

    const drawAtmosphere = (time: number, depth: number, drift: number) => {
      const ctx = p.drawingContext as CanvasRenderingContext2D;
      const grad = ctx.createLinearGradient(0, 0, p.width, p.height);
      grad.addColorStop(0, p.color((190 + drift * 90) % 360, 80, 20 + depth * 40, 0.6).toString());
      grad.addColorStop(1, p.color((330 + drift * 120) % 360, 90, 45 + depth * 30, 0.4).toString());
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, p.width, p.height);

      p.push();
      p.blendMode(p.ADD);
      p.noStroke();
      const glow = p.width * 0.4;
      const cx = p.width * 0.55 + p.sin(time * 0.2) * 40;
      const cy = p.height * 0.45 + p.cos(time * 0.15) * 30;
      const radial = ctx.createRadialGradient(cx, cy, glow * 0.1, cx, cy, glow);
      radial.addColorStop(0, p.color(200, 70, 90, 0.4).toString());
      radial.addColorStop(1, p.color(280, 60, 40, 0).toString());
      ctx.fillStyle = radial;
      ctx.fillRect(0, 0, p.width, p.height);
      p.pop();
    };

    p.draw = () => {
      const { params, audioLevel } = getState();
      const time = p.millis() * 0.001;
      const easedAudio = p.lerp(0, audioLevel, 0.7);

      p.clear();
      drawAtmosphere(time, params.depth, params.colorDrift);
      drawRibbons(time, Math.floor(params.ribbonCount), params.waveStrength, params.colorDrift, params.depth, easedAudio);
      updateParticles(time, params.particleShimmer, params.depth, easedAudio);

      p.push();
      p.noStroke();
      p.fill(0, 0, 0, 0.15);
      p.rect(0, 0, p.width, p.height);
      p.pop();
    };
  },
});

const createPerformanceLab = (): VisualPreset => ({
  id: 'performance-lab',
  name: 'Holographic Performance Lab',
  description:
    'Motor modular en tiempo real con partículas volumétricas, glitch, ASCII reactivo, feedback y distorsión tipo VHS.',
  parameters: [
    {
      key: 'intensity',
      label: 'Brillo / Bloom',
      min: 0.3,
      max: 1.8,
      defaultValue: 1,
      step: 0.01,
      description: 'Control global de glow, halos y mezcla aditiva.',
    },
    {
      key: 'noiseFlow',
      label: 'Flujo / Turbulencia',
      min: 0,
      max: 1.4,
      defaultValue: 0.65,
      step: 0.01,
      description: 'Velocidad de los campos de ruido que mueven partículas y cintas.',
    },
    {
      key: 'particleCount',
      label: 'Cantidad de partículas',
      min: 0.2,
      max: 1.6,
      defaultValue: 1,
      step: 0.05,
      description: 'Micro partículas, polvo y destellos volumétricos.',
    },
    {
      key: 'ribbonLayers',
      label: 'Capas de cintas',
      min: 2,
      max: 8,
      defaultValue: 5,
      step: 1,
      description: 'Cintas fluidas con parallax y gradientes holográficos.',
    },
    {
      key: 'holoLines',
      label: 'Líneas holográficas',
      min: 0,
      max: 1,
      defaultValue: 0.7,
      step: 0.01,
      description: 'Estructuras lineales y clusters neon.',
    },
    {
      key: 'asciiDensity',
      label: 'Densidad ASCII',
      min: 0.2,
      max: 1.4,
      defaultValue: 0.6,
      step: 0.02,
      description: 'Cantidad de caracteres y contraste del conversor.',
    },
    {
      key: 'pixelSize',
      label: 'Pixelación / VHS',
      min: 1,
      max: 22,
      defaultValue: 6,
      step: 1,
      description: 'Pixel glitch, distorsión VHS y aberración cromática.',
    },
    {
      key: 'feedback',
      label: 'Feedback / Trails',
      min: 0,
      max: 1,
      defaultValue: 0.35,
      step: 0.01,
      description: 'Cantidad de eco visual, motion blur y retroalimentación.',
    },
    {
      key: 'glitch',
      label: 'Glitch bursts',
      min: 0,
      max: 1,
      defaultValue: 0.25,
      step: 0.01,
      description: 'Distorsión cromática, tearing y estallidos.',
    },
    {
      key: 'fog',
      label: 'Niebla volumétrica',
      min: 0,
      max: 1,
      defaultValue: 0.55,
      step: 0.01,
      description: 'Capas de atmósfera y profundidad.',
    },
    {
      key: 'noteReactive',
      label: 'Reactivo a nota MIDI',
      min: 0,
      max: 1,
      defaultValue: 0.2,
      step: 0.01,
      description: 'Impulso aplicado a explosiones, ASCII y glitch cuando entra una nota.',
    },
  ],
  init: (p: p5, getState: () => SketchState) => {
    let base: p5.Graphics;
    let feedback: p5.Graphics;
    let asciiLayer: p5.Graphics;
    const particles: FlowParticle[] = [];

    const spawnParticle = (w: number, h: number) => ({
      pos: p.createVector(p.random(w), p.random(h)),
      vel: p.createVector(),
      life: p.random(80, 260),
    });

    const seed = (w: number, h: number, density: number) => {
      particles.length = 0;
      const count = Math.floor(700 * density);
      for (let i = 0; i < count; i += 1) particles.push(spawnParticle(w, h));
    };

    p.setup = () => {
      p.createCanvas(p.windowWidth, p.windowHeight);
      p.colorMode(p.HSB, 360, 100, 100, 1);
      base = p.createGraphics(p.width, p.height);
      feedback = p.createGraphics(p.width, p.height);
      asciiLayer = p.createGraphics(p.width, p.height);
      base.colorMode(p.HSB, 360, 100, 100, 1);
      feedback.colorMode(p.HSB, 360, 100, 100, 1);
      asciiLayer.colorMode(p.HSB, 360, 100, 100, 1);
      seed(p.width, p.height, 1);
    };

    p.windowResized = () => {
      p.resizeCanvas(p.windowWidth, p.windowHeight);
      base.resizeCanvas(p.width, p.height);
      feedback.resizeCanvas(p.width, p.height);
      asciiLayer.resizeCanvas(p.width, p.height);
      seed(p.width, p.height, getState().params.particleCount);
    };

    const drawAtmosphere = (time: number, fog: number, intensity: number, hueShift: number, aspectPush: number) => {
      const ctx = base.drawingContext as CanvasRenderingContext2D;
      const grad = ctx.createRadialGradient(
        base.width * 0.3,
        base.height * (0.4 + aspectPush * 0.05),
        base.width * 0.1,
        base.width * 0.55,
        base.height * 0.55,
        base.width,
      );
      grad.addColorStop(0, p.color((190 + hueShift * 90) % 360, 90, 20 + 40 * intensity, 0.45).toString());
      grad.addColorStop(0.6, p.color((320 + hueShift * 80) % 360, 90, 70, 0.35).toString());
      grad.addColorStop(1, p.color((140 + hueShift * 60) % 360, 70, 35, 0.1).toString());
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, base.width, base.height);

      base.push();
      base.blendMode(p.SCREEN);
      for (let i = 0; i < 4; i += 1) {
        const radius = base.width * (0.25 + i * 0.12);
        const cx = base.width * (0.2 + i * 0.18 + p.sin(time * 0.12 + i) * 0.04);
        const cy = base.height * (0.35 + i * 0.08 + p.cos(time * 0.1 + i) * 0.05 + aspectPush * 0.12);
        const g = ctx.createRadialGradient(cx, cy, radius * 0.1, cx, cy, radius);
        g.addColorStop(0, p.color((200 + i * 40 + hueShift * 70) % 360, 80, 90, 0.16 * fog).toString());
        g.addColorStop(1, p.color((260 + i * 55 + hueShift * 120) % 360, 70, 20, 0).toString());
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, base.width, base.height);
      }
      base.pop();
    };

    const drawRibbons = (
      time: number,
      layers: number,
      flow: number,
      intensity: number,
      audio: number,
      bands: { bass: number; mid: number; treble: number },
      aspectPush: number,
    ) => {
      base.push();
      base.noFill();
      base.blendMode(p.SCREEN);
      for (let i = 0; i < layers; i += 1) {
        const t = i / Math.max(1, layers - 1);
        const hue = (210 + t * 140 + bands.treble * 60) % 360;
        base.stroke(hue, 80, 100, 0.35 + 0.2 * intensity * (1 - t));
        base.strokeWeight(2.4 - t * 1.4 + bands.mid * 1.2);
        base.beginShape();
        for (let x = -40; x <= base.width + 40; x += 26) {
          const n = p.noise(x * 0.002 + i * 0.1, time * 0.4 + flow * 0.8, i * 0.2) - 0.5;
          const y =
            base.height * (0.4 + 0.2 * p.sin(time * 0.2 + i) + aspectPush * 0.2) +
            n * 280 * (0.4 + flow) +
            p.sin(time * 1.2 + x * 0.004 + i) * 60 * (0.5 + flow) -
            audio * 140 * (0.3 + t);
          base.curveVertex(x, y);
        }
        base.endShape();
      }
      base.pop();
    };

    const updateParticles = (time: number, density: number, flow: number, intensity: number, bands: any, pulse: number) => {
      const target = Math.floor(400 + 600 * density);
      while (particles.length < target) particles.push(spawnParticle(base.width, base.height));
      while (particles.length > target) particles.pop();

      base.push();
      base.blendMode(p.ADD);
      for (const pt of particles) {
        const angle = p.noise(pt.pos.x * 0.0015, pt.pos.y * 0.0015, time * 0.6) * p.TWO_PI * 2;
        const speed = 0.6 + flow * 2 + bands.mid * 1.2 + pulse * 1.5;
        pt.vel.set(p.cos(angle) * speed, p.sin(angle) * speed);
        pt.pos.add(pt.vel);
        pt.life -= 1;
        if (pt.pos.x < 0) pt.pos.x = base.width;
        if (pt.pos.x > base.width) pt.pos.x = 0;
        if (pt.pos.y < 0) pt.pos.y = base.height;
        if (pt.pos.y > base.height) pt.pos.y = 0;
        if (pt.life < 0) {
          pt.life = p.random(120, 260);
        }

        const hue = (p.noise(pt.pos.x * 0.003, time * 0.2) * 160 + 160 + bands.treble * 80) % 360;
        base.fill(hue, 80, 100, 0.25 * intensity + 0.2 * bands.bass + pulse * 0.4);
        base.noStroke();
        base.circle(pt.pos.x, pt.pos.y, 1.5 + density * 2.8 + pulse * 5);
      }
      base.pop();
    };

    const drawHoloLines = (time: number, amount: number, intensity: number, bands: any) => {
      base.push();
      base.strokeWeight(1.5 + bands.treble * 1.3);
      base.stroke((260 + time * 40 + bands.mid * 60) % 360, 90, 90, 0.3 * amount * intensity);
      for (let i = 0; i < 14; i += 1) {
        const y = (i / 14) * base.height + p.sin(time * 0.6 + i) * 20;
        base.line(0, y, base.width, y + p.sin(time * 0.8 + i) * 40 * amount);
      }
      base.pop();
    };

    const drawAscii = (density: number, pulse: number, bands: any) => {
      asciiLayer.clear();
      asciiLayer.push();
      asciiLayer.fill(180 + bands.mid * 80, 30, 100, 0.2 + pulse * 0.5);
      asciiLayer.noStroke();
      const grid = Math.max(6, Math.floor(22 - density * 12));
      asciiLayer.textSize(grid * (0.9 + bands.treble * 0.4 + pulse * 0.6));
      asciiLayer.textAlign(p.CENTER, p.CENTER);
      const chars = '░▒▓/\\*+x=<>#%@';
      for (let y = 0; y < asciiLayer.height; y += grid * 2) {
        for (let x = 0; x < asciiLayer.width; x += grid * 1.6) {
          const n = p.noise(x * 0.01, y * 0.01, p.millis() * 0.0008 + pulse * 2 + bands.bass * 0.5);
          const idx = Math.floor(n * chars.length) % chars.length;
          asciiLayer.text(chars[idx], x, y + Math.sin(n * p.TWO_PI) * grid * 0.5 * pulse);
        }
      }
      asciiLayer.pop();
    };

    const drawGlitch = (glitch: number, pixelSize: number, pulse: number, beat: number) => {
      const ctx = (p.drawingContext as CanvasRenderingContext2D)!;
      const shift = 6 + pixelSize * 0.8 + pulse * 8 + beat * 10 * glitch;
      ctx.globalCompositeOperation = 'lighter';
      p.tint(190, 80, 100, 0.7);
      p.image(base, shift, 0);
      p.tint(320, 80, 100, 0.6);
      p.image(base, -shift, 0);
      p.noTint();

      if (glitch + pulse + beat > 0.2) {
        const slices = 8;
        for (let i = 0; i < slices; i += 1) {
          const sy = (i / slices) * p.height;
          const sh = (p.height / slices) * (0.8 + Math.random() * 0.4);
          const dx = (Math.random() - 0.5) * shift * 1.4;
          p.copy(base, 0, sy, p.width, sh, dx, sy + Math.random() * 6 - 3, p.width, sh);
        }
      }
    };

    const applyFeedback = (amount: number) => {
      feedback.push();
      feedback.clear();
      const snap = p.get();
      feedback.image(snap, 0, 0);
      feedback.tint(0, 0, 100, amount * 0.65);
      feedback.pop();
      p.push();
      p.tint(0, 0, 100, amount * 0.8);
      p.image(feedback, 0, 0, p.width, p.height);
      p.pop();
    };

    const drawPixelation = (pixelSize: number, glitch: number) => {
      const step = Math.max(1, Math.floor(pixelSize));
      p.push();
      p.noSmooth();
      const w = Math.max(1, Math.floor(p.width / step));
      const h = Math.max(1, Math.floor(p.height / step));
      const snapshot = p.get();
      p.image(snapshot, 0, 0, w, h);
      const pixelated = p.get(0, 0, w, h);
      p.image(pixelated, 0, 0, p.width, p.height);
      p.pop();

      if (glitch > 0.15) {
        p.push();
        p.blendMode(p.DIFFERENCE);
        p.stroke(200, 80, 100, 0.3 * glitch);
        for (let i = 0; i < 16; i += 1) {
          const y = Math.random() * p.height;
          p.line(0, y, p.width, y + Math.sin(i) * 6 * glitch);
        }
        p.pop();
      }
    };

    p.draw = () => {
      const { params, audioLevel, audioBands, beat, midiPulse, orientation } = getState();
      const time = p.millis() * 0.001;
      const aspectPush = orientation === 'portrait' ? 0.3 : 0;
      const pulse = Math.max(midiPulse, beat * 0.6, params.noteReactive);

      base.clear();
      drawAtmosphere(time, params.fog, params.intensity, params.glitch, aspectPush);
      drawRibbons(time, Math.floor(params.ribbonLayers), params.noiseFlow, params.intensity, audioLevel, audioBands, aspectPush);
      updateParticles(time, params.particleCount, params.noiseFlow, params.intensity, audioBands, pulse);
      drawHoloLines(time, params.holoLines, params.intensity, audioBands);
      drawAscii(params.asciiDensity + pulse * 0.4, pulse, audioBands);

      p.clear();
      p.blendMode(p.BLEND);
      p.image(base, 0, 0, p.width, p.height);
      p.blendMode(p.ADD);
      p.image(asciiLayer, 0, 0, p.width, p.height);

      drawGlitch(params.glitch, params.pixelSize, pulse, beat);
      drawPixelation(params.pixelSize, params.glitch + pulse * 0.3);
      applyFeedback(params.feedback * (0.8 + audioLevel * 0.6));

      p.push();
      p.noStroke();
      p.fill(0, 0, 0, 0.08);
      p.rect(0, 0, p.width, p.height);
      p.pop();
    };
  },
});

export const presets: VisualPreset[] = [createPerformanceLab(), createNebulaBloom(), createChromaticCurrents()];
