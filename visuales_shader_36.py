#!/usr/bin/env python3
"""
Preset 36: Immersive 3D Mandelbulb Glitch
Category: Fractal / Glitch / Reactive
Mandelbrot 3D (Mandelbulb) inmersivo con colores cambiantes y efectos de glitch
reactivos al audio y notas MIDI del Circuit Tracks.

Características:
- Raymarching de Fractal Mandelbulb Power 8.
- Paleta de colores dinámica rotativa.
- Efectos de Glitch / Desplazamiento de UV reactivos a frecuencias altas y MIDI.
- Navegación de cámara suave controlada por notas MIDI y bajos.
- Iluminación volumétrica (glow) reactiva.
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

# Configuración de Audio
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

// MIDI Uniforms
uniform float iGlitch;    // Intensidad del glitch (MIDI Note / Highs)
uniform float iColorShift; // Desplazamiento de color (MIDI CC / Time)
uniform float iZoom;      // Ahora controla la apertura del t\u00fanel
uniform float iMorph;     // Modificaci\u00f3n del fractal (Power)

#define MAX_STEPS 64
#define MAX_DIST 60.0
#define SURF_DIST 0.005

// Funciones de utilidad
mat2 rot(float a) {
    float s = sin(a), c = cos(a);
    return mat2(c, -s, s, c);
}

float random(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
}

// Mandelbulb Distance Estimator
float mandelbulb(vec3 p) {
    vec3 z = p;
    float dr = 1.0;
    float r = 0.0;
    
    // El poder fractal cambia con MIDI (Morph) y el tiempo
    float power = 6.0 + sin(iTime * 0.2) * 2.0 + iMorph * 4.0;

    for (int i = 0; i < 6; i++) {
        r = length(z);
        if (r > 2.0) break;
        
        // Convert to polar
        float theta = acos(z.z / r);
        float phi = atan(z.y, z.x);
        dr = pow(r, power - 1.0) * power * dr + 1.0;
        
        // Scale & Rotate
        float zr = pow(r, power);
        theta = theta * power;
        phi = phi * power;
        
        // Back to cartesian
        z = zr * vec3(sin(theta) * cos(phi), sin(phi) * sin(theta), cos(theta));
        z += p;
    }
    return 0.5 * log(r) * r / dr;
}

float map(vec3 p) {
    // --- INFINITE TUNNEL LOGIC ---
    
    // 1. Movimiento hacia adelante (el fractal se mueve hacia -Z)
    // Velocidad constante y suave para un viaje ameno
    float speed = 1.8; 
    p.z += iTime * speed;
    
    // 2. Warp de espacio (Twist)
    p.xy *= rot(p.z * 0.1 + iColorShift); // Rotar el t\u00fanel con MIDI CC
    
    // 3. Domain Repetition (Crear infinito)
    float spacing = 4.0 + iZoom; // Zoom controla espaciado
    vec3 q = p;
    q.z = mod(p.z, spacing) - spacing * 0.5;
    
    // 4. Kaleidoscopic Folding (Crear hueco central)
    q.xy = abs(q.xy) - 1.2; // Fold para abrir camino
    // q.xy *= rot(0.785); // Rotaci\u00f3n extra para complejidad
    
    return mandelbulb(q);
}

float rayMarch(vec3 ro, vec3 rd) {
    float dO = 0.0;
    float dS;
    
    // Dither inicial para romper banding
    dO += random(gl_FragCoord.xy) * 0.1;

    for(int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + rd * dO;
        dS = map(p);
        dO += dS * 0.8; // Step m\u00e1s peque\u00f1o para m\u00e1s detalle
        if(dO > MAX_DIST || dS < SURF_DIST) break;
    }
    return dO;
}

vec3 getNormal(vec3 p) {
    float d = map(p);
    vec2 e = vec2(0.01, 0); // Epsilon m\u00e1s grande para performance
    vec3 n = d - vec3(
        map(p-e.xyy),
        map(p-e.yxy),
        map(p-e.yyx)
    );
    return normalize(n);
}

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.y;

    // --- GLITCH EFFECT (VFX) ---
    // Distorsi\u00f3n fuerte en el UV basada en High Freqs y MIDI
    float glitchIntensity = iGlitch + iHigh * 0.5;
    
    if (glitchIntensity > 0.1) {
        // Desplazamiento horizontal aleatorio (tearing)
        float noise = random(vec2(floor(uv.y * 20.0), iTime));
        if (noise < glitchIntensity * 0.5) {
            uv.x += (random(vec2(iTime, uv.y)) - 0.5) * 0.2;
        }
        
        // Zoom glitch brusco
        if (random(vec2(iTime * 10.0, 1.0)) < 0.05 * glitchIntensity) {
            uv *= 0.9; 
        }
    }

    // C\u00e1mara fija mirando al frente (el movimiento est\u00e1 en map())
    vec3 ro = vec3(0.0, 0.0, -2.0); 
    vec3 rd = normalize(vec3(uv, 1.0));
    
    // Camera wobble muy suave y lento (sin audio)
    rd.xy *= rot(sin(iTime * 0.3) * 0.05);

    // Render
    float d = rayMarch(ro, rd);
    vec3 col = vec3(0.0);
    
    if(d < MAX_DIST) {
        vec3 p = ro + rd * d;
        vec3 n = getNormal(p);
        
        // Iluminaci\u00f3n psicod\u00e9lica
        // Color basado en posici\u00f3n (hue shifting) + MIDI
        vec3 p_warp = p;
        p_warp.z -= iTime * 2.0; // Recuperar Z real para coloring consistente
        
        float paletteCyc = length(p_warp.xy) * 0.5 + p_warp.z * 0.2 + iTime * 0.5 + iColorShift;
        vec3 baseCol = 0.5 + 0.5 * cos(vec3(0,2,4) + paletteCyc);
        
        // Invertir colores con glitch fuerte
        if (glitchIntensity > 0.5 && mod(iTime, 0.2) < 0.1) {
            baseCol = 1.0 - baseCol;
        }
        
        float diff = clamp(dot(n, normalize(vec3(1, 2, -3))), 0.0, 1.0);
        
        col = baseCol * diff;
        
        // Rim lighting reactivo (brillo en bordes)
        float rim = pow(1.0 - max(dot(n, -rd), 0.0), 3.0);
        col += vec3(iLow, iMid*0.5, iHigh) * rim * 2.0;
        
        // Fog para profundidad infinita
        float fogAmt = 1.0 - exp(-d * 0.05);
        vec3 fogCol = vec3(0.05, 0.0, 0.1);
        col = mix(col, fogCol, fogAmt);
        
    } else {
        // Fondo infinito
        col = vec3(0.02, 0.0, 0.05);
        // Estrellas fugaces glitchy
        if (random(uv + iTime) > 0.995) col += vec3(1.0) * iHigh;
    }
    
    // --- POST PROCESS COLOR GLITCH (RGB SPLIT) ---
    // Sin texture(), usamos el hack de desplazar canales
    if (glitchIntensity > 0.05) {
        // El canal R y B se separan basados en la intensidad
        float split = glitchIntensity * 0.03;
        
        // Como ya calculamos 'col' para el pixel central, esto es un tinte aproximado
        // Para un efecto real, necesitar\u00edamos renderizar 3 veces con offsets de UV, muy caro.
        // Simplemente a\u00f1adimos ruido de color:
        col.r += random(uv + vec2(iTime, 0.0)) * split;
        col.b += random(uv - vec2(iTime, 0.0)) * split;
    }
    
    // Vignette
    col *= 1.0 - length(uv) * 0.6;
    
    // Gamma
    col = pow(col, vec3(0.4545));
    
    fragColor = vec4(col, 1.0);
}
"""

class MandelbrotGlitchPreset:
    def __init__(self):
        pygame.init()
        pygame.display.init()
        
        # Configuración de ventana 9:16
        self.target_width = 1080
        self.target_height = 1920
        self.aspect_ratio = self.target_width / self.target_height
        initial_h = 900
        initial_w = int(initial_h * self.aspect_ratio)

        self.screen = pygame.display.set_mode((initial_w, initial_h), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption('Preset 36: Mandelbrot Glitch 3D')

        # Audio Init
        self.audio_buffer = np.zeros(SAMPLES, dtype=np.float32)
        self.low = 0.0; self.mid = 0.0; self.high = 0.0
        self.setup_audio()

        # MIDI Init
        self.midi_input = self.connect_midi()
        self.midi_glitch_val = 0.0
        self.midi_color_val = 0.0
        self.midi_zoom_val = 0.0
        self.midi_morph_val = 0.0

        # Graphics Init
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
            print("MIDI: Circuit Tracks not found. Using auto-mode.")
        except:
            print("MIDI: Error connecting.")
        return None

    def setup_audio(self):
        try:
            devices = sdl_audio.get_audio_device_names(True)
            # Priorizar Scarlett u otros interfaces, sino el default
            target = next((d for d in devices if "Scarlett" in d), devices[0] if devices else None)
            if target:
                self.dev = sdl_audio.AudioDevice(target, True, 44100, sdl_audio.AUDIO_F32, 1, 1024, 0, self.callback)
                self.dev.pause(0)
                print(f"Audio Device: {target}")
            else:
                print("No audio device found.")
        except Exception as e:
            print(f"Audio Setup Error: {e}")

    def callback(self, dev, data):
        self.audio_buffer = np.frombuffer(data, dtype=np.float32)

    def process_midi(self):
        # Decaimiento natural de los valores MIDI
        self.midi_glitch_val *= 0.9
        
        if self.midi_input:
            for msg in self.midi_input.iter_pending():
                # Randomización basada en el canal y notas
                if msg.type == 'note_on' and msg.velocity > 0:
                    # Glitch en notas fuertes o canales aleatorios
                    if msg.channel in [0, 1, 2, 9]: # Canales típicos del Circuit
                        intensity = msg.velocity / 127.0
                        self.midi_glitch_val = intensity
                        
                        # Morphing aleatorio cada vez que entra una nota
                        if random.random() > 0.7:
                            self.midi_morph_val = random.random()
                            
                # Control Change para parámetros continuos (Knobs)
                if msg.type == 'control_change':
                    # Mapeos genéricos de Macros del Circuit (CC habituales: 74, 19, etc)
                    norm_val = msg.value / 127.0
                    if msg.control == 74: # Filter freq usualmente
                        self.midi_color_val = norm_val * 10.0
                    elif msg.control == 19: # Resonance usualmente
                        self.midi_zoom_val = norm_val

    def update_audio(self):
        if len(self.audio_buffer) == 0: return
        fft = np.abs(np.fft.rfft(self.audio_buffer))
        # Bandas de frecuencia
        self.low  = self.low * 0.9 + np.mean(fft[0:10]) * 0.1
        self.mid  = self.mid * 0.9 + np.mean(fft[10:50]) * 0.1
        self.high = self.high * 0.8 + np.mean(fft[50:150]) * 0.15 # Decay más rápido en agudos para glitch

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
        try:
            vs = shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER)
            fs = shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
            self.shader = shaders.compileProgram(vs, fs)
            self.locs = {
                'iTime': glGetUniformLocation(self.shader, 'iTime'),
                'iResolution': glGetUniformLocation(self.shader, 'iResolution'),
                'iLow': glGetUniformLocation(self.shader, 'iLow'),
                'iMid': glGetUniformLocation(self.shader, 'iMid'),
                'iHigh': glGetUniformLocation(self.shader, 'iHigh'),
                'iGlitch': glGetUniformLocation(self.shader, 'iGlitch'),
                'iColorShift': glGetUniformLocation(self.shader, 'iColorShift'),
                'iZoom': glGetUniformLocation(self.shader, 'iZoom'),
                'iMorph': glGetUniformLocation(self.shader, 'iMorph')
            }
        except Exception as e:
            print(f"Shader Error: {e}")
            pygame.quit()
            exit()

    def render(self):
        self.update_audio()
        self.process_midi()
        
        w, h = self.screen.get_size()
        glViewport(0, 0, w, h)
        glUseProgram(self.shader)
        
        time_sec = (pygame.time.get_ticks() - self.start_time) / 1000.0
        
        # Combinar audio y MIDI para las variables finales
        final_glitch = self.midi_glitch_val + (self.high * 0.5) # Glitch por MIDI o Hihats
        final_zoom = self.midi_zoom_val
        
        glUniform1f(self.locs['iTime'], time_sec)
        glUniform2f(self.locs['iResolution'], float(w), float(h))
        glUniform1f(self.locs['iLow'], self.low)
        glUniform1f(self.locs['iMid'], self.mid)
        glUniform1f(self.locs['iHigh'], self.high)
        
        glUniform1f(self.locs['iGlitch'], final_glitch)
        glUniform1f(self.locs['iColorShift'], self.midi_color_val)
        glUniform1f(self.locs['iZoom'], final_zoom)
        glUniform1f(self.locs['iMorph'], self.midi_morph_val)

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
    MandelbrotGlitchPreset().run()
