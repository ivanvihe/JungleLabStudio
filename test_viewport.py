#!/usr/bin/env python3
"""
Test para verificar cálculos de viewport
"""

# Simular el cálculo
target_width = 1080
target_height = 1920
target_aspect = target_width / target_height  # 0.5625

# Ventana de ejemplo (ancha)
w = 1200
h = 900

print("=" * 60)
print("TEST DE VIEWPORT")
print("=" * 60)
print(f"Target: {target_width}x{target_height} (aspect: {target_aspect:.4f})")
print(f"Ventana: {w}x{h}")
print()

a = w / h
print(f"Aspect ratio ventana: {a:.4f}")
print(f"¿Ventana más ancha que target? {a > target_aspect}")
print()

if a > target_aspect:
    vh = h
    vw = int(vh * target_aspect)
    vx = (w - vw) // 2
    vy = 0
    print("PILLARBOXING (barras laterales)")
    print(f"  Viewport height: {vh}")
    print(f"  Viewport width: {vw}")
    print(f"  Viewport X offset: {vx}")
    print(f"  Viewport Y offset: {vy}")
    print()
    print(f"Franja izquierda: x=0 to x={vx} (width={vx})")
    print(f"Viewport principal: x={vx} to x={vx+vw} (width={vw})")
    print(f"Franja derecha: x={vx+vw} to x={w} (width={w-(vx+vw)})")
    print()

    # Verificar que está centrado
    left_space = vx
    right_space = w - (vx + vw)
    print(f"Espacio izquierdo: {left_space}")
    print(f"Espacio derecho: {right_space}")
    print(f"¿Centrado? {left_space == right_space or abs(left_space - right_space) <= 1}")
else:
    vw = w
    vh = int(vw / target_aspect)
    vx = 0
    vy = (h - vh) // 2
    print("LETTERBOXING (barras arriba/abajo)")
    print(f"  Viewport width: {vw}")
    print(f"  Viewport height: {vh}")
    print(f"  Viewport X offset: {vx}")
    print(f"  Viewport Y offset: {vy}")
