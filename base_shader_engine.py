#!/usr/bin/env python3
"""
Base Shader Engine - Template para todos los presets
Incluye viewport centrado con líneas inclinadas indicadoras
"""

from __future__ import division
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL import shaders
import mido
from numpy import array

# Shader para dibujar las franjas con líneas inclinadas
FRANJA_VERTEX = """
#version 330 core
layout(location = 0) in vec2 vPos;
void main() { gl_Position = vec4(vPos, 0.0, 1.0); }
"""

FRANJA_FRAGMENT = """
#version 330 core
out vec4 fragColor;
uniform vec2 iResolution;

void main() {
    vec2 uv = gl_FragCoord.xy / iResolution.xy;

    // Líneas inclinadas diagonales
    float line = mod(gl_FragCoord.x + gl_FragCoord.y, 40.0);
    float pattern = step(line, 2.0) * 0.15;

    fragColor = vec4(pattern, pattern, pattern, 1.0);
}
"""

class BaseShaderEngine:
    """Clase base con viewport optimizado y líneas indicadoras"""

    def __init__(self, preset_name="Base Preset"):
        pygame.init()

        # Target resolution (9:16 vertical)
        self.target_width = 1080
        self.target_height = 1920
        self.target_aspect = self.target_width / self.target_height

        # Ventana inicial
        initial_height = 900
        initial_width = int(initial_height * self.target_aspect)

        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)
        self.screen = pygame.display.set_mode(
            (initial_width, initial_height),
            DOUBLEBUF | OPENGL | RESIZABLE
        )
        pygame.display.set_caption(f'{preset_name} [9:16]')

        # Shader para las franjas
        self.setup_franja_shader()

        # MIDI state
        self.kick_pulse = 0.0
        self.kick_target = 0.0
        self.hat_glitch = 0.0
        self.tom1_morph = 0.0
        self.tom2_spin = 0.0

        self.midi_input = self._connect_midi()
        self.clock = pygame.time.Clock()
        self.start_time = pygame.time.get_ticks()

    def setup_franja_shader(self):
        """Setup shader para dibujar franjas con líneas"""
        vs = shaders.compileShader(FRANJA_VERTEX, GL_VERTEX_SHADER)
        fs = shaders.compileShader(FRANJA_FRAGMENT, GL_FRAGMENT_SHADER)
        self.franja_shader = shaders.compileProgram(vs, fs)
        self.franja_resolution = glGetUniformLocation(self.franja_shader, 'iResolution')

        # Quad para las franjas
        verts = array([-1, -1, 1, -1, 1, 1, -1, 1], dtype='f')
        self.franja_vao = glGenVertexArrays(1)
        glBindVertexArray(self.franja_vao)
        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, verts, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)

    def _connect_midi(self):
        """Conectar a Circuit Tracks"""
        try:
            for port in mido.get_input_names():
                if 'CIRCUIT' in port.upper() or 'TRACKS' in port.upper():
                    return mido.open_input(port)
            print("⚠️  Circuit Tracks not found. Demo mode (K/H/T/Y)")
        except:
            pass
        return None

    def process_midi(self):
        """Procesar MIDI messages"""
        if self.midi_input:
            for msg in self.midi_input.iter_pending():
                if msg.type == 'note_on' and msg.velocity > 0:
                    self.handle_note(msg.note, msg.velocity / 127.0)

    def handle_note(self, note, velocity):
        """Override en subclases"""
        pass

    def update_params(self):
        """Smooth interpolation"""
        self.kick_pulse += (self.kick_target - self.kick_pulse) * 0.15
        self.kick_target *= 0.92
        self.hat_glitch *= 0.88
        self.tom1_morph *= 0.90
        self.tom2_spin *= 0.93

    def calculate_viewport(self, w, h):
        """Calcular viewport centrado con aspect ratio 9:16"""
        aspect = w / h
        if aspect > self.target_aspect:
            # Pillarboxing
            vh = h
            vw = int(vh * self.target_aspect)
            return (w - vw) // 2, 0, vw, vh
        else:
            # Letterboxing
            vw = w
            vh = int(vw / self.target_aspect)
            return 0, (h - vh) // 2, vw, vh

    def render_franjas(self, w, h, vx, vw):
        """Dibujar franjas con líneas inclinadas en los laterales"""
        if vx > 0:  # Solo si hay pillarboxing
            glUseProgram(self.franja_shader)
            glUniform2f(self.franja_resolution, float(w), float(h))
            glBindVertexArray(self.franja_vao)

            # Franja izquierda
            glViewport(0, 0, vx, h)
            glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

            # Franja derecha
            glViewport(vx + vw, 0, vx, h)
            glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
