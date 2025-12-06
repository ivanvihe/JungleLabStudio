#!/usr/bin/env python3
"""
Script para corregir sintaxis de FRANJA_VERTEX en todos los presets
"""

import re
import os

def fix_preset(preset_num):
    """Corrige sintaxis de FRANJA_VERTEX"""
    filename = f'visuales_shader_{preset_num}.py'

    if not os.path.exists(filename):
        return False

    with open(filename, 'r') as f:
        content = f.read()

    # Buscar el patrón incorrecto (multilínea sin quotes)
    pattern = r'FRANJA_VERTEX = "#version 330 core\nlayout\(location = 0\) in vec2 vPos;\nvoid main\(\) \{ gl_Position = vec4\(vPos, 0\.0, 1\.0\); \}"'

    if re.search(pattern, content):
        print(f"🔧 Fixing preset {preset_num} FRANJA_VERTEX syntax...")

        # Reemplazar con versión correcta (una línea con \n)
        replacement = r'FRANJA_VERTEX = "#version 330 core\\nlayout(location = 0) in vec2 vPos;\\nvoid main() { gl_Position = vec4(vPos, 0.0, 1.0); }"'

        content = re.sub(pattern, replacement, content)

        with open(filename, 'w') as f:
            f.write(content)

        print(f"✅ Preset {preset_num} sintaxis corregida")
        return True
    else:
        print(f"⏭️  Preset {preset_num}: sintaxis OK")
        return True

# Actualizar presets 3-22
presets = ['3', '4', '5', '6', '7', '8', '9', '10'] + [str(i) for i in range(11, 23)]

print("=" * 60)
print("CORRECCIÓN DE SINTAXIS FRANJA_VERTEX")
print("=" * 60)

success = 0
for p in presets:
    if fix_preset(p):
        success += 1

print()
print("=" * 60)
print(f"✅ Completado: {success}/{len(presets)}")
print("=" * 60)
