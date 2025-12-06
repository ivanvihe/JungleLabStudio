#!/usr/bin/env python3
"""
Preset 33: Psychedelic Liquid Chrome
Category: TouchDesigner Style / Domain Warping
Simulación de fluidos de alta viscosidad usando Domain Warping FBM.
Efecto de "aceite sobre agua" con paleta iridiscente.

Características:
- Doble Domain Warping fbm(p + fbm(p))
- Paleta de colores de alto contraste (Neon/Dark)
- Movimiento extremadamente suave
- Reactividad sutil: El sonido "empuja" el fluido
"""

from __future__ import division
import pygame
import pygame._sdl2.audio as sdl_audio
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np

SAMPLES = 1024

VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec2 position;
void main() {
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 330 core
out vec4 fragColor;

uniform float iTime;
uniform vec2 iResolution;
uniform float iLow;
uniform float iMid;
uniform float iHigh;

// === NOISE FUNCTIONS ===
float random(in vec2 _st) {
    return fract(sin(dot(_st.xy, vec2(12.9898,78.233))) * 43758.5453123);
}

float noise(in vec2 _st) {
    vec2 i = floor(_st);
    vec2 f = fract(_st);
    f = f * f * (3.0 - 2.0 * f);
    float a = random(i);
    float b = random(i + vec2(1.0, 0.0));
    float c = random(i + vec2(0.0, 1.0));
    float d = random(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

#define NUM_OCTAVES 5

float fbm(in vec2 _st) {
    float v = 0.0;
    float a = 0.5;
    vec2 shift = vec2(100.0);
    mat2 rot = mat2(cos(0.5), sin(0.5), -sin(0.5), cos(0.50));
    for (int i = 0; i < NUM_OCTAVES; ++i) {
        v += a * noise(_st);
        _st = rot * _st * 2.0 + shift;
        a *= 0.5;
    }
    return v;
}

void main() {
    vec2 st = (gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.y;
    // Zoom dinámico con bajos
    st *= 3.0 - iLow * 0.5;

    float t = iTime * 0.2;
    
    vec2 q = vec2(0.);
    q.x = fbm( st + 0.00*t);
    q.y = fbm( st + vec2(1.0));

    vec2 r = vec2(0.);
    // El sonido afecta la distorsión secundaria
    r.x = fbm( st + 1.0*q + vec2(1.7,9.2)+ 0.15*t + iMid * 0.1);
    r.y = fbm( st + 1.0*q + vec2(8.3,2.8)+ 0.126*t);

    float f = fbm(st + r);

    // Color grading sofisticado
    vec3 color = mix(vec3(0.101961,0.619608,0.666667),
                     vec3(0.666667,0.666667,0.498039),
                     clamp((f*f)*4.0,0.0,1.0));

    color = mix(color,
                vec3(0.0,0.0,0.164706),
                clamp(length(q),0.0,1.0));

    color = mix(color,
                vec3(0.666667,1.0,1.0),
                clamp(length(r.x),0.0,1.0));

    // Highlights reactivos
    color += vec3(iHigh * 0.5) * smoothstep(0.5, 0.8, f);
    
    // Contrast curve
    color = pow(color, vec3(1.2));
    
    fragColor = vec4((f*f*f+.6*f*f+.5*f)*color,1.);
}
"""

class ShaderVisualEngine:
    def __init__(self):
        pygame.init()
        pygame.display.init()
        
        self.target_width = 1080
        self.target_height = 1920
        self.aspect_ratio = self.target_width / self.target_height
        initial_h = 900
        initial_w = int(initial_h * self.aspect_ratio)

        self.screen = pygame.display.set_mode((initial_w, initial_h), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption('Preset 33: Liquid Chrome')

        self.audio_buffer = np.zeros(SAMPLES, dtype=np.float32)
        self.low = 0.0
        self.mid = 0.0
        self.high = 0.0

        self.setup_audio()
        self.setup_shaders()
        self.setup_quad()
        self.clock = pygame.time.Clock()
        self.start_time = pygame.time.get_ticks()

    def setup_audio(self):
        try:
            devices = sdl_audio.get_audio_device_names(True)
            target = next((d for d in devices if "Scarlett" in d), devices[0] if devices else None)
            if target:
                self.dev = sdl_audio.AudioDevice(target, True, 44100, sdl_audio.AUDIO_F32, 1, 1024, 0, self.callback)
                self.dev.pause(0)
        except: pass

    def callback(self, dev, data):
        self.audio_buffer = np.frombuffer(data, dtype=np.float32)

    def update_audio(self):
        if len(self.audio_buffer) == 0: return
        fft = np.abs(np.fft.rfft(self.audio_buffer))
        self.low  = self.low * 0.9 + np.mean(fft[0:10]) * 0.05
        self.mid  = self.mid * 0.9 + np.mean(fft[10:50]) * 0.05
        self.high = self.high * 0.9 + np.mean(fft[50:150]) * 0.05

    def setup_quad(self):
        vertices = np.array([-1.0, -1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0], dtype=np.float32)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)

    def setup_shaders(self):
        vs = shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER)
        fs = shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vs, fs)
        self.locs = {
            'iTime': glGetUniformLocation(self.shader, 'iTime'),
            'iResolution': glGetUniformLocation(self.shader, 'iResolution'),
            'iLow': glGetUniformLocation(self.shader, 'iLow'),
            'iMid': glGetUniformLocation(self.shader, 'iMid'),
            'iHigh': glGetUniformLocation(self.shader, 'iHigh')
        }

    def render(self):
        self.update_audio()
        w, h = self.screen.get_size()
        glViewport(0, 0, w, h)
        glUseProgram(self.shader)
        
        glUniform1f(self.locs['iTime'], (pygame.time.get_ticks() - self.start_time) / 1000.0)
        glUniform2f(self.locs['iResolution'], float(w), float(h))
        glUniform1f(self.locs['iLow'], self.low)
        glUniform1f(self.locs['iMid'], self.mid)
        glUniform1f(self.locs['iHigh'], self.high)

        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    running = False
            self.render()
            self.clock.tick(60)
        pygame.quit()

if __name__ == '__main__':
    ShaderVisualEngine().run()