#!/usr/bin/env python3
"""
Preset 5: Apollonian Gasket - Circle Packing Fractal
Category: Fractal/SDF Advanced
Infinite circle subdivision that evolves with kick
"""

from __future__ import division
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL import shaders
import mido
from numpy import array

KICK_NOTE = 60
CLOSEHAT_NOTE = 62
TOM1_NOTE = 64
TOM2_NOTE = 65

VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec3 vPos;
void main() { gl_Position = vec4(vPos, 1.0); }
"""

FRAGMENT_SHADER = """
#version 330 core
#define fragCoord gl_FragCoord.xy

uniform float iTime;
uniform vec2  iResolution;
uniform float iKickPulse;
uniform float iHatGlitch;
uniform float iTom1Morph;
uniform float iTom2Spin;

out vec4 fragColor;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

// Circle SDF
float sdCircle(vec2 p, vec2 c, float r) {
    return length(p - c) - r;
}

// Apollonian Gasket - recursive circle packing
float apollonianGasket(vec2 p, int depth) {
    float d = 1e10;
    float scale = 1.0;

    for(int i = 0; i < depth; i++) {
        // Three circles arrangement
        float r = 0.5 / scale;

        d = min(d, sdCircle(p, vec2(0.0, 0.0), r));
        d = min(d, sdCircle(p, vec2(r, 0.0), r * 0.5));
        d = min(d, sdCircle(p, vec2(-r * 0.5, r * 0.866), r * 0.5));
        d = min(d, sdCircle(p, vec2(-r * 0.5, -r * 0.866), r * 0.5));

        // Fold space for recursion
        p = abs(p);
        if(p.x + p.y < 0.0) p = -p;

        // Rotate and scale
        float angle = iTime * 0.1;
        float ca = cos(angle);
        float sa = sin(angle);
        p = mat2(ca, -sa, sa, ca) * p;

        scale *= 2.0;
        p *= 2.0;
    }

    return d;
}

void main()
{
    vec2 uv = fragCoord / iResolution.xy;
    vec2 p = (fragCoord - iResolution.xy * 0.5) / iResolution.x;

    // Kick evolves depth
    int depth = 4 + int(iKickPulse * 6.0);

    // Tom1 zooms
    float zoom = 1.0 + iTom1Morph * 2.0;
    p /= zoom;

    // Tom2 rotation
    float angle = iTom2Spin * 6.28;
    float ca = cos(angle);
    float sa = sin(angle);
    p = mat2(ca, -sa, sa, ca) * p;

    // Hat glitch
    if(iHatGlitch > 0.1) {
        p += vec2(
            hash(vec2(iTime * 10.0, uv.y)) - 0.5,
            hash(vec2(iTime * 10.0 + 1.0, uv.x)) - 0.5
        ) * iHatGlitch * 0.2;
    }

    float d = apollonianGasket(p, depth);

    // Distance field visualization
    float circle = smoothstep(0.02, 0.0, abs(d));
    float fill = smoothstep(0.0, -0.01, d);

    vec3 color = vec3(0.0);

    // Outline with kick glow
    color += circle * (0.8 + iKickPulse * 0.5);

    // Filled circles darker
    color += fill * 0.2;

    // Glow around circles
    float glow = 0.02 / (abs(d) + 0.02);
    color += glow * 0.1 * (0.5 + iKickPulse * 0.5);

    // Center glow
    float centerGlow = exp(-length(p) * 1.5) * 0.3 * iKickPulse;
    color += centerGlow;

    // Vignette
    color *= 1.0 - 0.4 * length(uv - 0.5);

    // Tone & gamma
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
        self.target_width = 1080
        self.target_height = 1920
        self.target_aspect = self.target_width / self.target_height

        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)
        self.screen = pygame.display.set_mode((int(900 * self.target_aspect), 900), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption('Preset 5: Apollonian Gasket [9:16]')

        self.vertex_shader = shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER)
        self.fragment_shader = shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(self.vertex_shader, self.fragment_shader)

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


        self.vertices = array([-1.0, -1.0, 0.0, 1.0, -1.0, 0.0, 1.0, 1.0, 0.0, -1.0, 1.0, 0.0], dtype='float32')
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices, GL_STATIC_DRAW)
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


        self.kick_pulse = 0.0
        self.kick_target = 0.0
        self.hat_glitch = 0.0
        self.tom1_morph = 0.0
        self.tom2_spin = 0.0
        self.midi_input = self._connect_midi()
        self.clock = pygame.time.Clock()
        self.start_time = pygame.time.get_ticks()

    def _connect_midi(self):
        try:
            for port in mido.get_input_names():
                if 'CIRCUIT' in port.upper() or 'TRACKS' in port.upper():
                    return mido.open_input(port)
            print("⚠️  Demo mode (K/H/T/Y)")
        except:
            pass
        return None

    def process_midi(self):
        if self.midi_input:
            for msg in self.midi_input.iter_pending():
                if msg.type == 'note_on' and msg.velocity > 0:
                    vel = msg.velocity / 127.0
                    if msg.note == KICK_NOTE:
                        self.kick_target = min(1.0, self.kick_target + vel * 0.7)
                    elif msg.note == CLOSEHAT_NOTE:
                        self.hat_glitch = min(1.0, self.hat_glitch + vel * 0.8)
                    elif msg.note == TOM1_NOTE:
                        self.tom1_morph = min(1.0, self.tom1_morph + vel * 0.6)
                    elif msg.note == TOM2_NOTE:
                        self.tom2_spin = min(1.0, self.tom2_spin + vel * 0.7)

    def update_params(self):
        self.kick_pulse += (self.kick_target - self.kick_pulse) * 0.15
        self.kick_target *= 0.92
        self.hat_glitch *= 0.88
        self.tom1_morph *= 0.90
        self.tom2_spin *= 0.93

    def calculate_viewport(self, w, h):
        aspect = w / h
        if aspect > self.target_aspect:
            vh = h
            vw = int(vh * self.target_aspect)
            return (w - vw) // 2, 0, vw, vh
        else:
            vw = w
            vh = int(vw / self.target_aspect)
            return 0, (h - vh) // 2, vw, vh

    def render(self):
        w, h = self.screen.get_size()
        vx, vy, vw, vh = self.calculate_viewport(w, h)

        glViewport(0, 0, w, h)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        # Dibujar franjas con líneas inclinadas
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
                    if event.key == K_k:
                        self.kick_target = min(1.0, self.kick_target + 0.7)
                    elif event.key == K_h:
                        self.hat_glitch = min(1.0, self.hat_glitch + 0.8)
                    elif event.key == K_t:
                        self.tom1_morph = min(1.0, self.tom1_morph + 0.6)
                    elif event.key == K_y:
                        self.tom2_spin = min(1.0, self.tom2_spin + 0.7)

            self.process_midi()
            self.update_params()
            self.render()
            self.clock.tick(60)

        if self.midi_input:
            self.midi_input.close()
        pygame.quit()

if __name__ == '__main__':
    ShaderVisualEngine().run()
