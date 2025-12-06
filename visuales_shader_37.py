#!/usr/bin/env python3
"""
Preset 37: Desert Swarm (Sand Particles & Sun Rays)
Category: Volumetric / Organic / Atmospheric
Simulación de partículas de arena/polvo volumétrico que se comportan como
bandadas (swarms) orgánicas, con iluminación de atardecer y rayos de sol (God Rays).

Características:
- Renderizado Volumétrico (Raymarching de densidad) para simular millones de partículas.
- Movimiento de fluidos (Curl Noise) para imitar el comportamiento de bandadas.
- Iluminación atmosférica con dispersión de luz (Sun Rays).
- Reactividad suave: La música altera la densidad y el color, no sacude la cámara.
"""

from __future__ import division
import pygame
import pygame._sdl2.audio as sdl_audio
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np
import mido
import random

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

// MIDI Params
uniform float iTurbulence; // Modifica el ruido (CC)
uniform float iSunIntensity; // Intensidad del sol (CC)
uniform float iGlitch;     // Glitch visual (Note)

// --------------------------------------------------------
// Noise & FBM Functions
// --------------------------------------------------------
mat2 rot(float a) { float s=sin(a), c=cos(a); return mat2(c,-s,s,c); }

float hash(float n) { return fract(sin(n) * 43758.5453123); }

float noise(vec3 x) {
    vec3 p = floor(x);
    vec3 f = fract(x);
    f = f*f*(3.0-2.0*f);
    float n = p.x + p.y*57.0 + 113.0*p.z;
    return mix(mix(mix( hash(n+  0.0), hash(n+  1.0),f.x),
                   mix( hash(n+ 57.0), hash(n+ 58.0),f.x),f.y),
               mix(mix( hash(n+113.0), hash(n+114.0),f.x),
                   mix( hash(n+170.0), hash(n+171.0),f.x),f.y),f.z);
}

// Fractal Brownian Motion para dar textura de "arena"
float fbm(vec3 p) {
    float f = 0.0;
    float w = 0.5;
    for(int i=0; i<5; i++) {
        f += w * noise(p);
        p *= 2.0;
        w *= 0.5;
    }
    return f;
}

// --------------------------------------------------------
// Volumetric Map (Density)
// --------------------------------------------------------
float map(vec3 p) {
    // Movimiento fluido (Flow)
    vec3 q = p;
    
    // Desplazamiento lento por el viento/tiempo
    q.x += iTime * 0.2;
    q.y -= iTime * 0.1;
    
    // Deformación orgánica (Swarm behavior simulado)
    // El audio (iLow) empuja las partículas suavemente
    float flow = iTime * 0.5 + iLow * 0.1;
    q.x += sin(q.z * 0.5 + flow) * 1.0;
    q.z += cos(q.y * 0.5 + flow) * 1.0;
    
    // Densidad base: Esferas deformadas dispersas
    float d = length(q) - 3.0;
    
    // Añadir textura de arena detallada
    // iTurbulence añade caos a la formación
    float sand = fbm(q * 2.0 + vec3(iTurbulence));
    
    // Forma final: Nube densa con huecos
    return max(-(length(p) - 1.0), sand - 0.4); 
}

// --------------------------------------------------------
// Main Rendering
// --------------------------------------------------------
void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.y;
    
    // --- Camera ---
    vec3 ro = vec3(0.0, 0.0, -4.0);
    vec3 rd = normalize(vec3(uv, 1.0));
    
    // Rotación suave de cámara (Mouse/Idle)
    ro.xz *= rot(iTime * 0.1);
    rd.xz *= rot(iTime * 0.1);

    // --- Volumetric Marching ---
    vec3 p = ro;
    vec3 col = vec3(0.0);
    float tot_density = 0.0;
    
    // Posición del Sol
    vec3 sunPos = normalize(vec3(0.5, 0.4, 0.5));
    
    // Raymarching de volumen (acumulativo)
    // Simula luz atravesando polvo/arena
    for(int i=0; i<64; i++) {
        float dens = map(p);
        
        // Si estamos dentro de la "arena" (densidad > threshold)
        if(dens > 0.01) {
            float dens_factor = dens * 0.05; // Opacidad parcial
            tot_density += dens_factor;
            
            // Color Arena/Oro
            vec3 sandColor = vec3(0.9, 0.7, 0.4); // Dorado base
            
            // Variación de color con música (Sutil)
            sandColor += vec3(iHigh * 0.5, iLow * 0.2, 0.0);
            
            // Iluminación direccional (Sol) dentro del volumen
            float sunDif = clamp(dot(normalize(p), sunPos), 0.0, 1.0);
            
            // Acumular color
            col += sandColor * dens_factor * (0.5 + sunDif * 2.0);
            
            // Auto-sombreado (densidad absorbe luz)
            col *= 1.0 - tot_density * 0.1;
        }
        
        p += rd * 0.15; // Step size
        if(tot_density > 1.0) break; // Saturación
    }
    
    // --- Background & Sun ---
    vec3 bg = vec3(0.6, 0.4, 0.2) * 0.2; // Fondo atardecer oscuro
    // Gradiente de cielo
    bg = mix(bg, vec3(0.1, 0.1, 0.3), uv.y + 0.5);
    
    // Dibujar Sol
    float sun = clamp(dot(rd, sunPos), 0.0, 1.0);
    bg += vec3(1.0, 0.9, 0.6) * pow(sun, 50.0) * iSunIntensity; // Sol disco
    bg += vec3(1.0, 0.6, 0.3) * pow(sun, 5.0) * 0.5; // Sol glow
    
    // God Rays (Simulado simple)
    // Si miramos al sol y hay densidad, aumentamos el brillo
    col += bg * (1.0 - tot_density * 0.8);
    
    // --- Glitch VFX (Natural/Organic) ---
    // Aberración cromática solo en golpes fuertes (iHigh)
    if (iGlitch > 0.1 || iHigh > 0.6) {
        float shift = (iGlitch + iHigh) * 0.01;
        // Tinte de canales simulando aberración
        col.r += shift;
        col.b -= shift;
        
        // Ruido de grano (Grain)
        col += (hash(dot(uv, vec2(iTime))) - 0.5) * 0.2;
    }

    // Tone mapping & Gamma
    col = smoothstep(0.0, 1.0, col);
    col = pow(col, vec3(0.4545));
    
    fragColor = vec4(col, 1.0);
}
"""

class DesertSwarmPreset:
    def __init__(self):
        pygame.init()
        pygame.display.init()
        
        self.target_width = 1080
        self.target_height = 1920
        self.aspect_ratio = self.target_width / self.target_height
        initial_h = 900
        initial_w = int(initial_h * self.aspect_ratio)

        self.screen = pygame.display.set_mode((initial_w, initial_h), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption('Preset 37: Desert Swarm')

        # Audio
        self.audio_buffer = np.zeros(SAMPLES, dtype=np.float32)
        self.low = 0.0; self.mid = 0.0; self.high = 0.0
        self.setup_audio()

        # MIDI
        self.midi_input = self.connect_midi()
        self.midi_turbulence = 0.0
        self.midi_sun = 1.0
        self.midi_glitch = 0.0

        self.setup_shaders()
        self.setup_quad()
        self.clock = pygame.time.Clock()
        self.start_time = pygame.time.get_ticks()

    def connect_midi(self):
        try:
            for port in mido.get_input_names():
                if 'CIRCUIT' in port.upper() or 'TRACKS' in port.upper():
                    print(f"MIDI Connected: {port}")
                    return mido.open_input(port)
        except: pass
        return None

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

    def process_midi(self):
        self.midi_glitch *= 0.9 # Decay
        if self.midi_input:
            for msg in self.midi_input.iter_pending():
                if msg.type == 'control_change':
                    norm = msg.value / 127.0
                    if msg.control == 19: # Knob 1
                        self.midi_turbulence = norm * 5.0
                    elif msg.control == 74: # Knob 2
                        self.midi_sun = norm * 2.0 + 0.5
                if msg.type == 'note_on':
                    self.midi_glitch = msg.velocity / 127.0

    def update_audio(self):
        if len(self.audio_buffer) == 0: return
        fft = np.abs(np.fft.rfft(self.audio_buffer))
        self.low  = self.low * 0.95 + np.mean(fft[0:10]) * 0.05
        self.mid  = self.mid * 0.95 + np.mean(fft[10:50]) * 0.05
        self.high = self.high * 0.9 + np.mean(fft[50:150]) * 0.1

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
            'iTurbulence': glGetUniformLocation(self.shader, 'iTurbulence'),
            'iSunIntensity': glGetUniformLocation(self.shader, 'iSunIntensity'),
            'iGlitch': glGetUniformLocation(self.shader, 'iGlitch')
        }

    def render(self):
        self.update_audio()
        self.process_midi()
        w, h = self.screen.get_size()
        glViewport(0, 0, w, h)
        glUseProgram(self.shader)
        
        glUniform1f(self.locs['iTime'], (pygame.time.get_ticks() - self.start_time) / 1000.0)
        glUniform2f(self.locs['iResolution'], float(w), float(h))
        glUniform1f(self.locs['iLow'], self.low)
        glUniform1f(self.locs['iMid'], self.mid)
        glUniform1f(self.locs['iHigh'], self.high)
        glUniform1f(self.locs['iTurbulence'], self.midi_turbulence)
        glUniform1f(self.locs['iSunIntensity'], self.midi_sun)
        glUniform1f(self.locs['iGlitch'], self.midi_glitch)

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
    DesertSwarmPreset().run()
