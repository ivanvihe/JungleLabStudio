"""
Configuración del Visual Engine Minimal
Ajusta estos parámetros para cambiar el comportamiento
"""

# Resolución y FPS
WIDTH = 1080  # Instagram Reels vertical
HEIGHT = 1920
TARGET_FPS = 60

# Forma generativa base
BASE_RADIUS = 100  # Radio base en píxeles
INITIAL_SIDES = 6  # Número inicial de lados (hexágono)

# Colores minimal
GRAY = (120, 120, 120)  # Forma principal
DARK_GRAY = (80, 80, 80)  # Ecos/glitch
BLACK = (0, 0, 0)  # Fondo

# Kick (pulso)
KICK_EXPANSION_MAX = 0.4  # Expansión máxima (40%)
KICK_PULSE_STRENGTH = 0.8  # Fuerza del pulso
PULSE_INTERPOLATION = 0.15  # Velocidad de interpolación del pulso
PULSE_DECAY = 0.92  # Decay del pulso
RADIUS_INTERPOLATION = 0.1  # Velocidad de interpolación del radio
RADIUS_RETURN = 0.08  # Velocidad de retorno al radio base

# Hats (glitch)
HAT_GLITCH_STRENGTH = 0.6  # Intensidad del glitch
HAT_MAX_OFFSET = 30  # Offset máximo en píxeles
HAT_NUM_ECHOES = 8  # Número máximo de ecos
GLITCH_DECAY = 0.88  # Decay de la intensidad del glitch
GLITCH_INTERPOLATION = 0.2  # Velocidad de interpolación de offsets
GLITCH_OFFSET_DECAY = 0.9  # Decay de los offsets

# Toms (transformación)
TOM_SHAPES = [3, 4, 5, 6, 8, 12]  # Geometrías disponibles
TOM_ROTATION_MAX = 3.0  # Velocidad máxima de rotación (grados/frame)
ROTATION_FRICTION = 0.98  # Fricción de la rotación

# Ruido orgánico
NOISE_AMPLITUDE = 8  # Amplitud del ruido sinusoidal
NOISE_SPEED = 0.02  # Velocidad del ruido

# Rendering
GLOW_LAYERS = [6, 9]  # Grosor de capas de glow
ALPHA_BASE = 200  # Alpha de la forma base
CENTER_DOT_SIZE = 3  # Tamaño del punto central

# MIDI Notes
KICK_NOTE = 60
CLOSEHAT_NOTE = 62
TOM1_NOTE = 64
TOM2_NOTE = 65

# Debug
MIDI_DEBUG_MESSAGES = 4  # Número de mensajes MIDI a mostrar
SHOW_FPS = True
UI_COLOR = (40, 40, 40)  # Color ultra discreto para UI
