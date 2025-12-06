#!/usr/bin/env python3
"""
Preset 30: Cosmic Swirl VFX - Espirales con Glitch
Category: Audio Reactive / Generative / Particle Systems / VFX
200 partículas en movimiento espiral con cambios de forma por MIDI kick
y efectos glitch VHS reactivos a frecuencias altas.

Características:
- 200 partículas en movimiento espiral dinámico
- MIDI Kick: Cambios aleatorios de forma (4 formas diferentes)
- Frecuencias altas: Glitch VHS, RGB split, distorsión
- Colores vibrantes y ciclos suaves
- Audio reactivo sutil
- Optimizado para rendimiento
"""

from __future__ import division
import pygame
import pygame._sdl2.audio as sdl_audio
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL import shaders
import mido
import numpy as np
from numpy import array

SAMPLES = 1024
KICK_NOTE, CLOSEHAT_NOTE, TOM1_NOTE, TOM2_NOTE = 60, 62, 64, 65

VERTEX_SHADER = "#version 330 core\nlayout(location = 0) in vec3 vPos;\nvoid main() { gl_Position = vec4(vPos, 1.0); }"

FRAGMENT_SHADER = """
#version 330 core
#define fragCoord gl_FragCoord.xy
uniform float iTime;
uniform vec2  iResolution;
uniform float iBass;
uniform float iMid;
uniform float iVolume;
uniform float iKick;
uniform float iHiFreq;  // Frecuencias altas para glitch
uniform float iFormMode;  // Modo de forma actual (0-3)
out vec4 fragColor;

#define PI 3.14159265359
#define NUM_PARTICLES 200.0

// Hash functions
float hash(float p) {
    p = fract(p * 0.1031);
    p *= p + 33.33;
    p *= p + p;
    return fract(p);
}

vec2 hash2(float p) {
    vec3 p3 = fract(vec3(p) * vec3(0.1031, 0.1030, 0.0973));
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.xx + p3.yz) * p3.zy);
}

// Diferentes formas de partículas (cambian con kick)
vec2 getParticlePos(float id, float t, float formMode) {
    vec2 seed = hash2(id);
    float timeOffset = hash(id + 100.0) * 1000.0;
    float localTime = t * 0.25 + timeOffset;  // Más velocidad

    vec2 pos;

    // Forma 0: Espiral centrífuga
    if(formMode < 0.5) {
        float angle = localTime + id * 0.4;
        float radius = 0.3 + sin(localTime * 0.4 + id) * 0.4;
        pos.x = cos(angle) * radius + sin(localTime * 0.3 + id * 2.0) * 0.25;
        pos.y = sin(angle) * radius * 1.5 + cos(localTime * 0.2 + id * 3.0) * 0.2;
    }
    // Forma 1: Doble espiral
    else if(formMode < 1.5) {
        float angle = localTime * (1.0 + hash(id + 50.0)) + id * 0.3;
        float radius = 0.5 + sin(localTime * 0.5 + id * 1.5) * 0.3;
        float side = step(0.5, hash(id + 20.0)) * 2.0 - 1.0;
        pos.x = cos(angle) * radius * side + sin(localTime * 0.25) * 0.15;
        pos.y = sin(angle) * radius * 1.6 + cos(localTime * 0.3 + id) * 0.15;
    }
    // Forma 2: Ondas horizontales
    else if(formMode < 2.5) {
        float wave = sin(id * 0.5 + localTime) * 0.7;
        float yPos = ((id / NUM_PARTICLES) - 0.5) * 2.5;
        pos.x = wave + sin(localTime * 0.4 + id * 2.0) * 0.2;
        pos.y = yPos + cos(localTime * 0.3 + id) * 0.1;
    }
    // Forma 3: Vórtice caótico
    else {
        float angle = localTime * 2.0 + id * 0.2;
        float radius = 0.4 + sin(localTime * 0.6 + id * 2.0) * 0.4;
        float chaos = sin(localTime * 0.8 + id * 3.0) * 0.3;
        pos.x = cos(angle) * radius + chaos;
        pos.y = sin(angle) * radius * 1.4 + sin(localTime + id * 4.0) * 0.25;
    }

    // Wrap en viewport vertical
    pos.x = fract(pos.x * 0.5 + 0.5) * 2.0 - 1.0;
    pos.y = fract(pos.y * 0.3 + 0.5) * 2.6 - 1.3;

    // Influencia sutil del audio
    pos *= 1.0 + iBass * 0.03;

    return pos;
}

// Dibujar partícula
float drawParticle(vec2 uv, vec2 particlePos, float id) {
    float dist = length(uv - particlePos);
    float size = 0.012 + hash(id + 50.0) * 0.008;
    size += iVolume * 0.006;

    float particle = smoothstep(size, 0.0, dist);
    float glowSize = size * 2.5;
    float glow = smoothstep(glowSize, 0.0, dist) * 0.25;

    return particle + glow;
}

// Efectos VHS Glitch
vec2 applyGlitch(vec2 uv, float intensity) {
    vec2 glitchUV = uv;

    if(intensity > 0.15) {
        // Scanline displacement
        float scanline = floor(uv.y * iResolution.y / 3.0);
        float glitchOffset = (hash(scanline + iTime * 10.0) - 0.5) * intensity * 0.1;
        glitchUV.x += glitchOffset;

        // Vertical jump
        float jumpChance = hash(floor(iTime * 30.0));
        if(jumpChance > 0.97) {
            glitchUV.y += (hash(iTime * 100.0) - 0.5) * intensity * 0.2;
        }

        // Block corruption
        vec2 blockID = floor(glitchUV * 8.0);
        float blockHash = hash(blockID.x + blockID.y * 57.0 + iTime * 5.0);
        if(blockHash > 0.98 - intensity * 0.1) {
            glitchUV += (hash2(blockHash) - 0.5) * intensity * 0.15;
        }
    }

    return glitchUV;
}

void main() {
    vec2 baseUV = (fragCoord - 0.5 * iResolution.xy) / iResolution.y;

    // Aplicar glitch VHS si hay frecuencias altas
    vec2 uv = applyGlitch(baseUV, iHiFreq);

    vec3 col = vec3(0.0);
    float t = iTime;

    // RGB Split con glitch
    float rgbSplit = iHiFreq * 0.02;
    vec3 colR = vec3(0.0);
    vec3 colG = vec3(0.0);
    vec3 colB = vec3(0.0);

    // Dibujar partículas con RGB split si hay glitch
    for(float i = 0.0; i < NUM_PARTICLES; i++) {
        vec2 pos = getParticlePos(i, t, iFormMode);

        // Color de partícula
        float hue = i / NUM_PARTICLES + t * 0.08 + iBass * 0.05;
        vec3 particleColor = 0.5 + 0.5 * cos(hue * 6.28 + vec3(0.0, 2.1, 4.2));
        particleColor *= (0.7 + iVolume * 0.25);

        // Si hay glitch, separar canales RGB
        if(iHiFreq > 0.2) {
            vec2 uvR = uv + vec2(-rgbSplit, 0.0);
            vec2 uvG = uv;
            vec2 uvB = uv + vec2(rgbSplit, 0.0);

            float pR = drawParticle(uvR, pos, i);
            float pG = drawParticle(uvG, pos, i);
            float pB = drawParticle(uvB, pos, i);

            colR += particleColor * pR * vec3(1.0, 0.0, 0.0);
            colG += particleColor * pG * vec3(0.0, 1.0, 0.0);
            colB += particleColor * pB * vec3(0.0, 0.0, 1.0);
        } else {
            float p = drawParticle(uv, pos, i);
            col += particleColor * p;
        }

        // Conexiones entre partículas (optimizado)
        if(iMid > 0.15 && i < NUM_PARTICLES - 1.0) {
            for(float j = i + 1.0; j < min(i + 2.0, NUM_PARTICLES); j++) {
                vec2 pos2 = getParticlePos(j, t, iFormMode);
                float dist = length(pos - pos2);

                if(dist < 0.3) {
                    vec2 pa = uv - pos;
                    vec2 ba = pos2 - pos;
                    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
                    float lineDist = length(pa - ba * h);

                    float lineThickness = 0.001;
                    float line = smoothstep(lineThickness, 0.0, lineDist);

                    vec3 color2 = 0.5 + 0.5 * cos((j / NUM_PARTICLES + t * 0.08) * 6.28 + vec3(0.0, 2.1, 4.2));
                    vec3 lineColor = mix(particleColor, color2, 0.5);

                    float fade = 1.0 - dist / 0.3;
                    col += lineColor * line * fade * 0.15;
                }
            }
        }
    }

    // Combinar canales RGB si hay glitch
    if(iHiFreq > 0.2) {
        col = colR + colG + colB;
    }

    // Glow ambiental
    float centerDist = length(uv);
    float ambient = 1.0 / (1.0 + centerDist * 3.0);
    col += vec3(0.02, 0.04, 0.06) * ambient * (0.05 + iVolume * 0.03);

    // Glitch color corruption
    if(iHiFreq > 0.4) {
        float corruption = hash(floor(uv.y * 20.0) + iTime * 15.0);
        if(corruption > 0.95) {
            col = 1.0 - col;  // Inversión de color
        }
    }

    // Chromatic noise
    if(iHiFreq > 0.3) {
        float noise = hash(dot(uv, vec2(12.9898, 78.233)) + iTime * 20.0);
        col += vec3(noise) * iHiFreq * 0.15;
    }

    // Tone mapping
    col = col / (col + 1.0);

    // Gamma
    col = pow(col, vec3(0.4545));

    // Vignette
    float vignette = 1.0 - length(uv) * 0.25;
    col *= vignette;

    fragColor = vec4(col, 1.0);
}
"""

FRANJA_VERTEX = "#version 330 core\nlayout(location = 0) in vec2 vPos;\nvoid main() { gl_Position = vec4(vPos, 0.0, 1.0); }"
FRANJA_FRAGMENT = """
#version 330 core
out vec4 fragColor;
uniform vec2 iResolution;
void main() {
    float line = mod(gl_FragCoord.x + gl_FragCoord.y, 40.0);
    float pattern = step(line, 2.0) * 0.08;
    fragColor = vec4(pattern * 0.8, pattern * 1.2, pattern * 1.5, 1.0);
}
"""

class ShaderVisualEngine:
    def __init__(self):
        pygame.init()
        self.target_width, self.target_height = 1080, 1920
        self.target_aspect = self.target_width / self.target_height
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)
        self.screen = pygame.display.set_mode((int(900 * self.target_aspect), 900), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption('Preset 30: Cosmic Swirl VFX [9:16]')

        # Shader principal
        vs = shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER)
        fs = shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vs, fs)
        self.uni_time = glGetUniformLocation(self.shader, 'iTime')
        self.uni_resolution = glGetUniformLocation(self.shader, 'iResolution')
        self.uni_bass = glGetUniformLocation(self.shader, 'iBass')
        self.uni_mid = glGetUniformLocation(self.shader, 'iMid')
        self.uni_volume = glGetUniformLocation(self.shader, 'iVolume')
        self.uni_kick = glGetUniformLocation(self.shader, 'iKick')
        self.uni_hifreq = glGetUniformLocation(self.shader, 'iHiFreq')
        self.uni_formmode = glGetUniformLocation(self.shader, 'iFormMode')

        # Shader franjas
        fvs = shaders.compileShader(FRANJA_VERTEX, GL_VERTEX_SHADER)
        ffs = shaders.compileShader(FRANJA_FRAGMENT, GL_FRAGMENT_SHADER)
        self.franja_shader = shaders.compileProgram(fvs, ffs)
        self.franja_resolution = glGetUniformLocation(self.franja_shader, 'iResolution')

        # VAO principal
        verts = array([-1, -1, 0, 1, -1, 0, 1, 1, 0, -1, 1, 0], dtype='f')
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, verts, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

        # VAO franjas
        fverts = array([-1, -1, 1, -1, 1, 1, -1, 1], dtype='f')
        self.franja_vao = glGenVertexArrays(1)
        glBindVertexArray(self.franja_vao)
        fvbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, fvbo)
        glBufferData(GL_ARRAY_BUFFER, fverts, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)

        # Audio y MIDI setup
        self.audio_buffer = np.zeros(SAMPLES, dtype=np.float32)
        self.bass_smoothed = 0.0
        self.mid_smoothed = 0.0
        self.vol_smoothed = 0.0
        self.hifreq_smoothed = 0.0

        # MIDI
        self.kick_pulse = 0.0
        self.kick_target = 0.0
        self.form_mode = 0.0  # Modo de forma actual (0-3)

        self.setup_audio()
        self.midi_input = self._connect_midi()

        self.clock = pygame.time.Clock()
        self.start_time = pygame.time.get_ticks()

    def _connect_midi(self):
        try:
            for port in mido.get_input_names():
                if 'CIRCUIT' in port.upper() or 'TRACKS' in port.upper():
                    print(f"MIDI: {port}")
                    return mido.open_input(port)
            print("⚠️  Demo mode (K key = kick)")
        except Exception as e:
            print(f"MIDI error: {e}")
        return None

    def process_midi(self):
        if self.midi_input:
            for msg in self.midi_input.iter_pending():
                if msg.type == 'note_on' and msg.velocity > 0:
                    v = msg.velocity / 127.0
                    if msg.note == KICK_NOTE:
                        self.kick_target = 1.0
                        # Cambiar a forma aleatoria
                        import random
                        self.form_mode = float(random.randint(0, 3))
                        print(f"Kick! Nueva forma: {int(self.form_mode)}")

    def setup_audio(self):
        try:
            devices = sdl_audio.get_audio_device_names(True)
            target = next((d for d in devices if "Scarlett" in d), devices[0] if devices else None)
            if target:
                print(f"Audio: {target}")
                self.dev = sdl_audio.AudioDevice(
                    target, True, 44100, sdl_audio.AUDIO_F32, 1, 1024, 0, self.callback
                )
                self.dev.pause(0)
        except Exception as e:
            print("Error Audio:", e)

    def callback(self, dev, data):
        raw = np.frombuffer(data, dtype=np.float32)
        l = min(len(raw), SAMPLES)
        self.audio_buffer[:l] = raw[:l]

    def update_audio_analysis(self):
        rms = np.sqrt(np.mean(self.audio_buffer**2)) * 8.0
        self.vol_smoothed += (rms - self.vol_smoothed) * 0.08

        fft = np.abs(np.fft.rfft(self.audio_buffer))

        # Bajos
        bass = np.mean(fft[1:10]) * 0.6
        self.bass_smoothed += (bass - self.bass_smoothed) * 0.12

        # Medios
        mid = np.mean(fft[10:50]) * 0.4
        self.mid_smoothed += (mid - self.mid_smoothed) * 0.1

        # Frecuencias altas (para glitch)
        hifreq = np.mean(fft[50:150]) * 0.8
        self.hifreq_smoothed += (hifreq - self.hifreq_smoothed) * 0.15

    def update_params(self):
        # Decay del kick
        self.kick_pulse += (self.kick_target - self.kick_pulse) * 0.2
        self.kick_target *= 0.85

    def calculate_viewport(self, w, h):
        a = w / h
        if a > self.target_aspect:
            vh = h
            vw = int(vh * self.target_aspect)
            return (w - vw) // 2, 0, vw, vh
        vw = w
        vh = int(vw / self.target_aspect)
        return 0, (h - vh) // 2, vw, vh

    def render(self):
        self.update_audio_analysis()
        self.update_params()

        w, h = self.screen.get_size()
        vx, vy, vw, vh = self.calculate_viewport(w, h)

        glViewport(0, 0, w, h)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        # Dibujar franjas laterales
        if vx > 0:
            glUseProgram(self.franja_shader)
            glUniform2f(self.franja_resolution, float(w), float(h))
            glBindVertexArray(self.franja_vao)
            glViewport(0, 0, vx, h)
            glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
            glViewport(vx + vw, 0, w - (vx + vw), h)
            glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

        # Dibujar shader principal
        glViewport(vx, vy, vw, vh)
        glUseProgram(self.shader)
        glUniform1f(self.uni_time, (pygame.time.get_ticks() - self.start_time) / 1000.0)
        glUniform2f(self.uni_resolution, float(vw), float(vh))
        glUniform1f(self.uni_bass, self.bass_smoothed)
        glUniform1f(self.uni_mid, self.mid_smoothed)
        glUniform1f(self.uni_volume, self.vol_smoothed)
        glUniform1f(self.uni_kick, self.kick_pulse)
        glUniform1f(self.uni_hifreq, self.hifreq_smoothed)
        glUniform1f(self.uni_formmode, self.form_mode)
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    running = False
                elif event.type == KEYDOWN:
                    # Demo mode: K = kick
                    if event.key == K_k:
                        self.kick_target = 1.0
                        import random
                        self.form_mode = float(random.randint(0, 3))
                        print(f"Kick! Nueva forma: {int(self.form_mode)}")

            self.process_midi()
            self.render()
            self.clock.tick(60)

        if hasattr(self, 'dev') and self.dev:
            self.dev.close()
        if self.midi_input:
            self.midi_input.close()
        pygame.quit()

if __name__ == '__main__':
    ShaderVisualEngine().run()
