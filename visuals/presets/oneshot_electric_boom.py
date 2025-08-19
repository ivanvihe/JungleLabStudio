# TODO: migrate to RenderBackend (ModernGL)
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
    """TouchDesigner-quality subwoofer shockwave visualization"""
    
    visual_name = "Oneshot Electric Boom"
    
    def __init__(self):
        super().__init__()
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.start_time = time.time()
        self.initialized = False

        # Shockwave state
        self.shockwaves = []
        self.max_shockwaves = 3
        
        # Visual parameters
        self.intensity = 1.0
        self.size_multiplier = 1.0
        self.wave_mode = 0  # 0=blue, 1=white, 2=warm
        
        # Pre-generate data
        self.vertices = None
        self.vertex_count = 0
        
        logging.info("TouchDesigner-quality Electric Boom created")
        
        # Auto-trigger on creation
        self.create_shockwave()

    def initializeGL(self):
        """Initialize OpenGL resources"""
        try:
            logging.debug("OneshotElectricBoomVisualizer.initializeGL called")
            
            # Clear any existing GL errors
            while glGetError() != GL_NO_ERROR:
                pass
            
            # Set up OpenGL state for high quality
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
            logging.info("TouchDesigner-quality shockwave initialized")
            
        except Exception as e:
            logging.error(f"Error in initialization: {e}")
            import traceback
            traceback.print_exc()

    def load_shaders(self):
        """Load TouchDesigner-quality shaders"""
        try:
            # High-quality vertex shader
            vertex_shader_source = """
            #version 330 core
            layout (location = 0) in vec2 aPos;
            layout (location = 1) in vec2 aTexCoord;
            layout (location = 2) in float aAge;
            layout (location = 3) in vec2 aCenter;
            layout (location = 4) in vec3 aColor;
            layout (location = 5) in float aRadius;
            
            uniform float time;
            uniform float intensity;
            uniform vec2 resolution;
            
            out vec2 texCoord;
            out vec3 color;
            out float alpha;
            out vec2 center;
            out float radius;
            out float age;
            
            void main()
            {
                gl_Position = vec4(aPos, 0.0, 1.0);
                texCoord = aTexCoord;
                color = aColor;
                center = aCenter;
                radius = aRadius;
                age = aAge;
                
                // Smooth fade with different curves for different wave types
                float fade1 = 1.0 - smoothstep(0.0, 4.0, aAge);
                float fade2 = exp(-aAge * 0.8);
                alpha = mix(fade1, fade2, 0.6) * intensity;
            }
            """
            
            # TouchDesigner-quality fragment shader
            fragment_shader_source = """
            #version 330 core
            in vec2 texCoord;
            in vec3 color;
            in float alpha;
            in vec2 center;
            in float radius;
            in float age;
            
            uniform float time;
            uniform vec2 resolution;
            
            out vec4 FragColor;
            
            // High-quality noise functions
            float hash(vec2 p) {
                return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
            }
            
            float noise(vec2 p) {
                vec2 i = floor(p);
                vec2 f = fract(p);
                vec2 u = f * f * (3.0 - 2.0 * f);
                return mix(mix(hash(i + vec2(0.0, 0.0)), 
                              hash(i + vec2(1.0, 0.0)), u.x),
                          mix(hash(i + vec2(0.0, 1.0)), 
                              hash(i + vec2(1.0, 1.0)), u.x), u.y);
            }
            
            float fbm(vec2 p) {
                float value = 0.0;
                float amplitude = 0.5;
                for (int i = 0; i < 6; i++) {
                    value += amplitude * noise(p);
                    p *= 2.0;
                    amplitude *= 0.5;
                }
                return value;
            }
            
            // TouchDesigner-style shockwave
            float shockwave(vec2 uv, vec2 center, float age, float baseRadius) {
                vec2 toCenter = uv - center;
                float dist = length(toCenter);
                
                // Multiple wave rings for complexity
                float wave = 0.0;
                
                // Main shockwave
                float waveRadius = age * 1.2 * baseRadius;
                float waveThickness = 0.08 + age * 0.02;
                float mainWave = exp(-pow(abs(dist - waveRadius) / waveThickness, 2.0));
                
                // Secondary waves
                float wave2Radius = age * 0.8 * baseRadius;
                float wave2Thickness = 0.06;
                float secondWave = exp(-pow(abs(dist - wave2Radius) / wave2Thickness, 2.0)) * 0.6;
                
                // Tertiary wave
                float wave3Radius = age * 1.5 * baseRadius;
                float wave3Thickness = 0.12;
                float thirdWave = exp(-pow(abs(dist - wave3Radius) / wave3Thickness, 2.0)) * 0.3;
                
                wave = mainWave + secondWave + thirdWave;
                
                // Add high-frequency detail
                float angle = atan(toCenter.y, toCenter.x);
                float angleNoise = fbm(vec2(angle * 8.0, age * 2.0)) * 0.1;
                float radiusNoise = fbm(vec2(dist * 12.0, time * 1.5)) * 0.05;
                
                // Apply noise modulation
                wave *= (1.0 + angleNoise + radiusNoise);
                
                // Distance-based intensity falloff
                float falloff = 1.0 / (1.0 + dist * 0.5);
                wave *= falloff;
                
                // Frequency-based modulation (like audio visualization)
                float freqMod = sin(dist * 30.0 - time * 15.0 + age * 10.0) * 0.1 + 1.0;
                wave *= freqMod;
                
                return clamp(wave, 0.0, 1.0);
            }
            
            // Inner energy core
            float energyCore(vec2 uv, vec2 center, float age) {
                vec2 toCenter = uv - center;
                float dist = length(toCenter);
                
                // Pulsing core
                float pulse = sin(time * 12.0 + age * 8.0) * 0.3 + 0.7;
                float coreRadius = 0.1 * (1.0 - age * 0.8);
                float core = exp(-pow(dist / coreRadius, 2.0)) * pulse;
                
                // Add plasma-like distortion
                float plasmaX = sin(time * 8.0 + uv.x * 20.0) * 0.02;
                float plasmaY = cos(time * 6.0 + uv.y * 15.0) * 0.02;
                vec2 plasmaUV = uv + vec2(plasmaX, plasmaY);
                vec2 plasmaToCenter = plasmaUV - center;
                float plasmaDist = length(plasmaToCenter);
                
                float plasmaCore = exp(-pow(plasmaDist / (coreRadius * 1.5), 2.0)) * 0.5;
                
                return core + plasmaCore;
            }
            
            void main()
            {
                // Convert texture coordinates to world space
                vec2 uv = texCoord * 2.0 - 1.0;
                uv.x *= resolution.x / resolution.y; // Aspect ratio correction
                
                vec2 worldCenter = center;
                worldCenter.x *= resolution.x / resolution.y;
                
                // Calculate effects
                float wave = shockwave(uv, worldCenter, age, radius);
                float core = energyCore(uv, worldCenter, age);
                
                // Combine effects
                float totalEffect = wave + core;
                
                // Color enhancement based on intensity
                vec3 finalColor = color;
                
                // Add energy glow based on effect intensity
                if (totalEffect > 0.5) {
                    finalColor = mix(color, vec3(1.0), (totalEffect - 0.5) * 0.8);
                }
                
                // Add blue/white rim lighting for high-intensity areas
                if (wave > 0.3) {
                    vec3 rimColor = mix(vec3(0.5, 0.8, 1.0), vec3(1.0), wave);
                    finalColor = mix(finalColor, rimColor, wave * 0.4);
                }
                // Discard fragments with negligible effect to keep background transparent
                if (totalEffect <= 0.001) {
                    discard;
                }

                FragColor = vec4(finalColor, totalEffect * alpha);
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
            
            logging.debug("TouchDesigner-quality shaders compiled")
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
            
            # Reserve space for high-quality shockwaves
            max_elements = 50  # Fewer elements but higher quality
            vertex_size = 12 * 4  # 12 floats per vertex * 4 bytes
            glBufferData(GL_ARRAY_BUFFER, max_elements * vertex_size * 6, None, GL_DYNAMIC_DRAW)
            
            # Set vertex attributes
            stride = 12 * 4  # 12 floats per vertex
            
            # Position (2 floats)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
            # Texture coordinates (2 floats)
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(2 * 4))
            # Age (1 float)
            glEnableVertexAttribArray(2)
            glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(4 * 4))
            # Center (2 floats)
            glEnableVertexAttribArray(3)
            glVertexAttribPointer(3, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(5 * 4))
            # Color (3 floats)
            glEnableVertexAttribArray(4)
            glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(7 * 4))
            # Radius (1 float)
            glEnableVertexAttribArray(5)
            glVertexAttribPointer(5, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(10 * 4))
            
            # Unbind
            glBindVertexArray(0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            
            logging.debug("High-quality geometry setup complete")
            return True
            
        except Exception as e:
            logging.error(f"Error setting up geometry: {e}")
            return False

    def create_shockwave(self, center_x=None, center_y=None):
        """Create a TouchDesigner-quality shockwave"""
        current_time = time.time() - self.start_time
        
        # Remove old shockwaves
        self.shockwaves = [wave for wave in self.shockwaves 
                          if (current_time - wave['birth_time']) < 5.0]
        
        # Don't create if at max
        if len(self.shockwaves) >= self.max_shockwaves:
            self.shockwaves.pop(0)
        
        # Random position if not specified
        if center_x is None:
            center_x = random.uniform(-0.6, 0.6)
        if center_y is None:
            center_y = random.uniform(-0.6, 0.6)
        
        # Get colors based on mode
        if self.wave_mode == 0:  # Blue energy
            base_color = (0.2, 0.6, 1.0)
        elif self.wave_mode == 1:  # White energy
            base_color = (0.9, 0.95, 1.0)
        else:  # Warm energy
            base_color = (1.0, 0.6, 0.2)
        
        # Create shockwave
        shockwave = {
            'center': (center_x, center_y),
            'birth_time': current_time,
            'color': base_color,
            'radius': 1.5 + random.uniform(-0.3, 0.3),  # Slight variation
            'intensity': 1.0 + random.uniform(-0.2, 0.2)
        }
        
        self.shockwaves.append(shockwave)
        logging.info(f"TouchDesigner shockwave at ({center_x:.2f}, {center_y:.2f})")

    def update_vertex_data(self):
        """Update vertex buffer with high-quality shockwaves"""
        try:
            current_time = time.time() - self.start_time
            vertices = []
            
            for shockwave in self.shockwaves:
                age = current_time - shockwave['birth_time']
                
                # Skip old shockwaves
                if age > 5.0:
                    continue
                
                center_x, center_y = shockwave['center']
                r, g, b = shockwave['color']
                radius = shockwave['radius'] * self.size_multiplier
                
                # Create large quad covering the entire effect area
                size = 2.0  # Cover entire screen
                
                # Create quad for shockwave
                vertices.extend([
                    -size, -size, 0.0, 0.0, age, center_x, center_y, r, g, b, radius, 0.0,
                    size, -size, 1.0, 0.0, age, center_x, center_y, r, g, b, radius, 0.0,
                    -size, size, 0.0, 1.0, age, center_x, center_y, r, g, b, radius, 0.0,
                    
                    size, -size, 1.0, 0.0, age, center_x, center_y, r, g, b, radius, 0.0,
                    size, size, 1.0, 1.0, age, center_x, center_y, r, g, b, radius, 0.0,
                    -size, size, 0.0, 1.0, age, center_x, center_y, r, g, b, radius, 0.0
                ])
            
            if vertices:
                self.vertices = np.array(vertices, dtype=np.float32)
                self.vertex_count = len(vertices) // 12
                
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
        """Render TouchDesigner-quality shockwaves"""
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
                glUniform2f(glGetUniformLocation(self.shader_program, "resolution"), 1920.0, 1080.0)  # Assume HD
                
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
                logging.error(f"TouchDesigner shockwave paint error: {e}")
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
            logging.debug("Cleaning up TouchDesigner-quality visualizer")
            
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
            self.shockwaves = []
            
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
            "Wave Mode": {
                "type": "slider",
                "min": 0,
                "max": 2,
                "value": self.wave_mode,
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
            elif name == "Wave Mode":
                self.wave_mode = int(value)
        except Exception as e:
            logging.error(f"Error updating control {name}: {e}")

    def trigger_action(self, action_name):
        """Handle MIDI triggers"""
        if action_name == "boom" or action_name == "explosion" or action_name == "shockwave":
            self.create_shockwave()
            logging.info("TouchDesigner SHOCKWAVE! Triggered via MIDI")