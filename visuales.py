#!/usr/bin/env python3
"""
MVP - Generador de Visuales Audiovisuales con MIDI
Controlado por Focusrite-Novation Circuit Tracks
Estilo: Ultra Minimal - Un solo visual generativo central
Formato: Instagram Reels (Vertical)
"""

import pygame
import mido
import numpy as np
import sys
import random
import math
from dataclasses import dataclass
from typing import List, Tuple

# Configuración
WIDTH = 1080
HEIGHT = 1920
FPS = 60

# Notas MIDI
KICK_NOTE = 60
CLOSEHAT_NOTE = 62
TOM1_NOTE = 64
TOM2_NOTE = 65

# Paleta minimal
GRAY = (120, 120, 120)
DARK_GRAY = (80, 80, 80)
BLACK = (0, 0, 0)


class GenerativeForm:
    """
    Forma generativa central única
    - Kick: Pulsa/expande la forma
    - Hats: Glitch/distorsión
    - Toms: Transformación de geometría
    """
    def __init__(self):
        # Centro de la pantalla
        self.x = WIDTH // 2
        self.y = HEIGHT // 2

        # Forma base
        self.num_points = 6  # Hexágono inicial
        self.base_radius = 100
        self.current_radius = self.base_radius
        self.target_radius = self.base_radius

        # Estado de pulso (kick)
        self.pulse_intensity = 0
        self.pulse_target = 0

        # Distorsión (hats)
        self.glitch_intensity = 0
        self.glitch_offset = []
        for i in range(20):
            self.glitch_offset.append({'x': 0, 'y': 0, 'target_x': 0, 'target_y': 0})

        # Transformación (toms)
        self.morph_state = 0  # 0 = círculo, 1 = triángulo, 2 = cuadrado, etc
        self.morph_progress = 0
        self.rotation = 0
        self.rotation_speed = 0

        # Ruido para variación orgánica
        self.noise_offset = 0

    def trigger_kick(self, velocity):
        """Kick pulsa la forma"""
        vel = velocity / 127.0
        self.pulse_target = min(1.0, self.pulse_target + vel * 0.8)
        self.target_radius = self.base_radius * (1 + vel * 0.4)

    def trigger_hat(self, velocity):
        """Hat causa glitch/distorsión"""
        vel = velocity / 127.0
        self.glitch_intensity = min(1.0, self.glitch_intensity + vel * 0.6)

        # Trigger nuevos offsets aleatorios
        for offset in self.glitch_offset:
            offset['target_x'] = random.uniform(-30, 30) * vel
            offset['target_y'] = random.uniform(-30, 30) * vel

    def trigger_tom(self, velocity, note):
        """Tom transforma la geometría"""
        vel = velocity / 127.0

        # Tom 1: cambia número de lados
        if note == TOM1_NOTE:
            shapes = [3, 4, 5, 6, 8, 12]  # triángulo, cuadrado, pentágono, hexágono, octágono, 12-gon
            self.num_points = random.choice(shapes)

        # Tom 2: cambia rotación
        elif note == TOM2_NOTE:
            self.rotation_speed = random.uniform(-3, 3) * vel

    def update(self):
        """Actualizar estado de la forma"""
        # Smooth interpolation del pulso
        self.pulse_intensity += (self.pulse_target - self.pulse_intensity) * 0.15
        self.pulse_target *= 0.92  # Decay

        # Smooth interpolation del radio
        self.current_radius += (self.target_radius - self.current_radius) * 0.1
        self.target_radius += (self.base_radius - self.target_radius) * 0.08  # Vuelve a base

        # Decay del glitch
        self.glitch_intensity *= 0.88

        # Smooth interpolation de offsets de glitch
        for offset in self.glitch_offset:
            offset['x'] += (offset['target_x'] - offset['x']) * 0.2
            offset['y'] += (offset['target_y'] - offset['y']) * 0.2
            offset['target_x'] *= 0.9
            offset['target_y'] *= 0.9

        # Rotación
        self.rotation += self.rotation_speed
        self.rotation_speed *= 0.98  # Friction

        # Ruido orgánico
        self.noise_offset += 0.02

    def draw(self, surface):
        """Renderizar la forma generativa"""
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # Calcular puntos de la forma
        points = []
        for i in range(self.num_points):
            angle = (i / self.num_points) * 2 * math.pi + math.radians(self.rotation)

            # Radio con variación de pulso y ruido orgánico
            noise = math.sin(self.noise_offset + i * 0.5) * 8
            radius = self.current_radius + noise + (self.pulse_intensity * 50)

            # Posición
            px = self.x + math.cos(angle) * radius
            py = self.y + math.sin(angle) * radius

            points.append((int(px), int(py)))

        # Dibujar forma principal
        if len(points) > 2:
            # Forma base
            alpha_base = 200
            pygame.draw.lines(s, (*GRAY, alpha_base), True, points, 3)

            # Glow sutil
            for thickness in [6, 9]:
                alpha_glow = alpha_base // (thickness // 2)
                pygame.draw.lines(s, (*GRAY, alpha_glow), True, points, thickness)

        # Dibujar ecos/glitch si hay intensidad
        if self.glitch_intensity > 0.1:
            num_echoes = int(self.glitch_intensity * 8)
            for i in range(num_echoes):
                if i < len(self.glitch_offset):
                    offset = self.glitch_offset[i]

                    # Puntos desplazados
                    echo_points = []
                    for px, py in points:
                        echo_points.append((
                            int(px + offset['x']),
                            int(py + offset['y'])
                        ))

                    # Alpha basado en intensidad
                    alpha_echo = int(self.glitch_intensity * 120 * (1 - i / num_echoes))

                    if len(echo_points) > 2:
                        pygame.draw.lines(s, (*DARK_GRAY, alpha_echo), True, echo_points, 2)

        # Punto central sutil
        center_alpha = int(100 + self.pulse_intensity * 100)
        pygame.draw.circle(s, (*GRAY, center_alpha), (int(self.x), int(self.y)), 3)

        surface.blit(s, (0, 0))


class VisualEngine:
    """Motor minimal - Un solo visual generativo"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Minimal Generative - Circuit Tracks")
        self.clock = pygame.time.Clock()
        self.running = True

        # Una sola forma generativa
        self.form = GenerativeForm()

        # Buffer para debug de MIDI
        self.midi_debug_buffer = []
        self.max_debug_messages = 4

        # Conectar MIDI
        self.midi_input = self._connect_midi()
        if not self.midi_input:
            print("No se pudo conectar al dispositivo MIDI")
            print("Modo demo: K=kick, H=hat, T=tom1, Y=tom2")

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
                print("MINIMAL GENERATIVE SYSTEM")
                print("="*60)
                print("Formato: Instagram Reels (1080x1920)")
                print("\nUn solo visual generativo central:")
                print(f"  Kick ({KICK_NOTE}): Pulsa/expande la forma")
                print(f"  Hats ({CLOSEHAT_NOTE}): Glitch/distorsión")
                print(f"  Tom 1 ({TOM1_NOTE}): Cambia geometría")
                print(f"  Tom 2 ({TOM2_NOTE}): Modula rotación")
                print("="*60)
                return mido.open_input(circuit_port)
            else:
                print("\n[WARNING] Circuit Tracks no encontrado")
                if available_ports:
                    print(f"Usando: {available_ports[0]}")
                    return mido.open_input(available_ports[0])
        except Exception as e:
            print(f"Error conectando MIDI: {e}")

        return None

    def handle_midi(self):
        """Procesar mensajes MIDI entrantes"""
        if not self.midi_input:
            return

        for msg in self.midi_input.iter_pending():
            if msg.type == 'note_on' and msg.velocity > 0:
                debug_msg = f"N={msg.note} V={msg.velocity}"
                self.midi_debug_buffer.append(debug_msg)

                if len(self.midi_debug_buffer) > self.max_debug_messages:
                    self.midi_debug_buffer.pop(0)

                # Trigger apropiado según nota
                if msg.note == KICK_NOTE:
                    self.form.trigger_kick(msg.velocity)
                    print(f"KICK - Velocity: {msg.velocity}")

                elif msg.note == CLOSEHAT_NOTE:
                    self.form.trigger_hat(msg.velocity)
                    print(f"HAT - Velocity: {msg.velocity}")

                elif msg.note in [TOM1_NOTE, TOM2_NOTE]:
                    self.form.trigger_tom(msg.velocity, msg.note)
                    print(f"TOM {msg.note} - Velocity: {msg.velocity}")

    def handle_keyboard(self, event):
        """Modo demo con teclado"""
        key_map = {
            pygame.K_k: (KICK_NOTE, 100),
            pygame.K_h: (CLOSEHAT_NOTE, 100),
            pygame.K_t: (TOM1_NOTE, 100),
            pygame.K_y: (TOM2_NOTE, 100),
        }

        if event.key in key_map:
            note, velocity = key_map[event.key]

            if note == KICK_NOTE:
                self.form.trigger_kick(velocity)
            elif note == CLOSEHAT_NOTE:
                self.form.trigger_hat(velocity)
            elif note in [TOM1_NOTE, TOM2_NOTE]:
                self.form.trigger_tom(velocity, note)

    def update(self):
        """Actualizar la forma generativa"""
        self.form.update()

    def draw(self):
        """Renderizar"""
        # Fondo negro limpio
        self.screen.fill(BLACK)

        # Dibujar forma generativa
        self.form.draw(self.screen)

        # UI minimal
        font = pygame.font.Font(None, 16)
        font_small = pygame.font.Font(None, 14)

        # FPS discreto
        fps_text = f"{int(self.clock.get_fps())}"
        text = font.render(fps_text, True, (40, 40, 40))
        self.screen.blit(text, (10, 10))

        if not self.midi_input:
            demo_text = font.render("K H T Y", True, (50, 50, 50))
            self.screen.blit(demo_text, (10, 30))

        # MIDI Debug muy discreto
        if self.midi_debug_buffer:
            debug_x = WIDTH - 80
            debug_y = HEIGHT - 15 - (len(self.midi_debug_buffer) * 14)

            for i, msg in enumerate(self.midi_debug_buffer):
                debug_text = font_small.render(msg, True, (50, 50, 50))
                self.screen.blit(debug_text, (debug_x, debug_y + i * 14))

        pygame.display.flip()

    def run(self):
        """Loop principal"""
        print("\n" + "="*60)
        print("MINIMAL GENERATIVE VISUAL ENGINE")
        print("="*60)
        print("Presiona ESC para salir\n")

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif not self.midi_input:
                        self.handle_keyboard(event)

            self.handle_midi()
            self.update()
            self.draw()

            self.clock.tick(FPS)

        if self.midi_input:
            self.midi_input.close()
        pygame.quit()


if __name__ == "__main__":
    engine = VisualEngine()
    engine.run()
