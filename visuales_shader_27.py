#!/usr/bin/env python3
"""
Preset 27: Radial Frequency Scope
Category: Audio Reactive / Generative
Inspirado en el shader "Music Visualizer" de Shadertoy, adaptado a Python/GLSL.

Característiques:
- Anillo central reactivo a frecuencias (FFT suave).
- Líneas orbitales que rotan (Lissajous lines).
- Coloración HSV dinámica basada en el ángulo y el tiempo.
- Efecto "Glow" aditivo.
- Reactividad: Frecuencias (FFT) modulan el brillo y el grosor.
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
FFT_SIZE = 512 # Tamaño de la textura de FFT

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

uniform float iTime;
uniform vec2 iResolution;
uniform sampler1D iAudioFFT; // Textura 1D con datos FFT
uniform float uVolume;

#define PI 3.14159265359
#define RADIUS 0.5
#define SPEED 0.5
#define BRIGHTNESS 0.2

// HSV to RGB
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

// Obtener frecuencia suave de la textura
float getFrequency(float x) {
    // x va de 0.0 a 1.0
    // Mapeamos x a las frecuencias bajas/medias (donde está la música)
    // Ignoramos frecuencias muy altas (> 0.5 de la textura)
    return texture(iAudioFFT, x * 0.5).r; 
}

// Anillo central
vec3 circleIllumination(vec2 uv, float radius) {
    float dist = length(uv);
    
    // Obtener frecuencia basada en el ángulo polar
    float angle = atan(uv.x, uv.y); // -PI a PI
    float normAngle = abs(angle / PI); // 0.0 a 1.0
    
    float freq = getFrequency(normAngle);
    
    // Radio variable con el bajo (freq en 0.0)
    float bass = getFrequency(0.05); 
    float dynamicRadius = radius + bass * 0.1;
    
    // Grosor del anillo (glow)
    float ring = 1.0 / abs(dist - dynamicRadius);
    
    // Color HSV rotativo
    vec3 col = hsv2rgb(vec3((angle + iTime * 0.5) / (PI * 2.0), 1.0, 1.0));
    
    // Modular brillo con frecuencia
    col *= ring * BRIGHTNESS * (freq + 0.1);
    
    return col;
}

// Líneas rotativas
vec3 doLine(vec2 uv, float radius) {
    // Color basado en tiempo
    vec3 col = hsv2rgb(vec3(uv.x * 0.2 + iTime * 0.1, 1.0, 1.0));
    
    // Frecuencia basada en la posición a lo largo de la línea
    float freq = getFrequency(abs(uv.x * 0.5));
    
    // Glow de la línea (1/y)
    float glow = 1.0 / (abs(uv.y) + 0.001); // Evitar división por cero
    
    col *= glow * BRIGHTNESS * freq;
    
    // Máscara circular inversa (solo dibujar fuera del radio)
    col *= smoothstep(radius, radius * 1.5, abs(uv.x));
    
    return col;
}

void main() {
    // Coordenadas centradas y corregidas
    vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.y;
    uv *= 2.0; // Zoom out un poco
    
    vec3 col = vec3(0.0);
    
    // 1. Círculo Central
    col += circleIllumination(uv, RADIUS);
    
    // 2. Líneas Rotativas
    float t = iTime * SPEED;
    
    // Línea 1
    float c = cos(t);
    float s = sin(t);
    vec2 rotUV = mat2(c, -s, s, c) * uv;
    col += doLine(rotUV, RADIUS);
    
    // Línea 2 (Contrarotación)
    float c2 = sin(t * 0.8); // Velocidad diferente
    float s2 = cos(t * 0.8);
    vec2 rotUV2 = mat2(c2, -s2, s2, c2) * uv;
    col += doLine(rotUV2, RADIUS);
    
    // Tone Mapping / Brillo extra si es muy fuerte
    // "Luma" boost del código original
    float luma = dot(col, vec3(0.299, 0.587, 0.114));
    col += max(luma - 0.8, 0.0) * 0.5; // Bloom fake
    
    // Fade out global si volumen es bajo
    col *= smoothstep(0.01, 0.05, uVolume);
    
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
        pygame.display.set_caption('Preset 27: Radial Frequency Scope')

        # Audio
        self.audio_buffer = np.zeros(SAMPLES, dtype=np.float32)
        self.fft_texture_data = np.zeros(FFT_SIZE, dtype=np.float32)
        self.setup_audio()
        
        self.vol_smoothed = 0.0
        
        self.setup_shaders()
        self.clock = pygame.time.Clock()
        self.start_time = pygame.time.get_ticks()

    def setup_audio(self):
        try:
            devices = sdl_audio.get_audio_device_names(True)
            target = next((d for d in devices if "Scarlett" in d), devices[0] if devices else None)
            if target:
                print(f"Connecting: {target}")
                self.dev = sdl_audio.AudioDevice(
                    target, True, 44100, sdl_audio.AUDIO_F32, 1, 1024, 0, self.callback
                )
                self.dev.pause(0)
        except Exception as e: print("Audio Error:", e)

    def callback(self, dev, data):
        raw = np.frombuffer(data, dtype=np.float32)
        l = min(len(raw), SAMPLES)
        self.audio_buffer[:l] = raw[:l] * 10.0 # Gain

    def update_fft(self):
        # Calcular FFT
        fft = np.abs(np.fft.rfft(self.audio_buffer))
        
        # Normalizar y suavizar
        fft = fft / SAMPLES * 10.0 # Boost visual
        
        # Mapear al buffer de textura (interpolación simple o truncado)
        # FFT size real es SAMPLES/2 + 1 (513). Queremos 512.
        l = min(len(fft), FFT_SIZE)
        self.fft_texture_data[:l] = fft[:l]
        
        # Volumen global
        rms = np.sqrt(np.mean(self.audio_buffer**2))
        self.vol_smoothed += (rms - self.vol_smoothed) * 0.1

    def setup_shaders(self):
        vs = shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER)
        fs = shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vs, fs)
        
        self.u_res = glGetUniformLocation(self.shader, 'iResolution')
        self.u_time = glGetUniformLocation(self.shader, 'iTime')
        self.u_vol = glGetUniformLocation(self.shader, 'uVolume')
        self.u_fft = glGetUniformLocation(self.shader, 'iAudioFFT')
        
        # Textura 1D para FFT
        self.tex_fft = glGenTextures(1)
        glBindTexture(GL_TEXTURE_1D, self.tex_fft)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        # Quad
        verts = np.array([-1,-1, 1,-1, 1,1, -1,1], dtype=np.float32)
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, verts, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)

    def render(self):
        self.update_fft()
        
        w, h = self.screen.get_size()
        glViewport(0, 0, w, h)
        glClearColor(0,0,0,1)
        glClear(GL_COLOR_BUFFER_BIT)
        
        glUseProgram(self.shader)
        glUniform2f(self.u_res, float(w), float(h))
        glUniform1f(self.u_time, (pygame.time.get_ticks() - self.start_time) / 1000.0)
        glUniform1f(self.u_vol, self.vol_smoothed)
        
        # Actualizar textura FFT
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_1D, self.tex_fft)
        glTexImage1D(GL_TEXTURE_1D, 0, GL_R32F, FFT_SIZE, 0, GL_RED, GL_FLOAT, self.fft_texture_data)
        glUniform1i(self.u_fft, 0)
        
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