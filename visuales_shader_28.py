#!/usr/bin/env python3
"""
Preset 28: Neon Kinetic Mandala
Category: Audio Reactive / Generative
Evolución del osciloscopio radial hacia formas geométricas complejas.
Utiliza simetría hexagonal caleidoscópica y SDFs pulsantes.

Característiques:
- Simetría Hexagonal (Kaleidoscope 6-fold).
- Núcleo Hexagonal Pulsante (Reactivo a Bajos).
- Rayos de Espectro (Reactivos a Frecuencias).
- Ecos Geométricos (Ripples).
- Colores Neón Alta Intensidad.
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
FFT_SIZE = 512

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
uniform sampler1D iAudioFFT; // Textura FFT
uniform float uVolume;

#define PI 3.14159265359
#define TAU 6.28318530718

// Utils
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

float getFreq(float x) {
    return texture(iAudioFFT, clamp(x, 0.01, 0.99)).r;
}

// Signed Distance Function: Hexagon
float sdHexagon(in vec2 p, in float r) {
    const vec3 k = vec3(-0.866025404, 0.5, 0.577350269);
    p = abs(p);
    p -= 2.0 * min(dot(k.xy, p), 0.0) * k.xy;
    p -= vec2(clamp(p.x, -k.z * r, k.z * r), r);
    return length(p) * sign(p.y);
}

// Rotation
mat2 rot(float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, -s, s, c);
}

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.y;
    uv *= 1.2; // Zoom inicial
    
    vec3 col = vec3(0.0);
    float t = iTime * 0.2;
    
    // 1. Rotación Global Reactiva
    // El bajo controla la velocidad de rotación del mandala entero
    float bass = getFreq(0.05);
    float rotSpeed = t + bass * 0.2;
    uv *= rot(rotSpeed);
    
    // 2. Simetría Caleidoscópica (Fold)
    // Dividimos el espacio en 6 sectores (Hexagonal)
    float r = length(uv);
    float a = atan(uv.y, uv.x);
    float segments = 6.0;
    // Mapeamos el ángulo al dominio [-PI/6, PI/6] repetido
    float a_folded = mod(a, TAU / segments) - (TAU / segments) / 2.0;
    // Reconstruimos UV en el espacio plegado
    vec2 uv_folded = vec2(cos(a_folded), sin(a_folded)) * r;
    
    // 3. Rayos de Espectro (Spectrum Beams)
    // Dibujamos rayos que salen del centro.
    // La longitud e intensidad dependen de frecuencias.
    // Usamos 'r' y 'a_folded' para muestrear FFT.
    float fft_index = abs(a_folded) * 2.0 + 0.05; // Mapeo angular a frecuencia
    float fft_val = getFreq(fft_index);
    
    // Forma del rayo
    float beamWidth = 0.01 + fft_val * 0.05;
    float beamAlpha = 1.0 - smoothstep(beamWidth, beamWidth + 0.02, abs(a_folded) * r);
    
    // Longitud del rayo
    float beamLen = 0.3 + fft_val * 1.2;
    beamAlpha *= smoothstep(beamLen, beamLen - 0.2, r);
    
    // Color de los rayos (Cyan/Blue/Purple gradient)
    vec3 beamCol = hsv2rgb(vec3(0.5 + r * 0.3 + t, 0.8, 1.0));
    col += beamCol * beamAlpha * 1.5; // Brillo extra
    
    // 4. Núcleo Hexagonal (Bass Core)
    // Un hexágono central que late con el bajo
    float hexRadius = 0.2 + bass * 0.15;
    float hexDist = abs(sdHexagon(uv_folded, hexRadius));
    
    // Glow intenso para el núcleo
    float coreGlow = 0.02 / (hexDist + 0.001);
    vec3 coreCol = vec3(1.0, 0.2, 0.6); // Magenta/Red Neon
    col += coreCol * coreGlow * (0.5 + bass);
    
    // 5. Ecos Hexagonales (Outer Ripples)
    // Múltiples hexágonos concéntricos que reaccionan a Medios/Agudos
    for(int i = 1; i <= 4; i++) {
        float fi = float(i);
        // Radio oscilante + expansión por volumen
        float ringR = 0.4 + fi * 0.25 + sin(t * 2.0 + fi) * 0.05;
        float ringDist = abs(sdHexagon(uv_folded, ringR));
        
        // Grosor variable con la frecuencia de esa banda
        float bandFreq = getFreq(0.2 + fi * 0.15);
        float ringGlow = 0.008 / (ringDist + 0.001);
        
        // Color cíclico (Gold/Green/Cyan)
        vec3 ringCol = hsv2rgb(vec3(fi * 0.15 + t + bandFreq, 0.9, 1.0));
        
        col += ringCol * ringGlow * bandFreq * 2.0;
    }
    
    // 6. Partículas de fondo (Sparkles)
    // Ruido simple basado en coordenadas
    float sparkle = fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453);
    if (sparkle > 0.98) {
        float twinkle = sin(iTime * 10.0 + sparkle * 100.0);
        if (twinkle > 0.5) col += vec3(0.5) * uVolume;
    }
    
    // Vignette para profundidad
    col *= 1.0 - smoothstep(0.5, 1.5, r);
    
    // Tone Mapping simple para evitar saturación extrema blanca
    col = col / (col + vec3(1.0));
    col = pow(col, vec3(0.4545)); // Gamma correction
    col *= 2.0; // Boost final

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
        pygame.display.set_caption('Preset 28: Neon Kinetic Mandala')

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
        self.audio_buffer[:l] = raw[:l] * 10.0 

    def update_fft(self):
        fft = np.abs(np.fft.rfft(self.audio_buffer))
        fft = fft / SAMPLES * 10.0 
        
        l = min(len(fft), FFT_SIZE)
        # Suavizado temporal de la textura FFT para menos jitter
        # Lerp entre estado anterior y nuevo
        self.fft_texture_data[:l] = self.fft_texture_data[:l] * 0.3 + fft[:l] * 0.7
        
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
        
        self.tex_fft = glGenTextures(1)
        glBindTexture(GL_TEXTURE_1D, self.tex_fft)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
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
