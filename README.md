# Visual Engine - Circuit Tracks

Generador de visuales audiovisuales controlado por Circuit Tracks.
Inspirado en artistas como miscsoul, pauric_freeman, Klsr.av, CRIS WAR.

**Formato**: Instagram Reels (1080x1920 - Vertical)

## Presets Disponibles

### Preset 1: Minimal Generative (default)
```bash
./run.sh     # o ./run.sh 1
```
**Estilo**: Ultra Minimal - Una forma generativa central
- Fondo negro limpio
- Una forma que respira y evoluciona
- Rendering en CPU con Pygame

[Ver documentación completa →](#preset-1-minimal-generative)

### Preset 2: Shader OpenGL
```bash
./run.sh 2
```
**Estilo**: Shaders GLSL generativos
- Fragment shaders en tiempo real
- Rendering en GPU
- Alta performance

[Ver documentación →](README_SHADER.md)

---

## Preset 1: Minimal Generative

### Concepto

Un solo visual generativo en el centro de la pantalla que responde a MIDI:
- **Fondo negro limpio**
- **Sin saturación visual**
- **Forma única que evoluciona**

## Mapeo MIDI - Circuit Tracks

| Nota | Sonido | Función | Efecto |
|------|--------|---------|--------|
| 60 | Kick | **Driver Principal** | Pulsa y expande la forma base |
| 62 | Close Hats | **Modulación Glitch** | Crea ecos/distorsión de la forma |
| 64 | Tom/Bell 1 | **Transformación** | Cambia geometría (3-12 lados) |
| 65 | Tom/Bell 2 | **Modulación Rotación** | Modula velocidad y dirección de rotación |

## Controles

- **Circuit Tracks**: Los pads modulan la forma generativa central
- **ESC**: Salir
- **Modo Demo** (sin MIDI): K=kick, H=hat, T=tom1, Y=tom2

## Sistema Generativo

### Forma Central
- **Posición**: Centro fijo de pantalla
- **Base**: Hexágono de 100px de radio
- **Evolución**: Continua con ruido orgánico
- **Geometría**: 3 a 12 lados (triángulo → dodecágono)

### Modulación por MIDI

**KICK (Driver Principal)**:
- Pulsa la forma (expansión hasta 40% según velocity)
- Interpolación suave de retorno
- Punto central brilla con el pulso

**HATS (Glitch/Distorsión)**:
- Crea 1-8 ecos desplazados de la forma
- Offsets aleatorios ±30px
- Decay suave de intensidad
- Interpolación fluida de posiciones

**TOM 1 (Transformación)**:
- Cambia número de lados aleatoriamente
- Opciones: 3, 4, 5, 6, 8, 12 lados
- Transición suave entre geometrías

**TOM 2 (Rotación)**:
- Modula velocidad de rotación (±3 grados/frame)
- Fricción natural (decay 0.98)
- Dirección aleatoria

## Características Técnicas

### Rendering Minimal
- Fondo negro puro (#000000)
- Forma principal: gris medio (120, 120, 120)
- Ecos/glitch: gris oscuro (80, 80, 80)
- Glow sutil de 2 capas
- UI ultra discreta

### Animaciones Suaves
- Pulso: interpolación 0.15, decay 0.92
- Radio: interpolación 0.1, retorno 0.08
- Glitch: interpolación 0.2, decay 0.9
- Rotación: fricción 0.98
- Ruido orgánico sinusoidal continuo

### Optimización
- Una sola forma (máximo rendimiento)
- 20 offsets de glitch pre-calculados
- Sin fade surface (render directo)
- 60 FPS garantizados

## Debug MIDI

Información muy discreta en esquina inferior derecha:
- Últimas 4 notas MIDI
- FPS en esquina superior izquierda

## Filosofía de Diseño

> **Less is more**

- Sin llenar la pantalla
- Una sola forma que respira
- Negro puro como canvas
- Gris como único color
- Evolución orgánica continua
- Los inputs MIDI modulan, no crean

## Próximos Pasos

### Visuales Avanzados
- [ ] Más modos de transformación (morph shapes)
- [ ] Partículas orbitales sutiles
- [ ] Trails opcionales muy sutiles
- [ ] Modos de blend entre geometrías

### Modulación
- [ ] CC MIDI para control continuo
- [ ] Parámetros configurables en tiempo real
- [ ] Presets guardables

### Performance
- [ ] Export a video
- [ ] Captura de frames para GIF
- [ ] Modo fullscreen sin UI
