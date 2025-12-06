#!/usr/bin/env python3
"""
Script para corregir el centrado del viewport en TODOS los presets
El problema: la franja derecha usa ancho 'vx' cuando debería usar el espacio restante real
"""

import re
import os
import glob

def fix_preset(filename):
    """Corrige el rendering del viewport"""

    with open(filename, 'r') as f:
        content = f.read()

    print(f"🔧 Fixing {filename}...")

    changed = False

    # Buscar el patrón del método render
    # Necesitamos cambiar la franja derecha para usar el ancho correcto

    # Patrón actual (incorrecto):
    # glViewport(vx + vw, 0, vx, h)
    #
    # Debería ser:
    # glViewport(vx + vw, 0, w - (vx + vw), h)

    pattern = r'glViewport\(vx \+ vw, 0, vx, h\)'
    replacement = r'glViewport(vx + vw, 0, w - (vx + vw), h)'

    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        print(f"  ✓ Franja derecha corregida")
        changed = True

    if changed:
        with open(filename, 'w') as f:
            f.write(content)
        print(f"✅ {filename} actualizado")
        return True
    else:
        print(f"⏭️  {filename}: ya estaba correcto o patrón no encontrado")
        return False

# Procesar todos los archivos visuales_shader_*.py
files = sorted(glob.glob('visuales_shader_*.py'))

print("=" * 70)
print("CORRECCIÓN DE CENTRADO DE VIEWPORT")
print("=" * 70)
print("Cambiando franja derecha de 'vx' a 'w - (vx + vw)'")
print()

success = 0
for filename in files:
    if fix_preset(filename):
        success += 1
    print()

print("=" * 70)
print(f"✅ Completado: {success}/{len(files)} archivos actualizados")
print("=" * 70)
