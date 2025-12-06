#!/usr/bin/env python3
"""
Test de rendimiento - Simula carga MIDI para verificar FPS
"""

import pygame
import sys
import time

# Inicializar pygame
pygame.init()
screen = pygame.display.set_mode((1080, 1920))
clock = pygame.time.Clock()

# Stats
frame_count = 0
start_time = time.time()
fps_samples = []

print("="*60)
print("TEST DE RENDIMIENTO")
print("="*60)
print("Simulando carga MIDI intensa...")
print("Presiona ESC para salir")
print()

running = True
test_duration = 10  # segundos

# Simular carga
from visuales import VisualEngine
import random

engine = VisualEngine()

# Generar eventos MIDI simulados
notes = [60, 62, 64, 65]
event_counter = 0

while running and (time.time() - start_time) < test_duration:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    # Simular input MIDI aleatorio
    if event_counter % 10 == 0:  # Cada 10 frames
        note = random.choice(notes)
        velocity = random.randint(80, 127)
        engine.spawn_visual(note, velocity)

    event_counter += 1

    # Actualizar y dibujar
    engine.update()
    engine.draw()

    # Medir FPS
    current_fps = clock.get_fps()
    if current_fps > 0:
        fps_samples.append(current_fps)

    clock.tick(60)
    frame_count += 1

# Resultados
elapsed = time.time() - start_time
avg_fps = sum(fps_samples) / len(fps_samples) if fps_samples else 0
min_fps = min(fps_samples) if fps_samples else 0
max_fps = max(fps_samples) if fps_samples else 0

print()
print("="*60)
print("RESULTADOS")
print("="*60)
print(f"Duración: {elapsed:.2f}s")
print(f"Frames totales: {frame_count}")
print(f"FPS promedio: {avg_fps:.2f}")
print(f"FPS mínimo: {min_fps:.2f}")
print(f"FPS máximo: {max_fps:.2f}")
print()

if avg_fps >= 55:
    print("✓ Rendimiento EXCELENTE (>55 FPS)")
elif avg_fps >= 45:
    print("✓ Rendimiento BUENO (>45 FPS)")
elif avg_fps >= 30:
    print("⚠ Rendimiento ACEPTABLE (>30 FPS)")
else:
    print("✗ Rendimiento BAJO (<30 FPS) - Considera reducir partículas")

print("="*60)

pygame.quit()
