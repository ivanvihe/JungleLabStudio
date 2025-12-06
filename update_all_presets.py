#!/usr/bin/env python3
"""
Script para actualizar TODOS los presets con optimizaciones:
- Franjas con líneas inclinadas
- Coordenadas centradas para formato vertical
- Reducción de iterations/partículas según tipo
"""

import re
import os

FRANJA_SHADERS = '''
FRANJA_VERTEX = "#version 330 core\\nlayout(location = 0) in vec2 vPos;\\nvoid main() { gl_Position = vec4(vPos, 0.0, 1.0); }"
FRANJA_FRAGMENT = """
#version 330 core
out vec4 fragColor;
uniform vec2 iResolution;
void main() {
    float line = mod(gl_FragCoord.x + gl_FragCoord.y, 40.0);
    float pattern = step(line, 2.0) * 0.12;
    fragColor = vec4(pattern, pattern, pattern, 1.0);
}
"""
'''

FRANJA_SETUP = '''
        # Shader franjas
        fvs = shaders.compileShader(FRANJA_VERTEX, GL_VERTEX_SHADER)
        ffs = shaders.compileShader(FRANJA_FRAGMENT, GL_FRAGMENT_SHADER)
        self.franja_shader = shaders.compileProgram(fvs, ffs)
        self.franja_resolution = glGetUniformLocation(self.franja_shader, 'iResolution')
'''

FRANJA_VAO = '''
        # VAO franjas
        fverts = array([-1, -1, 1, -1, 1, 1, -1, 1], dtype='f')
        self.franja_vao = glGenVertexArrays(1)
        glBindVertexArray(self.franja_vao)
        fvbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, fvbo)
        glBufferData(GL_ARRAY_BUFFER, fverts, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
'''

FRANJA_RENDER = '''
        # Dibujar franjas con líneas inclinadas
        if vx > 0:
            glUseProgram(self.franja_shader)
            glUniform2f(self.franja_resolution, float(w), float(h))
            glBindVertexArray(self.franja_vao)
            glViewport(0, 0, vx, h); glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
            glViewport(vx + vw, 0, vx, h); glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
'''

OPTIMIZATIONS = {
    # Fractales: Reducir raymarch iterations
    '4': {'raymarch': '80→60', 'coords': True},
    '5': {'coords': True},
    '6': {'raymarch': '100→60', 'coords': True},

    # Partículas: Reducir count
    '7': {'particles': '100→50', 'coords': True},
    '8': {'coords': True},
    '9': {'particles': '100→50', 'coords': True},

    # Glitch/Patterns: Reducir octavas
    '11': {'coords': True},
    '12': {'coords': True},
    '13': {'coords': True},
    '14': {'coords': True},
    '15': {'coords': True},
    '16': {'octaves': '6→4', 'coords': True},
    '17': {'coords': True},
    '18': {'coords': True},
    '19': {'octaves': '6→4', 'coords': True},
    '20': {'coords': True},
    '21': {'coords': True},
    '22': {'octaves': True, 'coords': True},
}

def update_preset(preset_num):
    """Actualiza un preset con todas las optimizaciones"""
    filename = f'visuales_shader_{preset_num}.py'

    if not os.path.exists(filename):
        print(f"⚠️  {filename} no encontrado")
        return False

    with open(filename, 'r') as f:
        content = f.read()

    print(f"🔄 Actualizando preset {preset_num}...")

    # 1. Añadir franjas shaders si no existen
    if 'FRANJA_VERTEX' not in content:
        # Insertar después de FRAGMENT_SHADER
        content = re.sub(
            r'("""\s*\n\n)(class ShaderVisualEngine)',
            r'\1' + FRANJA_SHADERS + r'\n\n\2',
            content
        )

    # 2. Corregir coordenadas si está mal centrado
    if 'coords' in OPTIMIZATIONS.get(preset_num, {}):
        # Buscar y reemplazar coordenadas descentradas
        content = re.sub(
            r'vec2 p = \(2\.0 \* fragCoord - iResolution\.xy\) / iResolution\.y;',
            'vec2 p = (fragCoord - iResolution.xy * 0.5) / iResolution.y;',
            content
        )

    # 3. Reducir raymarch iterations
    if 'raymarch' in OPTIMIZATIONS.get(preset_num, {}):
        content = re.sub(r'for\(int i = 0; i < (80|100); i\+\+\)', r'for(int i = 0; i < 60; i++)', content)

    # 4. Reducir partículas
    if 'particles' in OPTIMIZATIONS.get(preset_num, {}):
        content = re.sub(r'int numParticles = (\d+) \+ int\(iKickPulse \* (\d+)\.0\);',
                        lambda m: f'int numParticles = {int(m.group(1))//2} + int(iKickPulse * {int(m.group(2))//2}.0);',
                        content)
        content = re.sub(r'for\(int i = 0; i < 100; i\+\+\)', 'for(int i = 0; i < 50; i++)', content)

    # 5. Añadir setup de franjas shader en __init__ si no existe
    if 'self.franja_shader' not in content:
        # Buscar después de self.uni_tom2
        content = re.sub(
            r'(self\.uni_tom2 = glGetUniformLocation\(self\.shader, \'iTom2Spin\'\))',
            r'\1' + '\n' + FRANJA_SETUP,
            content
        )

    # 6. Añadir VAO de franjas si no existe
    if 'self.franja_vao' not in content:
        # Buscar después de glVertexAttribPointer para el VAO principal
        content = re.sub(
            r'(glVertexAttribPointer\(0, 3, GL_FLOAT, GL_FALSE, 0, None\))\n',
            r'\1' + '\n' + FRANJA_VAO + '\n',
            content
        )

    # 7. Actualizar método render para incluir franjas
    if 'Dibujar franjas' not in content:
        # Buscar el clear y viewport
        content = re.sub(
            r'(glViewport\(0, 0, w, h\); glClearColor\(0, 0, 0, 1\); glClear\(GL_COLOR_BUFFER_BIT\))\n\s+(# Dibujar shader principal|glViewport\(vx, vy, vw, vh\))',
            r'\1' + '\n' + FRANJA_RENDER + '\n        # Dibujar shader principal\n        glViewport(vx, vy, vw, vh)',
            content
        )

    # Guardar
    with open(filename, 'w') as f:
        f.write(content)

    print(f"✅ Preset {preset_num} actualizado")
    return True

# Actualizar todos los presets pendientes
presets_to_update = ['4', '5', '6', '7', '8', '9', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22']

print("=" * 60)
print("ACTUALIZACIÓN MASIVA DE PRESETS")
print("=" * 60)
print(f"Total a actualizar: {len(presets_to_update)} presets")
print()

success_count = 0
for preset_num in presets_to_update:
    if update_preset(preset_num):
        success_count += 1

print()
print("=" * 60)
print(f"✅ Completado: {success_count}/{len(presets_to_update)} presets actualizados")
print("=" * 60)
