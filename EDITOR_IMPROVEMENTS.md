# Mejoras del Editor Visual - JungleLabStudio

## Fecha: 2025-11-29

## 📋 Resumen de Cambios

Se han realizado mejoras significativas al editor visual del proyecto, incluyendo:

1. **Auto-Organize**: Reorganización automática de nodos
2. **Reorganización del menú contextual**: Nueva estructura de categorías
3. **8 Nuevos nodos VFX de Glitch**: Efectos de video profesionales

---

## 🔧 Cambios Implementados

### 1. Auto-Organize de Nodos

**Archivo**: `src/editor/graph/visual_graph.py`

**Funcionalidad**:
- Reorganiza automáticamente los nodos en el canvas
- Calcula capas jerárquicas basadas en dependencias
- Distribuye nodos con espaciado óptimo y equidistante
- Ordena nodos de izquierda a derecha según el flujo de datos

**Cómo usar**:
- Click derecho en el canvas
- Seleccionar "⚡ Auto-Organize"

**Parámetros de layout**:
- Espaciado horizontal: 300px entre columnas
- Espaciado vertical: 100px entre filas
- Algoritmo: Topological sort + layer assignment

---

### 2. Nuevo Menú Contextual

**Archivo**: `src/editor/ui/canvas.py`

**Nueva estructura de categorías**:

#### 📦 Core / Setup
- Init
- Output
- Preview

#### 🎹 MIDI Control
- MIDI Listener
- MIDI Launcher

#### 🎨 Generators
- Shadertoy Shader ⭐ (nuevo en menú)
- Custom Shader
- Noise Pattern
- Checkerboard
- Particle System
- Geometry

#### ⚡ Effects
- Blur
- Glow / Bloom
- Advanced Bloom
- Vignette
- Color Adjust
- Color Gradient
- Distort (Wave/Swirl)
- Transform (Rotate/Scale)
- Kaleidoscope
- Mirror
- Feedback / Trails
- Pixelate
- Edge Detect
- Posterize

#### 📺 VFX / Glitch (NUEVO)
- **Glitch VHS** - Efecto de cinta VHS
- **Glitch RGB Split** - Separación de canales RGB
- **Glitch Scanlines** - Líneas de escaneo/interlace
- **Glitch Noise** - Ruido digital/corrupción
- **Glitch Blocks** - Desplazamiento de bloques
- **Glitch Displacement** - Distorsión UV caótica
- **CRT Monitor** - Efecto de monitor CRT con curvatura
- **Datamosh** - Artefactos de compresión de video

#### 🎭 Compositing
- Blend
- Blend Modes (Screen/Multiply/etc)
- Composite
- Math Operation

---

## 🆕 Nodos VFX Creados

### 1. Glitch VHS (`vfx.glitch.vhs`)

**Archivo**: `src/nodes/vfx/glitch_vhs_node.py`

**Parámetros**:
- `intensity` (0.0-1.0): Intensidad general del efecto
- `speed` (0.0-5.0): Velocidad de animación
- `scanline_amount` (0.0-1.0): Cantidad de líneas de escaneo
- `tracking_error` (0.0-1.0): Error de tracking horizontal
- `color_bleed` (0.0-1.0): Sangrado de color cromático

**Características**:
- Tracking error horizontal
- Scanline jumps aleatorios
- RGB color bleed (chromatic aberration)
- Scanlines con flicker
- Noise grain
- Vignette de borde de cinta

---

### 2. Glitch RGB Split (`vfx.glitch.rgb`)

**Archivo**: `src/nodes/vfx/glitch_rgb_node.py`

**Parámetros**:
- `amount` (0.0-1.0): Cantidad de separación
- `speed` (0.0-5.0): Velocidad de animación
- `angle` (-π a π): Ángulo de separación
- `distortion` (0.0-1.0): Distorsión con ruido

**Características**:
- Separación de canales RGB direccional
- Distorsión animada con ruido
- Offset configurable por canal

---

### 3. Glitch Scanlines (`vfx.glitch.scanlines`)

**Archivo**: `src/nodes/vfx/glitch_scanlines_node.py`

**Parámetros**:
- `line_count` (50-1000): Número de líneas
- `intensity` (0.0-1.0): Intensidad del efecto
- `speed` (0.0-5.0): Velocidad de animación
- `distortion` (0.0-1.0): Distorsión horizontal
- `roll_speed` (0.0-2.0): Velocidad de roll vertical

**Características**:
- Patrón de scanlines configurable
- Random line jumps
- Vertical roll
- Scanline flicker
- Distorsión por línea

---

### 4. Glitch Noise (`vfx.glitch.noise`)

**Archivo**: `src/nodes/vfx/glitch_noise_node.py`

**Parámetros**:
- `intensity` (0.0-1.0): Intensidad del ruido
- `speed` (0.0-5.0): Velocidad de animación
- `grain_size` (1.0-20.0): Tamaño del grano

**Características**:
- Ruido digital pixelado
- Corrupción aleatoria de pixels
- Grain configurable

---

### 5. Glitch Blocks (`vfx.glitch.blocks`)

**Archivo**: `src/nodes/vfx/glitch_blocks_node.py`

**Parámetros**:
- `block_size` (4.0-128.0): Tamaño de bloques
- `intensity` (0.0-1.0): Intensidad de desplazamiento
- `speed` (0.0-5.0): Velocidad de animación
- `probability` (0.0-1.0): Probabilidad de glitch por bloque

**Características**:
- Desplazamiento de bloques aleatorio
- Control de probabilidad
- Dirección aleatoria por bloque

---

### 6. Glitch Displacement (`vfx.glitch.displacement`)

**Archivo**: `src/nodes/vfx/glitch_displacement_node.py`

**Parámetros**:
- `amount` (0.0-1.0): Cantidad de desplazamiento
- `speed` (0.0-5.0): Velocidad de animación
- `frequency` (1.0-50.0): Frecuencia del ruido
- `chaos` (0.0-1.0): Nivel de caos

**Características**:
- Desplazamiento UV basado en ruido
- Transiciones caóticas
- Control de frecuencia

---

### 7. CRT Monitor (`vfx.crt`)

**Archivo**: `src/nodes/vfx/crt_node.py`

**Parámetros**:
- `curvature` (0.0-1.0): Curvatura de la pantalla
- `scanline_intensity` (0.0-1.0): Intensidad de scanlines
- `vignette` (0.0-1.0): Viñeta de bordes
- `brightness` (0.5-2.0): Brillo general

**Características**:
- Curvatura de pantalla CRT
- Scanlines horizontales
- Vignette de bordes
- RGB separation en bordes
- Brightness boost

---

### 8. Datamosh (`vfx.datamosh`)

**Archivo**: `src/nodes/vfx/datamosh_node.py`

**Parámetros**:
- `intensity` (0.0-1.0): Intensidad del efecto
- `speed` (0.0-5.0): Velocidad de animación
- `motion_blur` (0.0-1.0): Cantidad de motion blur temporal
- `block_size` (4.0-64.0): Tamaño de bloques de compresión

**Características**:
- Simulación de I-frames/P-frames
- Motion vector displacement
- Temporal feedback buffer
- Block boundary artifacts
- Artefactos de compresión realistas

---

## 📁 Archivos Modificados

### Editor
- `src/editor/ui/canvas.py` - Menú contextual y categorías
- `src/editor/graph/visual_graph.py` - Auto-organize
- `src/editor/graph/visual_node.py` - Configuración de nodos VFX

### Sistema de Nodos
- `src/nodes/__init__.py` - Registro de nodos VFX
- `src/nodes/vfx/__init__.py` - Módulo VFX (nuevo)
- `src/nodes/vfx/*.py` - 8 nodos VFX (nuevos)

---

## 🎯 Uso en el Editor

### Auto-Organize

1. Crear varios nodos en el canvas
2. Conectarlos como desees
3. Click derecho en el canvas
4. Seleccionar "⚡ Auto-Organize"
5. Los nodos se reorganizan automáticamente

### Agregar Nodos VFX

1. Click derecho en el canvas
2. Expandir "VFX / Glitch"
3. Seleccionar el efecto deseado
4. El nodo aparece en la posición del cursor
5. Conectar con otros nodos

### Ejemplo de Preset con VFX

```yaml
preset:
  name: "Glitch Visual"

  nodes:
    - id: gen_shadertoy_001
      type: shadertoy
      params:
        shadertoy_code: |
          void mainImage(out vec4 fragColor, in vec2 fragCoord) {
              vec2 uv = fragCoord / iResolution.xy;
              vec3 col = 0.5 + 0.5 * cos(iTime + uv.xyx + vec3(0,2,4));
              fragColor = vec4(col, 1.0);
          }

    - id: vfx_glitch_vhs_001
      type: vfx.glitch.vhs
      params:
        intensity: 0.7
        speed: 1.5
        scanline_amount: 0.5
      inputs:
        input0: gen_shadertoy_001

    - id: vfx_crt_001
      type: vfx.crt
      params:
        curvature: 0.5
        scanline_intensity: 0.3
      inputs:
        input0: vfx_glitch_vhs_001

    - id: out_output_001
      type: output
      inputs:
        input0: vfx_crt_001
```

---

## 🔍 Verificación

Para verificar que los nodos están correctamente registrados:

```bash
cd src
source ../.venv/bin/activate
python -c "
from render.engine import VisualEngine
from core.graph.registry import NodeRegistry
vfx_nodes = [k for k in NodeRegistry._nodes.keys() if 'vfx' in k]
print('Nodos VFX registrados:', len(vfx_nodes))
for node in sorted(vfx_nodes):
    print(f'  - {node}')
"
```

**Salida esperada**:
```
Nodos VFX registrados: 8
  - vfx.crt
  - vfx.datamosh
  - vfx.glitch.blocks
  - vfx.glitch.displacement
  - vfx.glitch.noise
  - vfx.glitch.rgb
  - vfx.glitch.scanlines
  - vfx.glitch.vhs
```

---

## 🎨 Colores de Categorías en el Editor

- **Generators** (Azul): RGB(0.2, 0.6, 1.0)
- **Effects/VFX** (Naranja): RGB(0.9, 0.5, 0.2)
- **MIDI/Triggers** (Amarillo): RGB(1.0, 0.8, 0.2)
- **Compositing** (Gris): RGB(0.7, 0.7, 0.7)
- **Output** (Rojo): RGB(1.0, 0.3, 0.3)

---

## 📚 Próximas Mejoras Sugeridas

- [ ] Agregar más efectos VFX (Glitch Fractal, Glitch Time, etc.)
- [ ] Preset templates con efectos VFX pre-configurados
- [ ] Parámetros animados MIDI para VFX
- [ ] Preview en tiempo real de parámetros VFX
- [ ] Atajos de teclado para Auto-Organize (Ctrl+L)

---

## ✅ Testing

Todos los nodos han sido probados y funcionan correctamente:

- ✅ Auto-Organize reorganiza nodos correctamente
- ✅ Menú contextual muestra todas las categorías
- ✅ 8 nodos VFX se registran correctamente
- ✅ Nodos VFX renderizan sin errores
- ✅ Shadertoy aparece en categoría Generators

---

**Versión**: 2.1.0
**Autor**: JungleLabStudio + Claude
**Última actualización**: 2025-11-29
