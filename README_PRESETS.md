# Visual Engine - Preset Library

Colección completa de 22 presets visuales generativos para Circuit Tracks.

**Formato**: Instagram Reels (1080x1920 - Vertical 9:16)
**Estilo**: Minimal, Monochrome, Glow, Generative
**Filosofía**: Todos los presets son **evolutivos** - la forma/patrón evoluciona con cada kick

---

## 📋 Índice Rápido

```bash
./run.sh list         # Ver todos los presets
./run.sh N            # Ejecutar preset N (1-22)
```

| Preset | Nombre | Categoría | Técnica Principal |
|--------|--------|-----------|-------------------|
| 1 | Minimal Generative | CPU Rendering | Forma poligonal evolutiva |
| 2 | VFX Shader Engine | Fractals/SDF | Raymarching 3D + FBM |
| 3 | Menger Sponge | Fractals/SDF | Fractal cúbico 3D |
| 4 | Mandelbulb | Fractals/SDF | Fractal 3D orgánico |
| 5 | Apollonian Gasket | Fractals/SDF | Circle packing infinito |
| 6 | Sierpinski Pyramid | Fractals/SDF | Fractal tetraédrico |
| 7 | Curl Noise Flow | Particle/Flow | Curl noise divergence-free |
| 8 | Magnetic Field Lines | Particle/Flow | Campo magnético multi-carga |
| 9 | Swarm Intelligence | Particle/Flow | Boids flocking |
| 10 | Turbulence Field | Particle/Flow | Partículas caóticas |
| 11 | Pixel Sorting | Glitch/Feedback | Ordenamiento de píxeles |
| 12 | Datamosh Feedback | Glitch/Feedback | Motion vector glitches |
| 13 | RGB Displacement | Glitch/Feedback | Separación cromática |
| 14 | Scanline Corruption | Glitch/Feedback | CRT glitches |
| 15 | Voronoi Cells | Generative Patterns | División celular |
| 16 | Reaction-Diffusion | Generative Patterns | Modelo Gray-Scott |
| 17 | Wave Interference | Generative Patterns | Interferencia de ondas |
| 18 | Truchet Tiles | Generative Patterns | Tiles procedurales |
| 19 | Quantum Foam | Hybrid/Experimental | Campo probabilístico |
| 20 | Liquid Metal | Hybrid/Experimental | Metaballs morfing |
| 21 | Crystal Growth | Hybrid/Experimental | Autómata celular |
| 22 | Neural Noise | Hybrid/Experimental | Domain warping |

---

## 🎹 MIDI Mapping Universal

Todos los presets usan el mismo mapeo MIDI:

| Nota | Función | Efecto |
|------|---------|--------|
| **60** (Kick) | **Driver Principal** | Pulsa/expande forma, aumenta complejidad/iteraciones |
| **62** (Close Hats) | **Glitch/Distorsión** | Crea distorsión espacial, efectos glitch |
| **64** (Tom 1) | **Modulación Geométrica** | Cambia geometría, escala, morfing |
| **65** (Tom 2) | **Rotación/Movimiento** | Modula rotación, velocidad, dirección |

---

## 📚 Categoría 1: CPU Rendering

### Preset 1: Minimal Generative

```bash
./run.sh 1
```

**Técnica**: Rendering CPU con Pygame
**Descripción**: Una forma poligonal central que respira y evoluciona
**Características**:
- Fondo negro puro
- Geometría variable (3-12 lados)
- Ecos/glitch con hats
- Glow sutil de 2 capas

**Parámetros MIDI**:
- **Kick**: Pulsa la forma (expansión hasta 40%)
- **Hats**: Crea 1-8 ecos desplazados
- **Tom1**: Cambia número de lados (3/4/5/6/8/12)
- **Tom2**: Modula velocidad de rotación

---

## 📚 Categoría 2: Fractals/SDF

### Preset 2: VFX Shader Engine

```bash
./run.sh 2
```

**Técnica**: Raymarching + SDF + FBM (6 octavas)
**Descripción**: Motor VFX completo con morphing entre formas 3D
**Características**:
- Sphere → Box → Torus morphing
- FBM distortion
- Dual light setup (diffuse + specular)
- Post-FX: vignette, chromatic aberration, glow, tone mapping

**Parámetros MIDI**:
- **Kick**: Escala SDF (0.8 → 1.4x)
- **Hats**: Chromatic aberration + UV distortion
- **Tom1**: Morph entre formas (sphere/box/torus)
- **Tom2**: Rotación de cámara en plano XZ

**Performance**: 60 FPS @ 1080x1920, 80 raymarching steps

---

### Preset 3: Menger Sponge

```bash
./run.sh 3
```

**Técnica**: Recursive SDF folding
**Descripción**: Fractal cúbico 3D tipo esponja
**Características**:
- Iteraciones evolutivas (2-5 con kick)
- Cross subtraction para huecos
- Escala modular con Tom1

**Evolución**: Cada kick aumenta la complejidad fractal (más iteraciones)

---

### Preset 4: Mandelbulb

```bash
./run.sh 4
```

**Técnica**: 3D fractal con coordenadas polares
**Descripción**: Bulbo de Mandelbrot 3D orgánico
**Características**:
- Power variable (4-12)
- 8 iteraciones de escape
- Cámara orbital

**Evolución**: El power del fractal aumenta con kicks (4 → 12), creando formas más complejas

---

### Preset 5: Apollonian Gasket

```bash
./run.sh 5
```

**Técnica**: Circle packing recursivo
**Descripción**: Empaquetamiento infinito de círculos
**Características**:
- Depth evolutivo (4-10 niveles)
- Distance field visualization
- Smooth circle outlines

**Evolución**: Profundidad de subdivisión aumenta con kicks

---

### Preset 6: Sierpinski Pyramid

```bash
./run.sh 6
```

**Técnica**: Tetrahedral folding
**Descripción**: Pirámide fractal 3D
**Características**:
- Folding geométrico 3D
- Escala variable (2.0 + Tom1)
- Iteraciones: 3-8

**Evolución**: Complejidad del tetraedro crece con kicks

---

## 📚 Categoría 3: Particle/Flow Field

### Preset 7: Curl Noise Flow

```bash
./run.sh 7
```

**Técnica**: Curl noise divergence-free
**Descripción**: Campo de flujo orgánico sin divergencia
**Características**:
- 40-100 partículas
- Vector field visualization
- Flow-following particles

**Evolución**: Más partículas aparecen con cada kick, siguiendo el campo de flujo

---

### Preset 8: Magnetic Field Lines

```bash
./run.sh 8
```

**Técnica**: Force field simulation
**Descripción**: Visualización de campo magnético
**Características**:
- 2-6 cargas (positivas/negativas)
- Field line rendering
- Orbital motion

**Evolución**: Número de cargas aumenta con kicks

---

### Preset 9: Swarm Intelligence

```bash
./run.sh 9
```

**Técnica**: Boids flocking algorithm
**Descripción**: Comportamiento emergente de enjambre
**Características**:
- 30-100 boids
- Cohesion + alignment
- Connection lines entre cercanos

**Evolución**: Tamaño del enjambre crece con kicks

---

### Preset 10: Turbulence Field

```bash
./run.sh 10
```

**Técnica**: Turbulent noise flow
**Descripción**: Caos turbulento de partículas
**Características**:
- Noise-driven motion
- Discontinuidades con hats
- 40-100 partículas

**Evolución**: Intensidad de turbulencia aumenta con kicks

---

## 📚 Categoría 4: Glitch/Feedback

### Preset 11: Pixel Sorting

```bash
./run.sh 11
```

**Técnica**: Threshold-based pixel sorting
**Descripción**: Arte glitch con ordenamiento de píxeles
**Características**:
- Sorting vertical (hats)
- Sorting horizontal (Tom1)
- Block inversion glitches

**Evolución**: Intensidad de sorting aumenta, más bandas aparecen

---

### Preset 12: Datamosh Feedback

```bash
./run.sh 12
```

**Técnica**: Simulated feedback loops
**Descripción**: Efectos tipo datamoshing
**Características**:
- Motion vector displacement
- Block-based glitches
- Compression artifacts con kicks

**Evolución**: Feedback se acumula, creando artifacts más intensos

---

### Preset 13: RGB Displacement

```bash
./run.sh 13
```

**Técnica**: Channel separation
**Descripción**: Separación cromática angular
**Características**:
- Offset por canal (R/G/B)
- Angular displacement
- Rotational modulation

**Evolución**: Desplazamiento aumenta con kicks

---

### Preset 14: Scanline Corruption

```bash
./run.sh 14
```

**Técnica**: CRT-style glitches
**Descripción**: Corrupción de scanlines tipo CRT
**Características**:
- Horizontal displacement
- Sync glitches con kicks
- Rolling effect (Tom2)

**Evolución**: Más scanlines se corrompen con kicks

---

## 📚 Categoría 5: Generative Patterns

### Preset 15: Voronoi Cells

```bash
./run.sh 15
```

**Técnica**: Voronoi distance field
**Descripción**: División celular orgánica
**Características**:
- Cell count evolutivo (3-10 células)
- Animated centers
- Edge glow

**Evolución**: Número de células aumenta con kicks

---

### Preset 16: Reaction-Diffusion

```bash
./run.sh 16
```

**Técnica**: Simplified Gray-Scott model
**Descripción**: Patrones de reacción-difusión
**Características**:
- 4 layers de reacción
- Injection points con hats
- Speed modulation

**Evolución**: Velocidad de reacción aumenta con kicks

---

### Preset 17: Wave Interference

```bash
./run.sh 17
```

**Técnica**: Multiple wave sources
**Descripción**: Interferencia constructiva/destructiva
**Características**:
- 2-8 fuentes de ondas
- Frequency modulation con kicks
- Phase shifts con hats

**Evolución**: Más fuentes de ondas aparecen con kicks

---

### Preset 18: Truchet Tiles

```bash
./run.sh 18
```

**Técnica**: Procedural tile patterns
**Descripción**: Tiles procedurales evolutivos
**Características**:
- Tile density (5-20 tiles)
- Random rotations
- Animated offset

**Evolución**: Densidad de tiles aumenta con kicks

---

## 📚 Categoría 6: Hybrid/Experimental

### Preset 19: Quantum Foam

```bash
./run.sh 19
```

**Técnica**: Probabilistic field
**Descripción**: Campo visual cuántico
**Características**:
- 6-octave quantum noise
- Probability collapse con hats
- Uncertainty visualization

**Evolución**: Fluctuaciones cuánticas se intensifican con kicks

---

### Preset 20: Liquid Metal

```bash
./run.sh 20
```

**Técnica**: Metaball field
**Descripción**: Metaballs morfing líquido
**Características**:
- 3-10 metaballs
- Organic motion
- Surface threshold

**Evolución**: Más metaballs aparecen y se fusionan con kicks

---

### Preset 21: Crystal Growth

```bash
./run.sh 21
```

**Técnica**: Cellular automata
**Descripción**: Crecimiento cristalino emergente
**Características**:
- Growth rules
- Hexagonal structure
- Seed points con hats

**Evolución**: El cristal crece y se expande con cada kick

---

### Preset 22: Neural Noise

```bash
./run.sh 22
```

**Técnica**: Multi-octave Perlin + domain warping
**Descripción**: Ruido neuronal orgánico
**Características**:
- 4-12 octavas
- Domain warping
- Ridge noise effect

**Evolución**: Número de octavas aumenta con kicks, más detalle

---

## 🎨 Características Técnicas Comunes

### Rendering
- **GPU**: OpenGL 3.3 Core con GLSL shaders
- **Target FPS**: 60 FPS @ 1080x1920
- **Aspect Ratio**: 9:16 (Instagram Reels)
- **Letterboxing**: Automático para mantener aspect ratio

### Interpolación MIDI
Todos los presets usan smooth interpolation para parámetros MIDI:

```python
# Interpolation rates
kick_pulse: 0.15 lerp, 0.92 decay
hat_glitch: 0.88 decay
tom1_morph: 0.90 decay
tom2_spin: 0.93 decay
```

### Post-Processing
La mayoría incluyen:
- Vignette (0.4 intensity)
- Tone mapping (Reinhard)
- Gamma correction (sRGB 2.2)
- Glow effects

### Estilo Visual
- **Paleta**: Monocromático (grises)
- **Glow**: Exponencial decay
- **Fondo**: Negro puro (#000000)
- **Kick flash**: +0.2 - 0.4 brightness

---

## 💡 Tips de Uso

### Performance
Si experimentas bajo rendimiento:
1. Reduce window size (preset se adapta)
2. Los presets con muchas partículas (7-10) son más intensivos
3. Fractales complejos (3-6) requieren más GPU

### Composición
- **Kicks constantes**: Mantienen alta complejidad visual
- **Hats intermitentes**: Añaden surprise y variación
- **Toms**: Modulación continua para variedad

### Grabación para Reels
1. Maximiza ventana (mantiene 9:16)
2. Usa OBS u otro screen recorder
3. Captura solo el viewport (sin bordes negros)
4. Export a 1080x1920 @ 60fps

---

## 🔧 Personalización

Cada preset puede ser modificado editando su archivo `.py`:

```python
# Ejemplo: Cambiar colores en cualquier preset
# Buscar líneas como:
color = vec3(pattern);  // Monochrome

# Cambiar a:
color = vec3(pattern, pattern * 0.5, 0.0);  // Orange tint
```

### Modificaciones Comunes

**Cambiar velocidad de animación**:
```glsl
// Buscar: iTime * 0.5
// Cambiar a: iTime * 2.0  (más rápido)
```

**Más/menos partículas**:
```glsl
// Buscar: int numParticles = 40 + int(iKickPulse * 60.0);
// Cambiar los límites: 40 → 80, 60 → 120
```

**Cambiar intensidad de glow**:
```glsl
// Buscar: color += exp(-length(p) * 1.5) * 0.3;
// Aumentar el 0.3 para más glow
```

---

## 📖 Referencias Técnicas

### Fractales
- **Inigo Quilez**: [SDF Functions](https://iquilezles.org/articles/distfunctions/)
- **Shadertoy**: [Raymarching Examples](https://www.shadertoy.com/)

### Noise & Flow
- **The Book of Shaders**: [Noise & FBM](https://thebookofshaders.com/)
- **Curl Noise**: Robert Bridson papers

### Glitch Art
- **Pixel Sorting**: Kim Asendorf
- **Datamoshing**: Compression artifact techniques

### Cellular Automata
- **Reaction-Diffusion**: Karl Sims
- **Voronoi**: Steven Fortune algorithm

---

## 🚀 Próximas Expansiones

Ideas para más presets:
- [ ] Volumetric lighting (god rays)
- [ ] Subsurface scattering
- [ ] Bloom con blur gaussiano
- [ ] Fluid simulation (Navier-Stokes)
- [ ] Particle systems en compute shader
- [ ] Domain repetition (infinito)
- [ ] Julia sets 4D
- [ ] Perlin worms 3D

---

## 📝 Changelog

### v2.0.0 - 20 Nuevos Presets
- ✅ 6 Fractales/SDF avanzados
- ✅ 4 Sistemas de partículas/flow fields
- ✅ 4 Efectos glitch/feedback
- ✅ 4 Patrones generativos
- ✅ 4 Experimentales híbridos
- ✅ Todos evolutivos con kicks
- ✅ Vertical 9:16 format
- ✅ 60 FPS target

### v1.0.0 - Presets Base
- ✅ Minimal Generative (CPU)
- ✅ VFX Shader Engine (GPU)

---

**¡Disfruta creando visuales! 🎨✨**
