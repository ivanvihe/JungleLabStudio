# visuals/presets/intro_background.py
import logging
import numpy as np
import ctypes
import time
import math
import random
import string
from OpenGL.GL import *
from ..base_visualizer import BaseVisualizer

class IntroBackgroundVisualizer(BaseVisualizer):
    visual_name = "Intro Background"
    
    def __init__(self):
        super().__init__()
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.start_time = time.time()
        self.initialized = False
        
        # Grid configuration
        self.grid_width = 80
        self.grid_height = 25
        self.total_chars = self.grid_width * self.grid_height
        
        # Character data arrays
        self.current_chars = []  # Current characters displayed
        self.target_chars = []   # Target characters to transition to
        self.transition_progress = []  # 0.0 to 1.0 transition progress
        self.last_change_time = []  # When each character last changed
        
        # Animation state
        self.fill_progress = 0.0  # How much of screen is filled (0.0 to 1.0)
        self.fill_speed = 0.5     # Characters per second during fill
        self.reveal_started = False
        self.reveal_pending = False
        self.reveal_progress = 0.0
        
        # Control parameters
        self.fill_rate = 1.0
        self.change_frequency = 1.0
        self.transition_speed = 2.0
        self.brightness = 1.0
        
        # Character set
        self.charset = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # ROBOTICA reveal
        self.robotica_text = "ROBOTICA"
        self.robotica_positions = []
        
        logging.info("IntroBackgroundVisualizer created")

    def initializeGL(self):
        """Initialize OpenGL resources"""
        try:
            logging.debug("IntroBackgroundVisualizer.initializeGL called")
            
            # Clear any existing GL errors
            while glGetError() != GL_NO_ERROR:
                pass
            
            # Set up OpenGL state - black background
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glDisable(GL_DEPTH_TEST)
            
            # Initialize character grid
            self.init_character_grid()
            
            # Load shaders
            if not self.load_shaders():
                logging.error("Failed to load shaders")
                return
            
            # Setup geometry
            if not self.setup_geometry():
                logging.error("Failed to setup geometry")
                return
            
            self.initialized = True
            logging.info("✅ IntroBackgroundVisualizer initialized successfully")
            
        except Exception as e:
            logging.error(f"Error in IntroBackgroundVisualizer.initializeGL: {e}")
            import traceback
            traceback.print_exc()

    def init_character_grid(self):
        """Initialize the character grid"""
        self.current_chars = [' '] * self.total_chars
        self.target_chars = [' '] * self.total_chars
        self.transition_progress = [1.0] * self.total_chars
        self.last_change_time = [0.0] * self.total_chars
        
        # Calculate ROBOTICA positions (center of screen)
        self.center_row = self.grid_height // 2
        self.text_length = len(self.robotica_text)
        self.start_col = (self.grid_width - self.text_length) // 2

        self.robotica_positions = []
        for i, char in enumerate(self.robotica_text):
            col = self.start_col + i
            index = self.center_row * self.grid_width + col
            self.robotica_positions.append(index)

    def load_shaders(self):
        """Load and compile shaders for character rendering"""
        try:
            vertex_shader_source = """
            #version 330 core
            layout (location = 0) in vec2 aPos;
            layout (location = 1) in vec2 aTexCoord;
            layout (location = 2) in float aChar;
            layout (location = 3) in float aTransition;
            
            uniform float time;
            uniform float brightness;
            
            out vec2 texCoord;
            out float charCode;
            out float transition;
            out vec3 color;
            
            void main()
            {
                gl_Position = vec4(aPos, 0.0, 1.0);
                texCoord = aTexCoord;
                charCode = aChar;
                transition = aTransition;
                
                // Colorful characters on black background
                float rand = fract(sin(dot(aPos.xy, vec2(12.9898, 78.233)) + aChar) * 43758.5453);
                vec3 baseColor = vec3(fract(rand + 0.31), fract(rand + 0.63), fract(rand + 0.97));
                float alpha = brightness * (0.8 + 0.2 * sin(time * 2.0 + aPos.x * 10.0));
                color = baseColor * alpha;
            }
            """
            
            fragment_shader_source = """
            #version 330 core
            in vec2 texCoord;
            in float charCode;
            in float transition;
            in vec3 color;
            
            out vec4 FragColor;
            
            // Simple character rendering using texture coordinates
            float drawChar(vec2 uv, float c) {
                // Very basic character rendering
                // We'll create simple shapes for different character codes
                vec2 p = uv * 2.0 - 1.0; // Convert to -1,1 range
                
                float char_alpha = 0.0;
                
                // Different patterns for different character ranges
                float char_mod = mod(c, 10.0);
                
                if (char_mod < 2.0) {
                    // Rectangle pattern
                    char_alpha = step(abs(p.x), 0.6) * step(abs(p.y), 0.8);
                } else if (char_mod < 4.0) {
                    // Circle pattern
                    char_alpha = 1.0 - smoothstep(0.4, 0.6, length(p));
                } else if (char_mod < 6.0) {
                    // Cross pattern
                    char_alpha = step(abs(p.x), 0.2) + step(abs(p.y), 0.2);
                } else if (char_mod < 8.0) {
                    // Diagonal lines
                    float d1 = abs(p.x - p.y);
                    float d2 = abs(p.x + p.y);
                    char_alpha = step(d1, 0.2) + step(d2, 0.2);
                } else {
                    // Dots pattern
                    vec2 grid = floor(p * 3.0);
                    char_alpha = step(mod(grid.x + grid.y, 2.0), 0.5);
                }
                
                return clamp(char_alpha, 0.0, 1.0);
            }
            
            void main()
            {
                float char_alpha = drawChar(texCoord, charCode);
                
                // Apply transition effect (fade/blur)
                float transition_alpha = 1.0;
                if (transition < 1.0) {
                    // Create blur/fade effect during transition
                    vec2 blur_offset = vec2(sin(transition * 3.14159), cos(transition * 3.14159)) * 0.1;
                    float blur_alpha = drawChar(texCoord + blur_offset, charCode);
                    char_alpha = mix(blur_alpha * 0.5, char_alpha, transition);
                    transition_alpha = 0.5 + 0.5 * transition;
                }
                
                vec3 final_color = color;
                float final_alpha = char_alpha * transition_alpha;
                
                FragColor = vec4(final_color, final_alpha);
            }
            """
            
            # Compile vertex shader
            vertex_shader = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vertex_shader, vertex_shader_source)
            glCompileShader(vertex_shader)
            
            if not glGetShaderiv(vertex_shader, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(vertex_shader).decode()
                logging.error(f"Vertex shader compilation failed: {error}")
                return False
            
            # Compile fragment shader
            fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fragment_shader, fragment_shader_source)
            glCompileShader(fragment_shader)
            
            if not glGetShaderiv(fragment_shader, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(fragment_shader).decode()
                logging.error(f"Fragment shader compilation failed: {error}")
                return False
            
            # Link program
            self.shader_program = glCreateProgram()
            glAttachShader(self.shader_program, vertex_shader)
            glAttachShader(self.shader_program, fragment_shader)
            glLinkProgram(self.shader_program)
            
            if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(self.shader_program).decode()
                logging.error(f"Shader program linking failed: {error}")
                return False
            
            # Clean up shaders
            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            
            logging.debug("IntroBackgroundVisualizer shaders compiled successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error loading shaders: {e}")
            return False

    def setup_geometry(self):
        """Setup vertex data for character grid"""
        try:
            # Create vertices for each character position
            vertices = []
            
            self.char_width = 2.0 / self.grid_width
            self.char_height = 2.0 / self.grid_height
            char_width = self.char_width
            char_height = self.char_height
            
            for row in range(self.grid_height):
                for col in range(self.grid_width):
                    # Calculate position (-1 to 1 range)
                    x = -1.0 + (col + 0.5) * char_width
                    y = 1.0 - (row + 0.5) * char_height
                    
                    # Create quad for this character
                    half_w = char_width * 0.4
                    half_h = char_height * 0.4
                    
                    # Triangle 1
                    vertices.extend([
                        x - half_w, y - half_h, 0.0, 0.0, 0.0, 0.0,  # pos, texcoord, char, transition
                        x + half_w, y - half_h, 1.0, 0.0, 0.0, 0.0,
                        x - half_w, y + half_h, 0.0, 1.0, 0.0, 0.0
                    ])
                    
                    # Triangle 2
                    vertices.extend([
                        x + half_w, y - half_h, 1.0, 0.0, 0.0, 0.0,
                        x + half_w, y + half_h, 1.0, 1.0, 0.0, 0.0,
                        x - half_w, y + half_h, 0.0, 1.0, 0.0, 0.0
                    ])
            
            self.vertices = np.array(vertices, dtype=np.float32)
            
            # Create and bind VAO
            self.vao = glGenVertexArrays(1)
            glBindVertexArray(self.vao)
            
            # Create and bind VBO
            self.vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_DYNAMIC_DRAW)
            
            # Set vertex attributes
            stride = 6 * 4  # 6 floats per vertex
            
            # Position
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
            # Texture coordinates
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(2 * 4))
            # Character code
            glEnableVertexAttribArray(2)
            glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(4 * 4))
            # Transition
            glEnableVertexAttribArray(3)
            glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(5 * 4))
            
            # Unbind
            glBindVertexArray(0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            
            logging.debug("IntroBackgroundVisualizer geometry setup complete")
            return True
            
        except Exception as e:
            logging.error(f"Error setting up geometry: {e}")
            return False

    def update_animation(self, current_time):
        """Update the animation state"""
        dt = current_time - (getattr(self, 'last_update_time', 0))
        self.last_update_time = current_time
        
        # Phase 1: Fill screen with random characters
        if self.fill_progress < 1.0:
            self.fill_progress += self.fill_rate * dt
            chars_to_fill = int(self.fill_progress * self.total_chars)
            
            # Add new random characters leaving occasional gaps
            for i in range(min(chars_to_fill, self.total_chars)):
                if self.current_chars[i] == ' ' and random.random() > 0.15:
                    self.current_chars[i] = random.choice(self.charset)
                    self.target_chars[i] = self.current_chars[i]
                    self.transition_progress[i] = 1.0
                    self.last_change_time[i] = current_time
        
        # Phase 2: Random character changes
        for i in range(self.total_chars):
            if self.current_chars[i] != ' ':
                # Check if it's time to change this character
                time_since_change = current_time - self.last_change_time[i]
                change_interval = 2.0 + random.random() * 3.0  # 2-5 seconds as requested
                change_interval /= self.change_frequency
                
                if time_since_change > change_interval and self.transition_progress[i] >= 1.0:
                    # Start transition to new character
                    if i not in self.robotica_positions or not self.reveal_started:
                        self.target_chars[i] = random.choice(self.charset)
                        self.transition_progress[i] = 0.0
                        self.last_change_time[i] = current_time
                
                # Update transition progress
                if self.transition_progress[i] < 1.0:
                    self.transition_progress[i] += self.transition_speed * dt
                    if self.transition_progress[i] >= 1.0:
                        self.transition_progress[i] = 1.0
                        self.current_chars[i] = self.target_chars[i]
        
        # Phase 3: Reveal ROBOTICA when triggered
        if self.reveal_pending and self.fill_progress >= 1.0 and not self.reveal_started:
            self.reveal_started = True
            anim_time = current_time  # use current animation time
            for i, pos in enumerate(self.robotica_positions):
                if i < len(self.robotica_text):
                    self.target_chars[pos] = self.robotica_text[i]
                    self.transition_progress[pos] = 0.0
                    self.last_change_time[pos] = anim_time

    def update_vertex_data(self):
        """Update vertex buffer with current character data"""
        try:
            # Update character codes and transitions in vertex buffer
            vertex_count = self.total_chars * 6  # 6 vertices per character
            
            for char_idx in range(self.total_chars):
                # Get character code
                char_code = ord(self.current_chars[char_idx]) if self.current_chars[char_idx] != ' ' else 32
                transition = self.transition_progress[char_idx]
                
                # Update 6 vertices for this character
                for vertex_idx in range(6):
                    base_idx = (char_idx * 6 + vertex_idx) * 6  # 6 floats per vertex
                    self.vertices[base_idx + 4] = float(char_code)  # Character code
                    self.vertices[base_idx + 5] = transition  # Transition progress
            
            # Upload to GPU
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferSubData(GL_ARRAY_BUFFER, 0, self.vertices.nbytes, self.vertices)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            
        except Exception as e:
            logging.error(f"Error updating vertex data: {e}")

    def draw_robotica_background(self):
        """Draw semi-transparent backdrop and border for ROBOTICA text"""
        try:
            char_w = getattr(self, 'char_width', 2.0 / self.grid_width)
            char_h = getattr(self, 'char_height', 2.0 / self.grid_height)
            x_start = -1.0 + (self.start_col - 0.5) * char_w
            x_end = x_start + (self.text_length + 1.0) * char_w
            y_top = 1.0 - (self.center_row - 0.5) * char_h
            y_bottom = y_top - (1.5 * char_h)

            # Background rectangle
            glColor4f(0.0, 0.0, 0.0, 0.5)
            glBegin(GL_TRIANGLE_FAN)
            glVertex2f(x_start, y_top)
            glVertex2f(x_end, y_top)
            glVertex2f(x_end, y_bottom)
            glVertex2f(x_start, y_bottom)
            glEnd()

            # Border
            glColor4f(1.0, 1.0, 1.0, 0.8)
            glLineWidth(2.0)
            glBegin(GL_LINE_LOOP)
            glVertex2f(x_start, y_top)
            glVertex2f(x_end, y_top)
            glVertex2f(x_end, y_bottom)
            glVertex2f(x_start, y_bottom)
            glEnd()

            glColor4f(1.0, 1.0, 1.0, 1.0)

        except Exception as e:
            logging.error(f"Error drawing ROBOTICA background: {e}")

    def paintGL(self):
        """Render the visualization"""
        try:
            if not self.initialized or not self.shader_program:
                # Fallback rendering
                glClearColor(0.0, 0.0, 0.0, 1.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return

            # Clear with black background
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)
            
            # Update animation
            current_time = time.time() - self.start_time
            self.update_animation(current_time)
            self.update_vertex_data()

            # Draw overlay background if revealing text
            if self.reveal_started:
                self.draw_robotica_background()

            # Use shader program
            glUseProgram(self.shader_program)
            
            # Update uniforms
            glUniform1f(glGetUniformLocation(self.shader_program, "time"), current_time)
            glUniform1f(glGetUniformLocation(self.shader_program, "brightness"), self.brightness)
            
            # Draw characters
            if self.vao:
                glBindVertexArray(self.vao)
                glDrawArrays(GL_TRIANGLES, 0, self.total_chars * 6)
                glBindVertexArray(0)
            
            # Clean up
            glUseProgram(0)
            
        except Exception as e:
            # Only log errors occasionally to avoid spam
            if not hasattr(self, '_last_error_time') or \
               time.time() - self._last_error_time > 5:
                logging.error(f"IntroBackground paint error: {e}")
                self._last_error_time = time.time()

            # Fallback rendering
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def resizeGL(self, width, height):
        """Handle resize"""
        glViewport(0, 0, width, height)

    def cleanup(self):
        """Clean up OpenGL resources"""
        try:
            logging.debug("Cleaning up IntroBackgroundVisualizer")
            
            # Delete shader program
            if self.shader_program:
                try:
                    if glIsProgram(self.shader_program):
                        glDeleteProgram(self.shader_program)
                except:
                    pass
                finally:
                    self.shader_program = None
            
            # Delete VAO
            if self.vao:
                try:
                    glDeleteVertexArrays(1, [self.vao])
                except:
                    pass
                finally:
                    self.vao = None
            
            # Delete VBO
            if self.vbo:
                try:
                    glDeleteBuffers(1, [self.vbo])
                except:
                    pass
                finally:
                    self.vbo = None
            
            self.initialized = False
            logging.debug("IntroBackgroundVisualizer cleanup complete")
            
        except Exception as e:
            logging.debug(f"Cleanup error (non-critical): {e}")

    def get_controls(self):
        """Return available controls"""
        return {
            "Fill Rate": {
                "type": "slider",
                "min": 1,
                "max": 50,
                "value": int(self.fill_rate * 10),
                "default": 10
            },
            "Change Frequency": {
                "type": "slider",
                "min": 1,
                "max": 50,
                "value": int(self.change_frequency * 10),
                "default": 10
            },
            "Transition Speed": {
                "type": "slider",
                "min": 1,
                "max": 50,
                "value": int(self.transition_speed * 10),
                "default": 20
            },
            "Brightness": {
                "type": "slider",
                "min": 1,
                "max": 20,
                "value": int(self.brightness * 10),
                "default": 10
            }
        }

    def update_control(self, name, value):
        """Update a control value"""
        try:
            if name == "Fill Rate":
                self.fill_rate = value / 10.0
                logging.debug(f"Fill rate updated to {self.fill_rate}")
            elif name == "Change Frequency":
                self.change_frequency = value / 10.0
                logging.debug(f"Change frequency updated to {self.change_frequency}")
            elif name == "Transition Speed":
                self.transition_speed = value / 10.0
                logging.debug(f"Transition speed updated to {self.transition_speed}")
            elif name == "Brightness":
                self.brightness = value / 10.0
                logging.debug(f"Brightness updated to {self.brightness}")
        except Exception as e:
            logging.error(f"Error updating control {name}: {e}")

    def trigger_action(self, action_name):
        """Handle custom actions triggered via MIDI"""
        if action_name == "show_ROBOTICA_text":
            self.reveal_pending = True
