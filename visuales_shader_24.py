#!/usr/bin/env python3
"""
Preset 24: Fractal Tunnel - Box Journey con Bassline
Category: Fractal/Tunnel/Path Following + MIDI Reactive
Basat en shader de túnel fractal amb box central flotant

Característiques:
- Túnel fractal amb path dinàmic
- Box central reactiu que flota pel túnel
- BASSLINE (Canal 1): Controla velocitat del viatge i intensitat fractals
- Kick: Pulsa el box central
- Hat: Glitch/distorsió del path
- Tom1: Intensitat dels fractals
- Tom2: Rotació del box
"""

from __future__ import division
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL import shaders
import mido
from numpy import array

KICK_NOTE, CLOSEHAT_NOTE, TOM1_NOTE, TOM2_NOTE = 60, 62, 64, 65

VERTEX_SHADER = "#version 330 core\nlayout(location = 0) in vec3 vPos;\nvoid main() { gl_Position = vec4(vPos, 1.0); }"

FRAGMENT_SHADER = """
#version 330 core
#define fragCoord gl_FragCoord.xy
uniform float iTime;
uniform vec2  iResolution;
uniform float iKickPulse, iHatGlitch, iTom1Fractal, iTom2Spin;
uniform float iBassNote;  // Nota del bassline (normalizada 0-1)
uniform float iBassPulse; // Intensidad de la nota
out vec4 fragColor;

float det = 0.001, t, boxhit;
vec3 adv, boxp;

float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

mat2 rot(float a) {
    float s = sin(a), c = cos(a);
    return mat2(c, s, -s, c);
}

vec3 path(float t) {
    // Bassline modula la amplitud del path (más nota = más movimiento)
    float pathAmp = 10.0 + iBassNote * iBassPulse * 15.0;
    vec3 p = vec3(vec2(sin(t * 0.1), cos(t * 0.05)) * pathAmp, t);
    p.x += smoothstep(0.0, 0.5, abs(0.5 - fract(t * 0.02))) * pathAmp;

    // Hat glitch distorsiona el path
    if(iHatGlitch > 0.1) {
        p.xy += vec2(sin(t * 20.0), cos(t * 15.0)) * iHatGlitch * 3.0;
    }

    return p;
}

float fractal(vec2 p) {
    p = abs(5.0 - mod(p * 0.2, 10.0)) - 5.0;
    float ot = 1000.0;

    // Tom1 controla intensidad de los fractales
    float fractalIntensity = 7.0 + iTom1Fractal * 3.0;

    for (int i = 0; i < 7; i++) {
        p = abs(p) / clamp(p.x * p.y, 0.25, 2.0) - 1.0;
        if (i > 0) {
            float timeOffset = t * 0.05 * (1.0 + iBassNote * iBassPulse * 2.0);
            ot = min(ot, abs(p.x) + 0.7 * fract(abs(p.y) * 0.05 + timeOffset + float(i) * 0.3));
        }
    }
    ot = exp(-fractalIntensity * ot);
    return ot;
}

float box(vec3 p, vec3 l) {
    vec3 c = abs(p) - l;
    return length(max(vec3(0.0), c)) + min(0.0, max(c.x, max(c.y, c.z)));
}

float de(vec3 p) {
    boxhit = 0.0;
    vec3 p2 = p - adv;

    // Rotaciones del box moduladas por Tom2 y bassline
    float rotSpeed = 1.0 + iTom2Spin * 2.0 + iBassNote * iBassPulse;
    p2.xz *= rot(t * 0.2 * rotSpeed);
    p2.xy *= rot(t * 0.1 * rotSpeed);
    p2.yz *= rot(t * 0.15 * rotSpeed);

    // Kick pulsa el tamaño del box
    float boxSize = 1.0 + iKickPulse * 0.5;
    float b = box(p2, vec3(boxSize));

    p.xy -= path(p.z).xy;
    float s = sign(p.y);
    p.y = -abs(p.y) - 3.0;
    p.z = mod(p.z, 20.0) - 10.0;

    for (int i = 0; i < 5; i++) {
        p = abs(p) - 1.0;
        p.xz *= rot(radians(s * -45.0));
        p.yz *= rot(radians(90.0));
    }

    float f = -box(p, vec3(5.0, 5.0, 10.0));
    float d = min(f, b);
    if (d == b) boxp = p2, boxhit = 1.0;
    return d * 0.7;
}

vec3 march(vec3 from, vec3 dir) {
    vec3 p, g = vec3(0.0);
    float d, td = 0.0;

    for (int i = 0; i < 80; i++) {
        p = from + td * dir;
        d = de(p) * (1.0 - hash(gl_FragCoord.xy + t) * 0.3);
        if (d < det && boxhit < 0.5) break;
        td += max(det, abs(d));

        float f = fractal(p.xy) + fractal(p.xz) + fractal(p.yz);
        float b = fractal(boxp.xy) + fractal(boxp.xz) + fractal(boxp.yz);

        // Color del túnel fractal - tonos cian/azules
        vec3 colf = vec3(f * 0.5, f * 0.8, f);

        // Color del box - amarillo/naranja con kick
        vec3 colb = vec3(b + 0.1 + iKickPulse * 0.3, b * b + 0.05, 0.0);

        // Bassline aumenta el brillo general
        float brightnessBoost = 1.0 + iBassPulse * iBassNote * 0.5;

        g += colf / (3.0 + d * d * 2.0) * exp(-0.0015 * td * td) * step(5.0, td) / 2.0 * (1.0 - boxhit) * brightnessBoost;
        g += colb / (10.0 + d * d * 20.0) * boxhit * 0.5 * brightnessBoost;
    }
    return g;
}

mat3 lookat(vec3 dir, vec3 up) {
    dir = normalize(dir);
    vec3 rt = normalize(cross(dir, normalize(up)));
    return mat3(rt, cross(rt, dir), dir);
}

void main() {
    vec2 uv = (fragCoord - iResolution.xy * 0.5) / iResolution.y;

    // Bassline controla la velocidad del viaje
    float speedMultiplier = 7.0 + iBassNote * iBassPulse * 10.0;
    t = iTime * speedMultiplier;

    vec3 from = path(t);
    adv = path(t + 6.0 + sin(t * 0.1) * 3.0);

    vec3 dir = normalize(vec3(uv, 0.7));
    dir = lookat(adv - from, vec3(0.0, 1.0, 0.0)) * dir;

    vec3 col = march(from, dir);

    // Tone mapping & gamma
    col = col / (col + 1.0);
    col = pow(col, vec3(0.4545));

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
    fragColor = vec4(pattern, pattern * 1.2, pattern * 1.5, 1.0);
}
"""

class ShaderVisualEngine:
    def __init__(self):
        pygame.init()
        self.target_width, self.target_height = 1080, 1920
        self.target_aspect = self.target_width / self.target_height
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)
        self.screen = pygame.display.set_mode((int(900 * self.target_aspect), 900), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption('Preset 24: Fractal Tunnel [9:16]')

        vs = shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER)
        fs = shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vs, fs)
        self.uni_time = glGetUniformLocation(self.shader, 'iTime')
        self.uni_resolution = glGetUniformLocation(self.shader, 'iResolution')
        self.uni_kick = glGetUniformLocation(self.shader, 'iKickPulse')
        self.uni_hat = glGetUniformLocation(self.shader, 'iHatGlitch')
        self.uni_tom1 = glGetUniformLocation(self.shader, 'iTom1Fractal')
        self.uni_tom2 = glGetUniformLocation(self.shader, 'iTom2Spin')
        self.uni_bass_note = glGetUniformLocation(self.shader, 'iBassNote')
        self.uni_bass_pulse = glGetUniformLocation(self.shader, 'iBassPulse')

        # Shader franjas
        fvs = shaders.compileShader(FRANJA_VERTEX, GL_VERTEX_SHADER)
        ffs = shaders.compileShader(FRANJA_FRAGMENT, GL_FRAGMENT_SHADER)
        self.franja_shader = shaders.compileProgram(fvs, ffs)
        self.franja_resolution = glGetUniformLocation(self.franja_shader, 'iResolution')

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

        self.kick_pulse = self.kick_target = self.hat_glitch = self.tom1_fractal = self.tom2_spin = 0.0
        self.bass_note = 0.0  # Nota actual del bassline (0-1)
        self.bass_pulse = 0.0  # Intensidad de la nota
        self.midi_input = self._connect_midi()
        self.clock = pygame.time.Clock()
        self.start_time = pygame.time.get_ticks()

    def _connect_midi(self):
        try:
            for port in mido.get_input_names():
                if 'CIRCUIT' in port.upper() or 'TRACKS' in port.upper():
                    return mido.open_input(port)
            print("⚠️  Demo mode (K/H/T/Y/B)")
        except: pass
        return None

    def process_midi(self):
        if self.midi_input:
            for msg in self.midi_input.iter_pending():
                if msg.type == 'note_on' and msg.velocity > 0:
                    v = msg.velocity / 127.0

                    # Canal 1: Bassline (controla velocidad y brillo)
                    if msg.channel == 0:  # Canal 1 en mido (0-indexed)
                        # Normalizar nota (36-84 -> 0-1)
                        note_normalized = max(0.0, min(1.0, (msg.note - 36) / 48.0))
                        self.bass_note = note_normalized
                        self.bass_pulse = min(1.0, self.bass_pulse + v * 0.5)

                    # Notas de batería (cualquier canal)
                    if msg.note == KICK_NOTE: self.kick_target = min(1.0, self.kick_target + v * 0.7)
                    elif msg.note == CLOSEHAT_NOTE: self.hat_glitch = min(1.0, self.hat_glitch + v * 0.8)
                    elif msg.note == TOM1_NOTE: self.tom1_fractal = min(1.0, self.tom1_fractal + v * 0.6)
                    elif msg.note == TOM2_NOTE: self.tom2_spin = min(1.0, self.tom2_spin + v * 0.7)

    def update_params(self):
        self.kick_pulse += (self.kick_target - self.kick_pulse) * 0.15
        self.kick_target *= 0.92
        self.hat_glitch *= 0.88
        self.tom1_fractal *= 0.90
        self.tom2_spin *= 0.93
        self.bass_pulse *= 0.80  # Decay rápido para respuesta dinámica

    def calculate_viewport(self, w, h):
        a = w / h
        if a > self.target_aspect:
            vh = h; vw = int(vh * self.target_aspect); return (w - vw) // 2, 0, vw, vh
        vw = w; vh = int(vw / self.target_aspect); return 0, (h - vh) // 2, vw, vh

    def render(self):
        w, h = self.screen.get_size()
        vx, vy, vw, vh = self.calculate_viewport(w, h)

        glViewport(0, 0, w, h); glClearColor(0, 0, 0, 1); glClear(GL_COLOR_BUFFER_BIT)

        # Dibujar franjas con gradiente azul
        if vx > 0:
            glUseProgram(self.franja_shader)
            glUniform2f(self.franja_resolution, float(w), float(h))
            glBindVertexArray(self.franja_vao)
            glViewport(0, 0, vx, h); glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
            glViewport(vx + vw, 0, w - (vx + vw), h); glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

        # Dibujar shader principal
        glViewport(vx, vy, vw, vh)
        glUseProgram(self.shader)
        glUniform1f(self.uni_time, (pygame.time.get_ticks() - self.start_time) / 1000.0)
        glUniform2f(self.uni_resolution, float(vw), float(vh))
        glUniform1f(self.uni_kick, self.kick_pulse)
        glUniform1f(self.uni_hat, self.hat_glitch)
        glUniform1f(self.uni_tom1, self.tom1_fractal)
        glUniform1f(self.uni_tom2, self.tom2_spin)
        glUniform1f(self.uni_bass_note, self.bass_note)
        glUniform1f(self.uni_bass_pulse, self.bass_pulse)
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
                    if event.key == K_k: self.kick_target = min(1.0, self.kick_target + 0.7)
                    elif event.key == K_h: self.hat_glitch = min(1.0, self.hat_glitch + 0.8)
                    elif event.key == K_t: self.tom1_fractal = min(1.0, self.tom1_fractal + 0.6)
                    elif event.key == K_y: self.tom2_spin = min(1.0, self.tom2_spin + 0.7)
                    elif event.key == K_b:
                        self.bass_note = 0.5
                        self.bass_pulse = min(1.0, self.bass_pulse + 0.7)
            self.process_midi(); self.update_params(); self.render(); self.clock.tick(60)
        if self.midi_input: self.midi_input.close()
        pygame.quit()

if __name__ == '__main__': ShaderVisualEngine().run()
