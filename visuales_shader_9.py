#!/usr/bin/env python3
"""
Preset 9: Swarm Intelligence - Boids Flocking Behavior
Category: Particle/Flow Field
GPU-simulated emergent swarm behavior
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

vec2 hash2(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
    return fract(sin(p) * 43758.5453);
}

// Boid simulation
vec2 boidPosition(float id, float time) {
    vec2 seed = hash2(vec2(id, 0.0));

    // Flocking behavior params
    float speed = 0.5 + iKickPulse * 1.5;
    float cohesion = iTom1Morph * 0.5;
    float alignment = iTom2Spin * 0.3;

    vec2 pos = seed;

    // Swirl motion
    float angle = time * speed + seed.x * 6.28 + cohesion * 3.0;
    float radius = 0.3 + 0.2 * sin(time * 0.5 + seed.y * 6.28);

    pos += vec2(cos(angle), sin(angle)) * radius;

    // Hat glitch scatters the swarm
    if(iHatGlitch > 0.1) {
        pos += (hash2(vec2(id, time)) - 0.5) * iHatGlitch * 0.5;
    }

    return pos;
}

void main() {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 p = (fragCoord - iResolution.xy * 0.5) / iResolution.x;

    vec3 color = vec3(0.0);

    // Kick increases swarm size
    int numBoids = 30 + int(iKickPulse * 70.0);

    for(int i = 0; i < 50; i++) {
        if(i >= numBoids) break;

        float id = float(i);
        vec2 boidPos = boidPosition(id, iTime);

        // Wrap to screen
        boidPos = fract(boidPos + 0.5) - 0.5;
        boidPos *= 2.0;

        // Boid glow
        float dist = length(p - boidPos);
        float boid = 0.015 / (dist + 0.015);

        color += boid * (0.02 + iKickPulse * 0.03);

        // Trailing effect
        vec2 prevPos = boidPosition(id, iTime - 0.1);
        prevPos = fract(prevPos + 0.5) - 0.5;
        prevPos *= 2.0;
        float trail = length(p - prevPos);
        color += (0.01 / (trail + 0.01)) * 0.01;
    }

    // Connection lines between nearby boids
    for(int i = 0; i < 20; i++) {
        vec2 b1 = boidPosition(float(i), iTime);
        b1 = fract(b1 + 0.5) - 0.5;
        b1 *= 2.0;

        for(int j = i + 1; j < 25; j++) {
            vec2 b2 = boidPosition(float(j), iTime);
            b2 = fract(b2 + 0.5) - 0.5;
            b2 *= 2.0;

            if(length(b1 - b2) < 0.3) {
                // Line between boids
                float lineProx = length(p - (b1 + b2) * 0.5);
                color += 0.001 / (lineProx + 0.1);
            }
        }
    }

    // Center attractor glow
    color += exp(-length(p) * 2.0) * 0.3 * iKickPulse;

    // Vignette
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
        pygame.display.set_caption('Preset 9: Swarm Intelligence [9:16]')
        vs = shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER)
        fs = shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vs, fs)
        self.uni_time = glGetUniformLocation(self.shader, 'iTime')
        self.uni_resolution = glGetUniformLocation(self.shader, 'iResolution')
        self.uni_kick = glGetUniformLocation(self.shader, 'iKickPulse')
        self.uni_hat = glGetUniformLocation(self.shader, 'iHatGlitch')
        self.uni_tom1 = glGetUniformLocation(self.shader, 'iTom1Morph')
        self.uni_tom2 = glGetUniformLocation(self.shader, 'iTom2Spin')

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

        self.kick_pulse = self.kick_target = self.hat_glitch = self.tom1_morph = self.tom2_spin = 0.0
        self.midi_input = self._connect_midi()
        self.clock = pygame.time.Clock()
        self.start_time = pygame.time.get_ticks()

    def _connect_midi(self):
        try:
            for port in mido.get_input_names():
                if 'CIRCUIT' in port.upper() or 'TRACKS' in port.upper():
                    return mido.open_input(port)
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

        # Dibujar franjas con líneas inclinadas
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
