#!/usr/bin/env python3
"""
Script para actualizar los métodos render() con el código de franjas
"""

import re
import os

RENDER_FRANJA_CODE = '''
        # Dibujar franjas con líneas inclinadas
        if vx > 0:
            glUseProgram(self.franja_shader)
            glUniform2f(self.franja_resolution, float(w), float(h))
            glBindVertexArray(self.franja_vao)
            glViewport(0, 0, vx, h); glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
            glViewport(vx + vw, 0, vx, h); glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

        # Dibujar shader principal'''

def fix_preset(preset_num):
    """Actualiza el método render de un preset"""
    filename = f'visuales_shader_{preset_num}.py'

    if not os.path.exists(filename):
        return False

    with open(filename, 'r') as f:
        content = f.read()

    # Si ya tiene el código de franjas, skip
    if 'Dibujar franjas' in content:
        print(f"⏭️  Preset {preset_num}: ya tiene franjas en render()")
        return True

    print(f"🔧 Fixing preset {preset_num} render method...")

    # Patrón 1: Buscar viewport seguido de glUseProgram (sin comentario)
    pattern1 = r'(glViewport\([^)]+\))\s*\n\s*(glUseProgram\(self\.shader\))'
    if re.search(pattern1, content):
        content = re.sub(pattern1, r'\1' + RENDER_FRANJA_CODE + r'\n        \2', content)
        with open(filename, 'w') as f:
            f.write(content)
        print(f"✅ Preset {preset_num} actualizado (patrón 1)")
        return True

    # Patrón 2: Buscar clear seguido directamente de viewport
    pattern2 = r'(glClear\(GL_COLOR_BUFFER_BIT\))\s*\n\s*(glViewport\([^)]+\))\s*\n\s*(glUseProgram)'
    if re.search(pattern2, content):
        content = re.sub(pattern2, r'\1\n        \2' + RENDER_FRANJA_CODE + r'\n        \3', content)
        with open(filename, 'w') as f:
            f.write(content)
        print(f"✅ Preset {preset_num} actualizado (patrón 2)")
        return True

    # Patrón 3: Más general - después de cualquier glClear
    pattern3 = r'(glClear\(GL_COLOR_BUFFER_BIT\))\s*\n(\s+)(glViewport\([^)]+\)[^\n]*\n\s+glUseProgram)'
    if re.search(pattern3, content):
        content = re.sub(pattern3, r'\1\n\2glViewport(\2' + RENDER_FRANJA_CODE.strip() + r'\n\2\3', content)
        with open(filename, 'w') as f:
            f.write(content)
        print(f"✅ Preset {preset_num} actualizado (patrón 3)")
        return True

    print(f"⚠️  Preset {preset_num}: No se encontró patrón adecuado")
    return False

# Actualizar presets 3-22
presets = ['3', '4', '5', '6', '7', '8', '9', '10'] + [str(i) for i in range(11, 23)]

print("=" * 60)
print("ACTUALIZACIÓN DE MÉTODOS RENDER()")
print("=" * 60)

success = 0
for p in presets:
    if fix_preset(p):
        success += 1

print()
print("=" * 60)
print(f"✅ Completado: {success}/{len(presets)}")
print("=" * 60)
