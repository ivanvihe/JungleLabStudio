#!/usr/bin/env python3
"""
Preset 4: Mandelbulb - 3D Fractal Organic Evolution
Category: Fractal/SDF Advanced
Evolves power and detail with kicks
"""

from __future__ import division
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL import shaders
import mido
from sys import exit as exitsystem
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

// Mandelbulb SDF
float mandelbulb(vec3 pos, float power) {
    vec3 z = pos;
    float dr = 1.0;
    float r = 0.0;

    for(int i = 0; i < 8; i++) {
        r = length(z);
        if(r > 2.0) break;

        // Convert to polar
        float theta = acos(z.z / r);
        float phi = atan(z.y, z.x);
        dr = pow(r, power - 1.0) * power * dr + 1.0;

        // Scale and rotate
        float zr = pow(r, power);
        theta = theta * power;
        phi = phi * power;

        // Convert back to cartesian
        z = zr * vec3(
            sin(theta) * cos(phi),
            sin(phi) * sin(theta),
            cos(theta)
        );
        z += pos;
    }

    return 0.5 * log(r) * r / dr;
}

float map(vec3 p) {
    // Kick evolves power (4 to 12)
    float power = 4.0 + iKickPulse * 8.0;

    // Tom1 scales the bulb
    float scale = 1.0 + iTom1Morph * 0.5;

    // Hat distorts space
    if(iHatGlitch > 0.1) {
        p += vec3(
            hash(p.xy + iTime) - 0.5,
            hash(p.yz + iTime + 10.0) - 0.5,
            hash(p.xz + iTime + 20.0) - 0.5
        ) * iHatGlitch * 0.2;
    }

    return mandelbulb(p / scale, power) * scale;
}

vec3 calcNormal(vec3 p) {
    const float eps = 0.001;
    vec2 e = vec2(eps, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

float raymarch(vec3 ro, vec3 rd) {
    float t = 0.0;
    for(int i = 0; i < 60; i++) {
        vec3 p = ro + rd * t;
        float d = map(p);
        if(d < 0.001) break;
        t += d * 0.7;
        if(t > 20.0) break;
    }
    return t;
}

vec3 shade(vec3 p, vec3 rd, vec3 normal) {
    vec3 light = normalize(vec3(2.0, 3.0, 4.0));
    float diff = max(dot(normal, light), 0.0);

    vec3 h = normalize(light - rd);
    float spec = pow(max(dot(normal, h), 0.0), 16.0);

    // Organic color based on position + kick
    vec3 col = vec3(0.5 + 0.3 * sin(p.x * 2.0 + iKickPulse * 3.0));
    col *= diff * 0.8 + 0.2;
    col += spec * 0.3;

    return col;
}

void main()
{
    vec2 uv = fragCoord / iResolution.xy;
    vec2 p = (fragCoord - iResolution.xy * 0.5) / iResolution.x;

    // Orbiting camera
    float angle = iTime * 0.3 + iTom2Spin * 2.0;
    vec3 ro = vec3(3.0 * cos(angle), 0.5, 3.0 * sin(angle));
    vec3 target = vec3(0.0);

    vec3 forward = normalize(target - ro);
    vec3 right = normalize(cross(vec3(0.0, 1.0, 0.0), forward));
    vec3 up = cross(forward, right);
    vec3 rd = normalize(forward + p.x * right + p.y * up);

    float t = raymarch(ro, rd);

    vec3 color = vec3(0.0);

    if(t < 20.0) {
        vec3 pos = ro + rd * t;
        vec3 normal = calcNormal(pos);
        color = shade(pos, rd, normal);

        // AO
        color *= 1.0 - t / 20.0;
    } else {
        color = vec3(0.02 + iKickPulse * 0.1);
    }

    // Glow
    float glow = exp(-length(p) * 1.0) * 0.3;
    color += glow * (0.5 + iKickPulse * 0.5);

    // Vignette
    color *= 1.0 - 0.5 * length(p * 0.5);

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

        initial_height = 900
        initial_width = int(initial_height * self.target_aspect)

        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)
        self.screen = pygame.display.set_mode((initial_width, initial_height), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption('Preset 4: Mandelbulb [9:16]')

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
            available_ports = mido.get_input_names()
            for port in available_ports:
                if 'CIRCUIT' in port.upper() or 'TRACKS' in port.upper():
                    return mido.open_input(port)
            print("⚠️  Circuit Tracks not found. Demo mode (K/H/T/Y)")
            return None
        except:
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

    def calculate_viewport(self, window_width, window_height):
        window_aspect = window_width / window_height
        if window_aspect > self.target_aspect:
            viewport_height = window_height
            viewport_width = int(viewport_height * self.target_aspect)
            viewport_x = (window_width - viewport_width) // 2
            viewport_y = 0
        else:
            viewport_width = window_width
            viewport_height = int(viewport_width / self.target_aspect)
            viewport_x = 0
            viewport_y = (window_height - viewport_height) // 2
        return viewport_x, viewport_y, viewport_width, viewport_height

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
        current_time = (pygame.time.get_ticks() - self.start_time) / 1000.0
        glUniform1f(self.uni_time, current_time)
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
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                    elif event.key == K_k:
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
    engine = ShaderVisualEngine()
    engine.run()
