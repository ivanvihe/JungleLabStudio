# Plan de Implementación: Sistema de Importación de Código Comunitario

## Objetivo
Permitir importar y utilizar código de 5 fuentes externas en Jungle Lab Studio:
1. Shadertoy (GLSL shaders)
2. ISF Files (Interactive Shader Format)
3. Hydra (JavaScript patterns)
4. Taichi (Python GPU simulations)
5. p5py (Processing sketches)

---

## 1. Arquitectura General del Sistema de Importación

### 1.1 Estructura de Directorios
```
src/
├── community/
│   ├── __init__.py
│   ├── base_importer.py          # Clase base abstracta
│   ├── importers/
│   │   ├── __init__.py
│   │   ├── shadertoy_importer.py
│   │   ├── isf_importer.py
│   │   ├── hydra_importer.py
│   │   ├── taichi_importer.py
│   │   └── p5py_importer.py
│   ├── converters/
│   │   ├── __init__.py
│   │   ├── glsl_converter.py     # Conversión de dialectos GLSL
│   │   ├── js_to_python.py       # Hydra JS → Python
│   │   └── uniform_mapper.py     # Mapeo de uniforms
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── shader_validator.py
│   │   └── code_sanitizer.py
│   └── cache/
│       ├── __init__.py
│       └── preset_cache.py
├── nodes/
│   └── community/
│       ├── __init__.py
│       ├── community_shader_node.py
│       ├── taichi_physics_node.py
│       └── p5_generator_node.py
└── editor/
    └── ui/
        └── community_browser.py      # UI para explorar/importar
```

### 1.2 Archivos de Configuración
```
community_presets/
├── metadata.json                     # Índice de presets instalados
├── shadertoy/
│   └── [preset_id].yaml
├── isf/
│   └── [preset_id].yaml
├── hydra/
│   └── [preset_id].yaml
├── taichi/
│   └── [preset_id].yaml
└── p5py/
    └── [preset_id].yaml
```

---

## 2. Módulo Importador para Shadertoy

### 2.1 Archivos a Crear
- `src/community/importers/shadertoy_importer.py`
- `src/community/converters/glsl_converter.py`
- `src/nodes/community/shadertoy_node.py`

### 2.2 Funcionalidades Requeridas

#### 2.2.1 Conversión de Uniforms
```python
# Mapeo de uniforms de Shadertoy → Jungle Lab
SHADERTOY_UNIFORMS = {
    'iTime': 'u_time',              # Tiempo
    'iResolution': 'u_resolution',  # Resolución
    'iMouse': 'u_mouse',            # Mouse
    'iFrame': 'u_frame',            # Frame number
    'iChannelTime': 'u_channel_time',
    'iChannelResolution': 'u_channel_resolution',
    'iChannel0-3': 'u_texture0-3'   # Texturas de entrada
}
```

#### 2.2.2 Adaptación de Código GLSL
- Convertir `void mainImage(out vec4 fragColor, in vec2 fragCoord)` → `void main()`
- Reemplazar `fragCoord` → `gl_FragCoord`
- Ajustar coordenadas UV normalizadas

#### 2.2.3 Detección de Dependencias
- Identificar si usa texturas (iChannel0-3)
- Detectar audio inputs (no soportado inicialmente)
- Verificar versión de GLSL requerida

### 2.3 Formato YAML de Salida
```yaml
preset:
  name: "Fractal Tunnel"
  source: "shadertoy"
  url: "https://www.shadertoy.com/view/XsXXDN"
  author: "iq"
  license: "CC BY-NC-SA 3.0"
  tags: ["fractal", "tunnel", "3d"]

  nodes:
    - id: "shadertoy_001"
      type: "community.shadertoy"
      params:
        shader_code: |
          #version 330
          uniform float u_time;
          uniform vec2 u_resolution;
          out vec4 fragColor;

          void main() {
            vec2 uv = gl_FragCoord.xy / u_resolution.xy;
            // ... código convertido ...
          }
        requires_textures: false
        audio_reactive: false
```

### 2.4 API del Importador
```python
class ShadertoyImporter:
    def import_from_url(self, url: str) -> dict
    def import_from_code(self, code: str, metadata: dict) -> dict
    def validate_shader(self, code: str) -> bool
    def convert_uniforms(self, code: str) -> str
    def extract_dependencies(self, code: str) -> list
```

---

## 3. Módulo Importador para ISF Files

### 3.1 Archivos a Crear
- `src/community/importers/isf_importer.py`
- `src/community/converters/isf_parser.py`
- `src/nodes/community/isf_node.py`

### 3.2 Funcionalidades Requeridas

#### 3.2.1 Parser de JSON ISF
ISF usa un header JSON embebido en el shader:
```glsl
/*{
  "DESCRIPTION": "My Effect",
  "CATEGORIES": ["Generator"],
  "INPUTS": [
    {"NAME": "speed", "TYPE": "float", "DEFAULT": 1.0, "MIN": 0.0, "MAX": 10.0},
    {"NAME": "color", "TYPE": "color", "DEFAULT": [1.0, 0.0, 0.0, 1.0]}
  ]
}*/
```

#### 3.2.2 Conversión a Nodos Jungle Lab
- Parsear JSON metadata
- Crear parámetros dinámicamente desde INPUTS
- Mapear tipos de ISF → tipos de Jungle Lab:
  - `float` → parámetro float con min/max
  - `color` → parámetro color RGBA
  - `point2D` → vec2
  - `image` → textura de entrada

#### 3.2.3 Compatibilidad MIDI
- ISF no tiene soporte MIDI nativo
- Mapear parámetros ISF a sistema de triggers existente

### 3.3 API del Importador
```python
class ISFImporter:
    def import_from_file(self, filepath: str) -> dict
    def parse_isf_metadata(self, shader_code: str) -> dict
    def extract_glsl_code(self, shader_code: str) -> str
    def map_inputs_to_params(self, inputs: list) -> dict
    def generate_node_definition(self, metadata: dict, code: str) -> dict
```

---

## 4. Módulo Adaptador para Hydra

### 4.1 Archivos a Crear
- `src/community/importers/hydra_importer.py`
- `src/community/converters/js_to_glsl.py`
- `src/nodes/community/hydra_pattern_node.py`

### 4.2 Funcionalidades Requeridas

#### 4.2.1 Análisis de Patrones Hydra
Hydra usa sintaxis JavaScript encadenada:
```javascript
osc(10, 0.1, 1.2)
  .kaleid(4)
  .rotate(0.5)
  .modulateScale(noise(3), 0.5)
  .out()
```

#### 4.2.2 Estrategia de Conversión

**Opción A: Conversión a GLSL** (Recomendada)
- Crear biblioteca de funciones GLSL equivalentes a funciones Hydra
- Parsear árbol de llamadas JS
- Generar shader GLSL compuesto

**Opción B: Recrear en Python**
- Crear nodos nativos equivalentes
- Generar preset YAML con grafo de nodos

#### 4.2.3 Mapeo de Funciones Hydra
```python
HYDRA_FUNCTIONS = {
    'osc': 'oscillator',           # → generador de ondas
    'noise': 'noise_generator',    # → generador de ruido
    'kaleid': 'kaleidoscope',      # → efecto kaleidoscopio
    'rotate': 'transform_rotate',  # → rotación
    'scale': 'transform_scale',    # → escala
    'modulateScale': 'modulate',   # → modulación compleja
    'blend': 'blend_mode',         # → composición
}
```

### 4.3 Biblioteca GLSL de Funciones Hydra
Crear `shaders/hydra_lib.glsl`:
```glsl
// Funciones equivalentes a Hydra
vec3 osc(vec2 uv, float freq, float sync, float offset);
vec3 kaleid(vec2 uv, vec3 color, float sides);
vec2 rotate(vec2 uv, float angle);
// ... más funciones
```

### 4.4 API del Importador
```python
class HydraImporter:
    def import_from_code(self, js_code: str) -> dict
    def parse_hydra_chain(self, code: str) -> list  # AST de llamadas
    def generate_glsl_from_chain(self, chain: list) -> str
    def generate_node_graph(self, chain: list) -> dict  # Alternativa
    def map_hydra_params_to_uniforms(self, params: dict) -> dict
```

---

## 5. Módulo Integrador de Taichi

### 5.1 Archivos a Crear
- `src/community/importers/taichi_importer.py`
- `src/nodes/community/taichi_physics_node.py`
- `requirements.txt` (añadir `taichi>=1.7.0`)

### 5.2 Funcionalidades Requeridas

#### 5.2.1 Tipos de Simulaciones Soportadas
- **Particle Physics**: Sistema de partículas con física
- **Fluid Simulation**: Simulación de fluidos (SPH, MPM)
- **Cloth Simulation**: Telas y soft bodies
- **Fracture/Destruction**: Fracturas dinámicas

#### 5.2.2 Integración con ModernGL

**Estrategia: Taichi → NumPy → ModernGL Texture**
```python
# Taichi calcula simulación en GPU
@ti.kernel
def simulate_particles():
    # ... física de partículas en Taichi ...

# Exportar a NumPy
particle_data = particle_field.to_numpy()

# Transferir a ModernGL texture
texture.write(particle_data.tobytes())
```

#### 5.2.3 Wrapper Node
Crear nodo que:
- Inicializa contexto Taichi
- Ejecuta kernel Taichi cada frame
- Transfiere resultado a textura ModernGL
- Expone parámetros de simulación como parámetros de nodo

### 5.3 Formato de Preset Taichi
```yaml
preset:
  name: "Fluid Simulation"
  source: "taichi"
  author: "community"

  nodes:
    - id: "taichi_fluid_001"
      type: "community.taichi"
      params:
        simulation_type: "fluid"  # fluid, particles, cloth
        resolution: 512
        substeps: 5
        gravity: [0.0, -9.8]
        viscosity: 0.01

        # Código Taichi embebido
        kernel_code: |
          @ti.kernel
          def substep():
              for i in range(n_particles):
                  # ... simulación ...
```

### 5.4 API del Importador
```python
class TaichiImporter:
    def import_simulation(self, code: str, sim_type: str) -> dict
    def validate_taichi_kernel(self, code: str) -> bool
    def extract_parameters(self, code: str) -> list
    def create_wrapper_node(self, kernel_code: str) -> str
    def benchmark_performance(self, code: str) -> dict  # FPS estimado
```

---

## 6. Módulo Convertidor de p5py Sketches

### 6.1 Archivos a Crear
- `src/community/importers/p5py_importer.py`
- `src/community/converters/p5_to_glsl.py`
- `src/nodes/community/p5_generator_node.py`

### 6.2 Funcionalidades Requeridas

#### 6.2.1 Análisis de Sketches p5py
Estructura típica de un sketch p5py:
```python
def setup():
    size(512, 512)

def draw():
    background(0)
    fill(255)
    ellipse(mouseX, mouseY, 50, 50)
```

#### 6.2.2 Estrategia de Conversión

**Opción A: Ejecutar p5py y capturar output**
- Problemas: p5py usa OpenGL propio, conflicto con ModernGL

**Opción B: Convertir a GLSL** (Recomendada)
- Parsear AST de código Python
- Mapear funciones p5 → GLSL equivalente
- Generar shader procedural

**Opción C: CPU render → Texture**
- Ejecutar código p5py en memoria
- Capturar framebuffer como PIL Image
- Subir a textura ModernGL

#### 6.2.3 Mapeo de Funciones p5
```python
P5_TO_GLSL = {
    'ellipse': 'draw_circle',      # SDF de círculo
    'rect': 'draw_rect',           # SDF de rectángulo
    'line': 'draw_line',           # SDF de línea
    'fill': 'u_fill_color',        # Uniform de color
    'background': 'u_background',  # Clear color
    'noise': 'simplex_noise',      # Ruido Perlin/Simplex
}
```

### 6.3 Limitaciones Conocidas
- No todas las funciones p5 son convertibles a GLSL
- Funciones 3D requieren estrategia diferente
- Interacción con mouse/teclado requiere mapeo

### 6.4 API del Importador
```python
class P5PyImporter:
    def import_sketch(self, code: str) -> dict
    def parse_p5_code(self, code: str) -> dict  # AST
    def convert_to_glsl(self, ast: dict) -> str
    def identify_convertible_functions(self, code: str) -> list
    def extract_parameters(self, code: str) -> dict  # Variables globales
```

---

## 7. Sistema de Caché y Gestión de Presets

### 7.1 Archivos a Crear
- `src/community/cache/preset_cache.py`
- `src/community/cache/metadata_index.py`
- `community_presets/metadata.json`

### 7.2 Funcionalidades

#### 7.2.1 Metadata Index
```json
{
  "version": "1.0.0",
  "presets": [
    {
      "id": "shadertoy_fractal_001",
      "name": "Fractal Tunnel",
      "source": "shadertoy",
      "category": "generator",
      "tags": ["fractal", "3d", "tunnel"],
      "author": "iq",
      "license": "CC BY-NC-SA 3.0",
      "url": "https://www.shadertoy.com/view/XsXXDN",
      "thumbnail": "community_presets/thumbnails/shadertoy_fractal_001.png",
      "file": "community_presets/shadertoy/fractal_001.yaml",
      "imported_at": "2025-11-28T10:30:00Z",
      "performance": {"fps": 60, "complexity": "medium"}
    }
  ]
}
```

#### 7.2.2 Sistema de Thumbnails
- Renderizar preset al importar
- Capturar frame como thumbnail (256x256)
- Guardar en `community_presets/thumbnails/`

#### 7.2.3 Validación y Versionado
- Verificar integridad de presets (hash SHA-256)
- Sistema de versiones de presets
- Actualización automática si fuente cambió

### 7.3 API del Cache
```python
class PresetCache:
    def add_preset(self, preset: dict, source: str) -> str  # Returns ID
    def get_preset(self, preset_id: str) -> dict
    def list_presets(self, filters: dict = None) -> list
    def update_preset(self, preset_id: str, data: dict) -> bool
    def delete_preset(self, preset_id: str) -> bool
    def generate_thumbnail(self, preset_id: str) -> str
    def validate_preset(self, preset_id: str) -> dict
    def export_preset(self, preset_id: str, path: str) -> bool
```

---

## 8. UI para Explorar e Importar Código Comunitario

### 8.1 Archivos a Crear
- `src/editor/ui/community_browser.py`
- `src/editor/ui/import_wizard.py`
- `src/editor/ui/preset_preview.py`

### 8.2 Componentes de UI (ImGui)

#### 8.2.1 Community Browser Window
```
┌─ Community Presets ────────────────────────────┐
│ [Search: ___________] [Filter ▼] [Import URL] │
├────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│ │ Fractal  │ │ Particle │ │ Fluid    │        │
│ │ Tunnel   │ │ Flow     │ │ Motion   │        │
│ │ ⭐⭐⭐⭐⭐    │ │ ⭐⭐⭐⭐     │ │ ⭐⭐⭐       │        │
│ │ Shadertoy│ │ ISF      │ │ Taichi   │        │
│ └──────────┘ └──────────┘ └──────────┘        │
├────────────────────────────────────────────────┤
│ Selected: Fractal Tunnel                       │
│ Author: iq                                     │
│ License: CC BY-NC-SA 3.0                       │
│ Performance: 60 FPS (Medium complexity)        │
│                                                │
│ [Preview] [Import] [View Code] [Info]         │
└────────────────────────────────────────────────┘
```

#### 8.2.2 Import Wizard
```
┌─ Import from URL ──────────────────────────────┐
│ Source: [Shadertoy ▼]                          │
│ URL: [https://shadertoy.com/view/...____]      │
│                                                │
│ ○ Import as new preset                         │
│ ○ Add to current graph                         │
│                                                │
│ Settings:                                      │
│   □ Auto-generate thumbnail                    │
│   □ Enable MIDI mapping                        │
│   □ Audio reactive (if supported)              │
│                                                │
│ [Cancel] [Import]                              │
└────────────────────────────────────────────────┘
```

#### 8.2.3 Live Preview
- Renderizar preset en ventana pequeña
- Permitir ajustar parámetros antes de importar
- Mostrar estadísticas de rendimiento (FPS, GPU usage)

### 8.3 Funcionalidades de UI
```python
class CommunityBrowser:
    def render_browser_window(self)
    def render_preset_grid(self, presets: list)
    def render_preset_card(self, preset: dict)
    def render_filters(self)
    def render_search(self)
    def handle_import_url(self, url: str, source: str)
    def preview_preset(self, preset_id: str)
```

---

## 9. Sistema de Validación y Testing

### 9.1 Archivos a Crear
- `src/community/validators/shader_validator.py`
- `src/community/validators/code_sanitizer.py`
- `tests/test_importers.py`

### 9.2 Validaciones Requeridas

#### 9.2.1 Validación de Shaders
- Compilar shader con ModernGL para detectar errores
- Verificar uniforms requeridos existen
- Detectar funciones no soportadas
- Límite de complejidad (evitar infinite loops)

#### 9.2.2 Sanitización de Código
- **Seguridad**: No permitir operaciones de archivo/red
- **Performance**: Detectar loops infinitos potenciales
- **Compatibilidad**: Verificar versión GLSL compatible

#### 9.2.3 Tests Automáticos
- Test de compilación para cada shader importado
- Benchmark de rendimiento (debe mantener >30 FPS)
- Validación de metadatos

### 9.3 API del Validator
```python
class ShaderValidator:
    def validate_glsl(self, code: str, version: str = "330") -> dict
    def check_uniforms(self, code: str, required: list) -> bool
    def detect_complexity(self, code: str) -> str  # low/medium/high
    def compile_test(self, code: str, ctx: moderngl.Context) -> bool

class CodeSanitizer:
    def sanitize_python(self, code: str) -> str
    def check_security(self, code: str) -> list  # Lista de warnings
    def remove_unsafe_imports(self, code: str) -> str
    def limit_execution_time(self, code: str, max_time: float) -> str
```

---

## 10. Documentación y Ejemplos

### 10.1 Archivos a Crear
- `docs/COMMUNITY_IMPORT_GUIDE.md`
- `docs/examples/shadertoy_import_example.md`
- `docs/examples/isf_import_example.md`
- `docs/examples/hydra_conversion_example.md`
- `docs/examples/taichi_integration_example.md`
- `docs/examples/p5py_conversion_example.md`

### 10.2 Contenido de Documentación

#### 10.2.1 Guía de Usuario
- Cómo importar desde cada fuente
- Limitaciones conocidas
- Troubleshooting común
- Best practices

#### 10.2.2 Guía de Desarrollador
- API de cada importador
- Cómo añadir soporte para nueva fuente
- Estructura de datos de presets
- Sistema de plugins

#### 10.2.3 Ejemplos Prácticos
Para cada fuente:
1. Ejemplo simple
2. Ejemplo medio con parámetros
3. Ejemplo avanzado con múltiples nodos

---

## Resumen de Cambios por Módulo

### Archivos Nuevos (Total: ~35 archivos)
```
src/community/                        [13 archivos]
src/nodes/community/                  [5 archivos]
src/editor/ui/                        [3 archivos nuevos]
tests/                                [5 archivos test]
docs/                                 [6 documentos]
community_presets/                    [metadata + structure]
```

### Modificaciones a Archivos Existentes
```
src/nodes/registry.py                 # Registrar nuevos tipos de nodos
src/editor/ui/canvas.py               # Añadir botón "Community Browser"
src/core/config.py                    # Configuración de paths de comunidad
requirements.txt                      # Añadir taichi>=1.7.0
```

### Dependencias Adicionales
```
taichi>=1.7.0                         # Para simulaciones GPU
requests>=2.31.0                      # Para download de Shadertoy
beautifulsoup4>=4.12.0                # Para parsing HTML (opcional)
pillow>=10.1.0                        # Ya existe, para thumbnails
```

---

## Estimación de Complejidad

| Módulo | Archivos | Complejidad | Prioridad |
|--------|----------|-------------|-----------|
| 1. Arquitectura Base | 3 | Media | Alta |
| 2. Shadertoy Importer | 4 | Media | Alta |
| 3. ISF Importer | 4 | Media | Alta |
| 4. Hydra Adapter | 5 | Alta | Media |
| 5. Taichi Integrator | 3 | Alta | Media |
| 6. p5py Converter | 4 | Alta | Baja |
| 7. Cache System | 3 | Media | Alta |
| 8. UI Browser | 3 | Media | Alta |
| 9. Validation | 3 | Media | Alta |
| 10. Docs | 6 | Baja | Media |

---

## Orden de Implementación Recomendado

### Fase 1: Fundamentos (Semana 1-2)
1. Arquitectura base del sistema de importación
2. Sistema de caché y metadata
3. Validadores básicos

### Fase 2: Importadores Core (Semana 3-4)
4. Shadertoy importer (más simple y útil)
5. ISF importer (muy similar a Shadertoy)
6. UI Community Browser básico

### Fase 3: Importadores Avanzados (Semana 5-6)
7. Hydra adapter (más complejo)
8. Taichi integrator (requiere testing extensivo)

### Fase 4: Opcional (Semana 7+)
9. p5py converter (menor prioridad)
10. Features avanzadas de UI
11. Documentación completa

---

## Consideraciones de Seguridad

1. **Ejecución de Código Arbitrario**
   - Sandboxing de código Python importado
   - Límites de tiempo de ejecución
   - Whitelist de imports permitidos

2. **Shader Bombs**
   - Detección de loops infinitos
   - Timeout en compilación de shaders
   - Límite de complejidad

3. **Licencias**
   - Verificar y mostrar licencia de cada preset
   - Advertir sobre uso comercial si aplica
   - Atribución obligatoria

---

## Métricas de Éxito

- [ ] Importar shader de Shadertoy en <30 segundos
- [ ] Conversión ISF con 95%+ de compatibilidad
- [ ] Mantener >30 FPS con código importado
- [ ] UI responsive (<100ms de latencia)
- [ ] Cache de presets <50MB por 100 presets
- [ ] Tests passing al 100%

---

## Próximos Pasos

1. Revisar y aprobar este plan
2. Crear estructura de directorios básica
3. Implementar clase base `BaseImporter`
4. Comenzar con Shadertoy importer (MVP)
5. Iterar basándose en feedback

