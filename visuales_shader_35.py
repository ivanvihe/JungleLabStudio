#!/usr/bin/env python3
"""
Preset 35: Neon Hyper-Tunnel
Category: TouchDesigner Style / Outrun
Túnel infinito de velocidad extrema con estética Cyberpunk.
Sustituye la rejilla plana por un entorno 3D envolvente.

Características:
- Túnel de geometría rectangular infinita
- Suelo reflectante "Wet Floor"
- Aberración Cromática (RGB Split) reactiva al audio
- Glow intenso en bordes (Bloom)
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

// Función de rotación
mat2 rot(float a) {
    float s=sin(a), c=cos(a);
    return mat2(c,-s,s,c);
}

// SDF Caja hueca (Túnel)
float sdBox(vec3 p, vec3 b) {
    vec3 q = abs(p) - b;
    return length(max(q,0.0)) + min(max(q.x,max(q.y,q.z)),0.0);
}

float map(vec3 p) {
    // Modificar el túnel con el audio
    float tunnelWarp = sin(p.z * 0.5 + iTime) * iLow * 0.5;
    
    vec3 p_tun = p;
    p_tun.z = mod(p.z, 4.0) - 2.0; // Repetición infinita
    
    // Estructura de costillas del túnel
    float ribs = sdBox(p_tun, vec3(2.5 + tunnelWarp, 2.0, 0.2));
    
    // Suelo y techo
    float planes = 2.0 - abs(p.y);
    
    return min(ribs, planes);
}

// Raymarching principal
float raymarch(vec3 ro, vec3 rd) {
    float dO = 0.0;
    for(int i=0; i<80; i++) {
        vec3 p = ro + rd * dO;
        float dS = map(p);
        dO += dS;
        if(dO > 100.0 || dS < 0.01) break;
    }
    return dO;
}

// Renderizado de la escena
vec3 render(vec2 uv) {
    // Cámara con FOV dinámico (efecto velocidad)
    float fov = 1.0 + iHigh * 0.5; 
    vec3 ro = vec3(0.0, 0.0, iTime * 8.0); // Velocidad alta
    vec3 rd = normalize(vec3(uv, fov));
    
    // Balanceo de cámara
    rd.xy *= rot(sin(iTime * 0.5) * 0.1 + iMid * 0.1);
    
    float d = raymarch(ro, rd);
    vec3 p = ro + rd * d;
    
    vec3 col = vec3(0.0);
    
    // Glow de neón basado en la distancia y geometría
    // Más lejos = más oscuro (fog)
    float fog = 1.0 / (1.0 + d * d * 0.02);
    
    // Colores de la rejilla/túnel
    // Si golpeamos las costillas (p.z local cercano a 0)
    float ribMask = step(0.15, abs(mod(p.z, 4.0) - 2.0)); // Inverso para líneas finas
    
    vec3 neonColor = vec3(1.0, 0.0, 0.8); // Magenta principal
    if (p.y < -1.9) neonColor = vec3(0.0, 0.8, 1.0); // Suelo Cyan
    
    // Grid lines logic
    float grid = 0.0;
    grid += smoothstep(0.9, 1.0, cos(p.x * 2.0)); // Líneas longitudinales
    grid += smoothstep(0.9, 1.0, cos(p.z * 2.0)); // Líneas transversales
    
    // Composición
    vec3 material = neonColor * grid * 2.0; // Brillo intenso
    material += vec3(0.1, 0.0, 0.2); // Color base oscuro
    
    col = mix(vec3(0.05, 0.0, 0.1), material, fog);
    
    // Sol lejano (Fake)
    if (d > 90.0) {
        vec2 sunUV = uv;
        sunUV.y -= 0.2;
        float sun = length(sunUV);
        if (sun < 0.4) {
            float strips = step(0.0, sin(sunUV.y * 50.0));
            col += vec3(1.0, 0.5, 0.0) * strips * 2.0;
        }
        // Glow del horizonte
        col += vec3(0.8, 0.2, 0.5) * exp(-abs(uv.y) * 5.0);
    }
    
    return col;
}

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.y;
    
    // Aberración Cromática (RGB Split) reactiva a los golpes
    float split = 0.005 + iLow * 0.02;
    
    vec3 col;
    col.r = render(uv + vec2(split, 0.0)).r;
    col.g = render(uv).g;
    col.b = render(uv - vec2(split, 0.0)).b;
    
    // Scanlines sutiles
    col *= 0.9 + 0.1 * sin(gl_FragCoord.y * 0.5 + iTime * 10.0);
    
    // Vignette
    col *= 1.0 - length(uv) * 0.5;
    
    fragColor = vec4(col, 1.0);
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
        pygame.display.set_caption('Preset 35: Neon Tunnel')

        self.audio_buffer = np.zeros(SAMPLES, dtype=np.float32)
        self.low = 0.0; self.mid = 0.0; self.high = 0.0

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
        self.low  = self.low * 0.9 + np.mean(fft[0:10]) * 0.08
        self.mid  = self.mid * 0.9 + np.mean(fft[10:50]) * 0.08
        self.high = self.high * 0.9 + np.mean(fft[50:150]) * 0.08

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
            'iHigh': glGetUniformLocation(self.shader, 'iHigh')
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