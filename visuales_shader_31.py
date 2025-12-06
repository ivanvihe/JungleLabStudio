#!/usr/bin/env python3
"""
Preset 31: Triple Oscilloscope - Drones Visualizer
Category: Audio Reactive / Oscilloscope / Ambient
Tres osciloscopios simultáneos partiendo del centro,
cada uno dibujando patrones basados en diferentes rangos de frecuencia.
Diseñado para visualizar drones y sonidos ambientales sintéticos.

Características:
- 3 osciloscopios independientes (bajos, medios, altos)
- Cada uno con su propio color (verde, cyan, magenta)
- Patrones Lissajous suaves y fluidos
- Estela CRT clásica con persistencia
- Todos parten desde el centro
- Reactivo a frecuencias y dBs
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
SAMPLES = 2048  # Buffer más grande para mejor resolución de frecuencias
HISTORY_LENGTH = 100  # Cuadros de estela (1.5-2 segundos a 60fps)
LINE_WIDTH = 2.5
DRAW_SAMPLES = 768  # Puntos por osciloscopio (mayor definición)

VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec2 position;
uniform float uScale;
uniform vec2 uOffset;
void main() {
    vec2 pos = position * uScale + uOffset;
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
        pygame.display.set_caption('Preset 31: Triple Oscilloscope')

        # Audio & Data
        self.audio_buffer = np.zeros(SAMPLES, dtype=np.float32)

        # Tres historiales independientes (uno por osciloscopio)
        self.trail_low = collections.deque(maxlen=HISTORY_LENGTH)
        self.trail_mid = collections.deque(maxlen=HISTORY_LENGTH)
        self.trail_high = collections.deque(maxlen=HISTORY_LENGTH)

        # Análisis de frecuencias
        self.low_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0
        self.overall_level = 0.0

        self.setup_audio()
        self.setup_shaders()

        self.clock = pygame.time.Clock()
        self.start_time = pygame.time.get_ticks()

        # GL Setup
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # Additive blending
        glEnable(GL_LINE_SMOOTH)
        glLineWidth(LINE_WIDTH)
        glClearColor(0.0, 0.0, 0.0, 1.0)  # Negro puro

    def setup_audio(self):
        try:
            devices = sdl_audio.get_audio_device_names(True)
            print("Audio inputs:", devices)
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
        self.audio_buffer[:l] = raw[:l] * 15.0  # Gain para mejor visibilidad

    def analyze_audio(self):
        """Analiza el audio y separa en tres bandas de frecuencia"""
        if np.max(np.abs(self.audio_buffer)) < 0.001:
            self.low_energy *= 0.95
            self.mid_energy *= 0.95
            self.high_energy *= 0.95
            self.overall_level *= 0.95
            return

        # FFT para análisis de frecuencias
        fft = np.abs(np.fft.rfft(self.audio_buffer))
        fft_normalized = fft / SAMPLES

        # Nivel general (RMS) - muy suavizado
        rms = np.sqrt(np.mean(self.audio_buffer**2))
        self.overall_level += (rms - self.overall_level) * 0.08

        # Banda baja (20-250 Hz aprox) - bins 1-12 - muy suavizado
        low = np.mean(fft_normalized[1:13]) * 50.0
        self.low_energy += (low - self.low_energy) * 0.1

        # Banda media (250-2000 Hz aprox) - bins 13-95 - muy suavizado
        mid = np.mean(fft_normalized[13:96]) * 30.0
        self.mid_energy += (mid - self.mid_energy) * 0.09

        # Banda alta (2000-8000 Hz aprox) - bins 96-380 - muy suavizado
        high = np.mean(fft_normalized[96:381]) * 20.0
        self.high_energy += (high - self.high_energy) * 0.08

    def create_lissajous_pattern(self, band_type):
        """
        Crea patrones de Lissajous diferentes según la banda de frecuencia
        Todos parten del centro (0, 0)
        Con variaciones orgánicas para aspecto más natural
        """
        # Downsampling para mejor rendimiento
        step = len(self.audio_buffer) // DRAW_SAMPLES
        samples = self.audio_buffer[::step][:DRAW_SAMPLES]

        t = np.linspace(0, 2 * np.pi, len(samples))

        if band_type == 'low':
            # Bajos: Patrón circular con modulación muy lenta y orgánica
            # Más lento, se acelera con energía
            base_speed = 0.008
            energy_speed = self.low_energy * 0.008
            phase_offset = len(self.trail_low) * (base_speed + energy_speed)

            # Variación orgánica lenta en las frecuencias (respiración natural)
            organic_drift_x = np.sin(phase_offset * 0.3) * 0.12
            organic_drift_y = np.cos(phase_offset * 0.25) * 0.1

            freq_x = 0.8 + self.low_energy * 0.2 + organic_drift_x
            freq_y = 0.8 + self.low_energy * 0.15 + organic_drift_y

            # Más grande y expansivo con ligera asimetría orgánica (1.3x más grande)
            x = samples * np.cos(t * freq_x + phase_offset) * (1.3 + self.low_energy * 0.5)
            y = samples * np.sin(t * freq_y + phase_offset) * (1.3 + self.low_energy * 0.5)

            # Añadir ruido orgánico sutil (como imperfecciones naturales)
            organic_noise_x = np.sin(t * 7.3 + phase_offset * 0.8) * 0.02
            organic_noise_y = np.cos(t * 6.7 + phase_offset * 0.7) * 0.02
            x += organic_noise_x * (0.3 + self.low_energy * 0.4)
            y += organic_noise_y * (0.3 + self.low_energy * 0.4)

        elif band_type == 'mid':
            # Medios: Patrón que se metamorfosea según energía con flujo orgánico
            # Más lento, se acelera con energía
            base_speed = 0.01
            energy_speed = self.mid_energy * 0.01
            phase_offset = len(self.trail_mid) * (base_speed + energy_speed)

            # Deriva orgánica más pronunciada para medios
            organic_drift_x = np.sin(phase_offset * 0.35) * 0.15
            organic_drift_y = np.cos(phase_offset * 0.28) * 0.12

            freq_x = 1.5 + self.mid_energy * 0.8 + organic_drift_x
            freq_y = 0.9 + self.mid_energy * 0.6 + organic_drift_y

            # Factor de metamorfosis basado en energía con modulación orgánica
            morph_factor = self.mid_energy * 0.5 + np.sin(phase_offset * 0.2) * 0.15

            # Mezcla entre figura 8 y patrón más complejo (1.2x más grande)
            x = samples * (np.sin(t * freq_x + phase_offset) * (1.0 - morph_factor) +
                          np.sin(t * freq_x * 1.5 + phase_offset) * morph_factor) * (0.85 + self.mid_energy * 0.5)
            y = samples * (np.cos(t * freq_y + phase_offset) * (1.0 - morph_factor) +
                          np.sin(t * freq_y * 1.3 + phase_offset * 1.5) * morph_factor) * (0.85 + self.mid_energy * 0.5)

            # Ruido orgánico para medios (más sutil)
            organic_noise_x = np.sin(t * 8.1 + phase_offset) * 0.015
            organic_noise_y = np.cos(t * 7.9 + phase_offset * 0.9) * 0.015
            x += organic_noise_x * (0.4 + self.mid_energy * 0.3)
            y += organic_noise_y * (0.4 + self.mid_energy * 0.3)

        else:  # high
            # Altos: Patrón complejo tipo trébol con imperfecciones naturales
            # Más lento, se acelera con energía
            base_speed = 0.012
            energy_speed = self.high_energy * 0.012
            phase_offset = len(self.trail_high) * (base_speed + energy_speed)

            # Variaciones orgánicas sutiles para altos
            organic_drift_x = np.sin(phase_offset * 0.4) * 0.1
            organic_drift_y = np.cos(phase_offset * 0.32) * 0.08

            freq_x = 2.2 + self.high_energy * 0.4 + organic_drift_x
            freq_y = 1.6 + self.high_energy * 0.3 + organic_drift_y

            # Más grande con asimetría natural (1.2x más grande)
            x = samples * np.sin(t * freq_x + phase_offset) * (1.0 + self.high_energy * 0.7)
            y = samples * np.cos(t * freq_y + phase_offset) * (1.0 + self.high_energy * 0.7)

            # Ruido orgánico para altos (muy fino)
            organic_noise_x = np.sin(t * 9.7 + phase_offset * 1.1) * 0.01
            organic_noise_y = np.cos(t * 8.3 + phase_offset * 0.95) * 0.01
            x += organic_noise_x * (0.5 + self.high_energy * 0.3)
            y += organic_noise_y * (0.5 + self.high_energy * 0.3)

        # Aplicar suavizado más fuerte (media móvil)
        if len(x) > 5:
            window_size = 5  # Más suavizado
            x = np.convolve(x, np.ones(window_size)/window_size, mode='same')
            y = np.convolve(y, np.ones(window_size)/window_size, mode='same')

        # Clip para evitar overflow
        x = np.clip(x, -1.0, 1.0)
        y = np.clip(y, -1.0, 1.0)

        points = np.column_stack((x, y)).astype(np.float32)
        return points

    def update_trails(self):
        """Actualiza los tres historiales de trayectorias"""
        self.analyze_audio()

        # Solo añadir nuevos puntos si hay señal
        if self.overall_level > 0.01:
            self.trail_low.append(self.create_lissajous_pattern('low'))
            self.trail_mid.append(self.create_lissajous_pattern('mid'))
            self.trail_high.append(self.create_lissajous_pattern('high'))

    def setup_shaders(self):
        vs = shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER)
        fs = shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vs, fs)

        self.u_scale = glGetUniformLocation(self.shader, 'uScale')
        self.u_offset = glGetUniformLocation(self.shader, 'uOffset')
        self.u_color = glGetUniformLocation(self.shader, 'uColor')

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, DRAW_SAMPLES * 8, None, GL_DYNAMIC_DRAW)

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)

    def render_oscilloscope(self, trail, color_base, energy, orbital=False, intensity_multiplier=1.0):
        """Renderiza un osciloscopio con su estela"""
        if len(trail) == 0:
            return

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

        total = len(trail)

        for i, points in enumerate(trail):
            if len(points) == 0:
                continue

            # Fade muy gradual y suave
            progress = (i + 1) / total
            # Fade cúbico para desvanecimiento más suave
            alpha = progress * progress * progress

            # Intensificar con la energía de la banda (más sutil)
            alpha *= (0.4 + energy * 0.4) * intensity_multiplier

            # Color con fade
            color = (
                color_base[0] * alpha,
                color_base[1] * alpha,
                color_base[2] * alpha,
                alpha
            )

            glUniform4f(self.u_color, *color)
            glUniform1f(self.u_scale, 1.0)  # Escala global más grande

            # Calcular offset orbital si está activado
            if orbital:
                # Tiempo basado en el frame actual
                t = (pygame.time.get_ticks() - self.start_time) / 1000.0
                # Radio de órbita basado en energía (más lejos del centro)
                orbit_radius = 0.28 + energy * 0.3
                # Velocidad de órbita (muy lenta, se acelera con energía)
                orbit_speed = 0.08 + energy * 0.08
                # Ángulo de órbita progresivo
                orbit_angle = t * orbit_speed + (i / total) * 6.28

                offset_x = np.cos(orbit_angle) * orbit_radius
                offset_y = np.sin(orbit_angle) * orbit_radius

                glUniform2f(self.u_offset, offset_x, offset_y)
            else:
                glUniform2f(self.u_offset, 0.0, 0.0)  # Centro

            glBufferData(GL_ARRAY_BUFFER, points.nbytes, points, GL_DYNAMIC_DRAW)
            glDrawArrays(GL_LINE_STRIP, 0, len(points))

            # Punto brillante al final (solo en el frame más reciente)
            if i == total - 1:
                glPointSize(5.0 + energy * 6.0)
                glUniform4f(self.u_color,
                           color_base[0] * 1.2,
                           color_base[1] * 1.2,
                           color_base[2] * 1.2,
                           0.9)
                glDrawArrays(GL_POINTS, len(points)-1, 1)

    def render(self):
        w, h = self.screen.get_size()
        glViewport(0, 0, w, h)
        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(self.shader)

        # Colores clásicos de osciloscopio
        color_low = (0.2, 1.0, 0.3)    # Verde clásico (bajos)
        color_mid = (0.2, 0.8, 1.0)    # Cyan (medios)
        color_high = (1.0, 0.3, 0.8)   # Magenta (altos)

        # Renderizar los tres osciloscopios
        # Primero los bajos (atrás) - fijos en el centro - intensidad reducida
        self.render_oscilloscope(self.trail_low, color_low, self.low_energy, orbital=False, intensity_multiplier=0.4)

        # Luego los medios (medio) - ORBITANDO alrededor del centro
        self.render_oscilloscope(self.trail_mid, color_mid, self.mid_energy, orbital=True, intensity_multiplier=1.0)

        # Por último los altos (adelante) - fijos en el centro
        self.render_oscilloscope(self.trail_high, color_high, self.high_energy, orbital=False, intensity_multiplier=1.0)

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    running = False

            self.update_trails()
            self.render()
            self.clock.tick(60)

        if hasattr(self, 'dev') and self.dev:
            self.dev.close()
        pygame.quit()

if __name__ == '__main__':
    ShaderVisualEngine().run()
