#!/usr/bin/env python3
"""
Preset 3: Menger Sponge - Fractal Cube Evolution
Category: Fractal/SDF Advanced
OPTIMIZADO: Raymarching 100→60, centrado, franjas con líneas
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
uniform float iKickPulse, iHatGlitch, iTom1Morph, iTom2Spin;
out vec4 fragColor;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

float noise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1,0)), f.x), mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), f.x), f.y);
}

// Menger Sponge SDF
float sdBox(vec3 p, vec3 b) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
}

float sdCross(vec3 p) {
    float da = sdBox(p, vec3(1000.0, 1.0, 1.0));
    float db = sdBox(p, vec3(1.0, 1000.0, 1.0));
    float dc = sdBox(p, vec3(1.0, 1.0, 1000.0));
    return min(da, min(db, dc));
}

float mengerSponge(vec3 p, int iterations) {
    float d = sdBox(p, vec3(1.0));
    float s = 1.0;

    for(int i = 0; i < iterations; i++) {
        vec3 a = mod(p * s, 2.0) - 1.0;
        s *= 3.0;
        vec3 r = abs(1.0 - 3.0 * abs(a));
        float c = sdCross(r) / s;
        d = max(d, -c);
    }
    return d;
}

float map(vec3 p) {
    // OPTIMIZADO: Iterations 2 + kick*2 (era 3)
    int iterations = 2 + int(iKickPulse * 2.0);
    float scale = 0.8 + iTom1Morph * 0.6;

    if (iHatGlitch > 0.1) {
        p.xy += vec2(noise(p.xy * 5.0 + iTime) - 0.5, noise(p.xy * 5.0 + iTime + 10.0) - 0.5) * iHatGlitch * 0.3;
    }
    return mengerSponge(p / scale, iterations) * scale;
}

vec3 calcNormal(vec3 p) {
    const float eps = 0.001;
    vec2 e = vec2(eps, 0.0);
    return normalize(vec3(map(p + e.xyy) - map(p - e.xyy), map(p + e.yxy) - map(p - e.yxy), map(p + e.yyx) - map(p - e.yyx)));
}

// OPTIMIZADO: 100→60 iterations
float raymarch(vec3 ro, vec3 rd) {
    float t = 0.0;
    for(int i = 0; i < 60; i++) {
        float d = map(ro + rd * t);
        if(d < 0.0005) break;
        t += d * 0.5;
        if(t > 20.0) break;
    }
    return t;
}

vec3 shade(vec3 p, vec3 rd, vec3 normal) {
    vec3 light1 = normalize(vec3(2.0, 3.0, 4.0));
    vec3 light2 = normalize(vec3(-2.0, 1.0, -1.0));
    float diff1 = max(dot(normal, light1), 0.0);
    float diff2 = max(dot(normal, light2), 0.0) * 0.5;
    vec3 h = normalize(light1 - rd);
    float spec = pow(max(dot(normal, h), 0.0), 32.0);
    vec3 baseColor = vec3(0.6 + iKickPulse * 0.4);
    return baseColor * (diff1 * 0.8 + diff2 * 0.4) + spec * 0.5;
}

void main() {
    vec2 uv = fragCoord / iResolution.xy;
    // CENTRADO: Formato vertical correcto
    vec2 p = (fragCoord - iResolution.xy * 0.5) / iResolution.x;

    vec3 ro = vec3(0.0, 0.0, 3.5);
    vec3 rd = normalize(vec3(p, -1.5));

    // Tom2 rotation
    float angle = iTime * 0.2 + iTom2Spin * 3.0;
    mat2 rot = mat2(cos(angle), -sin(angle), sin(angle), cos(angle));
    rd.xz = rot * rd.xz;
    ro.xz = rot * ro.xz;

    float t = raymarch(ro, rd);
    vec3 color = vec3(0.0);

    if (t < 20.0) {
        vec3 pos = ro + rd * t;
        color = shade(pos, rd, calcNormal(pos));
        color *= 1.0 - t / 20.0; // AO
    } else {
        color = vec3(0.05) * (1.0 + iKickPulse * 0.3);
    }

    color += exp(-length(p) * 1.2) * 0.4 * (0.5 + iKickPulse * 0.5);
    color *= 1.0 - 0.4 * length(uv - 0.5);
    color = color / (color + 1.0);
    color = pow(color, vec3(0.4545));
    fragColor = vec4(color, 1.0);
}
"""

FRANJA_VERTEX = "#version 330 core\nlayout(location = 0) in vec2 vPos;\nvoid main() { gl_Position = vec4(vPos, 0.0, 1.0); }"
FRANJA_FRAGMENT = """
#version 330 core
out vec4 fragColor;
uniform vec2 iResolution;
void main() {
    float line = mod(gl_FragCoord.x + gl_FragCoord.y, 40.0);
    float pattern = step(line, 2.0) * 0.12;
    fragColor = vec4(pattern, pattern, pattern, 1.0);
}
"""

class ShaderVisualEngine:
    def __init__(self):
        pygame.init()
        self.target_width, self.target_height = 1080, 1920
        self.target_aspect = self.target_width / self.target_height
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)
        self.screen = pygame.display.set_mode((int(900 * self.target_aspect), 900), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption('Preset 3: Menger Sponge [9:16]')

        vs = shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER)
        fs = shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vs, fs)
        self.uni_time = glGetUniformLocation(self.shader, 'iTime')
        self.uni_resolution = glGetUniformLocation(self.shader, 'iResolution')
        self.uni_kick = glGetUniformLocation(self.shader, 'iKickPulse')
        self.uni_hat = glGetUniformLocation(self.shader, 'iHatGlitch')
        self.uni_tom1 = glGetUniformLocation(self.shader, 'iTom1Morph')
        self.uni_tom2 = glGetUniformLocation(self.shader, 'iTom2Spin')

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

        fverts = array([-1, -1, 1, -1, 1, 1, -1, 1], dtype='f')
        self.franja_vao = glGenVertexArrays(1)
        glBindVertexArray(self.franja_vao)
        fvbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, fvbo)
        glBufferData(GL_ARRAY_BUFFER, fverts, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)

        self.kick_pulse = self.kick_target = self.hat_glitch = self.tom1_morph = self.tom2_spin = 0.0
        self.midi_input = self._connect_midi()
        self.clock = pygame.time.Clock()
        self.start_time = pygame.time.get_ticks()

    def _connect_midi(self):
        try:
            for port in mido.get_input_names():
                if 'CIRCUIT' in port.upper() or 'TRACKS' in port.upper():
                    return mido.open_input(port)
            print("⚠️  Demo mode (K/H/T/Y)")
        except: pass
        return None

    def process_midi(self):
        if self.midi_input:
            for msg in self.midi_input.iter_pending():
                if msg.type == 'note_on' and msg.velocity > 0:
                    v = msg.velocity / 127.0
                    if msg.note == KICK_NOTE: self.kick_target = min(1.0, self.kick_target + v * 0.7)
                    elif msg.note == CLOSEHAT_NOTE: self.hat_glitch = min(1.0, self.hat_glitch + v * 0.8)
                    elif msg.note == TOM1_NOTE: self.tom1_morph = min(1.0, self.tom1_morph + v * 0.6)
                    elif msg.note == TOM2_NOTE: self.tom2_spin = min(1.0, self.tom2_spin + v * 0.7)

    def update_params(self):
        self.kick_pulse += (self.kick_target - self.kick_pulse) * 0.15
        self.kick_target *= 0.92
        self.hat_glitch *= 0.88
        self.tom1_morph *= 0.90
        self.tom2_spin *= 0.93

    def calculate_viewport(self, w, h):
        a = w / h
        if a > self.target_aspect:
            vh = h; vw = int(vh * self.target_aspect); return (w - vw) // 2, 0, vw, vh
        vw = w; vh = int(vw / self.target_aspect); return 0, (h - vh) // 2, vw, vh

    def render(self):
        w, h = self.screen.get_size()
        vx, vy, vw, vh = self.calculate_viewport(w, h)

        glViewport(0, 0, w, h); glClearColor(0, 0, 0, 1); glClear(GL_COLOR_BUFFER_BIT)

        if vx > 0:
            glUseProgram(self.franja_shader)
            glUniform2f(self.franja_resolution, float(w), float(h))
            glBindVertexArray(self.franja_vao)
            glViewport(0, 0, vx, h); glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
            glViewport(vx + vw, 0, w - (vx + vw), h); glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

        glViewport(vx, vy, vw, vh)
        # Dibujar shader principal
        glUseProgram(self.shader)
        glUniform1f(self.uni_time, (pygame.time.get_ticks() - self.start_time) / 1000.0)
        glUniform2f(self.uni_resolution, float(vw), float(vh))
        glUniform1f(self.uni_kick, self.kick_pulse)
        glUniform1f(self.uni_hat, self.hat_glitch)
        glUniform1f(self.uni_tom1, self.tom1_morph)
        glUniform1f(self.uni_tom2, self.tom2_spin)
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
                    elif event.key == K_t: self.tom1_morph = min(1.0, self.tom1_morph + 0.6)
                    elif event.key == K_y: self.tom2_spin = min(1.0, self.tom2_spin + 0.7)
            self.process_midi(); self.update_params(); self.render(); self.clock.tick(60)
        if self.midi_input: self.midi_input.close()
        pygame.quit()

if __name__ == '__main__': ShaderVisualEngine().run()
