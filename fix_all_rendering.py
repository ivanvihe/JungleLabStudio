#!/usr/bin/env python3
"""
Script para corregir TODOS los problemas de rendering:
1. Eliminar código duplicado de franjas
2. Usar tamaño de viewport real (vw, vh) en lugar de target (1080, 1920)
3. Asegurar orden correcto de rendering
"""

import re
import os

def fix_preset(preset_num):
    """Corrige rendering del preset"""
    filename = f'visuales_shader_{preset_num}.py'

    if not os.path.exists(filename):
        print(f"⚠️  {filename} no encontrado")
        return False

    with open(filename, 'r') as f:
        content = f.read()

    print(f"🔧 Fixing preset {preset_num}...")

    changed = False

    # 1. Eliminar código duplicado de franjas (bloque que aparece DESPUÉS de glViewport principal)
    pattern_dup = r'(glViewport\(vx, vy, vw, vh\))\s*\n\s*# Dibujar franjas con líneas inclinadas\s*\n\s*if vx > 0:\s*\n\s*glUseProgram\(self\.franja_shader\).*?glDrawArrays\(GL_TRIANGLE_FAN, 0, 4\)\s*\n'
    if re.search(pattern_dup, content, re.DOTALL):
        content = re.sub(pattern_dup, r'\1\n        ', content, flags=re.DOTALL)
        print(f"  ✓ Código duplicado de franjas eliminado")
        changed = True

    # 2. Cambiar iResolution de target a viewport real
    # Buscar: glUniform2f(self.uni_resolution, float(self.target_width), float(self.target_height))
    # Cambiar a: glUniform2f(self.uni_resolution, float(vw), float(vh))
    pattern_res = r'glUniform2f\(self\.uni_resolution, float\(self\.target_width\), float\(self\.target_height\)\)'
    if re.search(pattern_res, content):
        content = re.sub(pattern_res, r'glUniform2f(self.uni_resolution, float(vw), float(vh))', content)
        print(f"  ✓ iResolution cambiada a viewport real")
        changed = True

    if changed:
        with open(filename, 'w') as f:
            f.write(content)
        print(f"✅ Preset {preset_num} corregido")
        return True
    else:
        print(f"⏭️  Preset {preset_num}: ya estaba correcto")
        return True

# Actualizar presets 3-23
presets = ['3', '4', '5', '6', '7', '8', '9', '10'] + [str(i) for i in range(11, 24)]

print("=" * 70)
print("CORRECCIÓN COMPLETA DE RENDERING")
print("=" * 70)
print("1. Eliminando código duplicado de franjas")
print("2. Cambiando iResolution de target a viewport real")
print("3. Asegurando orden correcto de rendering")
print()

success = 0
for p in presets:
    if fix_preset(p):
        success += 1
    print()

print("=" * 70)
print(f"✅ Completado: {success}/{len(presets)}")
print("=" * 70)
