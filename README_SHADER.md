# Preset 2: VFX Shader Engine

Motor de visuales VFX basado en **OpenGL Shaders GLSL** controlado por Circuit Tracks.

## Ejecución

```bash
./run.sh 2
```

## Técnicas VFX Implementadas

### 🎨 Rendering 3D
- **Raymarching** - Renderizado volumétrico en tiempo real
- **Signed Distance Fields (SDF)** - Formas 3D matemáticas precisas
- **Smooth Boolean Operations** - Mezcla suave entre formas

### 🌊 Efectos Generativos
- **Fractal Brownian Motion (FBM)** - Ruido fractal de 6 octavas
- **Procedural Noise** - Distorsión orgánica del espacio
- **Morphing entre formas** - Esfera → Box → Torus

### ✨ Post-Processing
- **Vignette** - Oscurecimiento de bordes
- **Chromatic Aberration** - Separación RGB
- **Glow Effect** - Resplandor exponencial
- **Scanlines** - Líneas sutiles tipo CRT
- **Film Grain** - Ruido de película
- **Tone Mapping** - Reinhard
- **Gamma Correction** - sRGB

### 💡 Iluminación
- **Multiple Lights** - Dos fuentes de luz dinámicas
- **Diffuse Lighting** - Lambert shading
- **Specular Highlights** - Phong specular
- **Fresnel Effect** - Rim lighting
- **Ambient Occlusion** - Profundidad basada en distancia

## Mapeo MIDI → Efectos VFX

| Nota | Sonido | Efecto Shader | Descripción Técnica |
|------|--------|---------------|---------------------|
| 60 | Kick | **Expansion 3D** | Escala todas las formas SDF (0.8 → 1.4x) |
| 62 | Close Hats | **Glitch Multi-esfera** | Añade 3 esferas random + distorsión UV |
| 64 | Tom 1 | **Shape Morphing** | Interpola entre Sphere/Box/Torus con FBM |
| 65 | Tom 2 | **Camera Rotation** | Rota matriz de raydir en plano XZ |

## Desglose del Shader

### Scene SDF (Signed Distance Field)
```glsl
float map(vec3 p) {
    // 1. FBM distortion
    float distortion = fbm(p.xy * 2.0 + iTime * 0.3) * 0.3 * iTom1Morph;

    // 2. MIDI kick scaling
    float kickScale = 1.0 + iKickPulse * 0.8;

    // 3. Morph entre 3 formas
    float sphere = sdSphere(p, 0.8 * kickScale);
    float box = sdBox(p, vec3(0.6 * kickScale));
    float torus = sdTorus(p, vec2(0.7 * kickScale, 0.3));

    // 4. Smooth union
    return opSmoothUnion(shape1, shape2, 0.3);
}
```

### Raymarching Loop
```glsl
float raymarch(vec3 ro, vec3 rd) {
    float t = 0.0;
    for(int i = 0; i < 80; i++) {  // 80 steps
        vec3 p = ro + rd * t;
        float d = map(p);
        if(d < 0.001) break;  // Hit surface
        t += d;  // March
        if(t > 20.0) break;  // Max distance
    }
    return t;
}
```

### Lighting Model
```glsl
vec3 shade(vec3 p, vec3 rd, vec3 normal) {
    // Dual light setup
    vec3 color = baseColor * (diff1 * 0.8 + diff2 * 0.4);
    color += spec1 * 0.5;  // Specular
    color += fresnel * baseColor * 0.3;  // Rim
    color += iKickPulse * 0.5;  // MIDI reactive brightness
    return color;
}
```

## Personalización Avanzada

### Cambiar Formas
```glsl
// Añadir más SDF primitives
float sdCylinder(vec3 p, float h, float r) {
    vec2 d = abs(vec2(length(p.xz), p.y)) - vec2(r, h);
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0));
}

// En map():
float cylinder = sdCylinder(p, 1.0, 0.5);
mainShape = opSmoothUnion(mainShape, cylinder, 0.3);
```

### Modificar Post-FX
```glsl
// Más intensidad de chromatic aberration
if (iHatGlitch > 0.1) {  // En vez de 0.2
    color *= chromaticAberration(uv, iHatGlitch * 2.0);  // 2x
}

// Más glow
float glow = exp(-length(p) * 0.5) * 0.6;  // Era 0.8 y 0.3
```

### Cambiar Colores
```glsl
// Color base (línea 190)
vec3 baseColor = 0.5 + 0.5 * cos(iTime + p.xyx * 2.0 + vec3(0, 2, 4));

// Opciones:
vec3 monocromo = vec3(0.5);  // Blanco y negro
vec3 neon = vec3(0.0, 1.0, 1.0);  // Cyan
vec3 fire = vec3(1.0, 0.3, 0.0);  // Fuego
```

## Performance

- **Target**: 60 FPS @ 1080x1920
- **Raymarching**: 80 iterations máximo
- **FBM**: 6 octavas
- **Post-FX**: Conditional (solo con MIDI trigger)

### Optimizaciones Aplicadas

✅ Early exit en raymarch (< 0.001)
✅ Max distance limit (20.0)
✅ Conditional glitch spheres (solo si iHatGlitch > 0.1)
✅ Conditional chromatic aberration
✅ VSync habilitado

## Aspect Ratio

**Corregido para 9:16 (Instagram Reels)**:
```glsl
// UV normalization (línea 219)
vec2 p = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
```
Divide por `.y` en vez de `.xy` para mantener proporción vertical correcta.

## Próximos VFX

Ideas para expandir:
- [ ] Volumetric lighting (god rays)
- [ ] Subsurface scattering
- [ ] Bloom con blur gaussiano
- [ ] Motion blur
- [ ] Depth of field
- [ ] Fluid simulation (Navier-Stokes)
- [ ] Particle systems en compute shader
- [ ] Texture feedback loops
- [ ] Domain repetition (infinito de formas)

## Referencias

- **Inigo Quilez** - [SDF functions](https://iquilezles.org/articles/distfunctions/)
- **ShaderToy** - [Raymarching examples](https://www.shadertoy.com/)
- **The Book of Shaders** - [Noise & FBM](https://thebookofshaders.com/)

## Debug

Si ves performance bajo:
1. Reduce raymarching iterations (80 → 40)
2. Reduce FBM octaves (6 → 4)
3. Desactiva post-FX temporalmente
4. Reduce resolución de test
