# Shadertoy Compatibility System

Sistema de compatibilidad 100% con Shadertoy.com para JungleLabStudio.

## Fase 1 Completada ✅

### Componentes Implementados

1. **ShadertoyConverter** (`converter.py`)
   - Convierte código de Shadertoy a formato JungleLabStudio
   - Wrapper automático con todos los uniforms
   - Detección de dependencias
   - Validación de código

2. **ShadertoyNode** (`../nodes/shadertoy/shadertoy_node.py`)
   - Nodo compatible con shaders de Shadertoy
   - Uniforms implementados:
     - ✅ `iResolution` (vec3) - viewport resolution
     - ✅ `iTime` (float) - shader playback time
     - ✅ `iTimeDelta` (float) - render delta time
     - ✅ `iFrame` (int) - frame counter
     - ✅ `iMouse` (vec4) - mouse coordinates
     - ✅ `iDate` (vec4) - date/time info
     - ✅ `iSampleRate` (float) - audio sample rate
     - ✅ `iChannel0-3` (sampler2D) - texture inputs (estructura lista)
     - ✅ `iChannelTime[4]` (float) - channel playback time
     - ✅ `iChannelResolution[4]` (vec3) - channel resolution

## Uso

### En Preset YAML

```yaml
preset:
  name: "Mi Shader de Shadertoy"
  nodes:
    - id: mi_shader
      type: shadertoy
      params:
        shadertoy_code: |
          void mainImage(out vec4 fragColor, in vec2 fragCoord) {
              vec2 uv = fragCoord / iResolution.xy;
              fragColor = vec4(uv, 0.5 + 0.5 * sin(iTime), 1.0);
          }

    - id: output
      type: output
      inputs:
        input0: mi_shader
```

### Desde Python

```python
from shadertoy.converter import ShadertoyConverter
from nodes.shadertoy import ShadertoyNode

# Convertir código
converter = ShadertoyConverter()
shadertoy_code = """
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    fragColor = vec4(uv, 0.5, 1.0);
}
"""

glsl_code = converter.convert(shadertoy_code)

# Usar en nodo
node = ShadertoyNode(ctx, "test_shader", (1920, 1080))
node.set_shadertoy_code(shadertoy_code)
```

## Ejemplos Disponibles

Presets de prueba en `community_presets/shadertoy/`:

1. **simple_gradient.yaml** - Gradiente animado básico
2. **animated_circle.yaml** - Círculo en movimiento
3. **raymarching_sphere.yaml** - Esfera con raymarching

## Testing

Para probar el sistema:

```bash
# Cargar uno de los presets de ejemplo
python src/main.py community_presets/shadertoy/simple_gradient.yaml
```

## Próximos Pasos (Fase 2)

- [ ] Implementar TextureInputNode para iChannel0-3
- [ ] Sistema de mouse tracking completo
- [ ] Implementar ShadertoyBufferNode para multi-pass
- [ ] UI de importación desde URL/código
- [ ] Integración con API de Shadertoy

## Compatibilidad

### ✅ Funciona Ahora
- Shaders simples con `mainImage()`
- Uniforms: iTime, iResolution, iFrame, iDate, iMouse
- Coordenadas fragCoord en píxeles
- Aspect ratio correcto

### 🚧 En Desarrollo (Fase 2+)
- Texturas de entrada (iChannel0-3)
- Multi-pass rendering (BufferA, BufferB, etc.)
- Importación desde URL de Shadertoy
- Audio reactive inputs
- Cubemaps

## Notas Técnicas

### Diferencias de Coordenadas

**Shadertoy:**
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord)
// fragCoord está en píxeles: (0.5, 0.5) hasta (width-0.5, height-0.5)
```

**JungleLabStudio (interno):**
```glsl
in vec2 v_uv;  // Normalizado 0.0 a 1.0
```

**Solución:**
El vertex shader convierte automáticamente:
```glsl
v_fragCoord = in_uv * iResolution.xy;
```

### Compatibilidad OpenGL vs WebGL

- Shadertoy usa WebGL (OpenGL ES)
- JungleLabStudio usa OpenGL 3.3 Core
- GLSL syntax es ~95% compatible
- La mayoría de shaders funcionan sin modificaciones

## Recursos

- [Shadertoy.com](https://www.shadertoy.com/)
- [Shadertoy How To](https://www.shadertoy.com/howto)
- [WebGL Shadertoy Tutorial](https://webglfundamentals.org/webgl/lessons/webgl-shadertoy.html)
