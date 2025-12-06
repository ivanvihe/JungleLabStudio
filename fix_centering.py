#!/usr/bin/env python3
"""
Script para corregir el centrado en formato vertical
Para 9:16, necesitamos dividir por iResolution.x (el lado más corto)
"""

import re
import os

def fix_preset(preset_num):
    """Corrige el centrado del preset"""
    filename = f'visuales_shader_{preset_num}.py'

    if not os.path.exists(filename):
        return False

    with open(filename, 'r') as f:
        content = f.read()

    print(f"🔧 Fixing preset {preset_num} centering...")

    # Patrón incorrecto: dividir por iResolution.y
    # Correcto para vertical: dividir por iResolution.x (lado más corto)
    pattern = r'vec2 p = \(fragCoord - iResolution\.xy \* 0\.5\) / iResolution\.y;'
    replacement = r'vec2 p = (fragCoord - iResolution.xy * 0.5) / iResolution.x;'

    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)

        with open(filename, 'w') as f:
            f.write(content)

        print(f"✅ Preset {preset_num} centrado corregido")
        return True
    else:
        print(f"⏭️  Preset {preset_num}: patrón no encontrado o ya corregido")
        return True

# Actualizar presets 3-23
presets = ['3', '4', '5', '6', '7', '8', '9', '10'] + [str(i) for i in range(11, 24)]

print("=" * 60)
print("CORRECCIÓN DE CENTRADO PARA FORMATO VERTICAL")
print("=" * 60)
print("Cambiando: / iResolution.y  →  / iResolution.x")
print()

success = 0
for p in presets:
    if fix_preset(p):
        success += 1

print()
print("=" * 60)
print(f"✅ Completado: {success}/{len(presets)}")
print("=" * 60)
