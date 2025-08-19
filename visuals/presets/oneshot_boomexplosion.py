# TODO: migrate to RenderBackend (ModernGL)
# visuals/presets/oneshot_boomexplosion.py
import logging
import numpy as np
import ctypes
import time
import math
import random
from OpenGL.GL import *
from ..base_visualizer import BaseVisualizer

class OneshotBoomExplosionVisualizer(BaseVisualizer):
    """One-shot explosion visual for dramatic booms and bass drops"""
    
    visual_name = "Oneshot Boom Explosion"
    
    def __init__(self):
        super().__init__()
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.start_time = time.time()
        self.initialized = False

        # Explosion state - VERY SIMPLE
        self.explosions = []
        self.max_explosions = 3
        
        # Visual parameters
        self.intensity = 1.0
        self.size_multiplier = 1.0
        self.color_mode = 0
        
        # Pre-generate explosion data to avoid runtime issues
        self.vertices = None
        self.vertex_count = 0
        
        logging.info("OneshotBoomExplosionVisualizer created")
        
        # Auto-trigger the explosion on creation for one-shot behavior
        self.create_explosion()

    def initializeGL(self):
        """Initialize OpenGL resources - EXACTLY like intro_background"""
        try:
            logging.debug("OneshotBoomExplosionVisualizer.initializeGL called")
            
            # Clear any existing GL errors
            while glGetError() != GL_NO_ERROR:
                pass
            
            # Set up OpenGL state - EXACTLY like intro_background
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glDisable(GL_DEPTH_TEST)
            
            # Load shaders
            if not self.load_shaders():
                logging.error("Failed to load shaders")
                return
            
            # Setup geometry
            if not self.setup_geometry():
                logging.error("Failed to setup geometry")
                return
            
            self.initialized = True
            logging.info("OneshotBoomExplosionVisualizer initialized successfully")
            
        except Exception as e:
            logging.error(f"Error in OneshotBoomExplosionVisualizer.initializeGL: {e}")
            import traceback
            traceback.print_exc()

    def load_shaders(self):
        """Load and compile shaders - ULTRA SIMPLE like intro_background"""
        try:
            # VERY SIMPLE vertex shader - based on intro_background pattern
            vertex_shader_source = """
            #version 330 core
            layout (location = 0) in vec2 aPos;
            layout (location = 1) in vec2 aTexCoord;
            layout (location = 2) in float aAge;
            layout (location = 3) in vec3 aColor;
            
            uniform float time;
            uniform float intensity;
            
            out vec2 texCoord;
            out vec3 color;
            out float alpha;
            
            void main()
            {
                gl_Position = vec4(aPos, 0.0, 1.0);
                texCoord = aTexCoord;
                color = aColor;
                
                // Simple fade based on age
                float fade = 1.0 - smoothstep(0.0, 3.0, aAge);
                alpha = fade * intensity;
            }
            """
            
            # VERY SIMPLE fragment shader
            fragment_shader_source = """
            #version 330 core
            in vec2 texCoord;
            in vec3 color;
            in float alpha;
            
            out vec4 FragColor;
            
            void main()
            {
                // Simple circle
                vec2 center = texCoord - vec2(0.5);
                float dist = length(center);
                float circle = 1.0 - smoothstep(0.0, 0.5, dist);
                
                FragColor = vec4(color, circle * alpha);
            }
            """
            
            # Compile exactly like intro_background
            vertex_shader = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vertex_shader, vertex_shader_source)
            glCompileShader(vertex_shader)
            
            if not glGetShaderiv(vertex_shader, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(vertex_shader).decode()
                logging.error(f"Vertex shader compilation failed: {error}")
                return False
            
            fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fragment_shader, fragment_shader_source)
            glCompileShader(fragment_shader)
            
            if not glGetShaderiv(fragment_shader, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(fragment_shader).decode()
                logging.error(f"Fragment shader compilation failed: {error}")
                return False
            
            self.shader_program = glCreateProgram()
            glAttachShader(self.shader_program, vertex_shader)
            glAttachShader(self.shader_program, fragment_shader)
            glLinkProgram(self.shader_program)
            
            if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(self.shader_program).decode()
                logging.error(f"Shader program linking failed: {error}")
                return False
            
            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            
            logging.debug("OneshotBoomExplosionVisualizer shaders compiled successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error loading shaders: {e}")
            return False

    def setup_geometry(self):
        """Setup vertex data - EXACTLY like intro_background pattern"""
        try:
            # Start with NO particles - like intro_background starts empty
            vertices = []
            
            # Create basic structure for future particles
            self.vertices = np.array([0.0], dtype=np.float32)  # Empty but valid
            
            # Create and bind VAO
            self.vao = glGenVertexArrays(1)
            glBindVertexArray(self.vao)
            
            # Create and bind VBO
            self.vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            
            # Reserve space for particles (but start empty)
            max_particles = 100  # Much smaller number
            vertex_size = 8 * 4  # 8 floats per vertex * 4 bytes
            glBufferData(GL_ARRAY_BUFFER, max_particles * vertex_size * 6, None, GL_DYNAMIC_DRAW)  # 6 vertices per quad
            
            # Set vertex attributes
            stride = 8 * 4  # 8 floats per vertex
            
            # Position (2 floats)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
            # Texture coordinates (2 floats)
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(2 * 4))
            # Age (1 float)
            glEnableVertexAttribArray(2)
            glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(4 * 4))
            # Color (3 floats)
            glEnableVertexAttribArray(3)
            glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(5 * 4))
            
            # Unbind
            glBindVertexArray(0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            
            logging.debug("Explosion geometry setup complete")
            return True
            
        except Exception as e:
            logging.error(f"Error setting up geometry: {e}")
            return False

    def create_explosion(self, center_x=None, center_y=None):
        """Create a new explosion - VERY SIMPLE"""
        current_time = time.time() - self.start_time
        
        # Remove old explosions
        self.explosions = [exp for exp in self.explosions 
                          if (current_time - exp['birth_time']) < 3.0]
        
        # Don't create if at max
        if len(self.explosions) >= self.max_explosions:
            self.explosions.pop(0)
        
        # Random position if not specified
        if center_x is None:
            center_x = random.uniform(-0.5, 0.5)
        if center_y is None:
            center_y = random.uniform(-0.5, 0.5)
        
        # Create simple explosion
        explosion = {
            'center': (center_x, center_y),
            'birth_time': current_time,
            'particles': []
        }
        
        # Generate SIMPLE particles
        for i in range(20):  # Only 20 particles
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(0.1, 0.3)
            
            x = center_x + math.cos(angle) * radius
            y = center_y + math.sin(angle) * radius
            
            # Fire colors
            r = random.uniform(0.8, 1.0)
            g = random.uniform(0.2, 0.6)
            b = random.uniform(0.0, 0.2)
            
            particle = {
                'x': x, 'y': y,
                'r': r, 'g': g, 'b': b,
                'birth_time': current_time
            }
            
            explosion['particles'].append(particle)
        
        self.explosions.append(explosion)
        logging.info(f"Created SIMPLE explosion at ({center_x:.2f}, {center_y:.2f})")

    def update_vertex_data(self):
        """Update vertex buffer - EXACTLY like intro_background"""
        try:
            current_time = time.time() - self.start_time
            vertices = []
            
            for explosion in self.explosions:
                for particle in explosion['particles']:
                    age = current_time - particle['birth_time']
                    
                    # Skip dead particles
                    if age > 3.0:
                        continue
                    
                    # Create a simple quad for this particle
                    size = 0.05  # Fixed size
                    x, y = particle['x'], particle['y']
                    r, g, b = particle['r'], particle['g'], particle['b']
                    
                    # Triangle 1
                    vertices.extend([
                        x - size, y - size, 0.0, 0.0, age, r, g, b,  # Bottom-left
                        x + size, y - size, 1.0, 0.0, age, r, g, b,  # Bottom-right
                        x - size, y + size, 0.0, 1.0, age, r, g, b   # Top-left
                    ])
                    
                    # Triangle 2
                    vertices.extend([
                        x + size, y - size, 1.0, 0.0, age, r, g, b,  # Bottom-right
                        x + size, y + size, 1.0, 1.0, age, r, g, b,  # Top-right
                        x - size, y + size, 0.0, 1.0, age, r, g, b   # Top-left
                    ])
            
            if vertices:
                self.vertices = np.array(vertices, dtype=np.float32)
                self.vertex_count = len(vertices) // 8
                
                # Upload to GPU
                glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
                glBufferSubData(GL_ARRAY_BUFFER, 0, self.vertices.nbytes, self.vertices)
                glBindBuffer(GL_ARRAY_BUFFER, 0)
            else:
                self.vertex_count = 0
            
        except Exception as e:
            logging.error(f"Error updating vertex data: {e}")
            self.vertex_count = 0

    def paintGL(self):
        """Render - EXACTLY like intro_background pattern"""
        try:
            if not self.initialized or not self.shader_program:
                # Fallback rendering
                glClearColor(0.0, 0.0, 0.0, 0.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return

            # Clear with transparent background
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)
            
            # Update vertex data
            self.update_vertex_data()

            if self.vertex_count > 0:
                current_time = time.time() - self.start_time
                
                # Use shader program
                glUseProgram(self.shader_program)
                
                # Update uniforms
                glUniform1f(glGetUniformLocation(self.shader_program, "time"), current_time)
                glUniform1f(glGetUniformLocation(self.shader_program, "intensity"), self.intensity)
                
                # Draw
                if self.vao:
                    glBindVertexArray(self.vao)
                    glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)
                    glBindVertexArray(0)
                
                # Clean up
                glUseProgram(0)
            
        except Exception as e:
            # Only log errors occasionally
            if not hasattr(self, '_last_error_time') or \
               time.time() - self._last_error_time > 5:
                logging.error(f"BoomExplosion paint error: {e}")
                self._last_error_time = time.time()

            # Fallback rendering
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def resizeGL(self, width, height):
        """Handle resize"""
        glViewport(0, 0, width, height)

    def cleanup(self):
        """Clean up OpenGL resources"""
        try:
            logging.debug("Cleaning up OneshotBoomExplosionVisualizer")
            
            if self.shader_program:
                try:
                    if glIsProgram(self.shader_program):
                        glDeleteProgram(self.shader_program)
                except:
                    pass
                finally:
                    self.shader_program = None
            
            if self.vao:
                try:
                    glDeleteVertexArrays(1, [self.vao])
                except:
                    pass
                finally:
                    self.vao = None
            
            if self.vbo:
                try:
                    glDeleteBuffers(1, [self.vbo])
                except:
                    pass
                finally:
                    self.vbo = None
            
            self.initialized = False
            self.explosions = []
            
        except Exception as e:
            logging.debug(f"Cleanup error (non-critical): {e}")

    def get_controls(self):
        """Return available controls"""
        return {
            "Intensity": {
                "type": "slider",
                "min": 10,
                "max": 300,
                "value": int(self.intensity * 100),
                "default": 100
            },
            "Size": {
                "type": "slider",
                "min": 20,
                "max": 300,
                "value": int(self.size_multiplier * 100),
                "default": 100
            },
            "Color Mode": {
                "type": "slider",
                "min": 0,
                "max": 2,
                "value": self.color_mode,
                "default": 0
            }
        }

    def update_control(self, name, value):
        """Update control values"""
        try:
            if name == "Intensity":
                self.intensity = value / 100.0
            elif name == "Size":
                self.size_multiplier = value / 100.0
            elif name == "Color Mode":
                self.color_mode = int(value)
        except Exception as e:
            logging.error(f"Error updating control {name}: {e}")

    def trigger_action(self, action_name):
        """Handle MIDI triggers"""
        if action_name == "boom" or action_name == "explosion":
            self.create_explosion()
            logging.info("BOOM! Simple explosion triggered via MIDI")