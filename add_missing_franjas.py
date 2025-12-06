#!/usr/bin/env python3
"""
Añadir código de franjas a presets que no lo tienen
"""

import re

FRANJA_RENDER_CODE = """
        # Dibujar franjas con líneas inclinadas
        if vx > 0:
            glUseProgram(self.franja_shader)
            glUniform2f(self.franja_resolution, float(w), float(h))
            glBindVertexArray(self.franja_vao)
            glViewport(0, 0, vx, h); glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
            glViewport(vx + vw, 0, w - (vx + vw), h); glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

"""

def add_franjas(filename):
    """Añade código de franjas al preset"""

    with open(filename, 'r') as f:
        content = f.read()

    # Verificar si ya tiene franjas
    if 'if vx > 0:' in content and 'franja_shader' in content:
        print(f"⏭️  {filename}: ya tiene franjas")
        return False

    print(f"🔧 Añadiendo franjas a {filename}...")

    # Buscar el patrón: glClear seguido de glViewport(vx, vy, vw, vh)
    pattern = r'(glClear\(GL_COLOR_BUFFER_BIT\))\s*\n\s*(glViewport\(vx, vy, vw, vh\))'

    if re.search(pattern, content):
        # Insertar código de franjas entre el clear y el viewport principal
        content = re.sub(
            pattern,
            r'\1' + FRANJA_RENDER_CODE + r'        \2',
            content
        )

        with open(filename, 'w') as f:
            f.write(content)

        print(f"✅ {filename}: franjas añadidas")
        return True
    else:
        print(f"❌ {filename}: patrón no encontrado")
        return False

# Procesar presets 4 y 5
presets = ['visuales_shader_4.py', 'visuales_shader_5.py']

print("=" * 60)
print("AÑADIENDO FRANJAS A PRESETS FALTANTES")
print("=" * 60)

for preset in presets:
    add_franjas(preset)
    print()
