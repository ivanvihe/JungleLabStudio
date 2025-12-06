#!/usr/bin/env python3
"""
Preset 23: Fractal Morphing - Iterative Folding con Bassline
Category: Fractal/SDF Advanced + MIDI Reactive
OPTIMIZADO: Raymarching 64→60, centrado, franjas con líneas

Características:
- Fondo negro con estructuras blancas brillantes
- Glow controlado solo en superficies
- METAMORFOSIS: 5 tipos de folding diferentes según nota del bassline
- Canal 1 (Bassline): Cada nota transforma la estructura evolutivamente
- Batería (Kick/Hat/Toms): Modulan intensidad, glitch, complexity
"""

from __future__ import division
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL import shaders
import mido
from numpy import array

KICK_NOTE, CLOSEHAT_NOTE, TOM1_NOTE, TOM2_NOTE = 60, 62, 64, 65

VERTEX_SHADER = "#version 330 core\nlayout(location = 0) in vec3 vPos;\nvoid main() { gl_Position = vec4(vPos, 1.0); }"

FRAGMENT_SHADER = """
#version 330 core
#define fragCoord gl_FragCoord.xy
uniform float iTime;
uniform vec2  iResolution;
uniform float iKickPulse, iHatGlitch, iTom1Morph, iTom2Spin;
uniform float iBassNote;  // Nota del bassline (normalizada 0-1)
uniform float iBassPulse; // Intensidad de la nota
out vec4 fragColor;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

// Color palette - tonos blancos/grises sobre fondo negro
vec3 palette(float d) {
    // Tonos monocromáticos con variación sutil por kick
    vec3 color1 = vec3(0.8, 0.85, 0.9);  // Blanco azulado muy sutil
    vec3 color2 = vec3(1.0, 1.0, 1.0) * (0.9 + iKickPulse * 0.1);  // Blanco puro
    return mix(color1, color2, d);
}

vec2 rotate(vec2 p, float a) {
    float c = cos(a);
    float s = sin(a);
    return p * mat2(c, s, -s, c);
}

// Fractal pyramid con folding iterativo - metamorfosis por bassline
float map(vec3 p) {
    // Escalar estructura 50% más grande para más espacio entre elementos
    float scale = 1.5;
    p /= scale;

    // Tom1 controla número base de iterations (6-10)
    int baseIterations = 6 + int(iTom1Morph * 4.0);

    // Nota del bassline modula iterations (+0 a +3)
    int iterations = baseIterations + int(iBassNote * 3.0 * iBassPulse);

    // Nota del bassline determina el tipo de metamorfosis
    float morphType = iBassNote * 5.0;  // 0-5 diferentes tipos

    for(int i = 0; i < 13; i++) {  // Max iterations aumentado
        if(i >= iterations) break;

        float t = iTime * 0.15 + iTom2Spin * 0.5;

        // Rotaciones con variación modulada por nota
        float rotSpeed = 1.0 + iBassNote * iBassPulse;
        p.xz = rotate(p.xz, t * 1.1 * rotSpeed);
        p.xy = rotate(p.xy, t * 1.7 * rotSpeed);

        // Hat glitch distorsiona el folding
        if(iHatGlitch > 0.1) {
            p.x += sin(p.y * 10.0 + iTime) * iHatGlitch * 0.1;
        }

        // METAMORFOSIS según nota del bassline
        if(morphType < 1.0) {
            // Tipo 0: Rombos clásicos (notas bajas)
            p.xz = abs(p.xz);
            p.xz -= 0.5 + sin(t * 0.5) * 0.1;
        }
        else if(morphType < 2.0) {
            // Tipo 1: Folding triangular (notas medias-bajas)
            p = abs(p);
            if(p.x < p.y) p.xy = p.yx;
            p.x -= 0.6 + sin(t * 0.5) * 0.15;
        }
        else if(morphType < 3.0) {
            // Tipo 2: Folding octaédrico (notas medias)
            p = abs(p);
            if(p.x < p.y) p.xy = p.yx;
            if(p.x < p.z) p.xz = p.zx;
            p.x -= 0.7;
        }
        else if(morphType < 4.0) {
            // Tipo 3: Folding en espiral (notas medias-altas)
            p.xy = abs(p.xy);
            p.xz = rotate(p.xz, t * 2.0);
            p.xy -= 0.5 + sin(t) * 0.2;
        }
        else {
            // Tipo 4: Folding complejo tetraédrico (notas altas)
            p = abs(p);
            if(p.x < p.y) p.xy = p.yx;
            if(p.x < p.z) p.xz = p.zx;
            if(p.y < p.z) p.yz = p.zy;
            p.xy -= 0.6;
            p.z -= 0.3;
        }
    }

    return dot(sign(p), p) / 5.0 * scale;  // Compensar escala
}

// OPTIMIZADO: 64→60 iterations
vec4 raymarch(vec3 ro, vec3 rd) {
    float t = 0.0;
    vec3 col = vec3(0.0);
    float d;

    for(float i = 0.0; i < 60.0; i++) {
        vec3 p = ro + rd * t;
        d = map(p) * 0.5;

        if(d < 0.02) break;
        if(d > 100.0) break;

        // Glow solo cerca de superficies - elimina fog en espacio vacío
        if(d < 0.3) {  // Solo acumular glow cuando estamos cerca
            float brightness = 1.0 - smoothstep(0.0, 0.3, d);  // Más brillo cerca de superficie
            col += palette(length(p) * 0.1 + iKickPulse * 0.2) * brightness / (600.0 * (d));
        }
        t += d;
    }

    return vec4(col, 1.0 / (d * 100.0));
}

void main() {
    vec2 uv = fragCoord / iResolution.xy;

    // CENTRADO: Formato vertical correcto
    vec2 p = (fragCoord - iResolution.xy * 0.5) / iResolution.x;

    // Cámara orbital
    float orbitSpeed = iTime * 0.3 + iTom2Spin * 2.0;
    vec3 ro = vec3(0.0, 0.0, -50.0 + iKickPulse * 5.0);
    ro.xz = rotate(ro.xz, orbitSpeed);

    vec3 cf = normalize(-ro);
    vec3 cs = normalize(cross(cf, vec3(0.0, 1.0, 0.0)));
    vec3 cu = normalize(cross(cf, cs));

    vec3 uuv = ro + cf * 3.0 + p.x * cs + p.y * cu;
    vec3 rd = normalize(uuv - ro);

    // Raymarch
    vec4 col = raymarch(ro, rd);

    // Vignette muy sutil solo en bordes extremos
    col.rgb *= 1.0 - 0.1 * length(uv - 0.5);

    // Tone mapping & gamma
    col.rgb = col.rgb / (col.rgb + 1.0);
    col.rgb = pow(col.rgb, vec3(0.4545));

    fragColor = col;
}
"""

FRANJA_VERTEX = "#version 330 core\nlayout(location = 0) in vec2 vPos;\nvoid main() { gl_Position = vec4(vPos, 0.0, 1.0); }"
FRANJA_FRAGMENT = """
#version 330 core
out vec4 fragColor;
uniform vec2 iResolution;
void main() {
    float line = mod(gl_FragCoord.x + gl_FragCoord.y, 40.0);
    float pattern = step(line, 2.0) * 0.12;
    fragColor = vec4(pattern, pattern, pattern, 1.0);
}
"""

class ShaderVisualEngine:
    def __init__(self):
        pygame.init()
        self.target_width, self.target_height = 1080, 1920
        self.target_aspect = self.target_width / self.target_height
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)
        self.screen = pygame.display.set_mode((int(900 * self.target_aspect), 900), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption('Preset 23: Fractal Morphing [9:16]')

        vs = shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER)
        fs = shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vs, fs)
        self.uni_time = glGetUniformLocation(self.shader, 'iTime')
        self.uni_resolution = glGetUniformLocation(self.shader, 'iResolution')
        self.uni_kick = glGetUniformLocation(self.shader, 'iKickPulse')
        self.uni_hat = glGetUniformLocation(self.shader, 'iHatGlitch')
        self.uni_tom1 = glGetUniformLocation(self.shader, 'iTom1Morph')
        self.uni_tom2 = glGetUniformLocation(self.shader, 'iTom2Spin')
        self.uni_bass_note = glGetUniformLocation(self.shader, 'iBassNote')
        self.uni_bass_pulse = glGetUniformLocation(self.shader, 'iBassPulse')

        # Shader franjas
        fvs = shaders.compileShader(FRANJA_VERTEX, GL_VERTEX_SHADER)
        ffs = shaders.compileShader(FRANJA_FRAGMENT, GL_FRAGMENT_SHADER)
        self.franja_shader = shaders.compileProgram(fvs, ffs)
        self.franja_resolution = glGetUniformLocation(self.franja_shader, 'iResolution')

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

        self.kick_pulse = self.kick_target = self.hat_glitch = self.tom1_morph = self.tom2_spin = 0.0
        self.bass_note = 0.0  # Nota actual del bassline (0-1)
        self.bass_pulse = 0.0  # Intensidad de la nota
        self.midi_input = self._connect_midi()
        self.clock = pygame.time.Clock()
        self.start_time = pygame.time.get_ticks()

    def _connect_midi(self):
        try:
            for port in mido.get_input_names():
                if 'CIRCUIT' in port.upper() or 'TRACKS' in port.upper():
                    return mido.open_input(port)
            print("⚠️  Demo mode (K/H/T/Y)")
        except: pass
        return None

    def process_midi(self):
        if self.midi_input:
            for msg in self.midi_input.iter_pending():
                if msg.type == 'note_on' and msg.velocity > 0:
                    v = msg.velocity / 127.0

                    # Canal 1: Bassline (metamorfosis de estructura)
                    if msg.channel == 0:  # Canal 1 en mido (0-indexed)
                        # Normalizar nota (36-84 -> 0-1)
                        note_normalized = max(0.0, min(1.0, (msg.note - 36) / 48.0))
                        self.bass_note = note_normalized
                        self.bass_pulse = min(1.0, self.bass_pulse + v * 0.5)

                    # Notas de batería (cualquier canal)
                    if msg.note == KICK_NOTE: self.kick_target = min(1.0, self.kick_target + v * 0.7)
                    elif msg.note == CLOSEHAT_NOTE: self.hat_glitch = min(1.0, self.hat_glitch + v * 0.8)
                    elif msg.note == TOM1_NOTE: self.tom1_morph = min(1.0, self.tom1_morph + v * 0.6)
                    elif msg.note == TOM2_NOTE: self.tom2_spin = min(1.0, self.tom2_spin + v * 0.7)

    def update_params(self):
        self.kick_pulse += (self.kick_target - self.kick_pulse) * 0.15
        self.kick_target *= 0.92
        self.hat_glitch *= 0.88
        self.tom1_morph *= 0.90
        self.tom2_spin *= 0.93
        self.bass_pulse *= 0.80  # Decay rápido para respuesta dinámica

    def calculate_viewport(self, w, h):
        a = w / h
        if a > self.target_aspect:
            vh = h; vw = int(vh * self.target_aspect); return (w - vw) // 2, 0, vw, vh
        vw = w; vh = int(vw / self.target_aspect); return 0, (h - vh) // 2, vw, vh

    def render(self):
        w, h = self.screen.get_size()
        vx, vy, vw, vh = self.calculate_viewport(w, h)

        glViewport(0, 0, w, h); glClearColor(0, 0, 0, 1); glClear(GL_COLOR_BUFFER_BIT)

        # Dibujar franjas con líneas inclinadas
        if vx > 0:
            glUseProgram(self.franja_shader)
            glUniform2f(self.franja_resolution, float(w), float(h))
            glBindVertexArray(self.franja_vao)
            glViewport(0, 0, vx, h); glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
            glViewport(vx + vw, 0, w - (vx + vw), h); glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

        # Dibujar shader principal
        glViewport(vx, vy, vw, vh)
        glUseProgram(self.shader)
        glUniform1f(self.uni_time, (pygame.time.get_ticks() - self.start_time) / 1000.0)
        glUniform2f(self.uni_resolution, float(vw), float(vh))
        glUniform1f(self.uni_kick, self.kick_pulse)
        glUniform1f(self.uni_hat, self.hat_glitch)
        glUniform1f(self.uni_tom1, self.tom1_morph)
        glUniform1f(self.uni_tom2, self.tom2_spin)
        glUniform1f(self.uni_bass_note, self.bass_note)
        glUniform1f(self.uni_bass_pulse, self.bass_pulse)
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    running = False
                elif event.type == KEYDOWN:
                    if event.key == K_k: self.kick_target = min(1.0, self.kick_target + 0.7)
                    elif event.key == K_h: self.hat_glitch = min(1.0, self.hat_glitch + 0.8)
                    elif event.key == K_t: self.tom1_morph = min(1.0, self.tom1_morph + 0.6)
                    elif event.key == K_y: self.tom2_spin = min(1.0, self.tom2_spin + 0.7)
            self.process_midi(); self.update_params(); self.render(); self.clock.tick(60)
        if self.midi_input: self.midi_input.close()
        pygame.quit()

if __name__ == '__main__': ShaderVisualEngine().run()
