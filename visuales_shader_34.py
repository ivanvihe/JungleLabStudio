#!/usr/bin/env python3
"""
Preset 34: Interstellar V15 (Clean Cosmos)
Category: TouchDesigner Style / Volumetric Raymarching
Versión pulida sin distorsiones extrañas.

Cambios V15:
- ELIMINADO: "Quantum Ripple" (Onda de choque fea).
- MANTENIDO: Reactividad global (Brillo respira con la música).
- MANTENIDO: Destellos de estrellas (Scintillation) con agudos.
- MANTENIDO: Sistema orbital V14 (Anillos + Polvo).
"""

from __future__ import division
import pygame
import pygame._sdl2.audio as sdl_audio
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np

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
uniform float iVolume;

// === AJUSTES ===
#define ITERATIONS 13
#define FORMUPARAM 0.53
#define VOLSTEPS 18
#define STEPSIZE 0.1
#define ZOOM 0.800
#define TILE 0.850
#define SPEED 0.001
#define BRIGHTNESS 0.002
#define DARKMATTER 0.300
#define DISTFADING 0.730
#define SATURATION 0.850

#define SPHERE_Z 3.5
#define SPHERE_RAD 0.32 

mat2 rot(float a) {
    float s=sin(a), c=cos(a);
    return mat2(c,-s,s,c);
}

void main() {
    vec2 uv = gl_FragCoord.xy / iResolution.xy - 0.5;
    uv.y *= iResolution.y / iResolution.x;
    float r = length(uv);

    // === LENTE GRAVITACIONAL ESTÁTICA (LIMPIA) ===
    // Sin ondas de choque, solo la curvatura física del agujero
    float distortion = SPHERE_RAD * 0.15 / (r * r + 0.01);
    vec2 uv_distorted = uv * (1.0 - distortion * 0.6);
    
    vec3 dir = vec3(uv_distorted * ZOOM, 1.0);
    float time = iTime * SPEED;
    
    mat2 rotCam = rot(0.2);
    dir.xy *= rotCam;
    
    vec3 from = vec3(1.0, 0.5, 0.5);
    from += vec3(time * 2.0, time, -2.0);
    
    float holeRadius = SPHERE_RAD;
    float distToCenter = length(uv); // UV originales para máscara perfecta
    bool isHole = distToCenter < holeRadius;
    
    float s = 0.1;
    float fade = 1.0;
    vec3 v = vec3(0.0);
    vec3 diskAcc = vec3(0.0);
    
    mat2 diskTilt = rot(1.0);
    
    // Reactividad Global: El universo respira con el volumen
    float globalEnergy = 1.0 + iVolume * 2.0; 

    for (int r = 0; r < VOLSTEPS; r++) {
        vec3 p = from + s * dir * 0.5;
        
        // === DISCO Y PARTÍCULAS ===
        float distFromHolePlane = s - SPHERE_Z;
        vec3 pDisk = vec3(uv * s, distFromHolePlane);
        pDisk.yz *= diskTilt;
        
        float dR = length(pDisk.xz);
        float dH = abs(pDisk.y);
        
        if (dR > holeRadius * 1.1 && dR < holeRadius * 9.0) {
            if (dH < 0.05) {
                float angle = atan(pDisk.z, pDisk.x);
                
                // Anillos visibles
                float rings = sin(dR * 20.0 + iTime) * 0.5 + 0.5;
                rings = pow(rings, 2.0); 
                
                // Polvo brillante (Sparkles)
                float sparkleNoise = sin(dR * 30.0 + angle * 40.0 + iTime * 5.0);
                float sparkles = smoothstep(0.8, 1.0, sparkleNoise);
                
                // Fade vertical
                float dens = smoothstep(0.05, 0.0, dH);
                
                // COLORES
                vec3 cRing = vec3(0.4, 0.6, 0.8);
                vec3 cSpark = vec3(1.0, 0.9, 0.5); // Oro
                
                // Reactividad del Disco
                vec3 layer1 = cRing * rings * dens * (0.5 + iLow);
                vec3 layer2 = cSpark * sparkles * dens * (iHigh * 4.0);
                
                diskAcc += (layer1 + layer2) * 0.1 * fade * globalEnergy;
            }
        }
        
        // Oclusión Agujero Negro
        if (isHole && s > SPHERE_Z) {
             float rim = smoothstep(holeRadius * 0.99, holeRadius, distToCenter);
             v += vec3(0.1, 0.3, 0.8) * rim * 0.2 * fade;
             break;
        }

        // === NEBULOSA (FONDO) ===
        vec3 pf = abs(vec3(TILE) - mod(p, vec3(TILE * 2.0)));
        float pa, a = pa = 0.0;
        for (int i = 0; i < ITERATIONS; i++) { 
            pf = abs(pf) / dot(pf, pf) - FORMUPARAM; 
            a += abs(length(pf) - pa);
            pa = length(pf);
        }
        float dm = max(0.0, DARKMATTER - a * a * 0.001);
        a *= a * a;
        if (r > 6) fade *= 1.0 - dm; 
        
        // Destello de estrellas con Agudos
        float starFlash = 1.0 + iHigh * 3.0 * float(r > 12); 
        
        v += vec3(s, s*s, s*s*s*s) * a * BRIGHTNESS * fade * globalEnergy * starFlash;
        
        fade *= DISTFADING;
        s += STEPSIZE;
    }
    
    float len = length(v);
    v = mix(vec3(len), v, SATURATION);
    vec3 finalCol = v * 0.015 + vec3(0.01, 0.03, 0.1) * len * 0.005;
    
    // Sumar Disco
    finalCol += diskAcc;
    
    // Tone Mapping
    finalCol = pow(finalCol, vec3(1.1)); 
    finalCol *= 1.4;

    fragColor = vec4(finalCol, 1.0);
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

        self.screen = pygame.display.set_mode((initial_w, initial_h), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption('Preset 34: Clean Cosmos V15')

        self.audio_buffer = np.zeros(SAMPLES, dtype=np.float32)
        self.low = 0.0; self.mid = 0.0; self.high = 0.0; self.volume = 0.0

        self.setup_audio()
        self.setup_shaders()
        self.setup_quad()
        self.clock = pygame.time.Clock()
        self.start_time = pygame.time.get_ticks()

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

    def update_audio(self):
        if len(self.audio_buffer) == 0: return
        fft = np.abs(np.fft.rfft(self.audio_buffer))
        rms = np.sqrt(np.mean(self.audio_buffer**2))
        
        self.volume = self.volume * 0.85 + rms * 0.5
        
        self.low  = self.low * 0.85 + np.mean(fft[0:10]) * 0.4
        self.mid  = self.mid * 0.85 + np.mean(fft[10:50]) * 0.4
        self.high = self.high * 0.8 + np.mean(fft[50:150]) * 0.6

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
            'iVolume': glGetUniformLocation(self.shader, 'iVolume')
        }

    def render(self):
        self.update_audio()
        w, h = self.screen.get_size()
        glViewport(0, 0, w, h)
        glUseProgram(self.shader)
        
        glUniform1f(self.locs['iTime'], (pygame.time.get_ticks() - self.start_time) / 1000.0)
        glUniform2f(self.locs['iResolution'], float(w), float(h))
        glUniform1f(self.locs['iLow'], self.low)
        glUniform1f(self.locs['iMid'], self.mid)
        glUniform1f(self.locs['iHigh'], self.high)
        glUniform1f(self.locs['iVolume'], self.volume)

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
    ShaderVisualEngine().run()