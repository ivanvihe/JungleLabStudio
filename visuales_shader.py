#!/usr/bin/env python3
"""
Shader-based Visual Engine con MIDI
Controlado por Focusrite-Novation Circuit Tracks
Preset 2: OpenGL Shaders VFX Generativos
"""

from __future__ import division
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL import shaders
import mido
from sys import exit as exitsystem
from numpy import array

# Notas MIDI
KICK_NOTE = 60
CLOSEHAT_NOTE = 62
TOM1_NOTE = 64
TOM2_NOTE = 65

# Vertex Shader (fullscreen quad)
VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec3 vPos;
void main()
{
    gl_Position = vec4(vPos, 1.0);
}
"""

# Fragment Shader VFX Generativo
FRAGMENT_SHADER = """
#version 330 core
#define fragCoord gl_FragCoord.xy

uniform vec2  iMouse;
uniform float iTime;
uniform vec2  iResolution;

// MIDI uniforms
uniform float iKickPulse;
uniform float iHatGlitch;
uniform float iTom1Morph;
uniform float iTom2Spin;

out vec4 fragColor;

// === NOISE FUNCTIONS ===
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);

    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));

    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
    float value = 0.0;
    float amplitude = 0.5;
    for(int i = 0; i < 6; i++) {
        value += amplitude * noise(p);
        p *= 2.0;
        amplitude *= 0.5;
    }
    return value;
}

// === DISTANCE FUNCTIONS (SDF) ===
float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

float sdBox(vec3 p, vec3 b) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
}

float sdTorus(vec3 p, vec2 t) {
    vec2 q = vec2(length(p.xz) - t.x, p.y);
    return length(q) - t.y;
}

// Operaciones booleanas
float opSmoothUnion(float d1, float d2, float k) {
    float h = clamp(0.5 + 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return mix(d2, d1, h) - k * h * (1.0 - h);
}

// === SCENE SDF ===
float map(vec3 p) {
    // Aplicar distorsión basada en FBM
    float distortion = fbm(p.xy * 2.0 + iTime * 0.3) * 0.3 * iTom1Morph;
    p += distortion;

    // Kick modula el tamaño
    float kickScale = 1.0 + iKickPulse * 0.8;

    // Forma base - morphing entre esfera, box y torus
    float sphere = sdSphere(p, 0.8 * kickScale);
    float box = sdBox(p, vec3(0.6 * kickScale));
    float torus = sdTorus(p, vec2(0.7 * kickScale, 0.3));

    // Morph entre formas con Tom1
    float shape1 = mix(sphere, box, iTom1Morph);
    float shape2 = mix(box, torus, iTom1Morph);
    float mainShape = opSmoothUnion(shape1, shape2, 0.3);

    // Hat glitch - añade esferas aleatorias
    if (iHatGlitch > 0.1) {
        for(int i = 0; i < 3; i++) {
            vec3 offset = vec3(
                sin(iTime * 3.0 + float(i)),
                cos(iTime * 2.0 + float(i)),
                sin(iTime * 1.5 + float(i))
            ) * iHatGlitch;
            float glitchSphere = sdSphere(p - offset, 0.2 * iHatGlitch);
            mainShape = opSmoothUnion(mainShape, glitchSphere, 0.2);
        }
    }

    return mainShape;
}

// === RAYMARCHING ===
vec3 calcNormal(vec3 p) {
    const vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

float raymarch(vec3 ro, vec3 rd) {
    float t = 0.0;
    for(int i = 0; i < 80; i++) {
        vec3 p = ro + rd * t;
        float d = map(p);
        if(d < 0.001) break;
        t += d;
        if(t > 20.0) break;
    }
    return t;
}

// === LIGHTING ===
vec3 shade(vec3 p, vec3 rd, vec3 normal) {
    // Múltiples luces
    vec3 lightPos1 = vec3(2.0, 2.0, 2.0);
    vec3 lightPos2 = vec3(-2.0, -1.0, 3.0);

    vec3 lightDir1 = normalize(lightPos1 - p);
    vec3 lightDir2 = normalize(lightPos2 - p);

    // Diffuse
    float diff1 = max(dot(normal, lightDir1), 0.0);
    float diff2 = max(dot(normal, lightDir2), 0.0);

    // Specular
    vec3 halfDir1 = normalize(lightDir1 - rd);
    float spec1 = pow(max(dot(normal, halfDir1), 0.0), 32.0);

    // Fresnel
    float fresnel = pow(1.0 - max(dot(normal, -rd), 0.0), 3.0);

    // Color base con gradiente
    vec3 baseColor = 0.5 + 0.5 * cos(iTime + p.xyx * 2.0 + vec3(0, 2, 4));

    // Kick modula brillo
    float kickBrightness = iKickPulse * 0.5;

    // Combinar iluminación
    vec3 color = baseColor * (diff1 * 0.8 + diff2 * 0.4);
    color += spec1 * 0.5;
    color += fresnel * baseColor * 0.3;
    color += kickBrightness;

    return color;
}

// === POST-PROCESSING ===
vec3 chromaticAberration(vec2 uv, float amount) {
    vec2 offset = vec2(amount * 0.01, 0.0);
    return vec3(1.0 + offset.x, 1.0, 1.0 - offset.x);
}

// === MAIN ===
void main()
{
    // UV coordinates (0 a 1)
    vec2 uv = fragCoord / iResolution.xy;

    // Centered coordinates para 9:16 vertical
    // Normalizamos por altura para mantener aspecto correcto
    vec2 p = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

    // Camera setup
    vec3 ro = vec3(0.0, 0.0, 3.0);  // Ray origin
    vec3 rd = normalize(vec3(p, -1.5));  // Ray direction

    // Tom2 modula rotación de cámara
    float angle = iTime * (0.3 + iTom2Spin * 1.5);
    float ca = cos(angle);
    float sa = sin(angle);
    rd.xz = mat2(ca, -sa, sa, ca) * rd.xz;

    // Hat glitch en raydir
    if (iHatGlitch > 0.1) {
        rd.xy += vec2(
            hash(vec2(iTime * 10.0, uv.y)) - 0.5,
            hash(vec2(iTime * 10.0 + 1.0, uv.x)) - 0.5
        ) * iHatGlitch * 0.1;
        rd = normalize(rd);
    }

    // Raymarch
    float t = raymarch(ro, rd);

    vec3 color = vec3(0.0);

    if (t < 20.0) {
        // Hit surface
        vec3 p = ro + rd * t;
        vec3 normal = calcNormal(p);
        color = shade(p, rd, normal);

        // Ambient occlusion
        float ao = 1.0 - float(t) / 20.0;
        color *= ao;

    } else {
        // Background con FBM
        float bg = fbm(p * 2.0 + iTime * 0.1);
        color = vec3(bg * 0.1);

        // Kick ilumina el fondo
        color += iKickPulse * 0.2;
    }

    // === POST-PROCESSING ===

    // Vignette
    float vignette = 1.0 - 0.5 * length(p * 0.5);
    color *= vignette;

    // Chromatic aberration con hats
    if (iHatGlitch > 0.2) {
        color *= chromaticAberration(uv, iHatGlitch);
    }

    // Glow en los bordes
    float glow = exp(-length(p) * 0.8) * 0.3;
    color += glow * (0.5 + 0.5 * cos(iTime + vec3(0, 2, 4)));

    // Scanlines sutiles
    color *= 0.95 + 0.05 * sin(uv.y * iResolution.y * 2.0);

    // Noise grain
    float grain = hash(uv * iTime) * 0.05;
    color += grain;

    // Tone mapping
    color = color / (color + vec3(1.0));

    // Gamma correction
    color = pow(color, vec3(1.0 / 2.2));

    fragColor = vec4(color, 1.0);
}
"""


class ShaderVisualEngine:
    def __init__(self):
        pygame.init()

        # Target resolution (9:16 vertical - Instagram Reels)
        self.target_width = 1080
        self.target_height = 1920
        self.target_aspect = self.target_width / self.target_height  # 0.5625

        # Crear ventana redimensionable con tamaño inicial vertical
        # Iniciar con una ventana más pequeña que se vea bien en pantalla
        initial_height = 900  # Altura razonable para pantallas comunes
        initial_width = int(initial_height * self.target_aspect)  # Mantener aspect ratio

        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)
        self.screen = pygame.display.set_mode(
            (initial_width, initial_height),
            DOUBLEBUF | OPENGL | RESIZABLE
        )
        pygame.display.set_caption('VFX Shader Engine - Circuit Tracks [9:16 Vertical]')

        # Compile shaders
        self.vertex_shader = shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER)
        self.fragment_shader = shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)

        # Shader program
        self.shader = shaders.compileProgram(self.vertex_shader, self.fragment_shader)

        # Get uniform locations
        self.uni_mouse = glGetUniformLocation(self.shader, 'iMouse')
        self.uni_time = glGetUniformLocation(self.shader, 'iTime')
        self.uni_resolution = glGetUniformLocation(self.shader, 'iResolution')

        # MIDI uniform locations
        self.uni_kick = glGetUniformLocation(self.shader, 'iKickPulse')
        self.uni_hat = glGetUniformLocation(self.shader, 'iHatGlitch')
        self.uni_tom1 = glGetUniformLocation(self.shader, 'iTom1Morph')
        self.uni_tom2 = glGetUniformLocation(self.shader, 'iTom2Spin')

        # Create fullscreen quad
        self.vertices = array([-1.0, -1.0, 0.0,
                                1.0, -1.0, 0.0,
                                1.0,  1.0, 0.0,
                               -1.0,  1.0, 0.0], dtype='float32')

        # Generate VAO
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # Generate VBO
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices, GL_STATIC_DRAW)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

        # MIDI state
        self.kick_pulse = 0.0
        self.kick_target = 0.0
        self.hat_glitch = 0.0
        self.tom1_morph = 0.0
        self.tom2_spin = 0.0

        # Connect MIDI
        self.midi_input = self._connect_midi()

        self.clock = pygame.time.Clock()

    def _connect_midi(self):
        """Conectar al Circuit Tracks"""
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
                print("="*60)
                print("VFX SHADER ENGINE - Preset 2")
                print("="*60)
                print("Formato: Instagram Reels (1080x1920 - 9:16 VERTICAL)")
                print("\nTécnicas VFX:")
                print("  - Raymarching 3D")
                print("  - Signed Distance Fields (SDF)")
                print("  - Fractal Brownian Motion (FBM)")
                print("  - Chromatic Aberration")
                print("  - Vignette & Glow")
                print("\nShader MIDI mapping:")
                print(f"  Kick ({KICK_NOTE}): Expande formas 3D")
                print(f"  Hats ({CLOSEHAT_NOTE}): Glitch + esferas random")
                print(f"  Tom 1 ({TOM1_NOTE}): Morph entre formas")
                print(f"  Tom 2 ({TOM2_NOTE}): Rotación de cámara")
                print("="*60)
                return mido.open_input(circuit_port)
            else:
                print("\n[WARNING] Circuit Tracks no encontrado")
                print("Modo demo: sin MIDI")
                if available_ports:
                    print(f"Usando: {available_ports[0]}")
                    return mido.open_input(available_ports[0])
        except Exception as e:
            print(f"Error conectando MIDI: {e}")

        return None

    def calculate_viewport(self, window_width, window_height):
        """
        Calcula viewport con letterboxing para mantener aspect ratio 9:16
        Retorna: (x, y, width, height) del viewport
        """
        window_aspect = window_width / window_height

        if window_aspect > self.target_aspect:
            # Ventana más ancha - añadir barras negras a los lados
            viewport_height = window_height
            viewport_width = int(viewport_height * self.target_aspect)
            viewport_x = (window_width - viewport_width) // 2
            viewport_y = 0
        else:
            # Ventana más alta - añadir barras arriba/abajo
            viewport_width = window_width
            viewport_height = int(viewport_width / self.target_aspect)
            viewport_x = 0
            viewport_y = (window_height - viewport_height) // 2

        return viewport_x, viewport_y, viewport_width, viewport_height

    def handle_midi(self):
        """Procesar mensajes MIDI"""
        if not self.midi_input:
            return

        for msg in self.midi_input.iter_pending():
            if msg.type == 'note_on' and msg.velocity > 0:
                vel = msg.velocity / 127.0

                if msg.note == KICK_NOTE:
                    self.kick_target = min(1.0, self.kick_target + vel)
                    print(f"KICK - Velocity: {msg.velocity}")

                elif msg.note == CLOSEHAT_NOTE:
                    self.hat_glitch = min(1.0, self.hat_glitch + vel * 0.9)
                    print(f"HAT - Velocity: {msg.velocity}")

                elif msg.note == TOM1_NOTE:
                    self.tom1_morph = min(1.0, self.tom1_morph + vel * 0.3)
                    print(f"TOM1 - Velocity: {msg.velocity}")

                elif msg.note == TOM2_NOTE:
                    self.tom2_spin = vel * 2.0 - 1.0
                    print(f"TOM2 - Velocity: {msg.velocity}")

    def update_midi_params(self):
        """Actualizar parámetros MIDI con smooth decay"""
        self.kick_pulse += (self.kick_target - self.kick_pulse) * 0.25
        self.kick_target *= 0.88

        self.hat_glitch *= 0.9
        self.tom1_morph *= 0.985
        self.tom2_spin *= 0.97

    def mainloop(self):
        """Loop principal"""
        print("\nVFX Shader Engine iniciado")
        print("Ventana redimensionable - mantiene aspect ratio 9:16")
        print("Presiona ESC para salir\n")

        while True:
            delta = self.clock.tick(60)

            # Obtener tamaño actual de ventana
            window_width, window_height = self.screen.get_size()

            # Calcular viewport con letterboxing
            vp_x, vp_y, vp_width, vp_height = self.calculate_viewport(window_width, window_height)

            # Limpiar toda la ventana a negro
            glViewport(0, 0, window_width, window_height)
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)

            # Setear viewport solo para la región vertical
            glViewport(vp_x, vp_y, vp_width, vp_height)

            for event in pygame.event.get():
                if (event.type == QUIT) or (event.type == KEYUP and event.key == K_ESCAPE):
                    if self.midi_input:
                        self.midi_input.close()
                    pygame.quit()
                    exitsystem()

            # Handle MIDI
            self.handle_midi()
            self.update_midi_params()

            glUseProgram(self.shader)

            # Send uniform values
            # La resolución siempre es la target (1080x1920) independiente del tamaño de ventana
            glUniform2f(self.uni_resolution, float(self.target_width), float(self.target_height))
            glUniform2f(self.uni_mouse, *pygame.mouse.get_pos())
            glUniform1f(self.uni_time, pygame.time.get_ticks() / 1000.0)

            # Send MIDI uniforms
            glUniform1f(self.uni_kick, self.kick_pulse)
            glUniform1f(self.uni_hat, self.hat_glitch)
            glUniform1f(self.uni_tom1, self.tom1_morph)
            glUniform1f(self.uni_tom2, self.tom2_spin)

            # Draw fullscreen quad
            glBindVertexArray(self.vao)
            glDrawArrays(GL_QUADS, 0, 4)

            pygame.display.set_caption(
                f"VFX Shader [9:16] | FPS: {int(self.clock.get_fps())} | "
                f"Window: {window_width}x{window_height} | Viewport: {vp_width}x{vp_height}"
            )
            pygame.display.flip()


if __name__ == '__main__':
    ShaderVisualEngine().mainloop()
