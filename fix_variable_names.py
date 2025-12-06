#!/usr/bin/env python3
"""
Script para corregir nombres de variables en render methods
"""

import re
import os

def fix_preset(preset_num):
    """Corrige nombres de variables en método render"""
    filename = f'visuales_shader_{preset_num}.py'

    if not os.path.exists(filename):
        return False

    with open(filename, 'r') as f:
        content = f.read()

    # Solo procesar si tiene el código de franjas
    if 'Dibujar franjas' not in content:
        print(f"⏭️  Preset {preset_num}: no tiene código de franjas")
        return False

    print(f"🔧 Fixing preset {preset_num} variables...")

    # Patrón 1: window_width, window_height, vp_x, vp_y, vp_w, vp_h
    # Necesitamos añadir: w, h, vx, vy, vw, vh
    pattern1 = r'def render\(self\):\s*\n\s*window_width, window_height = self\.screen\.get_size\(\)\s*\n\s*vp_x, vp_y, vp_w, vp_h = self\.calculate_viewport\(window_width, window_height\)'

    replacement1 = '''def render(self):
        w, h = self.screen.get_size()
        vx, vy, vw, vh = self.calculate_viewport(w, h)'''

    if re.search(pattern1, content):
        content = re.sub(pattern1, replacement1, content)

        # También reemplazar el viewport inicial
        content = re.sub(
            r'glViewport\(0, 0, window_width, window_height\)',
            'glViewport(0, 0, w, h)',
            content
        )
        content = re.sub(
            r'glViewport\(vp_x, vp_y, vp_w, vp_h\)',
            'glViewport(vx, vy, vw, vh)',
            content
        )

        with open(filename, 'w') as f:
            f.write(content)
        print(f"✅ Preset {preset_num} variables corregidas")
        return True

    # Patrón 2: Ya usa w, h pero vp_* en lugar de vx, vy, vw, vh
    pattern2 = r'(\s+)w, h = self\.screen\.get_size\(\)\s*\n\s*vp_x, vp_y, vp_w, vp_h = self\.calculate_viewport'

    if re.search(pattern2, content):
        content = re.sub(
            r'vp_x, vp_y, vp_w, vp_h = self\.calculate_viewport\(w, h\)',
            'vx, vy, vw, vh = self.calculate_viewport(w, h)',
            content
        )
        content = re.sub(
            r'glViewport\(vp_x, vp_y, vp_w, vp_h\)',
            'glViewport(vx, vy, vw, vh)',
            content
        )

        with open(filename, 'w') as f:
            f.write(content)
        print(f"✅ Preset {preset_num} variables corregidas")
        return True

    print(f"⏭️  Preset {preset_num}: ya usa variables correctas o patrón no reconocido")
    return True

# Actualizar presets 3-22
presets = ['3', '4', '5', '6', '7', '8', '9', '10'] + [str(i) for i in range(11, 23)]

print("=" * 60)
print("CORRECCIÓN DE VARIABLES EN RENDER()")
print("=" * 60)

success = 0
for p in presets:
    if fix_preset(p):
        success += 1

print()
print("=" * 60)
print(f"✅ Completado: {success}/{len(presets)}")
print("=" * 60)
