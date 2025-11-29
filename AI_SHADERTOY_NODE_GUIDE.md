# Guía para IA: Agregar Nodos Shadertoy a JungleLabStudio

**Propósito**: Esta guía está diseñada para que un asistente de IA pueda crear presets visuales usando shaders de Shadertoy.com de forma fácil y correcta.

---

## 📋 Estructura del Proyecto

```
JungleLabStudio/
├── presets/              ← ÚNICO directorio de presets (YAML)
│   ├── shadertoy/        ← Presets importados de Shadertoy
│   ├── templates/        ← Templates y ejemplos
│   └── examples/         ← Ejemplos adicionales
├── src/
│   └── nodes/shadertoy/  ← Implementación del nodo Shadertoy
└── [documentación .md]
```

**IMPORTANTE**:
- Solo usar `./presets/` para guardar presets
- Todos los presets nuevos deben ser archivos `.yaml`
- Los presets de Shadertoy van en `./presets/shadertoy/`

---

## 🎯 Objetivo del Sistema

El usuario quiere poder:
1. **Pedirle a la IA** que agregue efectos visuales de Shadertoy.com
2. **Crear presets** mezclando nodos de Shadertoy con otros nodos nativos
3. **Usar el editor visual** para modificar los presets
4. **100% compatibilidad** con código de Shadertoy sin modificaciones

---

## 🔧 Cómo Funciona el Nodo Shadertoy

### Tipo de Nodo
```yaml
type: shadertoy
```

### Parámetros Principales

```yaml
params:
  shadertoy_code: |
    void mainImage(out vec4 fragColor, in vec2 fragCoord) {
        // Tu código Shadertoy aquí
    }
```

### Uniforms Disponibles (Shadertoy estándar)

El nodo `shadertoy` proporciona automáticamente todos los uniforms de Shadertoy:

- **`iTime`** (float): Tiempo en segundos desde el inicio
- **`iResolution`** (vec3): Resolución de la ventana (x, y, aspect)
- **`iTimeDelta`** (float): Delta de tiempo entre frames
- **`iFrame`** (int): Contador de frames
- **`iMouse`** (vec4): Posición del mouse (xy: actual, zw: click)
- **`iChannel0-3`** (sampler2D): Texturas de entrada (opcional)
- **`iDate`** (vec4): Fecha y hora (año, mes, día, segundos)
- **`iChannelTime[4]`** (float): Tiempo de reproducción de canales
- **`iChannelResolution[4]`** (vec3): Resolución de canales

**Puedes copiar código directamente de Shadertoy.com sin modificaciones.**

---

## 📝 Plantilla Base para Preset Shadertoy

```yaml
preset:
  name: "Mi Efecto Visual"
  description: "Descripción del efecto"
  author: "Autor"
  version: "1.0.0"
  source: "shadertoy"
  tags: ["shadertoy", "generativo", "ejemplo"]

  settings:
    bpm: 120.0
    audio_reactive: false
    midi_enabled: false

  nodes:
    # Nodo Shadertoy - Generador visual
    - id: visual_gen
      type: shadertoy
      position: [100, 100]
      params:
        shadertoy_code: |
          void mainImage(out vec4 fragColor, in vec2 fragCoord) {
              vec2 uv = fragCoord / iResolution.xy;
              vec3 col = 0.5 + 0.5 * cos(iTime + uv.xyx + vec3(0, 2, 4));
              fragColor = vec4(col, 1.0);
          }

    # Output - Siempre necesario
    - id: output
      type: output
      position: [300, 100]
      inputs:
        input0: visual_gen
```

---

## 🎨 Ejemplos de Casos de Uso

### 1. Shader Simple de Shadertoy

**Código Shadertoy original:**
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec3 col = vec3(uv, 0.5 + 0.5 * sin(iTime));
    fragColor = vec4(col, 1.0);
}
```

**Preset YAML:**
```yaml
preset:
  name: "Gradiente Animado"

  nodes:
    - id: gradient
      type: shadertoy
      params:
        shadertoy_code: |
          void mainImage(out vec4 fragColor, in vec2 fragCoord) {
              vec2 uv = fragCoord / iResolution.xy;
              vec3 col = vec3(uv, 0.5 + 0.5 * sin(iTime));
              fragColor = vec4(col, 1.0);
          }

    - id: output
      type: output
      inputs:
        input0: gradient
```

### 2. Shader con Post-Procesamiento

Combinar un shader de Shadertoy con efectos nativos:

```yaml
preset:
  name: "Túnel con Bloom"

  nodes:
    # Generador Shadertoy
    - id: tunnel
      type: shadertoy
      params:
        shadertoy_code: |
          void mainImage(out vec4 fragColor, in vec2 fragCoord) {
              vec2 uv = (fragCoord - 0.5 * iResolution.xy) / iResolution.y;
              float d = length(uv);
              float a = atan(uv.y, uv.x);
              vec2 tuv = vec2(a / 3.14159, 1.0 / d + iTime);
              vec3 col = 0.5 + 0.5 * cos(tuv.x * 10.0 + vec3(0, 2, 4));
              fragColor = vec4(col, 1.0);
          }

    # Efecto Bloom nativo
    - id: bloom
      type: effect.bloom
      position: [300, 100]
      params:
        threshold: 0.5
        intensity: 1.5
        radius: 3.0
      inputs:
        input0: tunnel

    # Output
    - id: output
      type: output
      inputs:
        input0: bloom
```

### 3. Múltiples Shaders Combinados

```yaml
preset:
  name: "Composición Multi-Shader"

  nodes:
    # Shader 1: Fondo
    - id: background
      type: shadertoy
      params:
        shadertoy_code: |
          void mainImage(out vec4 fragColor, in vec2 fragCoord) {
              vec2 uv = fragCoord / iResolution.xy;
              vec3 col = 0.5 + 0.5 * cos(iTime + uv.xyx + vec3(0, 2, 4));
              fragColor = vec4(col, 1.0);
          }

    # Shader 2: Partículas
    - id: particles
      type: shadertoy
      params:
        shadertoy_code: |
          void mainImage(out vec4 fragColor, in vec2 fragCoord) {
              vec2 uv = fragCoord / iResolution.xy;
              float d = length(uv - 0.5);
              float brightness = smoothstep(0.1, 0.0, d) * sin(iTime * 5.0);
              fragColor = vec4(vec3(brightness), 1.0);
          }

    # Blend - Combinar ambos
    - id: mix
      type: blend
      params:
        opacity: 0.7
        mode: 1  # Add
      inputs:
        input0: background
        input1: particles

    # Output
    - id: output
      type: output
      inputs:
        input0: mix
```

---

## 🔌 Conectar con Otros Nodos

### Nodos Nativos Disponibles

**Generadores:**
- `generator.noise` - Ruido Perlin/Simplex
- `generator.plasma` - Plasma procedural
- `generator.fractal` - Fractales (Mandelbrot, Julia)
- `generator.voronoi` - Patrones Voronoi
- `generator.pattern` - Patrones geométricos
- `generator.metaballs` - Metabolas líquidas

**Efectos:**
- `effect.bloom` - Resplandor/Bloom
- `effect.blur` - Desenfoque gaussiano
- `effect.feedback` - Trails/Estelas temporales
- `effect.chromatic` - Aberración cromática
- `effect.kaleidoscope` - Caleidoscopio
- `effect.mirror` - Espejo
- `effect.distort` - Distorsión
- `effect.pixelate` - Pixelación
- `effect.glitch` - Efectos glitch
- `effect.color` - Ajustes de color

**Composición:**
- `blend` - Mezclar texturas (mix, add, multiply, screen)
- `math.operation` - Operaciones matemáticas

**MIDI/Control:**
- `midi.listener` - Escuchar mensajes MIDI
- `midi.launcher` - Triggers MIDI

### Ejemplo: Shadertoy + MIDI

```yaml
preset:
  name: "Visual Reactivo a MIDI"

  settings:
    midi_enabled: true

  nodes:
    # MIDI Listener
    - id: midi_speed
      type: midi.listener
      params:
        device_index: 0
        normalize: 1.0
        smoothing: 0.1

    # Shader que usa parámetros animados
    - id: visual
      type: shadertoy
      params:
        shadertoy_code: |
          void mainImage(out vec4 fragColor, in vec2 fragCoord) {
              vec2 uv = fragCoord / iResolution.xy;
              // iTime se modula automáticamente por MIDI vía launcher
              vec3 col = 0.5 + 0.5 * cos(iTime * 2.0 + uv.xyx + vec3(0, 2, 4));
              fragColor = vec4(col, 1.0);
          }
        # Animación MIDI
        animate:
          speed:
            midi:
              launcher: midi_speed
              scale: 5.0

    - id: output
      type: output
      inputs:
        input0: visual
```

---

## 📚 Ejemplos Reales en el Proyecto

Consulta estos archivos en `./presets/shadertoy/`:

1. **`simple_gradient.yaml`** - Ejemplo básico
2. **`raymarching_sphere.yaml`** - Raymarching 3D
3. **`low_tech_tunnel_WcdczB.yaml`** - Túnel original de Shadertoy
4. **`low_tech_tunnel_enhanced.yaml`** - Túnel + efectos
5. **`tunnel_experimental.yaml`** - Combinación maximalista

---

## ✅ Checklist: Crear un Nuevo Preset

Cuando el usuario pida agregar un efecto de Shadertoy:

1. ✅ **Copiar código de Shadertoy** - Sin modificaciones
2. ✅ **Crear archivo .yaml** en `./presets/shadertoy/`
3. ✅ **Usar plantilla base** (ver arriba)
4. ✅ **Pegar código en `shadertoy_code`**
5. ✅ **Agregar metadatos**: name, description, tags
6. ✅ **Conectar al output**: `input0: <id_del_nodo_shadertoy>`
7. ✅ **[Opcional] Agregar efectos** de post-procesamiento
8. ✅ **[Opcional] Agregar MIDI** para control en vivo
9. ✅ **Guardar archivo** con nombre descriptivo
10. ✅ **Probar** ejecutando: `python src/main.py presets/shadertoy/<archivo>.yaml`

---

## 🚨 Errores Comunes a Evitar

### ❌ NO HACER:

```yaml
# ❌ No modificar código Shadertoy
shadertoy_code: |
  void main() {  # ← Incorrecto, debe ser mainImage()
      ...
  }

# ❌ No usar rutas incorrectas
# community_presets/  ← Ya no existe
# src/presets/        ← Solo para código core
```

### ✅ HACER:

```yaml
# ✅ Usar mainImage() original
shadertoy_code: |
  void mainImage(out vec4 fragColor, in vec2 fragCoord) {
      ...
  }

# ✅ Guardar en la ruta correcta
# ./presets/shadertoy/<nombre>.yaml
```

---

## 🎓 Workflow Recomendado

### Flujo de Trabajo para la IA

1. **Usuario pide agregar efecto de Shadertoy**

   Ejemplo: "Agrega un generador de esferas metálicas de Shadertoy"

2. **IA busca o recibe código de Shadertoy**

   El usuario puede proporcionar:
   - URL de Shadertoy
   - Código directo
   - Descripción del efecto

3. **IA crea preset YAML**

   ```yaml
   preset:
     name: "Esferas Metálicas"
     description: "Shader de esferas reflectivas de Shadertoy"

     nodes:
       - id: spheres
         type: shadertoy
         params:
           shadertoy_code: |
             # Código de Shadertoy aquí

       - id: output
         type: output
         inputs:
           input0: spheres
   ```

4. **IA pregunta por mejoras opcionales**

   - ¿Agregar bloom/resplandor?
   - ¿Agregar control MIDI?
   - ¿Combinar con otros generadores?

5. **IA guarda archivo**

   Guardar en: `./presets/shadertoy/esferas_metalicas.yaml`

6. **IA documenta**

   Explicar al usuario:
   - Qué hace el preset
   - Cómo ejecutarlo
   - Qué parámetros puede modificar

---

## 🔍 Referencias Rápidas

### Documentos del Proyecto

- `SHADERTOY_COMPLETE_GUIDE.md` - Guía completa de Shadertoy
- `NODE_REFERENCE.md` - Referencia de todos los nodos
- `YAML_DSL_REFERENCE.md` - Sintaxis YAML DSL
- `MIDI_SYSTEM_GUIDE.md` - Sistema MIDI
- `presets/shadertoy/TUNNEL_PRESETS_GUIDE.md` - Ejemplo completo

### Código Fuente

- `src/nodes/shadertoy/shadertoy_node.py` - Implementación del nodo
- `src/shadertoy/converter.py` - Conversor Shadertoy→GLSL
- `src/shadertoy/importer.py` - Importador automático

---

## 💡 Tips Avanzados

### Optimización de Performance

```yaml
# Si el shader es pesado, agregar nota en descripción
description: "⚠️ Alto consumo GPU - Reducir resolución si va lento"
```

### Multi-Pass (Buffers)

Para shaders que usan múltiples buffers (iChannel):

```yaml
nodes:
  # Buffer A
  - id: buffer_a
    type: shadertoy
    params:
      shadertoy_code: |
        void mainImage(out vec4 fragColor, in vec2 fragCoord) {
            // Buffer A code
            vec4 prev = texture(iChannel0, fragCoord / iResolution.xy);
            fragColor = prev * 0.99;  # Feedback
        }

  # Buffer con feedback loop
  - id: feedback_buf
    type: utility.buffer
    inputs:
      input0: buffer_a

  # Conectar feedback
  # (Requiere configuración especial - ver ejemplos avanzados)
```

### Variables Configurables

Para parámetros que el usuario pueda ajustar:

```yaml
params:
  # Parámetros expuestos
  speed: 1.0
  color_shift: 0.0

  shadertoy_code: |
    // Usar parámetros en el shader
    #define SPEED 1.0
    #define COLOR_SHIFT 0.0

    void mainImage(out vec4 fragColor, in vec2 fragCoord) {
        float t = iTime * SPEED + COLOR_SHIFT;
        // ...
    }
```

---

## 🎯 Resumen para IA

**Cuando el usuario pida agregar efectos de Shadertoy:**

1. Crear archivo `.yaml` en `./presets/shadertoy/`
2. Usar plantilla base con nodo `type: shadertoy`
3. Pegar código en `shadertoy_code: |` sin modificar
4. Conectar a `output` con `inputs: { input0: <id> }`
5. Opcionalmente agregar efectos/MIDI
6. Guardar y documentar al usuario

**El sistema es 100% compatible con Shadertoy.com - copiar y pegar directamente.**

---

## 📞 Ayuda y Soporte

Si algo no funciona:
1. Verificar que el código Shadertoy sea válido
2. Revisar logs de errores del shader
3. Consultar ejemplos en `./presets/shadertoy/`
4. Revisar `SHADERTOY_COMPLETE_GUIDE.md`

---

**¡Listo para crear visuales increíbles con Shadertoy! 🚀✨**
