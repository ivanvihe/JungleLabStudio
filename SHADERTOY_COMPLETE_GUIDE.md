# Shadertoy Compatibility System - Complete Guide

Complete documentation for the Shadertoy compatibility system in JungleLabStudio.

## Overview

JungleLabStudio is now 100% compatible with Shadertoy.com shaders. You can:
- ✅ Import Shadertoy shader code snippets directly
- ✅ Create Shadertoy-style visuals using native generator nodes
- ✅ Use all Shadertoy uniforms (iTime, iResolution, iMouse, iChannel0-3, etc.)
- ✅ Build complex multi-pass effects
- ✅ Export as YAML presets

## Table of Contents

1. [Quick Start](#quick-start)
2. [Importing Shadertoy Code](#importing-shadertoy-code)
3. [Native Generator Nodes](#native-generator-nodes)
4. [Shadertoy Uniforms Reference](#shadertoy-uniforms-reference)
5. [Example Presets](#example-presets)
6. [Advanced Usage](#advanced-usage)

---

## Quick Start

### Method 1: Import Shadertoy Code

```python
from shadertoy.importer import quick_import

# Paste your Shadertoy shader code
shader_code = """
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec3 col = 0.5 + 0.5 * cos(iTime + uv.xyx + vec3(0, 2, 4));
    fragColor = vec4(col, 1.0);
}
"""

# Import to YAML preset
quick_import(
    code=shader_code,
    name="Rainbow Gradient",
    output_path="community_presets/my_shader.yaml"
)
```

### Method 2: Use Native Generators

Create a YAML preset using Shadertoy-style generator nodes:

```yaml
preset:
  name: "Plasma Effect"

  nodes:
    - id: plasma
      type: generator.plasma
      params:
        effect_type: 0  # Plasma mode
        frequency: 4.0
        speed: 1.0

    - id: output
      type: output
      inputs:
        source: plasma
```

### Method 3: Use the ImGui UI

1. Launch the editor
2. Open the Shadertoy Importer window
3. Paste your shader code
4. Click "Validate Shader"
5. Click "Import to Preset"
6. Click "Save to File" or "Load to Editor"

---

## Importing Shadertoy Code

### Using Python API

```python
from shadertoy.importer import ShadertoyImporter

importer = ShadertoyImporter()

# Import shader
preset = importer.import_from_code(
    code=shader_code,
    name="My Effect",
    author="Your Name",
    description="Amazing visual effect"
)

# Save to file
importer.save_preset(preset, "presets/my_effect.yaml")
```

### Using ImGui UI

The UI is located at `src/editor/ui/shadertoy_importer.py`:

```python
from editor.ui.shadertoy_importer import ShadertoyImporterUI, render_shadertoy_window

# In your editor initialization
shadertoy_ui = ShadertoyImporterUI(editor_state)

# In render loop
if show_shadertoy_window:
    show_shadertoy_window = render_shadertoy_window(editor_state, shadertoy_ui)
```

### Validation

Before importing, validate your shader:

```python
from shadertoy.converter import ShadertoyConverter

converter = ShadertoyConverter()
validation = converter.validate_shader(shader_code)

if validation['valid']:
    print("✓ Valid Shadertoy code")

    # Check dependencies
    deps = converter.detect_dependencies(shader_code)
    if deps['uses_channels']:
        print("Uses texture channels")
    if deps['uses_mouse']:
        print("Uses mouse input")
else:
    print(f"✗ Invalid: {validation['error']}")
```

---

## Native Generator Nodes

Create Shadertoy-style visuals without writing code using these native nodes.

### 1. Raymarching Node (`generator.raymarching`)

3D raymarching with signed distance functions (SDFs).

**Parameters:**
- `primitive`: 0=Sphere, 1=Box, 2=Torus, 3=Capsule
- `camera_distance`: Distance from origin (1.0-10.0)
- `camera_rotate`: Auto-rotate camera (0=off, 1=on)
- `light_dir_x/y/z`: Light direction (-1.0 to 1.0)
- `material_color`: RGB material color
- `ambient`: Ambient light (0.0-1.0)
- `diffuse`: Diffuse light (0.0-1.0)
- `specular`: Specular highlight (0.0-1.0)
- `shininess`: Specular exponent (1.0-128.0)
- `max_steps`: Raymarch steps (10-200)
- `max_dist`: Max raymarch distance (5.0-100.0)

**Example:**
```yaml
- id: sphere
  type: generator.raymarching
  params:
    primitive: 0
    camera_distance: 3.0
    camera_rotate: 1.0
    material_color: [0.8, 0.4, 0.2]
    ambient: 0.3
    diffuse: 0.7
    specular: 0.5
```

### 2. Fractal Node (`generator.fractal`)

Mandelbrot, Julia, and Burning Ship fractals.

**Parameters:**
- `fractal_type`: 0=Mandelbrot, 1=Julia, 2=Burning Ship
- `zoom`: Zoom level (0.1-100.0)
- `center_x/y`: View center (-2.0 to 2.0)
- `julia_c_x/y`: Julia set constant (for Julia fractals)
- `max_iterations`: Escape iterations (10-500)
- `color_intensity`: Color mapping intensity (0.0-5.0)
- `color_offset`: Color phase (0.0-6.28)

**Example:**
```yaml
- id: mandelbrot
  type: generator.fractal
  params:
    fractal_type: 0
    zoom: 2.0
    center_x: -0.5
    center_y: 0.0
    max_iterations: 150
    color_intensity: 2.0
```

### 3. Voronoi Node (`generator.voronoi`)

Voronoi diagrams and cellular patterns.

**Parameters:**
- `scale`: Pattern scale (1.0-20.0)
- `mode`: 0=Distance, 1=Cells, 2=Edges, 3=Both
- `color_mode`: 0=Distance, 1=Random, 2=Gradient
- `animate`: Animate cells (0=off, 1=on)
- `edge_thickness`: Edge line width (0.01-0.2)
- `distance_power`: Distance metric (1.0-4.0)

**Example:**
```yaml
- id: voronoi
  type: generator.voronoi
  params:
    scale: 5.0
    mode: 3  # Cells + Edges
    color_mode: 1  # Random colors
    animate: 1.0
```

### 4. Domain Warp Node (`generator.domain_warp`)

Organic patterns using domain warping (marble, clouds).

**Parameters:**
- `scale`: Pattern scale (0.5-10.0)
- `warp_amount`: Warping strength (0.0-5.0)
- `octaves`: Noise octaves (1-8)
- `lacunarity`: Frequency multiplier (1.0-4.0)
- `persistence`: Amplitude decay (0.0-1.0)
- `warp_octaves`: Warping iterations (1-5)
- `color_a/b`: Color gradient (RGB)

**Example:**
```yaml
- id: marble
  type: generator.domain_warp
  params:
    scale: 4.0
    warp_amount: 1.5
    octaves: 5
    warp_octaves: 3
    color_a: [0.1, 0.05, 0.02]
    color_b: [0.9, 0.85, 0.8]
```

### 5. Plasma Node (`generator.plasma`)

Psychedelic plasma and tunnel effects.

**Parameters:**
- `effect_type`: 0=Plasma, 1=Tunnel, 2=Radial, 3=Combined
- `frequency`: Pattern density (0.5-20.0)
- `speed`: Animation speed (0.0-5.0)
- `distortion`: Pattern distortion (0.0-5.0)
- `color_speed`: Color animation speed (0.0-5.0)
- `color_offset`: Color phase (0.0-6.28)
- `brightness`: Overall brightness (0.0-2.0)
- `contrast`: Pattern contrast (0.0-3.0)

**Example:**
```yaml
- id: tunnel
  type: generator.plasma
  params:
    effect_type: 1  # Tunnel
    frequency: 6.0
    speed: 1.5
    brightness: 1.2
```

### 6. Metaballs Node (`generator.metaballs`)

Organic blob/liquid effects.

**Parameters:**
- `num_balls`: Number of metaballs (2-8)
- `threshold`: Blob merge threshold (0.3-3.0)
- `ball_size`: Individual ball size (0.1-1.0)
- `animation_speed`: Movement speed (0.0-3.0)
- `animation_chaos`: Movement randomness (0.0-2.0)
- `color_a/b`: Color gradient (RGB)
- `glow`: Glow intensity (0.0-2.0)
- `smoothness`: Edge smoothness (0.01-0.5)

**Example:**
```yaml
- id: blobs
  type: generator.metaballs
  params:
    num_balls: 6
    threshold: 1.0
    ball_size: 0.35
    glow: 0.8
    color_a: [0.1, 0.2, 0.6]
    color_b: [0.9, 0.3, 0.8]
```

### 7. Pattern Node (`generator.pattern`)

Geometric patterns, tiles, and kaleidoscopes.

**Parameters:**
- `pattern_type`: 0=Grid, 1=Hexagon, 2=Kaleidoscope, 3=Truchet, 4=Spiral
- `scale`: Pattern scale (1.0-20.0)
- `rotation`: Rotation angle (0.0-6.28)
- `symmetry`: Kaleidoscope symmetry (2-12)
- `thickness`: Line/shape thickness (0.01-0.5)
- `animate`: Animate pattern (0=off, 1=on)
- `color_mode`: 0=Mono, 1=Gradient, 2=Rainbow
- `color_a/b`: Color gradient (RGB)

**Example:**
```yaml
- id: kaleidoscope
  type: generator.pattern
  params:
    pattern_type: 2  # Kaleidoscope
    scale: 3.0
    symmetry: 8
    color_mode: 2  # Rainbow
```

---

## Shadertoy Uniforms Reference

All Shadertoy uniforms are fully supported:

| Uniform | Type | Description |
|---------|------|-------------|
| `iTime` | float | Elapsed time in seconds |
| `iTimeDelta` | float | Time since last frame |
| `iFrame` | int | Frame counter |
| `iResolution` | vec3 | Viewport resolution (x, y, aspect) |
| `iMouse` | vec4 | Mouse position and click state |
| `iChannel0-3` | sampler2D | Texture input channels |
| `iChannelTime[4]` | float | Per-channel playback time |
| `iChannelResolution[4]` | vec3 | Per-channel resolution |
| `iDate` | vec4 | Year, month, day, time of day |
| `iSampleRate` | float | Audio sample rate (44100) |

### Coordinate System

Shadertoy uses pixel coordinates:
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // fragCoord ranges from (0.5, 0.5) to (resolution.x - 0.5, resolution.y - 0.5)
    vec2 uv = fragCoord / iResolution.xy;  // Normalize to 0-1
}
```

The converter automatically handles this conversion!

---

## Example Presets

### Simple Gradient
```yaml
preset:
  name: "Simple Gradient"

  nodes:
    - id: shader
      type: shadertoy
      params:
        shader_code: |
          void mainImage(out vec4 fragColor, in vec2 fragCoord) {
              vec2 uv = fragCoord / iResolution.xy;
              fragColor = vec4(uv.x, uv.y, 0.5, 1.0);
          }

    - id: output
      type: output
      inputs:
        source: shader
```

### Animated Circle
```yaml
preset:
  name: "Pulsing Circle"

  nodes:
    - id: shader
      type: shadertoy
      params:
        shader_code: |
          void mainImage(out vec4 fragColor, in vec2 fragCoord) {
              vec2 uv = fragCoord / iResolution.xy;
              uv = uv * 2.0 - 1.0;
              uv.x *= iResolution.x / iResolution.y;

              float d = length(uv);
              float circle = smoothstep(0.5, 0.48, d);
              float pulse = 0.5 + 0.5 * sin(iTime * 2.0);

              vec3 col = vec3(circle * pulse);
              fragColor = vec4(col, 1.0);
          }

    - id: output
      type: output
      inputs:
        source: shader
```

### Complex Effect (Multiple Generators)
```yaml
preset:
  name: "Marble Sphere"

  nodes:
    # Texture
    - id: marble
      type: generator.domain_warp
      params:
        scale: 4.0
        warp_amount: 1.5

    # 3D Object
    - id: sphere
      type: generator.raymarching
      params:
        primitive: 0
        camera_rotate: 1.0

    # Combine
    - id: blend
      type: effect.blend
      mode: multiply
      inputs:
        a: sphere
        b: marble
      params:
        opacity: 0.8

    - id: output
      type: output
      inputs:
        source: blend
```

---

## Advanced Usage

### Multi-Pass Shaders

Some Shadertoy shaders use multiple render passes (BufferA, BufferB, etc.):

```python
from shadertoy.importer import ShadertoyImporter

importer = ShadertoyImporter()

passes = [
    {
        'code': buffer_a_code,
        'name': 'BufferA',
        'channels': [None, 'BufferB', None, None]  # iChannel1 = BufferB
    },
    {
        'code': buffer_b_code,
        'name': 'BufferB',
        'channels': ['BufferA', None, None, None]  # iChannel0 = BufferA
    },
    {
        'code': image_code,
        'name': 'Image',
        'channels': ['BufferA', 'BufferB', None, None]
    }
]

preset = importer.import_multipass(
    passes=passes,
    name="Multi-Pass Effect",
    author="Artist Name"
)
```

### Custom Texture Channels

Specify custom textures for iChannel inputs:

```yaml
nodes:
  # Texture generator
  - id: noise_tex
    type: generator.noise
    params:
      scale: 10.0

  # Shadertoy shader using the texture
  - id: shader
    type: shadertoy
    inputs:
      channel0: noise_tex  # iChannel0
    params:
      shader_code: |
        void mainImage(out vec4 fragColor, in vec2 fragCoord) {
            vec2 uv = fragCoord / iResolution.xy;
            vec4 tex = texture(iChannel0, uv);
            fragColor = tex;
        }
```

### MIDI Control

All node parameters can be MIDI-controlled:

```yaml
nodes:
  - id: plasma
    type: generator.plasma
    params:
      frequency: 4.0
    midi_mappings:
      frequency:
        channel: 0
        cc: 1  # Modulation wheel
        min: 1.0
        max: 20.0
```

### Combining with Effects

Chain Shadertoy generators with effect nodes:

```yaml
nodes:
  # Generator
  - id: fractal
    type: generator.fractal

  # Apply bloom
  - id: bloom
    type: effect.bloom
    inputs:
      source: fractal
    params:
      intensity: 0.5

  # Apply color correction
  - id: color
    type: effect.color
    inputs:
      source: bloom
    params:
      brightness: 1.2
      saturation: 1.3
```

---

## File Structure

```
JungleLabStudio/
├── src/
│   ├── shadertoy/
│   │   ├── __init__.py
│   │   ├── converter.py          # GLSL conversion
│   │   ├── importer.py           # Import system
│   │   └── README.md             # Quick reference
│   │
│   ├── nodes/
│   │   ├── shadertoy/
│   │   │   └── shadertoy_node.py  # Main Shadertoy node
│   │   │
│   │   └── generators/
│   │       ├── raymarching_node.py
│   │       ├── fractal_node.py
│   │       ├── voronoi_node.py
│   │       ├── domain_warp_node.py
│   │       ├── plasma_node.py
│   │       ├── metaballs_node.py
│   │       └── pattern_node.py
│   │
│   └── editor/
│       └── ui/
│           └── shadertoy_importer.py  # ImGui UI
│
├── community_presets/
│   └── shadertoy/
│       ├── simple_gradient.yaml
│       ├── animated_circle.yaml
│       ├── raymarching_sphere.yaml
│       ├── plasma_tunnel.yaml
│       ├── liquid_blobs.yaml
│       ├── mandelbrot_zoom.yaml
│       ├── kaleidoscope.yaml
│       └── marble_sphere.yaml
│
├── tests/
│   ├── test_shadertoy_basic.py
│   └── test_shadertoy_integration.py
│
└── docs/
    ├── SHADERTOY_COMPATIBILITY_PLAN.md
    ├── SHADERTOY_PHASE1_COMPLETE.md
    └── SHADERTOY_COMPLETE_GUIDE.md  (this file)
```

---

## Troubleshooting

### "Invalid Shadertoy code"

Make sure your code contains a `mainImage` function:
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // Your code here
}
```

### "Shader compilation failed"

Check for GLSL syntax errors. Remember:
- Use `texture(iChannel0, uv)` not `texture2D`
- GLSL 330 syntax required
- Check uniform names match Shadertoy exactly

### Missing textures

If your shader uses `iChannel0-3`, you need to provide texture inputs:
```yaml
inputs:
  channel0: some_texture_node
```

Or the importer will create placeholder noise textures.

### Performance issues

For expensive shaders (many raymarching steps, high iterations):
- Reduce `max_iterations`
- Reduce `max_steps`
- Lower resolution
- Use simpler fallback for preview

---

## Resources

- **Shadertoy.com**: https://www.shadertoy.com
- **GLSL Reference**: https://www.khronos.org/opengl/wiki/OpenGL_Shading_Language
- **Inigo Quilez Articles**: https://iquilezles.org/articles/

---

## Credits

Shadertoy compatibility system created for JungleLabStudio.

Shadertoy.com is created by Pol Jeremias and Inigo Quilez.

Many techniques and patterns inspired by the amazing Shadertoy community.
