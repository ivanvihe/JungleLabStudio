#!/usr/bin/env python3
"""
Preset 29: Particle Constellation - Estructuras Generativas
Category: Audio Reactive / Generative / Particle Systems
Sistema de partículas que forman estructuras geométricas cambiantes.

Características:
- Partículas que forman estructuras 3D complejas
- Morphing entre geometrías (esfera, cubo, torus, etc)
- Conexiones procedurales entre partículas
- Bajos: Explosión y reorganización
- Medios: Complejidad de la estructura
- Volumen: Intensidad y brillo
"""

from __future__ import division
import pygame
import pygame._sdl2.audio as sdl_audio
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np
from numpy import array

SAMPLES = 1024

VERTEX_SHADER = "#version 330 core\nlayout(location = 0) in vec3 vPos;\nvoid main() { gl_Position = vec4(vPos, 1.0); }"

FRAGMENT_SHADER = """
#version 330 core
#define fragCoord gl_FragCoord.xy
uniform float iTime;
uniform vec2  iResolution;
uniform float iBass;
uniform float iMid;
uniform float iVolume;
out vec4 fragColor;

#define PI 3.14159265359
#define NUM_PARTICLES 60.0

mat2 rot(float a) {
    float s = sin(a), c = cos(a);
    return mat2(c, s, -s, c);
}

// Hash para generar posiciones procedurales
vec3 hash33(float p) {
    vec3 p3 = fract(vec3(p) * vec3(0.1031, 0.1030, 0.0973));
    p3 += dot(p3, p3.yxz + 33.33);
    return fract((p3.xxy + p3.yxx) * p3.zyx);
}

// Diferentes estructuras geométricas
vec3 spherePattern(float id, float t) {
    float theta = id * PI * 2.0 / NUM_PARTICLES;
    float phi = asin(-1.0 + (2.0 * id) / NUM_PARTICLES);
    return vec3(
        cos(theta) * cos(phi),
        sin(phi),
        sin(theta) * cos(phi)
    );
}

vec3 cubePattern(float id, float t) {
    vec3 p = hash33(id) * 2.0 - 1.0;
    return normalize(p) * (abs(p.x) + abs(p.y) + abs(p.z)) * 0.5;
}

vec3 torusPattern(float id, float t) {
    float angle1 = id * PI * 2.0 / NUM_PARTICLES;
    float angle2 = id * PI * 8.0 / NUM_PARTICLES;
    float R = 1.0;
    float r = 0.5;
    return vec3(
        (R + r * cos(angle2)) * cos(angle1),
        r * sin(angle2),
        (R + r * cos(angle2)) * sin(angle1)
    );
}

vec3 helixPattern(float id, float t) {
    // Rotación ultra lenta del helix
    float angle = id * PI * 4.0 / NUM_PARTICLES + t * 0.15;
    float height = (id / NUM_PARTICLES - 0.5) * 3.0;
    return vec3(
        cos(angle),
        height,
        sin(angle)
    );
}

vec3 expandingPattern(float id, float t) {
    vec3 base = hash33(id) * 2.0 - 1.0;
    // Pulsación ultra lenta y suave
    float pulse = sin(t * 0.4 + id * 0.5) * 0.5 + 0.5;
    return normalize(base) * (0.8 + pulse * 0.6);
}

// Función principal de posición de partícula
vec3 getParticlePos(float id, float t) {
    // Morphing entre diferentes patrones - MUY LENTO
    // Audio casi no afecta la velocidad
    float morphSpeed = 0.05 + iBass * 0.005;
    float morphPhase = t * morphSpeed;
    float structureType = mod(floor(morphPhase), 5.0);
    float blend = fract(morphPhase);
    blend = smoothstep(0.05, 0.95, blend); // Transición ultra gradual

    vec3 pos1, pos2;

    // Seleccionar estructuras según morphPhase
    if(structureType < 1.0) {
        pos1 = spherePattern(id, t);
        pos2 = cubePattern(id, t);
    } else if(structureType < 2.0) {
        pos1 = cubePattern(id, t);
        pos2 = torusPattern(id, t);
    } else if(structureType < 3.0) {
        pos1 = torusPattern(id, t);
        pos2 = helixPattern(id, t);
    } else if(structureType < 4.0) {
        pos1 = helixPattern(id, t);
        pos2 = expandingPattern(id, t);
    } else {
        pos1 = expandingPattern(id, t);
        pos2 = spherePattern(id, t);
    }

    // Blend entre estructuras
    vec3 pos = mix(pos1, pos2, blend);

    // Expansión muy sutil controlada por volumen (sin volumen más juntas, con volumen más separadas)
    float separation = 0.7 + iVolume * 0.15;
    pos *= separation;

    // Rotación global muy lenta - velocidad casi no afectada por volumen
    float rotSpeed = 0.08 + iVolume * 0.03;
    pos.xy *= rot(t * rotSpeed * 0.5);
    pos.yz *= rot(t * rotSpeed * 0.4);

    return pos;
}

// Dibujar partícula
float drawParticle(vec2 uv, vec3 particlePos, vec3 camPos, mat3 camRot) {
    vec3 worldPos = particlePos;
    vec3 viewPos = camRot * (worldPos - camPos);

    if(viewPos.z > 0.0) {
        vec2 screenPos = viewPos.xy / viewPos.z;
        float dist = length(uv - screenPos);

        // Tamaño con reactividad muy sutil
        float size = 0.02 + iVolume * 0.01;
        float particle = smoothstep(size, 0.0, dist);

        // Glow muy reducido (menos neblina)
        float glow = 0.008 / (dist + 0.015) * (0.15 + iVolume * 0.1);

        return particle + glow * 0.3;
    }

    return 0.0;
}

// Conexiones entre partículas
float drawConnection(vec2 uv, vec3 p1, vec3 p2, vec3 camPos, mat3 camRot) {
    vec3 v1 = camRot * (p1 - camPos);
    vec3 v2 = camRot * (p2 - camPos);

    if(v1.z > 0.0 && v2.z > 0.0) {
        vec2 s1 = v1.xy / v1.z;
        vec2 s2 = v2.xy / v2.z;

        // Distancia del punto a la línea
        vec2 pa = uv - s1;
        vec2 ba = s2 - s1;
        float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
        float dist = length(pa - ba * h);

        float thickness = 0.002 * (1.0 + iMid * 0.15);
        return smoothstep(thickness, 0.0, dist) * 0.3;
    }

    return 0.0;
}

void main() {
    vec2 uv = (fragCoord - 0.5 * iResolution.xy) / iResolution.y;
    vec3 col = vec3(0.0);

    float t = iTime;

    // Cámara
    vec3 camPos = vec3(0.0, 0.0, -3.5);
    mat3 camRot = mat3(1.0);

    // Fondo negro puro
    vec3 bgColor = vec3(0.0, 0.0, 0.0);
    col = bgColor;

    // Dibujar partículas y conexiones
    for(float i = 0.0; i < NUM_PARTICLES; i++) {
        vec3 pos = getParticlePos(i, t);

        // Color de la partícula
        float hue = i / NUM_PARTICLES + t * 0.1 + iBass * 0.1;
        vec3 particleColor = 0.5 + 0.5 * cos(hue * 6.28 + vec3(0.0, 2.0, 4.0));

        // Intensidad con volumen muy sutil y controlada (menos neblina)
        particleColor *= (0.8 + iVolume * 0.3);

        // Dibujar partícula
        float p = drawParticle(uv, pos, camPos, camRot);
        col += particleColor * p;

        // Conexiones con partículas cercanas
        if(iMid > 0.1) {
            for(float j = i + 1.0; j < min(i + 8.0, NUM_PARTICLES); j++) {
                vec3 pos2 = getParticlePos(j, t);
                float dist = length(pos - pos2);

                // Solo conectar si están cerca
                if(dist < 1.5) {
                    float conn = drawConnection(uv, pos, pos2, camPos, camRot);
                    vec3 connColor = mix(particleColor,
                                        0.5 + 0.5 * cos((j / NUM_PARTICLES + t * 0.1) * 6.28 + vec3(0.0, 2.0, 4.0)),
                                        0.5);
                    col += connColor * conn * (1.0 - dist / 1.5);
                }
            }
        }
    }

    // Glow general casi eliminado (fondo más negro)
    float centerGlow = 1.0 / (1.0 + length(uv) * 3.0);
    col += vec3(0.05, 0.1, 0.15) * centerGlow * (0.01 + iVolume * 0.02);

    // Tone mapping
    col = col / (col + 1.0);

    // Gamma
    col = pow(col, vec3(0.4545));

    // Vignette más suave (menos oscurecimiento en bordes)
    float vignette = 1.0 - length(uv) * 0.3;
    col *= vignette;

    fragColor = vec4(col, 1.0);
}
"""

FRANJA_VERTEX = "#version 330 core\nlayout(location = 0) in vec2 vPos;\nvoid main() { gl_Position = vec4(vPos, 0.0, 1.0); }"
FRANJA_FRAGMENT = """
#version 330 core
out vec4 fragColor;
uniform vec2 iResolution;
void main() {
    float line = mod(gl_FragCoord.x + gl_FragCoord.y, 40.0);
    float pattern = step(line, 2.0) * 0.08;
    fragColor = vec4(pattern * 0.8, pattern * 1.2, pattern * 1.5, 1.0);
}
"""

class ShaderVisualEngine:
    def __init__(self):
        pygame.init()
        self.target_width, self.target_height = 1080, 1920
        self.target_aspect = self.target_width / self.target_height
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)
        self.screen = pygame.display.set_mode((int(900 * self.target_aspect), 900), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption('Preset 29: Particle Constellation [9:16]')

        # Shader principal
        vs = shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER)
        fs = shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vs, fs)
        self.uni_time = glGetUniformLocation(self.shader, 'iTime')
        self.uni_resolution = glGetUniformLocation(self.shader, 'iResolution')
        self.uni_bass = glGetUniformLocation(self.shader, 'iBass')
        self.uni_mid = glGetUniformLocation(self.shader, 'iMid')
        self.uni_volume = glGetUniformLocation(self.shader, 'iVolume')

        # Shader franjas
        fvs = shaders.compileShader(FRANJA_VERTEX, GL_VERTEX_SHADER)
        ffs = shaders.compileShader(FRANJA_FRAGMENT, GL_FRAGMENT_SHADER)
        self.franja_shader = shaders.compileProgram(fvs, ffs)
        self.franja_resolution = glGetUniformLocation(self.franja_shader, 'iResolution')

        # VAO principal
        verts = array([-1, -1, 0, 1, -1, 0, 1, 1, 0, -1, 1, 0], dtype='f')
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, verts, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

        # VAO franjas
        fverts = array([-1, -1, 1, -1, 1, 1, -1, 1], dtype='f')
        self.franja_vao = glGenVertexArrays(1)
        glBindVertexArray(self.franja_vao)
        fvbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, fvbo)
        glBufferData(GL_ARRAY_BUFFER, fverts, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)

        # Audio setup
        self.audio_buffer = np.zeros(SAMPLES, dtype=np.float32)
        self.bass_smoothed = 0.0
        self.mid_smoothed = 0.0
        self.vol_smoothed = 0.0
        self.setup_audio()

        self.clock = pygame.time.Clock()
        self.start_time = pygame.time.get_ticks()

    def setup_audio(self):
        try:
            devices = sdl_audio.get_audio_device_names(True)
            target = next((d for d in devices if "Scarlett" in d), devices[0] if devices else None)
            if target:
                print(f"Audio: {target}")
                self.dev = sdl_audio.AudioDevice(
                    target, True, 44100, sdl_audio.AUDIO_F32, 1, 1024, 0, self.callback
                )
                self.dev.pause(0)
        except Exception as e:
            print("Error Audio:", e)

    def callback(self, dev, data):
        raw = np.frombuffer(data, dtype=np.float32)
        l = min(len(raw), SAMPLES)
        self.audio_buffer[:l] = raw[:l]

    def update_audio_analysis(self):
        rms = np.sqrt(np.mean(self.audio_buffer**2)) * 8.0
        # Suavizado muy gradual del volumen para movimientos suaves
        self.vol_smoothed += (rms - self.vol_smoothed) * 0.08

        fft = np.abs(np.fft.rfft(self.audio_buffer))
        bass = np.mean(fft[1:10]) * 0.6
        # Suavizado muy gradual de bajos
        self.bass_smoothed += (bass - self.bass_smoothed) * 0.12

        mid = np.mean(fft[10:50]) * 0.4
        # Suavizado muy gradual de medios
        self.mid_smoothed += (mid - self.mid_smoothed) * 0.1

    def calculate_viewport(self, w, h):
        a = w / h
        if a > self.target_aspect:
            vh = h
            vw = int(vh * self.target_aspect)
            return (w - vw) // 2, 0, vw, vh
        vw = w
        vh = int(vw / self.target_aspect)
        return 0, (h - vh) // 2, vw, vh

    def render(self):
        self.update_audio_analysis()

        w, h = self.screen.get_size()
        vx, vy, vw, vh = self.calculate_viewport(w, h)

        glViewport(0, 0, w, h)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        # Dibujar franjas laterales
        if vx > 0:
            glUseProgram(self.franja_shader)
            glUniform2f(self.franja_resolution, float(w), float(h))
            glBindVertexArray(self.franja_vao)
            glViewport(0, 0, vx, h)
            glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
            glViewport(vx + vw, 0, w - (vx + vw), h)
            glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

        # Dibujar shader principal
        glViewport(vx, vy, vw, vh)
        glUseProgram(self.shader)
        glUniform1f(self.uni_time, (pygame.time.get_ticks() - self.start_time) / 1000.0)
        glUniform2f(self.uni_resolution, float(vw), float(vh))
        glUniform1f(self.uni_bass, self.bass_smoothed)
        glUniform1f(self.uni_mid, self.mid_smoothed)
        glUniform1f(self.uni_volume, self.vol_smoothed)
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

        if hasattr(self, 'dev') and self.dev:
            self.dev.close()
        pygame.quit()

if __name__ == '__main__':
    ShaderVisualEngine().run()
