# Presets - JungleLabStudio

Directorio unificado de presets visuales en formato YAML DSL.

## 📁 Estructura

```
presets/
├── README.md           ← Este archivo
├── library.json        ← Índice de presets disponibles
├── shadertoy/          ← Shaders importados de Shadertoy.com
├── templates/          ← Templates y ejemplos base
├── examples/           ← Ejemplos adicionales
└── media/              ← Archivos media (texturas, videos)
```

## 🎯 Propósito

Este es el **único directorio** para almacenar presets en JungleLabStudio.

**Foco principal**: Shaders y efectos visuales de **Shadertoy.com**

## 📝 Formato de Presets

Todos los presets están en formato **YAML DSL**:

```yaml
preset:
  name: "Mi Preset"
  description: "Descripción del efecto visual"
  author: "Autor"
  version: "1.0.0"
  tags: ["tag1", "tag2"]

  settings:
    bpm: 120.0
    audio_reactive: false
    midi_enabled: false

  nodes:
    - id: visual
      type: shadertoy  # u otro tipo de nodo
      params:
        # parámetros del nodo
      inputs:
        # conexiones

    - id: output
      type: output
      inputs:
        input0: visual
```

## 🚀 Cómo Usar

### Ejecutar un Preset

```bash
python src/main.py presets/shadertoy/mi_preset.yaml
```

### Crear Nuevo Preset

1. Copiar template base desde `templates/`
2. Modificar parámetros y código
3. Guardar en carpeta apropiada:
   - Shadertoy → `shadertoy/`
   - Ejemplos → `examples/`
   - Custom → raíz de `presets/`

### Importar desde Shadertoy

Ver guía completa en: `../AI_SHADERTOY_NODE_GUIDE.md`

## 📂 Descripción de Carpetas

### `/shadertoy/`

Presets que usan shaders de Shadertoy.com.

**Características**:
- 100% compatible con código de Shadertoy
- Sin modificaciones necesarias al código
- Soporte completo de uniforms Shadertoy (iTime, iResolution, etc.)

**Ejemplos**:
- `simple_gradient.yaml` - Gradiente animado básico
- `raymarching_sphere.yaml` - Raymarching 3D
- `low_tech_tunnel_WcdczB.yaml` - Túnel procedural
- Ver `TUNNEL_PRESETS_GUIDE.md` para más info

### `/templates/`

Plantillas y ejemplos de presets DSL YAML.

**Incluye**:
- Ejemplos de uso de nodos nativos
- Plantillas MIDI
- Ejemplos de composición
- Referencias de sintaxis

### `/examples/`

Ejemplos adicionales y presets de demostración.

### `/media/`

Archivos media utilizados por los presets:
- Texturas
- Videos
- Imágenes
- Audio samples

## 🎨 Tipos de Nodos Disponibles

### Generadores
- `shadertoy` - Shaders de Shadertoy.com ⭐
- `generator.noise` - Ruido procedural
- `generator.plasma` - Plasma
- `generator.fractal` - Fractales
- `generator.voronoi` - Voronoi
- `generator.pattern` - Patrones geométricos
- `generator.metaballs` - Metabolas

### Efectos
- `effect.bloom` - Resplandor
- `effect.blur` - Desenfoque
- `effect.feedback` - Trails/Estelas
- `effect.chromatic` - Aberración cromática
- `effect.kaleidoscope` - Caleidoscopio
- `effect.distort` - Distorsión
- `effect.pixelate` - Pixelación
- `effect.glitch` - Glitch
- `effect.color` - Ajustes de color

### Composición
- `blend` - Mezclar texturas
- `math.operation` - Operaciones matemáticas

### Control
- `midi.listener` - MIDI input
- `midi.launcher` - MIDI triggers

Ver: `../NODE_REFERENCE.md` para lista completa.

## 📚 Documentación

- **`AI_SHADERTOY_NODE_GUIDE.md`** - Guía para crear nodos Shadertoy
- **`SHADERTOY_COMPLETE_GUIDE.md`** - Guía completa de Shadertoy
- **`NODE_REFERENCE.md`** - Referencia de nodos
- **`YAML_DSL_REFERENCE.md`** - Sintaxis YAML DSL
- **`MIDI_SYSTEM_GUIDE.md`** - Sistema MIDI

## 🔧 Desarrollo

### Agregar Nuevo Preset Shadertoy

1. Ir a [Shadertoy.com](https://www.shadertoy.com)
2. Copiar código del shader
3. Crear nuevo archivo `.yaml`:

```yaml
preset:
  name: "Nombre del Efecto"
  description: "Descripción"
  source: "shadertoy"
  tags: ["shadertoy"]

  nodes:
    - id: shader
      type: shadertoy
      params:
        shadertoy_code: |
          void mainImage(out vec4 fragColor, in vec2 fragCoord) {
              // Pegar código aquí
          }

    - id: output
      type: output
      inputs:
        input0: shader
```

4. Guardar en `presets/shadertoy/<nombre>.yaml`
5. Ejecutar: `python src/main.py presets/shadertoy/<nombre>.yaml`

### Combinar con Efectos

```yaml
nodes:
  - id: shader
    type: shadertoy
    params:
      shadertoy_code: |
        # código

  - id: bloom
    type: effect.bloom
    params:
      intensity: 1.5
    inputs:
      input0: shader

  - id: output
    type: output
    inputs:
      input0: bloom
```

## ⚡ Tips de Performance

- Los shaders de Shadertoy pueden ser intensivos en GPU
- Reducir resolución de ventana si va lento
- Limitar efectos de post-procesamiento
- Ver ejemplos optimizados en `shadertoy/`

## 🎯 Roadmap

- [ ] Más presets de Shadertoy importados
- [ ] Librería curada de efectos
- [ ] Categorización por tipo de efecto
- [ ] Presets con control MIDI pre-configurado
- [ ] Sistema de tags mejorado

## 📞 Ayuda

Si necesitas ayuda:
1. Revisa los ejemplos en `shadertoy/` y `templates/`
2. Consulta la documentación en la raíz del proyecto
3. Verifica logs de error del shader

---

**Última actualización**: 2025-11-29
**Versión**: 2.0 (Reorganización completa - Solo YAML + Shadertoy)
