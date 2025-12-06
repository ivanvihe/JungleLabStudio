#!/usr/bin/env python3
"""
Preset 32: Geometric Minimalism - Cross Grid
Category: Audio Reactive / Geometric / MIDI Reactive
Cubos minimalistas en formación de cruz que reaccionan al kick y audio.

Características:
- 4 filas de cubos en forma de cruz (arriba, abajo, izquierda, derecha)
- Bounce suave sincronizado con kick MIDI (nota 60)
- Efectos VFX de colores reactivos al audio de entrada
- Estilo minimalista con glow y colores dinámicos
"""

from __future__ import division
import pygame
import pygame._sdl2.audio as sdl_audio
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np
import mido

# Configuración
SAMPLES = 1024  # Menor buffer para latencia ultra baja

# Notas MIDI
KICK_NOTE = 60
CLOSEHAT_NOTE = 62
TOM1_NOTE = 64
TOM2_NOTE = 65

VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec2 position;
out vec2 vUV;
void main() {
    vUV = position * 0.5 + 0.5;
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 330 core
in vec2 vUV;
out vec4 fragColor;

uniform float iTime;
uniform vec2 iResolution;
uniform float iLow;
uniform float iMid;
uniform float iHigh;
uniform float iVolume;
uniform float iKickPulse;  // Bounce del kick MIDI

#define MAX_STEPS 80
#define MAX_DIST 50.0
#define SURF_DIST 0.001

// Rotación 2D
mat2 rot(float a) {
    float s = sin(a), c = cos(a);
    return mat2(c, -s, s, c);
}

// SDF Caja
float sdBox(vec3 p, vec3 b) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
}

// Paleta de colores vibrantes (Iquilez)
vec3 palette(float t) {
    vec3 a = vec3(0.5, 0.5, 0.5);
    vec3 b = vec3(0.5, 0.5, 0.5);
    vec3 c = vec3(1.0, 1.0, 1.0);
    vec3 d = vec3(0.00, 0.33, 0.67);
    return a + b * cos(6.28318 * (c * t + d));
}

// Escena: 4 filas de cubos en forma de cruz
float GetDist(vec3 p) {
    vec3 p_orig = p;

    // Bounce suave del kick (afecta el tamaño de todos los cubos)
    float bounce = 1.0 + iKickPulse * 0.15;  // Bounce muy suave: 0-15%

    float d = MAX_DIST;

    // Configuración de cubos
    float cubeSize = 0.3 * bounce;
    float spacing = 1.2;
    int numCubes = 3;  // 3 cubos por fila (más el central = 4 en cada dirección)

    // Cubo central (común a ambas filas)
    float centerCube = sdBox(p, vec3(cubeSize));
    d = min(d, centerCube);

    // Fila horizontal (izquierda y derecha)
    for(int i = 1; i <= numCubes; i++) {
        vec3 pLeft = p - vec3(-spacing * float(i), 0.0, 0.0);
        vec3 pRight = p - vec3(spacing * float(i), 0.0, 0.0);

        float cubeLeft = sdBox(pLeft, vec3(cubeSize));
        float cubeRight = sdBox(pRight, vec3(cubeSize));

        d = min(d, cubeLeft);
        d = min(d, cubeRight);
    }

    // Fila vertical (arriba y abajo)
    for(int i = 1; i <= numCubes; i++) {
        vec3 pUp = p - vec3(0.0, spacing * float(i), 0.0);
        vec3 pDown = p - vec3(0.0, -spacing * float(i), 0.0);

        float cubeUp = sdBox(pUp, vec3(cubeSize));
        float cubeDown = sdBox(pDown, vec3(cubeSize));

        d = min(d, cubeUp);
        d = min(d, cubeDown);
    }

    return d;
}

// Raymarching
float RayMarch(vec3 ro, vec3 rd) {
    float dO = 0.0;
    for(int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + rd * dO;
        float dS = GetDist(p);
        dO += dS;
        if(dO > MAX_DIST || dS < SURF_DIST) break;
    }
    return dO;
}

// Normales
vec3 GetNormal(vec3 p) {
    float d = GetDist(p);
    vec2 e = vec2(0.01, 0);
    vec3 n = d - vec3(
        GetDist(p - e.xyy),
        GetDist(p - e.yxy),
        GetDist(p - e.yyx)
    );
    return normalize(n);
}

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.y;

    // Cámara fija mirando a la cruz
    vec3 ro = vec3(0.0, 0.0, -8.0);
    vec3 rd = normalize(vec3(uv.x, uv.y, 1.0));

    // Rotación suave de cámara
    rd.xy *= rot(sin(iTime * 0.1) * 0.1);

    float d = RayMarch(ro, rd);

    vec3 col = vec3(0.0);

    if(d < MAX_DIST) {
        vec3 p = ro + rd * d;
        vec3 n = GetNormal(p);

        // Iluminación
        vec3 lightPos = vec3(2.0, 3.0, -5.0);
        vec3 l = normalize(lightPos - p);
        float dif = clamp(dot(n, l), 0.2, 1.0);

        // Color base con paleta reactiva al audio
        float colorShift = iTime * 0.1 + iMid * 2.0;
        vec3 baseCol = palette(length(p.xy) * 0.3 + colorShift);

        // Fresnel
        float fresnel = pow(1.0 - abs(dot(rd, n)), 3.0);

        col = baseCol * dif;
        col += fresnel * vec3(1.0) * 0.5;

        // Glow reactivo al kick
        col += vec3(1.0, 0.3, 0.6) * iKickPulse * 0.8;
    }

    // Fondo oscuro
    vec3 bgCol = vec3(0.02, 0.02, 0.05);
    col = mix(bgCol, col, step(0.01, d - MAX_DIST * 0.99));

    // VFX de colores superpuestos (overlay) reactivo al audio
    vec2 uvScreen = gl_FragCoord.xy / iResolution.xy;
    float vfxIntensity = iVolume * 0.3;

    // Efecto de ondas de color
    float wave1 = sin(uvScreen.x * 10.0 + iTime * 2.0 + iLow * 5.0) * 0.5 + 0.5;
    float wave2 = sin(uvScreen.y * 10.0 - iTime * 1.5 + iMid * 5.0) * 0.5 + 0.5;

    vec3 vfxColor = palette(iTime * 0.2 + iHigh * 2.0);
    vec3 vfxOverlay = vfxColor * wave1 * wave2 * vfxIntensity;

    // Blend aditivo para efectos VFX
    col += vfxOverlay;

    // Vignette sutil
    float vignette = pow(16.0 * uvScreen.x * uvScreen.y * (1.0 - uvScreen.x) * (1.0 - uvScreen.y), 0.2);
    col *= vignette;

    fragColor = vec4(col, 1.0);
}
"""

class ShaderVisualEngine:
    def __init__(self):
        pygame.init()
        pygame.display.init()

        # High Definition Setup
        self.target_width = 1080
        self.target_height = 1920
        self.aspect_ratio = self.target_width / self.target_height
        initial_h = 900
        initial_w = int(initial_h * self.aspect_ratio)

        self.screen = pygame.display.set_mode(
            (initial_w, initial_h),
            DOUBLEBUF | OPENGL | RESIZABLE
        )
        pygame.display.set_caption('Preset 32: Geometric Cross')

        # Audio reactivity
        self.audio_buffer = np.zeros(SAMPLES, dtype=np.float32)
        self.low_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0
        self.volume = 0.0

        # MIDI reactivity
        self.kick_pulse = 0.0
        self.midi_input = None

        self.setup_audio()
        self.setup_midi()
        self.setup_shaders()
        self.setup_quad()
        self.clock = pygame.time.Clock()
        self.start_time = pygame.time.get_ticks()

    def setup_audio(self):
        try:
            devices = sdl_audio.get_audio_device_names(True)
            target = next((d for d in devices if "Scarlett" in d), devices[0] if devices else None)
            if target:
                self.dev = sdl_audio.AudioDevice(
                    target, True, 44100, sdl_audio.AUDIO_F32, 1, 1024, 0, self.callback
                )
                self.dev.pause(0)
        except Exception as e:
            print("Audio Init Failed (Running visual only):", e)

    def callback(self, dev, data):
        raw = np.frombuffer(data, dtype=np.float32)
        self.audio_buffer = raw

    def setup_midi(self):
        """Conectar al Circuit Tracks MIDI"""
        try:
            available_ports = mido.get_input_names()
            print("Puertos MIDI disponibles:")
            for port in available_ports:
                print(f"  - {port}")

            circuit_port = None
            for port in available_ports:
                if 'CIRCUIT' in port.upper() and 'TRACKS' in port.upper():
                    circuit_port = port
                    break

            if circuit_port:
                print(f"\nConectando a Circuit Tracks: {circuit_port}")
                self.midi_input = mido.open_input(circuit_port)
            else:
                print("\n[WARNING] Circuit Tracks no encontrado")
                if available_ports:
                    print(f"Usando: {available_ports[0]}")
                    self.midi_input = mido.open_input(available_ports[0])
        except Exception as e:
            print(f"Error conectando MIDI: {e}")
            print("Modo visual only (sin MIDI)")

    def handle_midi(self):
        """Procesar mensajes MIDI del Circuit Tracks"""
        if not self.midi_input:
            return

        for msg in self.midi_input.iter_pending():
            if msg.type == 'note_on' and msg.velocity > 0:
                # Kick trigger - bounce suave
                if msg.note == KICK_NOTE:
                    vel = msg.velocity / 127.0
                    self.kick_pulse = min(1.0, self.kick_pulse + vel * 0.6)

    def update_audio_vars(self):
        if len(self.audio_buffer) == 0: return

        fft = np.abs(np.fft.rfft(self.audio_buffer))
        self.volume = np.linalg.norm(self.audio_buffer) * 0.1

        # Smooth dampening
        self.low_energy  = self.low_energy * 0.9 + (np.mean(fft[0:10]) * 0.05) * 0.1
        self.mid_energy  = self.mid_energy * 0.9 + (np.mean(fft[10:50]) * 0.05) * 0.1
        self.high_energy = self.high_energy * 0.9 + (np.mean(fft[50:150]) * 0.05) * 0.1

        # Decay suave del kick pulse
        self.kick_pulse *= 0.92

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
            'iHigh': glGetUniformLocation(self.shader, 'iHigh'),
            'iVolume': glGetUniformLocation(self.shader, 'iVolume'),
            'iKickPulse': glGetUniformLocation(self.shader, 'iKickPulse')
        }

    def render(self):
        self.handle_midi()  # Procesar MIDI
        self.update_audio_vars()
        w, h = self.screen.get_size()
        glViewport(0, 0, w, h)
        glUseProgram(self.shader)

        t = (pygame.time.get_ticks() - self.start_time) / 1000.0

        glUniform1f(self.locs['iTime'], t)
        glUniform2f(self.locs['iResolution'], float(w), float(h))
        glUniform1f(self.locs['iLow'], self.low_energy)
        glUniform1f(self.locs['iMid'], self.mid_energy)
        glUniform1f(self.locs['iHigh'], self.high_energy)
        glUniform1f(self.locs['iVolume'], self.volume)
        glUniform1f(self.locs['iKickPulse'], self.kick_pulse)

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

        if self.midi_input:
            self.midi_input.close()
        pygame.quit()

if __name__ == '__main__':
    ShaderVisualEngine().run()