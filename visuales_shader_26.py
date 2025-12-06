#!/usr/bin/env python3
"""
Preset 26: Ethereal Volumetric Dust (Fragment Shader Version)
Category: Audio Reactive / Generative
Sistema de partículas volumétrico generado puramente en el Fragment Shader.
Garantiza compatibilidad total (mismo método que los otros presets).

Característiques:
- Generación: "Raymarching" simplificado de capas de ruido 3D.
- Reactividad:
    - Graves: Respiración y expansión del espacio.
    - Agudos: Destellos y turbulencia.
    - Volumen: Velocidad de viaje y brillo global.
"""

from __future__ import division
import pygame
import pygame._sdl2.audio as sdl_audio
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np

# Configuración
SAMPLES = 1024

VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec2 vPos;
void main() {
    gl_Position = vec4(vPos, 0.0, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 330 core
out vec4 fragColor;

uniform vec2 iResolution;
uniform float iTime;
uniform float uVolume;
uniform float uLowFreq;
uniform float uHighFreq;

// Hash simple
float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

// Ruido 2D
float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
}

// Starfield Layer
float starLayer(vec2 uv, float scale, float seed) {
    vec2 id = floor(uv * scale);
    vec2 pos = fract(uv * scale) - 0.5;
    
    // Random per cell
    float n = hash(id + seed);
    
    // Threshold para decidir si hay estrella
    // Menos es más estrellas
    if (n > 0.9 + (0.08 * (1.0 - uVolume))) return 0.0; 
    
    // Posición offset random en la celda
    vec2 offset = (vec2(hash(id + seed*2.0), hash(id + seed*3.0)) - 0.5) * 0.8;
    
    // Distancia
    float d = length(pos - offset);
    
    // Brillo (Point shape)
    // Modulado por audio (High Freq hace destellos)
    float brightness = 0.02 / d;
    brightness *= smoothstep(1.0, 0.1, d); // Soft limit
    
    // Twinkle
    float twinkle = sin(iTime * 5.0 + n * 100.0) * 0.5 + 0.5;
    brightness *= 0.5 + 0.5 * twinkle + uHighFreq * 2.0;
    
    return brightness;
}

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.y;
    
    // Rotación lenta de cámara
    float ang = iTime * 0.05;
    float s = sin(ang);
    float c = cos(ang);
    mat2 rot = mat2(c, -s, s, c);
    uv = rot * uv;
    
    // Respiración (Zoom) con Bajos
    float zoom = 1.0 + uLowFreq * 0.2;
    uv /= zoom;
    
    vec3 col = vec3(0.0);
    
    // Generar capas de estrellas/polvo
    // Parallax: Capas se mueven a diferentes velocidades
    float t = iTime * (0.1 + uVolume * 0.2); // Velocidad global
    
    for (float i = 0.0; i < 5.0; i++) {
        float depth = fract(i * 0.2 + t); // 0.0 a 1.0 moviéndose
        float scale = mix(20.0, 0.5, depth); // Lejos (grande scale UV) -> Cerca (pequeño scale UV)
        float fade = smoothstep(0.0, 0.2, depth) * smoothstep(1.0, 0.8, depth); // Fade in/out
        
        vec2 layerUV = uv * scale + i * 12.34; // Offset por capa
        
        // Añadir capa
        float stars = starLayer(layerUV, 10.0, i); // Grid interno 10.0
        
        // Colorizar capa
        // Las lejanas más azules, cercanas más blancas
        vec3 layerCol = mix(vec3(0.2, 0.4, 0.8), vec3(0.8, 0.9, 1.0), depth);
        
        col += layerCol * stars * fade;
    }
    
    // Fondo: Ruido nebuloso muy sutil
    float nebula = noise(uv * 3.0 + vec2(iTime * 0.1));
    col += vec3(0.05, 0.05, 0.1) * nebula * (0.5 + uVolume);
    
    // Vignette
    col *= 1.0 - length(uv * 0.8);
    
    fragColor = vec4(col, 1.0);
}
"""

class ShaderVisualEngine:
    def __init__(self):
        pygame.init()
        pygame.display.init()
        
        self.target_width = 1080
        self.target_height = 1920
        self.target_aspect = self.target_width / self.target_height
        
        initial_h = 900
        initial_w = int(initial_h * self.target_aspect)

        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)
        self.screen = pygame.display.set_mode(
            (initial_w, initial_h),
            DOUBLEBUF | OPENGL | RESIZABLE
        )
        pygame.display.set_caption('Preset 26: Ethereal Dust (Fragment)')

        # Audio
        self.audio_buffer = np.zeros(SAMPLES, dtype=np.float32)
        self.setup_audio()
        
        # Analysis
        self.smoothed_vol = 0.0
        self.smoothed_low = 0.0
        self.smoothed_high = 0.0
        
        self.setup_scene()
        
        self.clock = pygame.time.Clock()
        self.start_time = pygame.time.get_ticks()

    def setup_audio(self):
        try:
            devices = sdl_audio.get_audio_device_names(True)
            print("Inputs:", devices)
            target = next((d for d in devices if "Scarlett" in d), devices[0] if devices else None)
            if target:
                print(f"Connecting: {target}")
                self.dev = sdl_audio.AudioDevice(
                    target, True, 44100, sdl_audio.AUDIO_F32, 1, 1024, 0, self.callback
                )
                self.dev.pause(0)
        except Exception as e:
            print("Audio Error:", e)

    def callback(self, dev, data):
        raw = np.frombuffer(data, dtype=np.float32)
        l = min(len(raw), SAMPLES)
        self.audio_buffer[:l] = raw[:l] * 20.0

    def analyze_audio(self):
        rms = np.sqrt(np.mean(self.audio_buffer**2))
        fft = np.abs(np.fft.rfft(self.audio_buffer)) / SAMPLES
        low = np.mean(fft[1:10]) * 5.0
        high = np.mean(fft[50:]) * 20.0
        
        self.smoothed_vol += (rms - self.smoothed_vol) * 0.1
        self.smoothed_low += (low - self.smoothed_low) * 0.1
        self.smoothed_high += (high - self.smoothed_high) * 0.1

    def setup_scene(self):
        vs = shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER)
        fs = shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vs, fs)
        
        self.u_res = glGetUniformLocation(self.shader, 'iResolution')
        self.u_time = glGetUniformLocation(self.shader, 'iTime')
        self.u_vol = glGetUniformLocation(self.shader, 'uVolume')
        self.u_high = glGetUniformLocation(self.shader, 'uHighFreq')
        self.u_low = glGetUniformLocation(self.shader, 'uLowFreq')
        
        # Quad Fullscreen (Igual que los otros presets que sí funcionan)
        verts = np.array([-1, -1, 1, -1, 1, 1, -1, 1], dtype=np.float32)
        
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, verts, GL_STATIC_DRAW)
        
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)

    def render(self):
        self.analyze_audio()
        w, h = self.screen.get_size()
        glViewport(0, 0, w, h)
        glClearColor(0,0,0,1)
        glClear(GL_COLOR_BUFFER_BIT)
        
        glUseProgram(self.shader)
        glUniform2f(self.u_res, float(w), float(h))
        glUniform1f(self.u_time, (pygame.time.get_ticks() - self.start_time) / 1000.0)
        glUniform1f(self.u_vol, self.smoothed_vol)
        glUniform1f(self.u_low, self.smoothed_low)
        glUniform1f(self.u_high, self.smoothed_high)
        
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
        
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    running = False
            
            self.render()
            self.clock.tick(60)
        
        if hasattr(self, 'dev') and self.dev: self.dev.close()
        pygame.quit()

if __name__ == '__main__':
    ShaderVisualEngine().run()