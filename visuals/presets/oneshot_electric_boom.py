# visuals/presets/oneshot_electric_boom.py
import logging
import numpy as np
import ctypes
import time
import math
import random
from OpenGL.GL import *
from ..base_visualizer import BaseVisualizer

class OneshotElectricBoomVisualizer(BaseVisualizer):
    """One-shot electric explosion with shockwave for cinematic bass drops"""
    
    visual_name = "Oneshot Electric Boom"
    
    def __init__(self):
        super().__init__()
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.start_time = time.time()
        self.initialized = False

        # Electric explosion state
        self.explosions = []
        self.max_explosions = 2
        
        # Visual parameters
        self.intensity = 1.0
        self.size_multiplier = 1.0
        self.electric_mode = 0  # 0=blue, 1=white, 2=rainbow
        
        # Pre-generate explosion data
        self.vertices = None
        self.vertex_count = 0
        
        logging.info("OneshotElectricBoomVisualizer created")
        
        # Auto-trigger the electric explosion on creation
        self.create_electric_explosion()

    def initializeGL(self):
        """Initialize OpenGL resources"""
        try:
            logging.debug("OneshotElectricBoomVisualizer.initializeGL called")
            
            # Clear any existing GL errors
            while glGetError() != GL_NO_ERROR:
                pass
            
            # Set up OpenGL state
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
            logging.info("⚡ OneshotElectricBoomVisualizer initialized successfully")
            
        except Exception as e:
            logging.error(f"Error in OneshotElectricBoomVisualizer.initializeGL: {e}")
            import traceback
            traceback.print_exc()

    def load_shaders(self):
        """Load and compile electric explosion shaders"""
        try:
            # Electric explosion vertex shader
            vertex_shader_source = """
            #version 330 core
            layout (location = 0) in vec2 aPos;
            layout (location = 1) in vec2 aTexCoord;
            layout (location = 2) in float aAge;
            layout (location = 3) in vec3 aColor;
            layout (location = 4) in float aType; // 0=lightning, 1=shockwave, 2=spark
            
            uniform float time;
            uniform float intensity;
            
            out vec2 texCoord;
            out vec3 color;
            out float alpha;
            out float effectType;
            out float age;
            
            void main()
            {
                vec2 pos = aPos;
                
                // Add electric jitter for lightning bolts
                if (aType < 0.5) { // Lightning
                    float jitter = sin(time * 50.0 + aPos.x * 100.0) * 0.02 * (1.0 - aAge / 4.0);
                    pos.x += jitter;
                    pos.y += sin(time * 30.0 + aPos.y * 80.0) * 0.015 * (1.0 - aAge / 4.0);
                }
                
                gl_Position = vec4(pos, 0.0, 1.0);
                texCoord = aTexCoord;
                color = aColor;
                effectType = aType;
                age = aAge;
                
                // Different fade patterns for different effects
                if (aType < 0.5) { // Lightning - quick flash
                    alpha = (1.0 - smoothstep(0.0, 1.5, aAge)) * intensity;
                } else if (aType < 1.5) { // Shockwave - slower fade
                    alpha = (1.0 - smoothstep(0.0, 3.0, aAge)) * intensity * 0.7;
                } else { // Sparks - medium fade
                    alpha = (1.0 - smoothstep(0.0, 2.0, aAge)) * intensity;
                }
            }
            """
            
            # Electric explosion fragment shader
            fragment_shader_source = """
            #version 330 core
            in vec2 texCoord;
            in vec3 color;
            in float alpha;
            in float effectType;
            in float age;
            
            uniform float time;
            
            out vec4 FragColor;
            
            // Electric noise function
            float electricNoise(vec2 uv, float scale) {
                return fract(sin(dot(uv * scale, vec2(12.9898, 78.233))) * 43758.5453);
            }
            
            // Lightning bolt pattern
            float lightningBolt(vec2 uv) {
                vec2 center = uv - vec2(0.5);
                float angle = atan(center.y, center.x);
                float dist = length(center);
                
                // Create jagged lightning pattern
                float lightning = 0.0;
                for (int i = 0; i < 3; i++) {
                    float freq = float(i + 1) * 10.0;
                    float noise = electricNoise(vec2(angle * freq, dist * freq + time * 2.0), 1.0);
                    lightning += noise * (1.0 / float(i + 1));
                }
                
                // Make it more bolt-like
                float bolt = 1.0 - smoothstep(0.0, 0.3, abs(center.x + sin(center.y * 20.0 + time * 5.0) * 0.1));
                bolt *= 1.0 - smoothstep(0.4, 0.8, dist);
                bolt *= lightning;
                
                return bolt;
            }
            
            // Shockwave ring
            float shockwave(vec2 uv) {
                vec2 center = uv - vec2(0.5);
                float dist = length(center);
                
                // Expanding ring
                float ring_radius = age * 0.4;
                float ring_thickness = 0.05 + age * 0.02;
                float ring = 1.0 - smoothstep(ring_radius - ring_thickness, ring_radius, dist);
                ring *= smoothstep(ring_radius, ring_radius + ring_thickness, dist);
                
                // Add electric distortion
                float distortion = sin(atan(center.y, center.x) * 16.0 + time * 10.0) * 0.02;
                ring *= 1.0 + distortion;
                
                return ring;
            }
            
            // Electric spark
            float electricSpark(vec2 uv) {
                vec2 center = uv - vec2(0.5);
                float dist = length(center);
                
                // Pulsing electric sphere
                float pulse = sin(time * 20.0 + dist * 50.0) * 0.3 + 0.7;
                float spark = 1.0 - smoothstep(0.0, 0.2, dist);
                spark *= pulse;
                
                // Add electric crackling
                float crackle = electricNoise(uv * 20.0 + time * 5.0, 1.0);
                spark *= 0.7 + crackle * 0.3;
                
                return spark;
            }
            
            void main()
            {
                float effect = 0.0;
                
                if (effectType < 0.5) { // Lightning
                    effect = lightningBolt(texCoord);
                } else if (effectType < 1.5) { // Shockwave
                    effect = shockwave(texCoord);
                } else { // Sparks
                    effect = electricSpark(texCoord);
                }
                
                // Add electric glow
                vec3 finalColor = color;
                if (effectType < 0.5) { // Lightning - bright white core
                    finalColor = mix(color, vec3(1.0), effect * 0.5);
                } else if (effectType < 1.5) { // Shockwave - electric blue
                    finalColor = mix(color, vec3(0.3, 0.7, 1.0), effect * 0.3);
                }
                
                FragColor = vec4(finalColor, effect * alpha);
            }
            """
            
            # Compile shaders
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
            
            logging.debug("Electric explosion shaders compiled successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error loading shaders: {e}")
            return False

    def setup_geometry(self):
        """Setup vertex data"""
        try:
            # Start empty
            self.vertices = np.array([0.0], dtype=np.float32)
            
            # Create and bind VAO
            self.vao = glGenVertexArrays(1)
            glBindVertexArray(self.vao)
            
            # Create and bind VBO
            self.vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            
            # Reserve space for electric effects
            max_elements = 200  # More elements for complex electric effects
            vertex_size = 9 * 4  # 9 floats per vertex * 4 bytes
            glBufferData(GL_ARRAY_BUFFER, max_elements * vertex_size * 6, None, GL_DYNAMIC_DRAW)
            
            # Set vertex attributes
            stride = 9 * 4  # 9 floats per vertex
            
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
            # Effect type (1 float)
            glEnableVertexAttribArray(4)
            glVertexAttribPointer(4, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8 * 4))
            
            # Unbind
            glBindVertexArray(0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            
            logging.debug("Electric explosion geometry setup complete")
            return True
            
        except Exception as e:
            logging.error(f"Error setting up geometry: {e}")
            return False

    def create_electric_explosion(self, center_x=None, center_y=None):
        """Create a new electric explosion with shockwave"""
        current_time = time.time() - self.start_time
        
        # Remove old explosions
        self.explosions = [exp for exp in self.explosions 
                          if (current_time - exp['birth_time']) < 4.0]
        
        # Don't create if at max
        if len(self.explosions) >= self.max_explosions:
            self.explosions.pop(0)
        
        # Random position if not specified
        if center_x is None:
            center_x = random.uniform(-0.3, 0.3)
        if center_y is None:
            center_y = random.uniform(-0.3, 0.3)
        
        # Create electric explosion
        explosion = {
            'center': (center_x, center_y),
            'birth_time': current_time,
            'elements': []
        }
        
        # Get colors based on mode
        if self.electric_mode == 0:  # Blue electric
            base_colors = [(0.2, 0.8, 1.0), (0.0, 0.5, 1.0), (0.6, 0.9, 1.0)]
        elif self.electric_mode == 1:  # White electric
            base_colors = [(1.0, 1.0, 1.0), (0.8, 0.8, 1.0), (0.9, 0.9, 0.9)]
        else:  # Rainbow electric
            base_colors = [(1.0, 0.0, 0.5), (0.0, 1.0, 0.8), (0.8, 0.0, 1.0)]
        
        # Create lightning bolts (type 0)
        for i in range(8):
            angle = random.uniform(0, 2 * math.pi)
            length = random.uniform(0.3, 0.8)
            
            end_x = center_x + math.cos(angle) * length
            end_y = center_y + math.sin(angle) * length
            
            color = random.choice(base_colors)
            
            element = {
                'type': 0,  # Lightning
                'start': (center_x, center_y),
                'end': (end_x, end_y),
                'color': color,
                'birth_time': current_time
            }
            explosion['elements'].append(element)
        
        # Create shockwave (type 1)
        shockwave = {
            'type': 1,  # Shockwave
            'center': (center_x, center_y),
            'color': base_colors[0],
            'birth_time': current_time
        }
        explosion['elements'].append(shockwave)
        
        # Create electric sparks (type 2)
        for i in range(12):
            spark_x = center_x + random.uniform(-0.4, 0.4)
            spark_y = center_y + random.uniform(-0.4, 0.4)
            
            spark = {
                'type': 2,  # Spark
                'pos': (spark_x, spark_y),
                'color': random.choice(base_colors),
                'birth_time': current_time + random.uniform(0, 0.5)  # Delayed sparks
            }
            explosion['elements'].append(spark)
        
        self.explosions.append(explosion)
        logging.info(f"⚡ Created ELECTRIC explosion at ({center_x:.2f}, {center_y:.2f})")

    def update_vertex_data(self):
        """Update vertex buffer with electric effects"""
        try:
            current_time = time.time() - self.start_time
            vertices = []
            
            for explosion in self.explosions:
                for element in explosion['elements']:
                    age = current_time - element['birth_time']
                    
                    # Skip elements that haven't started or are too old
                    if age < 0 or age > 4.0:
                        continue
                    
                    element_type = float(element['type'])
                    r, g, b = element['color']
                    
                    if element['type'] == 0:  # Lightning bolt
                        start_x, start_y = element['start']
                        end_x, end_y = element['end']
                        
                        # Create thick line as quad
                        thickness = 0.02 * (1.0 - age / 2.0)  # Shrinking thickness
                        
                        # Calculate perpendicular vector
                        dx = end_x - start_x
                        dy = end_y - start_y
                        length = math.sqrt(dx*dx + dy*dy)
                        if length > 0:
                            perpx = -dy / length * thickness
                            perpy = dx / length * thickness
                        else:
                            perpx = perpy = 0
                        
                        # Create quad for lightning bolt
                        vertices.extend([
                            start_x - perpx, start_y - perpy, 0.0, 0.0, age, r, g, b, element_type,
                            start_x + perpx, start_y + perpy, 1.0, 0.0, age, r, g, b, element_type,
                            end_x - perpx, end_y - perpy, 0.0, 1.0, age, r, g, b, element_type,
                            
                            start_x + perpx, start_y + perpy, 1.0, 0.0, age, r, g, b, element_type,
                            end_x + perpx, end_y + perpy, 1.0, 1.0, age, r, g, b, element_type,
                            end_x - perpx, end_y - perpy, 0.0, 1.0, age, r, g, b, element_type
                        ])
                    
                    elif element['type'] == 1:  # Shockwave
                        center_x, center_y = element['center']
                        size = 0.8  # Large shockwave
                        
                        # Create quad for shockwave
                        vertices.extend([
                            center_x - size, center_y - size, 0.0, 0.0, age, r, g, b, element_type,
                            center_x + size, center_y - size, 1.0, 0.0, age, r, g, b, element_type,
                            center_x - size, center_y + size, 0.0, 1.0, age, r, g, b, element_type,
                            
                            center_x + size, center_y - size, 1.0, 0.0, age, r, g, b, element_type,
                            center_x + size, center_y + size, 1.0, 1.0, age, r, g, b, element_type,
                            center_x - size, center_y + size, 0.0, 1.0, age, r, g, b, element_type
                        ])
                    
                    elif element['type'] == 2:  # Electric spark
                        spark_x, spark_y = element['pos']
                        size = 0.06
                        
                        # Create quad for spark
                        vertices.extend([
                            spark_x - size, spark_y - size, 0.0, 0.0, age, r, g, b, element_type,
                            spark_x + size, spark_y - size, 1.0, 0.0, age, r, g, b, element_type,
                            spark_x - size, spark_y + size, 0.0, 1.0, age, r, g, b, element_type,
                            
                            spark_x + size, spark_y - size, 1.0, 0.0, age, r, g, b, element_type,
                            spark_x + size, spark_y + size, 1.0, 1.0, age, r, g, b, element_type,
                            spark_x - size, spark_y + size, 0.0, 1.0, age, r, g, b, element_type
                        ])
            
            if vertices:
                self.vertices = np.array(vertices, dtype=np.float32)
                self.vertex_count = len(vertices) // 9
                
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
        """Render electric explosion"""
        try:
            if not self.initialized or not self.shader_program:
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
                logging.error(f"ElectricBoom paint error: {e}")
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
            logging.debug("Cleaning up OneshotElectricBoomVisualizer")
            
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
            "Electric Mode": {
                "type": "slider",
                "min": 0,
                "max": 2,
                "value": self.electric_mode,
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
            elif name == "Electric Mode":
                self.electric_mode = int(value)
        except Exception as e:
            logging.error(f"Error updating control {name}: {e}")

    def trigger_action(self, action_name):
        """Handle MIDI triggers"""
        if action_name == "boom" or action_name == "explosion" or action_name == "electric":
            self.create_electric_explosion()
            logging.info("⚡ ELECTRIC BOOM! Triggered via MIDI")