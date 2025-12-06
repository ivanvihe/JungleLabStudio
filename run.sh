#!/bin/bash
# Visual Engine Launcher
# Usage:
#   ./run.sh     - Ejecuta preset 1 (minimal generative)
#   ./run.sh N   - Ejecuta preset N (1-31)

source venv/bin/activate

PRESET=${1:-1}

case $PRESET in
    1)
        echo "🎨 Preset 1: Minimal Generative"
        python3 visuales.py
        ;;
    2)
        echo "🎨 Preset 2: VFX Shader Engine"
        python3 visuales_shader.py
        ;;
    3)
        echo "🎨 Preset 3: Menger Sponge Fractal"
        python3 visuales_shader_3.py
        ;;
    4)
        echo "🎨 Preset 4: Mandelbulb 3D Fractal"
        python3 visuales_shader_4.py
        ;;
    5)
        echo "🎨 Preset 5: Apollonian Gasket"
        python3 visuales_shader_5.py
        ;;
    6)
        echo "🎨 Preset 6: Sierpinski Pyramid"
        python3 visuales_shader_6.py
        ;;
    7)
        echo "🎨 Preset 7: Curl Noise Flow"
        python3 visuales_shader_7.py
        ;;
    8)
        echo "🎨 Preset 8: Magnetic Field Lines"
        python3 visuales_shader_8.py
        ;;
    9)
        echo "🎨 Preset 9: Swarm Intelligence"
        python3 visuales_shader_9.py
        ;;
    10)
        echo "🎨 Preset 10: Turbulence Field"
        python3 visuales_shader_10.py
        ;;
    11)
        echo "🎨 Preset 11: Pixel Sorting Glitch"
        python3 visuales_shader_11.py
        ;;
    12)
        echo "🎨 Preset 12: Datamosh Feedback"
        python3 visuales_shader_12.py
        ;;
    13)
        echo "🎨 Preset 13: RGB Displacement"
        python3 visuales_shader_13.py
        ;;
    14)
        echo "🎨 Preset 14: Scanline Corruption"
        python3 visuales_shader_14.py
        ;;
    15)
        echo "🎨 Preset 15: Voronoi Cells"
        python3 visuales_shader_15.py
        ;;
    16)
        echo "🎨 Preset 16: Reaction-Diffusion"
        python3 visuales_shader_16.py
        ;;
    17)
        echo "🎨 Preset 17: Wave Interference"
        python3 visuales_shader_17.py
        ;;
    18)
        echo "🎨 Preset 18: Truchet Tiles"
        python3 visuales_shader_18.py
        ;;
    19)
        echo "🎨 Preset 19: Quantum Foam"
        python3 visuales_shader_19.py
        ;;
    20)
        echo "🎨 Preset 20: Liquid Metal"
        python3 visuales_shader_20.py
        ;;
    21)
        echo "🎨 Preset 21: Crystal Growth"
        python3 visuales_shader_21.py
        ;;
    22)
        echo "🎨 Preset 22: Neural Noise"
        python3 visuales_shader_22.py
        ;;
    23)
        echo "🎨 Preset 23: Fractal Morphing (Bassline Reactive)"
        python3 visuales_shader_23.py
        ;;
    24)
        echo "🎨 Preset 24: Fractal Tunnel (Bassline Reactive)"
        python3 visuales_shader_24.py
        ;;
    25)
        echo "🎨 Preset 25: Oscilloscope Glitch (Audio Reactive)"
        python3 visuales_shader_25.py
        ;;
    26)
        echo "🎨 Preset 26: Ethereal Particle Organism (Audio Reactive)"
        python3 visuales_shader_26.py
        ;;
    27)
        echo "🎨 Preset 27: Radial Frequency Scope (Audio Reactive)"
        python3 visuales_shader_27.py
        ;;
    28)
        echo "🎨 Preset 28: Neon Kinetic Mandala (Audio Reactive)"
        python3 visuales_shader_28.py
        ;;
    29)
        echo "🎨 Preset 29: Particle Constellation (Audio Reactive)"
        python3 visuales_shader_29.py
        ;;
    30)
        echo "🎨 Preset 30: Cosmic Swirl VFX (Audio Reactive)"
        python3 visuales_shader_30.py
        ;;
    31)
        echo "🎨 Preset 31: Triple Oscilloscope (Audio Reactive)"
        python3 visuales_shader_31.py
        ;;
    32)
        echo "🎨 Preset 32: Geometric Minimalism (Audio Reactive)"
        python3 visuales_shader_32.py
        ;;
    33)
        echo "🎨 Preset 33: Organic Fluid (Audio Reactive)"
        python3 visuales_shader_33.py
        ;;
    34)
        echo "🎨 Preset 34: Atmospheric Particles (Audio Reactive)"
        python3 visuales_shader_34.py
        ;;
    35)
        echo "🎨 Preset 35: Synthwave Retro (Audio Reactive)"
        python3 visuales_shader_35.py
        ;;
    36)
        echo "🎨 Preset 36: Mandelbrot Glitch 3D (Audio + MIDI)"
        python3 visuales_shader_36.py
        ;;
    37)
        echo "🎨 Preset 37: Desert Swarm (Sand Particles & Sun Rays)"
        python3 visuales_shader_37.py
        ;;
    list)
        echo "Lista completa de presets disponibles:"
        ./list_presets.sh
        exit 0
        ;;
    *)
        echo "❌ Preset inválido: $PRESET"
        echo "Uso: ./run.sh [1-31|list]"
        echo "Ejecuta './run.sh list' para ver todos los presets disponibles"
        exit 1
        ;;
esac
