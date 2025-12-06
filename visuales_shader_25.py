#!/usr/bin/env python3
"""
Preset 25: Analog XY Oscilloscope + Glitch VFX
Category: Audio Reactive
Osciloscopio XY (Lissajous) con estela y efectos de Glitch/VFX reactivos.
Simula un monitor vectorial CRT dañado o interferencias VHS.

Característiques:
- Mode XY: X=Audio, Y=Audio(Phase)
- Estela: Persistencia de buffers anteriores
- VFX Audio Reactivos (Frecuencias Altas/Kick):
    1. Deflection Glitch: El haz se deforma y tiembla (Vertex Displacement)
    2. RGB Split: Separación de canales de color (Chromatic Aberration vectorial)
    3. Intensity Boost: El brillo aumenta con la intensidad
"""

from __future__ import division
import pygame
import pygame._sdl2.audio as sdl_audio
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np
import collections

# Configuración
SAMPLES = 1024        # Tamaño del buffer de audio
HISTORY_LENGTH = 30   # Cuadros de estela (Reducido un poco para performance x3 draws)
LINE_WIDTH = 2.0
XY_PHASE = 15         # Desfase estéreo

VERTEX_SHADER = """
#version 330 core
layout(location = 0) in float audio_val_x;
layout(location = 1) in float audio_val_y;

uniform float uScale;
uniform float uAspectRatio;
uniform vec2 uOffset;       # Desplazamiento (para RGB split)
uniform float uGlitch;      # Intensidad de glitch (0.0 - 1.0)
uniform float uTime;

// Pseudo-random
float hash(float n) { return fract(sin(n) * 43758.5453123); }
float noise(float p) {
    float fl = floor(p);
    float fc = fract(p);
    return mix(hash(fl), hash(fl + 1.0), fc);
}

void main() {
    vec2 pos = vec2(audio_val_x, audio_val_y);
    
    // Escalar
    pos *= uScale;
    
    // 1. Deflection Glitch (Vertex Displacement)
    if (uGlitch > 0.05) {
        // Ruido de alta frecuencia para "temblor"
        float shake = (hash(uTime * 100.0 + gl_VertexID) - 0.5) * uGlitch * 0.1;
        
        // Ondulación tipo VHS "tracking error"
        float wave = sin(pos.y * 10.0 + uTime * 20.0) * uGlitch * 0.2;
        
        // Instabilidad vertical
        float v_jump = noise(uTime * 15.0) * uGlitch * 0.5;
        if (v_jump > 0.4) pos.y += v_jump;
        
        pos.x += shake + wave;
        pos.y += shake;
    }

    // 2. RGB Split Offset
    pos += uOffset;

    // Corregir aspecto
    pos.x *= uAspectRatio; 
    
    gl_Position = vec4(pos, 0.0, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 330 core
out vec4 fragColor;
uniform vec4 uColor;

void main() {
    fragColor = uColor;
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
        
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
        
        self.screen = pygame.display.set_mode(
            (initial_w, initial_h),
            DOUBLEBUF | OPENGL | RESIZABLE
        )
        pygame.display.set_caption('Preset 25: Scope Glitch')

        # Audio & Data
        self.audio_buffer = np.zeros(SAMPLES, dtype=np.float32)
        self.trail_history = collections.deque(maxlen=HISTORY_LENGTH)
        self.high_freq_energy = 0.0 # Para detectar glitches
        
        self.setup_audio()
        self.setup_shaders()
        
        self.clock = pygame.time.Clock()
        self.start_time = pygame.time.get_ticks()

        # GL Setup
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE) # Additive blending
        glEnable(GL_LINE_SMOOTH)
        glLineWidth(LINE_WIDTH)
        glClearColor(0.05, 0.05, 0.05, 1.0) # Negro casi puro (CRT apagado no es negro 100%)

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
        self.audio_buffer[:l] = raw[:l] * 20.0 # Gain

    def analyze_audio(self):
        # FFT simple para detectar agudos/transitorios
        if np.max(np.abs(self.audio_buffer)) < 0.01:
            self.high_freq_energy *= 0.9
            return

        fft = np.abs(np.fft.rfft(self.audio_buffer))
        # Normalizar por tamaño
        fft /= SAMPLES
        
        # Banda alta (aprox top 30% bins)
        h_band = np.mean(fft[int(len(fft)*0.7):]) * 100.0
        
        # Suavizado
        self.high_freq_energy = self.high_freq_energy * 0.6 + h_band * 0.4

    def setup_shaders(self):
        vs = shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER)
        fs = shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vs, fs)
        
        self.u_scale = glGetUniformLocation(self.shader, 'uScale')
        self.u_aspect = glGetUniformLocation(self.shader, 'uAspectRatio')
        self.u_color = glGetUniformLocation(self.shader, 'uColor')
        self.u_offset = glGetUniformLocation(self.shader, 'uOffset')
        self.u_glitch = glGetUniformLocation(self.shader, 'uGlitch')
        self.u_time = glGetUniformLocation(self.shader, 'uTime')
        
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, SAMPLES * 4 * 2, None, GL_DYNAMIC_DRAW)
        
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        glEnableVertexAttribArray(0)
        glEnableVertexAttribArray(1)

    def update_trail(self):
        self.analyze_audio()
        
        data = self.audio_buffer
        offset = XY_PHASE
        if len(data) > offset:
            x = data[:-offset]
            y = data[offset:]
            points = np.column_stack((x, y)).astype(np.float32)
            self.trail_history.append(points)

    def render(self):
        w, h = self.screen.get_size()
        glViewport(0, 0, w, h)
        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(self.shader)
        
        t = (pygame.time.get_ticks() - self.start_time) / 1000.0
        glUniform1f(self.u_time, t)
        
        # Glitch logic
        # Mapear energía alta a intensidad de glitch (0 a 1)
        glitch_intensity = min(1.0, self.high_freq_energy * 0.5)
        # Threshold: Solo glitch si hay suficiente energía
        if glitch_intensity < 0.15: glitch_intensity = 0.0
        
        glUniform1f(self.u_glitch, glitch_intensity)
        glUniform1f(self.u_aspect, 1.0) # Sin distorsión aspect
        
        if len(self.trail_history) == 0:
            pygame.display.flip()
            return

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        
        # Render Loop
        total = len(self.trail_history)
        
        # DECISIÓN: Si hay mucho glitch, dibujamos RGB Split (3 pases). Si no, normal (1 pase).
        is_glitching = glitch_intensity > 0.2
        passes = ['R', 'G', 'B'] if is_glitching else ['Normal']
        
        for p_type in passes:
            
            # Configurar Color y Offset por pase
            if p_type == 'Normal':
                base_col = (0.2, 1.0, 0.4) # Verde Scope
                glUniform2f(self.u_offset, 0.0, 0.0)
            elif p_type == 'R':
                base_col = (1.0, 0.2, 0.2) # Rojo
                off = glitch_intensity * 0.05
                glUniform2f(self.u_offset, -off, 0.0)
            elif p_type == 'G':
                base_col = (0.2, 1.0, 0.2) # Verde
                glUniform2f(self.u_offset, 0.0, 0.0)
            elif p_type == 'B':
                base_col = (0.2, 0.2, 1.0) # Azul
                off = glitch_intensity * 0.05
                glUniform2f(self.u_offset, off, 0.0)

            # Dibujar historial
            for i, points in enumerate(self.trail_history):
                prog = (i + 1) / total
                alpha = prog * prog
                
                # Si estamos en glitch, el alpha puede parpadear
                if is_glitching:
                    alpha *= (0.5 + 0.5 * np.sin(t * 50.0))
                
                glUniform4f(self.u_color, 
                           base_col[0] * alpha, 
                           base_col[1] * alpha, 
                           base_col[2] * alpha, 
                           alpha)
                
                glUniform1f(self.u_scale, 0.8)
                
                # Solo subir datos una vez por frame (optimización)
                # Pero aquí iteramos pases. El VBO data es el mismo, no cambia.
                # Debemos asegurarnos de no resubir datos en cada pase 'p_type'.
                # Podemos subirlo solo en el primer pase del loop externo?
                # Simplificación: Subir siempre. Python overhead > GPU bandwidth aquí.
                if p_type == passes[0]: 
                     glBufferData(GL_ARRAY_BUFFER, points.nbytes, points, GL_DYNAMIC_DRAW)
                
                glVertexAttribPointer(0, 1, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(0))
                glVertexAttribPointer(1, 1, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(4))
                
                glDrawArrays(GL_LINE_STRIP, 0, len(points))
                
                # Punto brillante al final (solo en pase G o Normal)
                if i == total - 1 and (p_type == 'Normal' or p_type == 'G'):
                    glPointSize(5.0 + glitch_intensity * 10.0) # Punto explota con glitch
                    glDrawArrays(GL_POINTS, len(points)-1, 1)

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    running = False
            
            self.update_trail()
            self.render()
            self.clock.tick(60)
            
        if hasattr(self, 'dev') and self.dev:
            self.dev.close()
        pygame.quit()

if __name__ == '__main__':
    ShaderVisualEngine().run()