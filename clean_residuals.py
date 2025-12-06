#!/usr/bin/env python3
"""
Limpiar líneas residuales del código duplicado
"""

import re
import os

def clean_preset(preset_num):
    """Limpia líneas residuales"""
    filename = f'visuales_shader_{preset_num}.py'

    if not os.path.exists(filename):
        return False

    with open(filename, 'r') as f:
        content = f.read()

    # Eliminar líneas sueltas de glViewport que están mal indentadas o fuera de lugar
    # Buscar patrón: glViewport(...) justo después de otro glViewport(vx, vy, vw, vh)
    pattern = r'(glViewport\(vx, vy, vw, vh\))\s*\n\s+glViewport\([^)]+\); glDrawArrays\([^)]+\)\s*\n'

    if re.search(pattern, content):
        content = re.sub(pattern, r'\1\n', content)

        with open(filename, 'w') as f:
            f.write(content)

        print(f"✅ Preset {preset_num}: líneas residuales eliminadas")
        return True
    else:
        print(f"⏭️  Preset {preset_num}: OK")
        return True

# Actualizar presets 3-23
presets = ['3', '4', '5', '6', '7', '8', '9', '10'] + [str(i) for i in range(11, 24)]

print("=" * 60)
print("LIMPIEZA DE LÍNEAS RESIDUALES")
print("=" * 60)

for p in presets:
    clean_preset(p)

print("=" * 60)
