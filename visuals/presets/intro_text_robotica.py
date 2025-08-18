# visuals/presets/intro_text_robotica.py - COMPLETE FIXED VERSION
import logging
import numpy as np
import ctypes
import time
import random
from OpenGL.GL import *  # Legacy fallback
from ..base_visualizer import BaseVisualizer
from ..render_backend import GLBackend

class IntroTextRoboticaVisualizer(BaseVisualizer):
    """Overlay visualizer that displays the text 'R O B O T I C A' with a transparent background."""

    visual_name = "Intro Text ROBOTICA"

    # 5x7 block font patterns for required letters
    LETTER_PATTERNS = {
        "R": [
            "11110",
            "10001",
            "10001",
            "11110",
            "10100",
            "10010",
            "10001",
        ],
        "O": [
            "01110",
            "10001",
            "10001",
            "10001",
            "10001",
            "10001",
            "01110",
        ],
        "B": [
            "11110",
            "10001",
            "10001",
            "11110",
            "10001",
            "10001",
            "11110",
        ],
        "T": [
            "11111",
            "00100",
            "00100",
            "00100",
            "00100",
            "00100",
            "00100",
        ],
        "I": [
            "11111",
            "00100",
            "00100",
            "00100",
            "00100",
            "00100",
            "11111",
        ],
        "C": [
            "01110",
            "10001",
            "10000",
            "10000",
            "10000",
            "10001",
            "01110",
        ],
        "A": [
            "01110",
            "10001",
            "10001",
            "11111",
            "10001",
            "10001",
            "10001",
        ],
    }

    def __init__(self):
        super().__init__()
        self.text = "R O B O T I C A"
        self.initialized = False
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.vertices = None
        self.vertex_count = 0
        
        # Visual parameters
        self.text_alpha = 1.0
        self.text_scale = 1.0
        self.text_color = [1.0, 1.0, 1.0]  # White by default
        
        # Animation parameters for cinematic effect
        self.start_time = None
        self.animation_duration = 15.0  # Total animation duration in seconds
        self.fade_duration = 6.0        # How long each letter takes to fade in (5-10 seconds)
        self.letter_delay = 0.3         # Much faster start between letters
        
        # Letter animation order (random as requested: O T B O I A C R)
        # "R O B O T I C A" -> indices: 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
        #  R   O   B   O   T   I   C   A  (skipping spaces at 1,3,5,7,9,11,13,15)
        #  0   2   4   6   8  10  12  14
        self.animation_order = [2, 8, 4, 6, 10, 14, 12, 0]  # O T B O I A C R
        # Corresponds to:     O  T  B  O  I  A  C  R
        
        # Track individual letter alphas for animation
        self.letter_alphas = [0.0] * len(self.text)
        self.letter_start_times = [None] * len(self.text)
        
        logging.info("IntroTextRoboticaVisualizer created")

    def initializeGL(self, backend=None):
        """Initialize OpenGL resources using the provided backend."""
        self.backend = backend or GLBackend()
        try:
            logging.debug("IntroTextRoboticaVisualizer.initializeGL called")

            if not self.load_shaders():
                logging.error("Failed to load shaders")
                return

            if not self.setup_text_geometry():
                logging.error("Failed to setup text geometry")
                return

            self.initialized = True
            logging.info("✅ IntroTextRoboticaVisualizer initialized successfully")

        except Exception as e:
            logging.error(f"Error in IntroTextRoboticaVisualizer.initializeGL: {e}")
            import traceback
            traceback.print_exc()

    def load_shaders(self):
        """Load and compile shaders for text rendering"""
        try:
            vertex_shader_source = """
            #version 330 core
            layout (location = 0) in vec2 aPos;
            layout (location = 1) in float aLetterIndex;

            uniform float globalAlpha;
            uniform float scale;
            uniform vec3 color;
            uniform float letterAlphas[16];  // Max 16 letters including spaces
            uniform float time;

            out vec3 textColor;
            out float textAlpha;

            void main()
            {
                vec2 scaledPos = aPos * scale;
                gl_Position = vec4(scaledPos, 0.0, 1.0);
                textColor = color;

                // Get individual letter alpha
                int letterIdx = int(aLetterIndex);
                float letterAlpha = (letterIdx >= 0 && letterIdx < 16) ? letterAlphas[letterIdx] : 0.0;

                // Add subtle glow effect during fade-in
                float glow = 1.0 + 0.3 * sin(time * 4.0) * letterAlpha;

                textAlpha = globalAlpha * letterAlpha * glow;
            }
            """

            fragment_shader_source = """
            #version 330 core
            in vec3 textColor;
            in float textAlpha;

            out vec4 FragColor;

            void main()
            {
                FragColor = vec4(textColor, textAlpha);
            }
            """

            self.shader_program = self.backend.program(
                vertex_shader_source, fragment_shader_source
            )

            logging.debug("IntroTextRoboticaVisualizer shaders compiled successfully")
            return True

        except Exception as e:
            logging.error(f"Error loading shaders: {e}")
            return False

    def setup_text_geometry(self):
        """Setup vertex data for the text 'ROBOTICA' - FIXED SIZE"""
        try:
            vertices = []

            letter_height = 0.18
            cell_size = letter_height / 7.0
            letter_width = 5 * cell_size
            letter_spacing = cell_size * 0.6
            word_spacing = cell_size * 1.8

            total_width = 0.0
            for char in self.text:
                if char == ' ':
                    total_width += word_spacing
                else:
                    total_width += letter_width + letter_spacing
            total_width -= letter_spacing

            start_x = -total_width / 2.0
            start_y = -letter_height / 2.0

            current_x = start_x
            letter_index = 0

            for char_idx, char in enumerate(self.text):
                if char == ' ':
                    current_x += word_spacing
                    continue

                pattern = self.LETTER_PATTERNS.get(char)
                if pattern:
                    letter_vertices = self.generate_letter_vertices(
                        pattern, current_x, start_y, cell_size, char_idx
                    )
                    vertices.extend(letter_vertices)

                current_x += letter_width + letter_spacing
                letter_index += 1

            if not vertices:
                logging.error("No vertices generated for text")
                return False

            self.vertices = np.array(vertices, dtype=np.float32)
            self.vertex_count = len(vertices) // 3

            self.vbo = self.backend.buffer(self.vertices.tobytes())
            self.vao = self.backend.vertex_array(
                self.shader_program,
                [(self.vbo, '2f 1f', 'aPos', 'aLetterIndex')],
            )

            logging.debug(f"Text geometry setup complete: {self.vertex_count} vertices")
            return True

        except Exception as e:
            logging.error(f"Error setting up text geometry: {e}")
            return False

    def generate_letter_vertices(self, pattern, start_x, start_y, cell_size, letter_index):
        """Generate vertices for a single letter based on its pattern"""
        vertices = []
        
        for row_idx, row_data in enumerate(pattern):
            for col_idx, pixel in enumerate(row_data):
                if pixel == '1':
                    # Calculate cell position
                    x = start_x + col_idx * cell_size
                    y = start_y + (len(pattern) - row_idx - 1) * cell_size
                    
                    # Create a quad (2 triangles) for this cell
                    # Each vertex: [x, y, letterIndex]
                    
                    # Triangle 1
                    vertices.extend([
                        x, y, float(letter_index),                           # Bottom-left
                        x + cell_size, y, float(letter_index),              # Bottom-right
                        x, y + cell_size, float(letter_index)               # Top-left
                    ])
                    
                    # Triangle 2
                    vertices.extend([
                        x + cell_size, y, float(letter_index),              # Bottom-right
                        x + cell_size, y + cell_size, float(letter_index),  # Top-right
                        x, y + cell_size, float(letter_index)               # Top-left
                    ])
        
        return vertices

    def update_animation(self, current_time):
        """Update the cinematic letter animation"""
        if self.start_time is None:
            self.start_time = current_time
            # Initialize letter start times based on animation order
            for i, letter_idx in enumerate(self.animation_order):
                if letter_idx < len(self.text) and self.text[letter_idx] != ' ':
                    # Much faster start with less randomness
                    delay = i * self.letter_delay + random.uniform(-0.1, 0.1)
                    self.letter_start_times[letter_idx] = self.start_time + delay
                    logging.debug(f"Letter {self.text[letter_idx]} (idx {letter_idx}) will start at {delay:.2f}s")
        
        # Update each letter's alpha based on its start time
        for letter_idx, start_time in enumerate(self.letter_start_times):
            if start_time is not None and current_time >= start_time:
                # Calculate fade progress
                fade_progress = (current_time - start_time) / self.fade_duration
                fade_progress = min(1.0, max(0.0, fade_progress))
                
                # Smooth fade curve (ease-out)
                fade_progress = 1.0 - (1.0 - fade_progress) ** 2
                
                self.letter_alphas[letter_idx] = fade_progress
                
                # Debug logging for first few seconds
                if fade_progress < 1.0:
                    logging.debug(f"Letter {self.text[letter_idx]} fade: {fade_progress:.2f}")
    
    def reset_animation(self):
        """Reset the animation to start from beginning"""
        self.start_time = None
        self.letter_alphas = [0.0] * len(self.text)
        self.letter_start_times = [None] * len(self.text)
        logging.info("Animation reset - all letters will restart")

    def paintGL(self, current_time=0.0, size=None, backend=None):
        """Render the text using the backend with cinematic animation"""
        backend = backend or self.backend or GLBackend()
        try:
            if not self.initialized or not self.shader_program or not self.vao:
                backend.clear(0.0, 0.0, 0.0, 0.0)
                return

            backend.clear(0.0, 0.0, 0.0, 0.0)

            self.update_animation(current_time)

            backend.uniform(self.shader_program, "globalAlpha", self.text_alpha)
            backend.uniform(self.shader_program, "scale", self.text_scale)
            backend.uniform(self.shader_program, "color", self.text_color)
            backend.uniform(self.shader_program, "time", current_time)

            alphas_array = self.letter_alphas + [0.0] * (16 - len(self.letter_alphas))
            backend.uniform(self.shader_program, "letterAlphas", alphas_array)

            self.vao.render()

        except Exception as e:
            if not hasattr(self, '_last_error_time') or \
               time.time() - self._last_error_time > 5:
                logging.error(f"IntroTextRobotica paint error: {e}")
                self._last_error_time = time.time()

            backend.clear(0.0, 0.0, 0.0, 0.0)

    def resizeGL(self, width, height, backend=None):
        """Handle resize"""
        if backend:
            backend.set_viewport(0, 0, width, height)
        else:
            glViewport(0, 0, width, height)

    def cleanup(self):
        """Clean up OpenGL resources"""
        try:
            logging.debug("Cleaning up IntroTextRoboticaVisualizer")

            if self.vao:
                if hasattr(self.vao, "release"):
                    try:
                        self.vao.release()
                    except Exception:
                        pass
                else:
                    try:
                        glDeleteVertexArrays(1, [self.vao.vao])
                    except Exception:
                        pass
                self.vao = None

            if self.vbo:
                if hasattr(self.vbo, "release"):
                    try:
                        self.vbo.release()
                    except Exception:
                        pass
                else:
                    try:
                        glDeleteBuffers(1, [self.vbo.buffer_id])
                    except Exception:
                        pass
                self.vbo = None

            if self.shader_program:
                if hasattr(self.shader_program, "release"):
                    try:
                        self.shader_program.release()
                    except Exception:
                        pass
                else:
                    try:
                        if glIsProgram(self.shader_program):
                            glDeleteProgram(self.shader_program)
                    except Exception:
                        pass
                self.shader_program = None

            self.initialized = False
            logging.debug("IntroTextRoboticaVisualizer cleanup complete")

        except Exception as e:
            logging.debug(f"Cleanup error (non-critical): {e}")

    def get_controls(self):
        """Return available controls"""
        return {
            "Text Alpha": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.text_alpha * 100),
                "default": 100
            },
            "Text Scale": {
                "type": "slider",
                "min": 10,
                "max": 200,
                "value": int(self.text_scale * 100),
                "default": 100
            },
            "Animation Speed": {
                "type": "slider",
                "min": 10,
                "max": 100,
                "value": int((1.0 - self.letter_delay) * 100),  # Fixed calculation
                "default": 70
            },
            "Fade Duration": {
                "type": "slider",
                "min": 20,
                "max": 100,
                "value": int(self.fade_duration * 10),
                "default": 60
            },
            "Red": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.text_color[0] * 100),
                "default": 100
            },
            "Green": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.text_color[1] * 100),
                "default": 100
            },
            "Blue": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.text_color[2] * 100),
                "default": 100
            }
        }

    def update_control(self, name, value):
        """Update a control value"""
        try:
            if name == "Text Alpha":
                self.text_alpha = value / 100.0
                logging.debug(f"Text alpha updated to {self.text_alpha}")
            elif name == "Text Scale":
                self.text_scale = value / 100.0
                logging.debug(f"Text scale updated to {self.text_scale}")
            elif name == "Animation Speed":
                self.letter_delay = 1.0 - (value / 100.0)  # Fixed: higher value = faster
                logging.debug(f"Animation speed updated: letter_delay = {self.letter_delay}")
            elif name == "Fade Duration":
                self.fade_duration = value / 10.0
                logging.debug(f"Fade duration updated to {self.fade_duration}")
            elif name == "Red":
                self.text_color[0] = value / 100.0
                logging.debug(f"Red color updated to {self.text_color[0]}")
            elif name == "Green":
                self.text_color[1] = value / 100.0
                logging.debug(f"Green color updated to {self.text_color[1]}")
            elif name == "Blue":
                self.text_color[2] = value / 100.0
                logging.debug(f"Blue color updated to {self.text_color[2]}")
        except Exception as e:
            logging.error(f"Error updating control {name}: {e}")
    
    def trigger_action(self, action_name):
        """Handle custom actions triggered via MIDI"""
        if action_name == "restart_animation":
            self.reset_animation()
            logging.info("Animation restarted")
