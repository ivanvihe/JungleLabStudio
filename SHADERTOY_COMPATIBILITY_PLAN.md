# Plan de Compatibilidad 100% con Shadertoy.com

## Objetivo
Hacer JungleLabStudio 100% compatible con shaders de Shadertoy.com, permitiendo importar y ejecutar cualquier shader de la plataforma sin modificaciones.

---

## 1. Análisis de Compatibilidad

### 1.1 Diferencias Clave entre Shadertoy y JungleLabStudio

#### Shadertoy
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    fragColor = vec4(uv, 0.0, 1.0);
}
```

#### JungleLabStudio Actual
```glsl
#version 330
in vec2 v_uv;
out vec4 fragColor;
uniform float u_time;

void main() {
    fragColor = vec4(v_uv, 0.0, 1.0);
}
```

### 1.2 Uniforms de Shadertoy (Completos)

| Shadertoy | Tipo | Descripción | JungleLabStudio Equivalente |
|-----------|------|-------------|----------------------------|
| `iResolution` | `vec3` | Viewport resolution (x, y, aspect) | `u_resolution` (vec2) |
| `iTime` | `float` | Shader playback time (seconds) | `u_time` |
| `iTimeDelta` | `float` | Render time (seconds) | **NUEVO** |
| `iFrame` | `int` | Shader playback frame | **NUEVO** |
| `iMouse` | `vec4` | Mouse coords (xy: current, zw: click) | **NUEVO** |
| `iChannel0` | `sampler2D` | Input texture 0 | **NUEVO** |
| `iChannel1` | `sampler2D` | Input texture 1 | **NUEVO** |
| `iChannel2` | `sampler2D` | Input texture 2 | **NUEVO** |
| `iChannel3` | `sampler2D` | Input texture 3 | **NUEVO** |
| `iChannelTime[4]` | `float` | Channel playback time | **NUEVO** |
| `iChannelResolution[4]` | `vec3` | Channel resolution | **NUEVO** |
| `iDate` | `vec4` | Date (year, month, day, seconds) | **NUEVO** |
| `iSampleRate` | `float` | Audio sample rate (44100) | **NUEVO** |

---

## 2. Arquitectura del Sistema de Compatibilidad

### 2.1 Estructura de Archivos

```
src/
├── nodes/
│   ├── shadertoy/
│   │   ├── __init__.py
│   │   ├── shadertoy_node.py         # Nodo principal compatible con Shadertoy
│   │   ├── buffer_node.py            # Multi-pass buffer (BufferA, BufferB, etc.)
│   │   ├── texture_input_node.py     # Input de texturas para iChannel
│   │   ├── cubemap_node.py           # Input de cubemaps
│   │   └── mouse_input_node.py       # Sistema de mouse input
│   └── generators/
│       └── shader_node.py            # Ya existe
│
├── shadertoy/
│   ├── __init__.py
│   ├── converter.py                  # Conversor de código Shadertoy → JungleLabStudio
│   ├── importer.py                   # Importador desde URL/código
│   ├── uniforms.py                   # Manager de uniforms de Shadertoy
│   ├── parser.py                     # Parser de dependencias
│   └── validator.py                  # Validador de shaders
│
├── shaders/
│   └── shadertoy/
│       ├── wrapper_template.glsl     # Template para wrapping
│       ├── common_functions.glsl     # Funciones comunes de Shadertoy
│       └── examples/                 # Ejemplos importados
│
└── editor/
    └── ui/
        └── shadertoy_importer.py     # UI para importar desde Shadertoy

community_presets/
└── shadertoy/                        # Presets importados de Shadertoy
    └── [shader_id].yaml
```

### 2.2 Flujo de Conversión

```
1. ENTRADA: Código Shadertoy
   ↓
2. Parser: Detectar dependencias (buffers, texturas, cubemaps)
   ↓
3. Converter: Transformar mainImage() → main()
   ↓
4. Uniforms Manager: Mapear uniforms de Shadertoy
   ↓
5. Node Generator: Crear grafo de nodos YAML
   ↓
6. SALIDA: Preset YAML listo para cargar
```

---

## 3. Componentes a Implementar

### 3.1 ShadertoyNode (Nodo Principal)

**Archivo:** `src/nodes/shadertoy/shadertoy_node.py`

#### Características:
- Hereda de `GeneratorNode`
- Conversión automática de `mainImage()` a `main()`
- Todos los uniforms de Shadertoy implementados
- Soporte para 4 canales de textura (iChannel0-3)
- Mouse input tracking
- Frame counter
- Delta time tracking

#### Estructura del Nodo:
```python
@NodeRegistry.register("shadertoy")
class ShadertoyNode(GeneratorNode):
    """
    Nodo 100% compatible con shaders de Shadertoy.com

    Soporta:
    - mainImage(out vec4 fragColor, in vec2 fragCoord)
    - Todos los uniforms oficiales de Shadertoy
    - Multi-pass rendering (BufferA, BufferB, etc.)
    - iChannel0-3 para texturas/buffers
    - Mouse input (iMouse)
    - Date/time (iDate)
    """

    def __init__(self, ctx, node_id, resolution):
        super().__init__(ctx, node_id, resolution)

        # Frame counter
        self.frame_count = 0
        self.delta_time = 0.0

        # Mouse state
        self.mouse_pos = [0.0, 0.0]      # Current mouse position
        self.mouse_click = [0.0, 0.0]    # Last click position
        self.mouse_down = False

        # Channel inputs (textures from other nodes or files)
        self.channels = [None, None, None, None]

        # Auto-wrapped shader code
        self.shadertoy_code = ""
        self.is_converted = False

    def set_shadertoy_code(self, code: str):
        """Set raw Shadertoy code - will be auto-wrapped"""
        self.shadertoy_code = code
        self._convert_and_compile()

    def _convert_and_compile(self):
        """Convert Shadertoy code to JungleLabStudio format"""
        from shadertoy.converter import ShadertoyConverter

        converter = ShadertoyConverter()
        glsl_code = converter.convert(self.shadertoy_code)

        # Compile shader
        self._compile_shader(glsl_code)
        self.is_converted = True

    def render(self):
        """Render with all Shadertoy uniforms"""
        if not self.shader_program or not self.vao:
            return

        self.fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 0.0)

        # Standard Shadertoy uniforms
        self._set_uniform('iResolution', (self.resolution[0], self.resolution[1],
                                          self.resolution[0]/self.resolution[1]))
        self._set_uniform('iTime', self.time)
        self._set_uniform('iTimeDelta', self.delta_time)
        self._set_uniform('iFrame', self.frame_count)

        # Mouse uniform (xy: current, zw: click)
        mouse_uniform = (*self.mouse_pos, *self.mouse_click)
        self._set_uniform('iMouse', mouse_uniform)

        # Date uniform (year, month, day, time_in_seconds)
        import datetime
        now = datetime.datetime.now()
        date_uniform = (now.year, now.month, now.day,
                       now.hour * 3600 + now.minute * 60 + now.second)
        self._set_uniform('iDate', date_uniform)

        # Audio sample rate
        self._set_uniform('iSampleRate', 44100.0)

        # Bind channel textures (iChannel0-3)
        for i, channel in enumerate(self.channels):
            if channel:
                channel.use(location=i)
                self._set_uniform(f'iChannel{i}', i)

                # Channel resolution
                if hasattr(channel, 'size'):
                    ch_res = (*channel.size, channel.size[0]/channel.size[1])
                    self._set_uniform(f'iChannelResolution[{i}]', ch_res)

                # Channel time (for video inputs - TODO)
                self._set_uniform(f'iChannelTime[{i}]', 0.0)

        # Render
        self.vao.render(moderngl.TRIANGLE_STRIP)
        self.frame_count += 1
```

### 3.2 Converter (Convertidor de Código)

**Archivo:** `src/shadertoy/converter.py`

#### Funcionalidad:
```python
class ShadertoyConverter:
    """
    Convierte código de Shadertoy al formato de JungleLabStudio
    """

    WRAPPER_TEMPLATE = """
#version 330

// ==================== VERTEX SHADER ====================
#ifdef VERTEX_SHADER
in vec2 in_pos;
in vec2 in_uv;
out vec2 v_fragCoord;

void main() {
    v_fragCoord = in_uv * iResolution.xy;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
#endif

// ==================== FRAGMENT SHADER ====================
#ifdef FRAGMENT_SHADER
in vec2 v_fragCoord;
out vec4 fragColor;

// Shadertoy uniforms
uniform vec3 iResolution;
uniform float iTime;
uniform float iTimeDelta;
uniform int iFrame;
uniform vec4 iMouse;
uniform sampler2D iChannel0;
uniform sampler2D iChannel1;
uniform sampler2D iChannel2;
uniform sampler2D iChannel3;
uniform vec3 iChannelResolution[4];
uniform float iChannelTime[4];
uniform vec4 iDate;
uniform float iSampleRate;

// ==================== SHADERTOY CODE ====================
{SHADERTOY_CODE}

// ==================== WRAPPER ====================
void main() {
    mainImage(fragColor, v_fragCoord);
}
#endif
"""

    def convert(self, shadertoy_code: str) -> str:
        """
        Convierte código de Shadertoy a formato compatible

        Args:
            shadertoy_code: Código original de Shadertoy

        Returns:
            Código GLSL completo listo para compilar
        """
        # Insertar código en el template
        wrapped_code = self.WRAPPER_TEMPLATE.replace(
            '{SHADERTOY_CODE}',
            shadertoy_code
        )

        return wrapped_code

    def detect_dependencies(self, code: str) -> dict:
        """
        Detecta qué canales y features usa el shader

        Returns:
            {
                'channels': [0, 1],  # iChannel0, iChannel1 usados
                'uses_mouse': True,
                'uses_audio': False,
                'buffer_count': 0,   # Número de buffers (BufferA, etc.)
            }
        """
        deps = {
            'channels': [],
            'uses_mouse': False,
            'uses_audio': False,
            'buffer_count': 0,
        }

        # Detectar iChannel0-3
        for i in range(4):
            if f'iChannel{i}' in code:
                deps['channels'].append(i)

        # Detectar mouse
        if 'iMouse' in code:
            deps['uses_mouse'] = True

        # Detectar audio (iSampleRate)
        if 'iSampleRate' in code:
            deps['uses_audio'] = True

        return deps
```

### 3.3 Importer (Importador desde Shadertoy.com)

**Archivo:** `src/shadertoy/importer.py`

#### Funcionalidad:
```python
class ShadertoyImporter:
    """
    Importa shaders desde Shadertoy.com
    """

    def import_from_url(self, url: str) -> dict:
        """
        Importa shader desde URL de Shadertoy

        Args:
            url: https://www.shadertoy.com/view/XXXXXX

        Returns:
            preset_data: Datos del preset en formato YAML
        """
        # Extraer ID del shader
        shader_id = self._extract_shader_id(url)

        # Obtener datos del shader via API de Shadertoy
        # Nota: Shadertoy tiene una API pública
        shader_data = self._fetch_shader_data(shader_id)

        # Generar preset YAML
        preset = self._generate_preset(shader_data)

        return preset

    def import_from_code(self, code: str, metadata: dict = None) -> dict:
        """
        Importa desde código directo

        Args:
            code: Código del shader
            metadata: Metadatos opcionales (nombre, autor, etc.)
        """
        converter = ShadertoyConverter()
        deps = converter.detect_dependencies(code)

        # Generar preset
        preset = {
            'preset': {
                'name': metadata.get('name', 'Shadertoy Import'),
                'author': metadata.get('author', 'Unknown'),
                'source': 'shadertoy',
                'tags': ['shadertoy', 'imported'],
                'nodes': []
            }
        }

        # Crear nodo Shadertoy principal
        main_node = {
            'id': 'shadertoy_main',
            'type': 'shadertoy',
            'params': {
                'shadertoy_code': code
            }
        }

        # Agregar nodos de input si es necesario
        for channel_idx in deps['channels']:
            # Crear nodo de textura de entrada
            texture_node = {
                'id': f'texture_ch{channel_idx}',
                'type': 'shadertoy.texture_input',
                'params': {
                    'texture_path': f'assets/textures/default_ch{channel_idx}.png'
                }
            }
            preset['preset']['nodes'].append(texture_node)

            # Conectar al canal
            if 'inputs' not in main_node:
                main_node['inputs'] = {}
            main_node['inputs'][f'channel{channel_idx}'] = f'texture_ch{channel_idx}'

        preset['preset']['nodes'].append(main_node)

        # Agregar nodo de output
        preset['preset']['nodes'].append({
            'id': 'output',
            'type': 'output',
            'inputs': {
                'input0': 'shadertoy_main'
            }
        })

        return preset

    def _fetch_shader_data(self, shader_id: str) -> dict:
        """
        Obtiene datos del shader desde la API de Shadertoy

        API: https://www.shadertoy.com/api/v1/shaders/SHADER_ID?key=API_KEY
        """
        # TODO: Implementar usando requests
        # Nota: Requiere API key de Shadertoy (gratis)
        pass
```

### 3.4 Buffer Node (Multi-Pass Rendering)

**Archivo:** `src/nodes/shadertoy/buffer_node.py`

Muchos shaders de Shadertoy usan múltiples buffers (BufferA, BufferB, etc.) para efectos complejos como feedback, simulaciones, etc.

```python
@NodeRegistry.register("shadertoy.buffer")
class ShadertoyBufferNode(ShadertoyNode):
    """
    Buffer node para multi-pass rendering de Shadertoy

    Equivalente a BufferA, BufferB, BufferC, BufferD en Shadertoy
    """

    def __init__(self, ctx, node_id, resolution):
        super().__init__(ctx, node_id, resolution)

        # Persistent texture para feedback
        self.persistent_texture = self.ctx.texture(resolution, 4, dtype="f1")
        self.persistent_fbo = self.ctx.framebuffer(
            color_attachments=[self.persistent_texture]
        )

    def render(self):
        """Render y mantener estado entre frames"""
        super().render()

        # Copiar resultado al buffer persistente
        self._copy_to_persistent()

    def _copy_to_persistent(self):
        """Copiar texture actual al buffer persistente"""
        # Implementar copy usando blit o shader copy
        pass

    def get_persistent_texture(self):
        """Obtener textura del frame anterior"""
        return self.persistent_texture
```

### 3.5 Texture Input Node

**Archivo:** `src/nodes/shadertoy/texture_input_node.py`

```python
@NodeRegistry.register("shadertoy.texture_input")
class TextureInputNode(GeneratorNode):
    """
    Nodo para cargar texturas desde archivos
    Usado para iChannel0-3 inputs
    """

    def __init__(self, ctx, node_id, resolution):
        super().__init__(ctx, node_id, resolution)

        self.texture_path = ""
        self.loaded_texture = None

    def set_texture_path(self, path: str):
        """Cargar textura desde path"""
        from PIL import Image
        import numpy as np

        img = Image.open(path).convert('RGBA')
        img_data = np.array(img, dtype='f4') / 255.0

        self.loaded_texture = self.ctx.texture(img.size, 4, data=img_data.tobytes())
        self.loaded_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

    def render(self):
        """Render textura cargada al FBO"""
        if not self.loaded_texture:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        # Blit texture al FBO
        self.fbo.use()
        self.loaded_texture.use(location=0)
        # Render fullscreen quad con textura
        # TODO: Implementar shader de blit simple
```

### 3.6 Mouse Input Node

**Archivo:** `src/nodes/shadertoy/mouse_input_node.py`

```python
@NodeRegistry.register("shadertoy.mouse")
class MouseInputNode:
    """
    Captura input del mouse para iMouse uniform
    """

    def __init__(self):
        self.mouse_pos = [0.0, 0.0]
        self.mouse_click = [0.0, 0.0]
        self.mouse_down = False

    def update_mouse(self, x: float, y: float, button_down: bool):
        """Actualizar estado del mouse"""
        self.mouse_pos = [x, y]

        if button_down and not self.mouse_down:
            # Click nuevo
            self.mouse_click = [x, y]

        self.mouse_down = button_down

    def get_mouse_uniform(self) -> tuple:
        """Retornar vec4 para iMouse"""
        return (*self.mouse_pos, *self.mouse_click)
```

---

## 4. Biblioteca de Funciones Comunes de Shadertoy

**Archivo:** `src/shaders/shadertoy/common_functions.glsl`

Muchos shaders de Shadertoy usan funciones que no están en GLSL estándar:

```glsl
// ==================== SHADERTOY COMMON FUNCTIONS ====================
// Funciones auxiliares comunes en Shadertoy

#ifndef SHADERTOY_COMMON_H
#define SHADERTOY_COMMON_H

// rot() - Matriz de rotación 2D (común en Shadertoy)
mat2 rot(float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, -s, s, c);
}

// pmod() - Polar modulus (repetición polar)
vec2 pmod(vec2 p, float repetitions) {
    float angle = 2.0 * 3.14159265 / repetitions;
    float a = atan(p.y, p.x) + angle / 2.0;
    float r = length(p);
    float c = floor(a / angle);
    a = mod(a, angle) - angle / 2.0;
    return vec2(cos(a), sin(a)) * r;
}

// smoothmin() - Smooth minimum (mezcla suave)
float smoothmin(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0) / k;
    return min(a, b) - h * h * k * 0.25;
}

// Paletas de color comunes en Shadertoy (iq's palette)
vec3 palette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a + b * cos(6.28318 * (c * t + d));
}

// Palette helpers
vec3 palette1(float t) {
    return palette(t, vec3(0.5), vec3(0.5), vec3(1.0), vec3(0.0, 0.33, 0.67));
}

vec3 palette2(float t) {
    return palette(t, vec3(0.5), vec3(0.5), vec3(1.0), vec3(0.0, 0.1, 0.2));
}

vec3 palette3(float t) {
    return palette(t, vec3(0.5), vec3(0.5), vec3(2.0), vec3(0.5, 0.2, 0.25));
}

// Repeat space
vec3 repeat(vec3 p, vec3 c) {
    return mod(p + 0.5 * c, c) - 0.5 * c;
}

vec2 repeat(vec2 p, vec2 c) {
    return mod(p + 0.5 * c, c) - 0.5 * c;
}

// SDF comunes (algunas ya pueden estar en sdf.glsl)
float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

float sdBox(vec3 p, vec3 b) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
}

float sdTorus(vec3 p, vec2 t) {
    vec2 q = vec2(length(p.xz) - t.x, p.y);
    return length(q) - t.y;
}

#endif // SHADERTOY_COMMON_H
```

---

## 5. UI de Importación

**Archivo:** `src/editor/ui/shadertoy_importer.py`

```python
class ShadertoyImporterUI:
    """
    Ventana de ImGui para importar shaders de Shadertoy
    """

    def __init__(self):
        self.show_window = False
        self.import_url = ""
        self.import_code = ""
        self.shader_name = ""
        self.shader_author = ""
        self.import_mode = 0  # 0: URL, 1: Código directo

    def render(self):
        """Renderizar ventana de importación"""
        if not self.show_window:
            return

        imgui.begin("Import from Shadertoy", True)

        # Tabs para diferentes modos de importación
        if imgui.begin_tab_bar("ImportMode"):

            # Tab 1: Desde URL
            if imgui.begin_tab_item("From URL")[0]:
                imgui.text("Paste Shadertoy URL:")
                changed, self.import_url = imgui.input_text(
                    "##url",
                    self.import_url,
                    256
                )

                imgui.text("Example: https://www.shadertoy.com/view/XsXXDN")

                if imgui.button("Import from URL"):
                    self._import_from_url()

                imgui.end_tab_item()

            # Tab 2: Desde código
            if imgui.begin_tab_item("From Code")[0]:
                imgui.text("Paste Shadertoy shader code:")

                changed, self.import_code = imgui.input_text_multiline(
                    "##code",
                    self.import_code,
                    10000,
                    width=-1,
                    height=300
                )

                _, self.shader_name = imgui.input_text("Name", self.shader_name, 256)
                _, self.shader_author = imgui.input_text("Author", self.shader_author, 256)

                if imgui.button("Import Code"):
                    self._import_from_code()

                imgui.end_tab_item()

            imgui.end_tab_bar()

        imgui.end()

    def _import_from_url(self):
        """Importar desde URL"""
        from shadertoy.importer import ShadertoyImporter

        importer = ShadertoyImporter()
        preset = importer.import_from_url(self.import_url)

        # Guardar preset
        self._save_preset(preset)

        # Notificar usuario
        print(f"Imported shader from {self.import_url}")

    def _import_from_code(self):
        """Importar desde código"""
        from shadertoy.importer import ShadertoyImporter

        importer = ShadertoyImporter()
        preset = importer.import_from_code(
            self.import_code,
            metadata={
                'name': self.shader_name or 'Unnamed Shader',
                'author': self.shader_author or 'Unknown'
            }
        )

        # Guardar preset
        self._save_preset(preset)

    def _save_preset(self, preset_data: dict):
        """Guardar preset a archivo YAML"""
        import yaml
        from pathlib import Path

        # Crear directorio si no existe
        output_dir = Path('community_presets/shadertoy')
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generar nombre de archivo
        preset_name = preset_data['preset']['name'].lower().replace(' ', '_')
        output_path = output_dir / f'{preset_name}.yaml'

        # Guardar
        with open(output_path, 'w') as f:
            yaml.dump(preset_data, f, default_flow_style=False)

        print(f"Saved preset to {output_path}")
```

---

## 6. Integración con el Editor

### 6.1 Modificaciones en Canvas

**Archivo:** `src/editor/ui/canvas.py`

Agregar botón "Import Shadertoy" en el menú:

```python
# En el menú principal o toolbar
if imgui.menu_item("Import from Shadertoy...")[0]:
    self.shadertoy_importer.show_window = True
```

### 6.2 Registro de Nodos

**Archivo:** `src/nodes/registry.py` o donde se registren nodos

Asegurar que todos los nodos de Shadertoy estén registrados:

```python
from nodes.shadertoy.shadertoy_node import ShadertoyNode
from nodes.shadertoy.buffer_node import ShadertoyBufferNode
from nodes.shadertoy.texture_input_node import TextureInputNode
from nodes.shadertoy.mouse_input_node import MouseInputNode

# Ya se registran automáticamente con el decorator @NodeRegistry.register()
```

---

## 7. Compatibilidad de Features Avanzadas

### 7.1 Multi-Pass Shaders (BufferA, BufferB, etc.)

Shadertoy permite múltiples "tabs" de shader (Image, BufferA, BufferB, etc.) que se renderizan en secuencia.

**Estrategia:**
1. Detectar cuántos buffers usa el shader
2. Crear un nodo `shadertoy.buffer` por cada buffer
3. Conectarlos en orden:
   - BufferA → BufferB → BufferC → Image

**Ejemplo de Preset Multi-Pass:**
```yaml
preset:
  name: "Multi-Pass Shader"
  nodes:
    - id: buffer_a
      type: shadertoy.buffer
      params:
        shadertoy_code: |
          void mainImage(out vec4 fragColor, in vec2 fragCoord) {
              // BufferA code
          }
      inputs:
        channel0: buffer_b  # Feedback desde BufferB

    - id: buffer_b
      type: shadertoy.buffer
      params:
        shadertoy_code: |
          void mainImage(out vec4 fragColor, in vec2 fragCoord) {
              // BufferB code
          }
      inputs:
        channel0: buffer_a  # Input desde BufferA

    - id: shadertoy_main
      type: shadertoy
      params:
        shadertoy_code: |
          void mainImage(out vec4 fragColor, in vec2 fragCoord) {
              // Image code
          }
      inputs:
        channel0: buffer_a
        channel1: buffer_b

    - id: output
      type: output
      inputs:
        input0: shadertoy_main
```

### 7.2 Cubemaps

Shadertoy soporta cubemaps como inputs. Necesitamos:

**Archivo:** `src/nodes/shadertoy/cubemap_node.py`

```python
@NodeRegistry.register("shadertoy.cubemap")
class CubemapInputNode(GeneratorNode):
    """
    Nodo para cargar cubemaps (6 texturas)
    """

    def __init__(self, ctx, node_id, resolution):
        super().__init__(ctx, node_id, resolution)

        self.cubemap_faces = {
            'px': None,  # Positive X
            'nx': None,  # Negative X
            'py': None,  # Positive Y
            'ny': None,  # Negative Y
            'pz': None,  # Positive Z
            'nz': None,  # Negative Z
        }

        self.cubemap_texture = None

    def load_cubemap(self, face_paths: dict):
        """
        Cargar cubemap desde 6 imágenes

        Args:
            face_paths: {'px': 'path/to/px.png', 'nx': ..., etc.}
        """
        from PIL import Image
        import numpy as np

        # Cargar las 6 caras
        face_size = 512  # Tamaño de cada cara

        # TODO: Implementar carga de cubemap en ModernGL
        # self.cubemap_texture = self.ctx.texture_cube(...)
```

### 7.3 Video/Webcam Input

Shadertoy soporta video y webcam. Para fase inicial, esto es opcional.

**TODO:** Implementar `VideoInputNode` que captura frames de video/webcam y los envía a iChannel.

### 7.4 Audio Input

Shadertoy tiene soporte para FFT de audio (waveform y spectrum).

**Integración con sistema de audio existente:**

El proyecto ya tiene sistema de audio (`src/input_output/audio.py`). Conectar FFT bands a iChannel:

```python
# En ShadertoyNode
def set_audio_texture(self, fft_data: np.ndarray):
    """
    Crear textura de audio FFT para iChannel

    Args:
        fft_data: Array de FFT (512 samples)
    """
    # Crear textura 1D o 2D con datos de FFT
    # Formato común en Shadertoy: 512x2 texture
    # - Row 0: FFT actual
    # - Row 1: FFT suavizado
```

---

## 8. Testing y Validación

### 8.1 Shaders de Prueba

Crear suite de test con shaders representativos de Shadertoy:

**Archivo:** `tests/test_shadertoy_compatibility.py`

```python
import pytest
from shadertoy.converter import ShadertoyConverter
from shadertoy.importer import ShadertoyImporter

# Shaders de prueba (del más simple al más complejo)
SIMPLE_SHADER = """
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    fragColor = vec4(uv, 0.5 + 0.5 * sin(iTime), 1.0);
}
"""

MOUSE_SHADER = """
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 mouse = iMouse.xy / iResolution.xy;
    float d = length(uv - mouse);
    fragColor = vec4(vec3(smoothstep(0.1, 0.0, d)), 1.0);
}
"""

TEXTURE_SHADER = """
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    fragColor = texture(iChannel0, uv);
}
"""

def test_simple_conversion():
    converter = ShadertoyConverter()
    glsl = converter.convert(SIMPLE_SHADER)

    # Verificar que contiene mainImage
    assert 'mainImage' in glsl
    # Verificar que contiene wrapper
    assert 'void main()' in glsl
    # Verificar uniforms
    assert 'uniform vec3 iResolution' in glsl
    assert 'uniform float iTime' in glsl

def test_dependency_detection():
    converter = ShadertoyConverter()

    # Test simple (sin dependencias)
    deps = converter.detect_dependencies(SIMPLE_SHADER)
    assert deps['channels'] == []
    assert deps['uses_mouse'] == False

    # Test con mouse
    deps = converter.detect_dependencies(MOUSE_SHADER)
    assert deps['uses_mouse'] == True

    # Test con textura
    deps = converter.detect_dependencies(TEXTURE_SHADER)
    assert 0 in deps['channels']

def test_preset_generation():
    importer = ShadertoyImporter()
    preset = importer.import_from_code(
        SIMPLE_SHADER,
        metadata={'name': 'Test Shader', 'author': 'Test'}
    )

    # Verificar estructura del preset
    assert 'preset' in preset
    assert 'nodes' in preset['preset']
    assert len(preset['preset']['nodes']) > 0

    # Verificar nodo principal
    main_node = next(n for n in preset['preset']['nodes'] if n['type'] == 'shadertoy')
    assert 'shadertoy_code' in main_node['params']
```

### 8.2 Shaders Representativos para Testing

Lista de shaders de Shadertoy para probar (ordenados por complejidad):

1. **Protean Clouds** - https://www.shadertoy.com/view/3l23Rh
   - Simple, sin texturas
   - Usa solo iTime, iResolution

2. **Seascape** - https://www.shadertoy.com/view/Ms2SD1
   - Raymarching clásico
   - Sin texturas externas

3. **Happy Jumping** - https://www.shadertoy.com/view/3lsSzf
   - Usa iMouse
   - Interactivo

4. **Elevated** - https://www.shadertoy.com/view/MdX3Rr
   - Usa iChannel0 (texture)
   - Raymarching con textura

5. **Snail** - https://www.shadertoy.com/view/ld3Gz2
   - Multi-pass (BufferA)
   - Complejo

---

## 9. Documentación

### 9.1 Guía de Usuario

**Archivo:** `docs/SHADERTOY_IMPORT_GUIDE.md`

```markdown
# Importar Shaders de Shadertoy

## Método 1: Desde URL

1. Ve a Shadertoy.com y encuentra un shader
2. Copia la URL (ej: https://www.shadertoy.com/view/XsXXDN)
3. En JungleLabStudio:
   - Menu → Import → From Shadertoy
   - Pega la URL
   - Click "Import"

## Método 2: Desde Código

1. Copia el código del shader de Shadertoy
2. En JungleLabStudio:
   - Menu → Import → From Shadertoy
   - Tab "From Code"
   - Pega el código
   - Ingresa nombre y autor
   - Click "Import Code"

## Features Soportadas

✅ Uniforms básicos (iTime, iResolution, iFrame, etc.)
✅ Mouse input (iMouse)
✅ Texturas de entrada (iChannel0-3)
✅ Multi-pass rendering (BufferA, BufferB, etc.)
✅ Date/time (iDate)
⚠️  Audio input (parcial - usa sistema de audio de JungleLabStudio)
⚠️  Video input (en desarrollo)
⚠️  Cubemaps (en desarrollo)

## Limitaciones Conocidas

- Algunos shaders muy complejos pueden tener problemas de rendimiento
- WebGL 2.0 features no soportados en algunos casos
- Shadertoy usa WebGL, JungleLabStudio usa OpenGL 3.3 (mayoría compatible)
```

### 9.2 Guía de Desarrollador

**Archivo:** `docs/SHADERTOY_DEVELOPER_GUIDE.md`

```markdown
# Desarrollar Compatibilidad con Shadertoy

## Arquitectura

El sistema de compatibilidad con Shadertoy consta de:

1. **ShadertoyNode**: Nodo que ejecuta shaders de Shadertoy
2. **Converter**: Convierte código de Shadertoy a formato compatible
3. **Importer**: Importa desde URL o código
4. **Buffer Nodes**: Para multi-pass rendering

## Agregar Soporte para Nueva Feature

### Ejemplo: Agregar soporte para nuevo uniform

1. Agregar uniform al wrapper template en `converter.py`:
```glsl
uniform float iMyNewUniform;
```

2. Setear valor en `shadertoy_node.py`:
```python
def render(self):
    # ...
    self._set_uniform('iMyNewUniform', self.my_value)
```

## Testing

Ejecutar tests de compatibilidad:
```bash
pytest tests/test_shadertoy_compatibility.py -v
```
```

---

## 10. Plan de Implementación Gradual

### Fase 1: Fundamentos (1-2 semanas)
- [x] Análisis completo de Shadertoy
- [ ] Implementar `ShadertoyConverter`
- [ ] Implementar `ShadertoyNode` básico (solo iTime, iResolution)
- [ ] Testing con shaders simples

### Fase 2: Uniforms Completos (1 semana)
- [ ] Agregar todos los uniforms (iMouse, iFrame, iDate, etc.)
- [ ] Implementar `MouseInputNode`
- [ ] Testing con shaders interactivos

### Fase 3: Texturas (1 semana)
- [ ] Implementar `TextureInputNode`
- [ ] Soporte para iChannel0-3
- [ ] Testing con shaders que usan texturas

### Fase 4: Multi-Pass (1-2 semanas)
- [ ] Implementar `ShadertoyBufferNode`
- [ ] Sistema de conexión de buffers
- [ ] Testing con shaders multi-pass complejos

### Fase 5: Importador y UI (1 semana)
- [ ] Implementar `ShadertoyImporter`
- [ ] API de Shadertoy integration
- [ ] UI de importación (ImGui)
- [ ] Testing end-to-end

### Fase 6: Features Avanzadas (2-3 semanas)
- [ ] Soporte de audio/FFT
- [ ] Cubemaps
- [ ] Video input (opcional)
- [ ] Optimizaciones de rendimiento

### Fase 7: Polish y Documentación (1 semana)
- [ ] Suite de tests completa
- [ ] Documentación de usuario
- [ ] Documentación de desarrollador
- [ ] Galería de ejemplos

**Total Estimado: 8-11 semanas**

---

## 11. Métricas de Éxito

- [ ] Importar shader simple en <30 segundos
- [ ] 90%+ de shaders públicos de Shadertoy funcionan sin modificaciones
- [ ] Mantener >30 FPS en shaders de complejidad media
- [ ] Suite de tests con 20+ shaders representativos
- [ ] Documentación completa

---

## 12. Recursos y Referencias

### Documentación Oficial
- [Shadertoy How To](https://www.shadertoy.com/howto)
- [WebGL Shadertoy Tutorial](https://webglfundamentals.org/webgl/lessons/webgl-shadertoy.html)
- [Shadertoy Unofficial Guide](https://shadertoyunofficial.wordpress.com/)

### Tutoriales
- [Shadertoy for Absolute Beginners](https://agatedragon.blog/2024/01/14/shadertoy-introduction/)
- [GLSL Practice with Shadertoy](https://viclw17.github.io/2018/06/12/GLSL-Practice-With-Shadertoy)
- [Importing Shadertoy to TouchDesigner](https://nvoid.gitbooks.io/introduction-to-touchdesigner/content/GLSL/12-6-Importing-Shadertoy.html)

### Stack Overflow
- [fragCoord vs iResolution](https://stackoverflow.com/questions/58684315/shadertoy-fragcoord-vs-iresolution-vs-fragcolor)
- [How does ShaderToy work?](https://stackoverflow.com/questions/19449590/webgl-glsl-how-does-a-shadertoy-work)

### Repositorios de Referencia
- [shader-toy VSCode Extension](https://github.com/stevensona/shader-toy)
- [Shadertoy cheatsheet](https://gist.github.com/markknol/d06c0167c75ab5c6720fe9083e4319e1)

---

## 13. Notas Adicionales

### Diferencias OpenGL vs WebGL

Shadertoy usa WebGL (basado en OpenGL ES), JungleLabStudio usa OpenGL 3.3 Core.

**Compatibilidad:**
- ✅ GLSL syntax es muy similar
- ✅ Funciones matemáticas idénticas
- ⚠️  Algunos WebGL 2.0 features pueden requerir adaptación
- ⚠️  Precisión de floats puede diferir ligeramente

### Optimizaciones Futuras

- **Shader Compilation Cache**: Cachear shaders compilados para evitar recompilación
- **Hot Reload**: Detectar cambios en código y recompilar automáticamente
- **GPU Profiling**: Detectar shaders que causan drops de FPS
- **Auto-Optimization**: Sugerir optimizaciones para shaders lentos

### Extensiones Posibles

- **Shadertoy Gallery**: Browser integrado de shaders populares
- **Shader Editor**: Editor de código GLSL con syntax highlighting
- **Shader Variations**: Sistema para crear variaciones de parámetros
- **Export to Shadertoy**: Exportar desde JungleLabStudio a formato Shadertoy

---

## Conclusión

Este plan proporciona una ruta completa para lograr 100% compatibilidad con Shadertoy.com en JungleLabStudio. La implementación gradual permite:

1. **Validación temprana** con shaders simples
2. **Iteración incremental** de features
3. **Testing continuo** en cada fase
4. **Flexibilidad** para ajustar prioridades

El sistema de nodos de JungleLabStudio es ideal para esta integración, ya que permite:
- Conectar múltiples buffers fácilmente
- Reutilizar texturas entre shaders
- Combinar shaders de Shadertoy con efectos nativos
- Controlar shaders con MIDI/Audio

**Próximo paso:** Comenzar con Fase 1 - Implementar `ShadertoyConverter` y `ShadertoyNode` básico.
