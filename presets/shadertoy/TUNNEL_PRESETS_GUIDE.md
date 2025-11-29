# Low Tech Tunnel - Preset Guide

Presets importados del shader "Low Tech Tunnel" de Shadertoy.com
URL: https://www.shadertoy.com/view/WcdczB

## Presets Disponibles

### 1. `low_tech_tunnel_WcdczB.yaml` - Original

**Qué es:**
El shader original de Shadertoy sin modificaciones.

**Características:**
- Raymarching tunnel con path curvo
- Esfera/orbe animada siguiendo el camino
- Textura procedural con ruido
- Barras de cine (letterbox)
- Solo 28 pasos de raymarching (muy optimizado!)

**Cuándo usar:**
- Quieres el efecto exacto de Shadertoy
- Máximo rendimiento
- Estudio del código original

**Cómo ejecutar:**
```bash
python src/main.py community_presets/shadertoy/low_tech_tunnel_WcdczB.yaml
```

---

### 2. `low_tech_tunnel_enhanced.yaml` - Mejorado con Efectos

**Qué es:**
Versión mejorada del original con post-procesamiento.

**Efectos añadidos:**
1. **Bloom** - Resplandor brillante alrededor de las luces
2. **Chromatic Aberration** - Aberración cromática sutil
3. **Color Grading** - Ajustes de brillo, contraste, saturación
4. **Feedback** - Estelas/trails para efecto psicodélico

**Pipeline de nodos:**
```
Tunnel Shader → Bloom → Chromatic → Color → Feedback → Output
```

**Cuándo usar:**
- Performances VJ
- Quieres más impacto visual
- Estilo más psicodélico

**Controles sugeridos:**
- `feedback.amount` - Controla intensidad de trails
- `bloom.intensity` - Controla resplandor
- `color.hue_shift` - Cambio de color en vivo

**Cómo ejecutar:**
```bash
python src/main.py community_presets/shadertoy/low_tech_tunnel_enhanced.yaml
```

---

### 3. `tunnel_native_recreation.yaml` - Recreación Nativa

**Qué es:**
Recreación del efecto usando SOLO nodos nativos, SIN código Shadertoy.

**Nodos usados:**
1. **PlasmaNode** (modo Tunnel) - Base del túnel
2. **DomainWarpNode** - Textura de detalle procedural
3. **MetaballsNode** - Orbe animada
4. **BlendNode** - Composición de capas
5. **BloomNode** - Resplandor final
6. **ColorNode** - Ajuste de color

**Pipeline:**
```
Plasma (tunnel) ──┬──→ Blend → Bloom → Color → Output
                  │
DomainWarp ───────┘
                  │
Metaballs ────────┘ (screen blend)
```

**Cuándo usar:**
- Quieres control total sobre cada elemento
- Aprender cómo funcionan los generadores nativos
- Modificar el efecto sin tocar código
- MIDI mapping completo

**Ventajas:**
- ✅ Control separado de cada capa
- ✅ MIDI mapping de todos los parámetros
- ✅ Fácil de modificar sin código
- ✅ Combinar con otros generadores

**MIDI Controls incluidos:**
- CC1 → Velocidad del túnel
- CC2 → Frecuencia del túnel
- CC3 → Brillo del orbe
- CC4 → Intensidad de bloom
- CC5 → Cambio de matiz

**Cómo ejecutar:**
```bash
python src/main.py community_presets/shadertoy/tunnel_native_recreation.yaml
```

---

### 4. `tunnel_experimental.yaml` - Mix Experimental

**Qué es:**
Versión maximalista que combina el shader original con múltiples generadores y efectos.

**Capas incluidas:**
1. Shader Shadertoy original
2. Patrón kaleidoscopio (overlay)
3. Fractal Julia (multiply)
4. Patrón Voronoi (edges)
5. Bloom
6. Chromatic aberration
7. Color grading
8. Feedback trails
9. Pixelate (opcional)
10. Glitch (opcional)

**Pipeline completo:**
```
Tunnel Shader ──┬──→ Blend (Kaleidoscope) ──→ Blend (Fractal) ──→
                │
Kaleidoscope ───┘
                │
Fractal ────────┘
                │
                ↓
        Blend (Voronoi) → Bloom → Chromatic → Color →
                │
Voronoi ────────┘

                ↓
        Feedback → Pixelate → Glitch → Output
```

**Cuándo usar:**
- Performances VJ experimentales
- Quieres máximo control creativo
- Explorar posibilidades del sistema
- Live coding visual

**MIDI Controls (16 CCs):**
- CC1-2: Kaleidoscopio (simetría, escala)
- CC3-4: Fractal (zoom, color)
- CC5-7: Opacidad de cada capa
- CC8-9: Bloom y chromatic
- CC10-12: Color (brillo, saturación, matiz)
- CC13-14: Feedback (cantidad, rotación)
- CC15: Pixelate (tamaño de píxel)
- CC16: Glitch (cantidad)

**Cómo ejecutar:**
```bash
python src/main.py community_presets/shadertoy/tunnel_experimental.yaml
```

---

## Comparación Rápida

| Preset | Nodos | MIDI | Rendimiento | Complejidad | Uso |
|--------|-------|------|-------------|-------------|-----|
| **Original** | 2 | No | ⚡⚡⚡ Muy Alto | ⭐ Simple | Estudio/Referencia |
| **Enhanced** | 6 | No | ⚡⚡ Alto | ⭐⭐ Medio | VJ Live |
| **Native** | 7 | ✅ Sí (5) | ⚡⚡ Alto | ⭐⭐⭐ Avanzado | Control Total |
| **Experimental** | 13 | ✅ Sí (16) | ⚡ Medio | ⭐⭐⭐⭐ Experto | Experimental |

---

## Cómo Modificar los Presets

### Cambiar Colores

Edita los parámetros `color_a` y `color_b` en los nodos generadores:

```yaml
params:
  color_a: [0.0, 0.1, 0.3]  # RGB (azul oscuro)
  color_b: [1.0, 0.6, 0.2]  # RGB (naranja)
```

### Añadir/Quitar Efectos

Simplemente comenta o elimina nodos:

```yaml
# Desactivar feedback
# - id: feedback
#   type: effect.feedback
#   ...

# Cambiar output para conectar directamente a color
- id: output
  type: output
  inputs:
    source: color  # En vez de feedback
```

### Ajustar Velocidad

Modifica el parámetro `speed`:

```yaml
params:
  speed: 2.0  # Más rápido
  speed: 0.5  # Más lento
```

### Cambiar Intensidad

Ajusta `brightness` y `contrast`:

```yaml
params:
  brightness: 1.5  # Más brillante
  contrast: 1.8    # Más contraste
  saturation: 2.0  # Más saturado
```

---

## Combinaciones Sugeridas

### 1. Túnel Minimal (Buen Rendimiento)
```yaml
Tunnel Shader → Bloom (suave) → Output
```

### 2. Túnel Psicodélico
```yaml
Tunnel Shader → Feedback (alto) → Chromatic → Bloom → Output
```

### 3. Túnel Glitch
```yaml
Tunnel Shader → Glitch → Pixelate → Chromatic → Output
```

### 4. Túnel Caleidoscópico
```yaml
Tunnel Shader → Kaleidoscope (overlay 0.5) → Bloom → Output
```

### 5. Túnel Fractal
```yaml
Tunnel Shader → Fractal (multiply 0.6) → Domain Warp → Output
```

---

## Tips de Performance

### Si va lento:

1. **Reducir efectos**:
   - Quita feedback
   - Quita chromatic aberration
   - Reduce bloom radius

2. **Bajar calidad**:
   - Reduce resolución de window
   - Baja bloom quality
   - Reduce feedback samples

3. **Optimizar generadores**:
   - Reduce `max_iterations` en fractales
   - Reduce `num_balls` en metaballs
   - Simplifica patrones

### Para máximo FPS:

Usa solo el preset original sin efectos adicionales.

---

## Crear Tus Propias Variaciones

### Plantilla Base

```yaml
preset:
  name: "Mi Túnel Custom"

  nodes:
    - id: tunnel
      type: shadertoy
      params:
        shader_code: |
          # ... código del shader ...

    # Añade tus efectos aquí

    - id: output
      type: output
      inputs:
        source: tunnel  # o tu último efecto
```

### Generadores Recomendados para Combinar

- **PlasmaNode**: Fondos psicodélicos
- **FractalNode**: Detalles matemáticos
- **VoronoiNode**: Patrones celulares
- **DomainWarpNode**: Texturas orgánicas
- **PatternNode**: Geometría
- **MetaballsNode**: Elementos líquidos

### Efectos Recomendados

- **Bloom**: Siempre queda bien
- **Feedback**: Para trails psicodélicos
- **ChromaticAberration**: Toque analógico
- **ColorNode**: Control de color básico
- **BlendNode**: Combinar capas

---

## Recursos Adicionales

- **Documentación completa**: `SHADERTOY_COMPLETE_GUIDE.md`
- **Referencia de nodos**: `NODE_REFERENCE.md`
- **YAML DSL**: `YAML_DSL_REFERENCE.md`
- **MIDI mapping**: `MIDI_SYSTEM_GUIDE.md`

---

## Créditos

**Shader original**: "Low Tech Tunnel" por @bug, @FabriceNeyret2, @HexaPhoenix, @GregRostami
**URL**: https://www.shadertoy.com/view/WcdczB
**Presets**: JungleLabStudio

¡Disfruta creando visuales increíbles! 🚀✨
