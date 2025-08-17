# TODO: migrate to RenderBackend (ModernGL)
# visuals/presets/infinite_neural_network.py
import logging
import numpy as np
import ctypes
import time
import math
import random
from OpenGL.GL import *
from ..base_visualizer import BaseVisualizer

class InfiniteNeuralNetworkVisualizer(BaseVisualizer):
    """TouchDesigner-quality infinite zoom neural network with connected particles"""
    
    visual_name = "Infinite Neural Network"
    
    def __init__(self):
        super().__init__()
        self.shader_program = None
        self.particle_vao = None
        self.particle_vbo = None
        self.line_vao = None
        self.line_vbo = None
        self.start_time = time.time()
        self.initialized = False

        # Network state
        self.particles = []
        self.connections = []
        self.max_particles = 150
        self.max_connections = 300
        
        # Visual parameters
        self.intensity = 1.0
        self.zoom_speed = 0.3
        self.connection_distance = 0.4
        self.particle_spawn_rate = 0.8
        self.color_mode = 0  # 0=cyan/pink, 1=blue/white, 2=rainbow
        
        # Zoom system for infinite effect
        self.zoom_level = 1.0
        self.zoom_layers = 3  # Multiple layers for seamless zoom
        
        # Pre-generate data
        self.particle_vertices = None
        self.line_vertices = None
        self.particle_count = 0
        self.line_count = 0
        
        logging.info("TouchDesigner-quality Infinite Neural Network created")
        
        # Generate initial particles
        self.generate_initial_particles()

    def initializeGL(self):
        """Initialize OpenGL resources"""
        try:
            logging.debug("InfiniteNeuralNetworkVisualizer.initializeGL called")
            
            # Clear any existing GL errors
            while glGetError() != GL_NO_ERROR:
                pass
            
            # Set up OpenGL state for high quality
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # Additive blending for glow
            glDisable(GL_DEPTH_TEST)
            glEnable(GL_PROGRAM_POINT_SIZE)  # For point sprites
            
            # Load shaders
            if not self.load_shaders():
                logging.error("Failed to load shaders")
                return
            
            # Setup geometry
            if not self.setup_geometry():
                logging.error("Failed to setup geometry")
                return
            
            self.initialized = True
            logging.info("🌌 TouchDesigner-quality infinite neural network initialized")
            
        except Exception as e:
            logging.error(f"Error in initialization: {e}")
            import traceback
            traceback.print_exc()

    def load_shaders(self):
        """Load TouchDesigner-quality neural network shaders"""
        try:
            # Particle vertex shader
            particle_vertex_shader = """
            #version 330 core
            layout (location = 0) in vec2 aPos;
            layout (location = 1) in vec3 aColor;
            layout (location = 2) in float aSize;
            layout (location = 3) in float aAge;
            layout (location = 4) in float aBrightness;
            layout (location = 5) in float aLayer;
            
            uniform float time;
            uniform float intensity;
            uniform float zoomLevel;
            uniform vec2 resolution;
            
            out vec3 color;
            out float alpha;
            out float size;
            
            void main()
            {
                // Apply zoom transformation
                float layerScale = pow(2.0, aLayer);
                vec2 scaledPos = aPos * layerScale / zoomLevel;
                
                // Wrap positions for infinite scroll
                scaledPos = mod(scaledPos + 1.0, 2.0) - 1.0;
                
                gl_Position = vec4(scaledPos, 0.0, 1.0);
                
                // Calculate size with zoom and pulsing
                float pulse = sin(time * 4.0 + aPos.x * 10.0 + aPos.y * 8.0) * 0.3 + 0.7;
                gl_PointSize = aSize * pulse * intensity * (10.0 / zoomLevel) * layerScale;
                
                color = aColor;
                size = aSize;
                
                // Fade based on zoom level and age
                float zoomFade = smoothstep(0.1, 1.0, layerScale / zoomLevel);
                float ageFade = 1.0 - smoothstep(0.0, 20.0, aAge);
                alpha = aBrightness * zoomFade * ageFade * intensity;
            }
            """
            
            # Particle fragment shader
            particle_fragment_shader = """
            #version 330 core
            in vec3 color;
            in float alpha;
            in float size;
            
            uniform float time;
            
            out vec4 FragColor;
            
            void main()
            {
                // Create circular particle with glow
                vec2 coord = gl_PointCoord - vec2(0.5);
                float dist = length(coord);
                
                // Core particle
                float core = exp(-pow(dist / 0.2, 2.0));
                
                // Outer glow
                float glow = exp(-pow(dist / 0.4, 1.5)) * 0.6;
                
                // Combine effects
                float intensity = core + glow;
                
                // Add sparkle effect
                float sparkle = sin(time * 15.0 + size * 100.0) * 0.2 + 0.8;
                intensity *= sparkle;
                
                // Discard weak fragments
                if (intensity < 0.01) discard;
                
                FragColor = vec4(color, intensity * alpha);
            }
            """
            
            # Line vertex shader
            line_vertex_shader = """
            #version 330 core
            layout (location = 0) in vec2 aPos;
            layout (location = 1) in vec3 aColor;
            layout (location = 2) in float aAlpha;
            layout (location = 3) in float aLayer;
            
            uniform float time;
            uniform float intensity;
            uniform float zoomLevel;
            
            out vec3 color;
            out float alpha;
            
            void main()
            {
                // Apply zoom transformation
                float layerScale = pow(2.0, aLayer);
                vec2 scaledPos = aPos * layerScale / zoomLevel;
                
                // Wrap positions for infinite scroll
                scaledPos = mod(scaledPos + 1.0, 2.0) - 1.0;
                
                gl_Position = vec4(scaledPos, 0.0, 1.0);
                
                color = aColor;
                
                // Fade based on zoom level
                float zoomFade = smoothstep(0.1, 1.0, layerScale / zoomLevel);
                alpha = aAlpha * zoomFade * intensity * 0.7;
            }
            """
            
            # Line fragment shader
            line_fragment_shader = """
            #version 330 core
            in vec3 color;
            in float alpha;
            
            uniform float time;
            
            out vec4 FragColor;
            
            void main()
            {
                // Simple line with slight glow
                FragColor = vec4(color, alpha);
            }
            """
            
            # Compile particle shaders
            particle_vs = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(particle_vs, particle_vertex_shader)
            glCompileShader(particle_vs)
            
            if not glGetShaderiv(particle_vs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(particle_vs).decode()
                logging.error(f"Particle vertex shader compilation failed: {error}")
                return False
            
            particle_fs = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(particle_fs, particle_fragment_shader)
            glCompileShader(particle_fs)
            
            if not glGetShaderiv(particle_fs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(particle_fs).decode()
                logging.error(f"Particle fragment shader compilation failed: {error}")
                return False
            
            self.particle_program = glCreateProgram()
            glAttachShader(self.particle_program, particle_vs)
            glAttachShader(self.particle_program, particle_fs)
            glLinkProgram(self.particle_program)
            
            if not glGetProgramiv(self.particle_program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(self.particle_program).decode()
                logging.error(f"Particle shader program linking failed: {error}")
                return False
            
            # Compile line shaders
            line_vs = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(line_vs, line_vertex_shader)
            glCompileShader(line_vs)
            
            if not glGetShaderiv(line_vs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(line_vs).decode()
                logging.error(f"Line vertex shader compilation failed: {error}")
                return False
            
            line_fs = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(line_fs, line_fragment_shader)
            glCompileShader(line_fs)
            
            if not glGetShaderiv(line_fs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(line_fs).decode()
                logging.error(f"Line fragment shader compilation failed: {error}")
                return False
            
            self.line_program = glCreateProgram()
            glAttachShader(self.line_program, line_vs)
            glAttachShader(self.line_program, line_fs)
            glLinkProgram(self.line_program)
            
            if not glGetProgramiv(self.line_program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(self.line_program).decode()
                logging.error(f"Line shader program linking failed: {error}")
                return False
            
            # Clean up individual shaders
            glDeleteShader(particle_vs)
            glDeleteShader(particle_fs)
            glDeleteShader(line_vs)
            glDeleteShader(line_fs)
            
            logging.debug("TouchDesigner-quality neural network shaders compiled")
            return True
            
        except Exception as e:
            logging.error(f"Error loading shaders: {e}")
            return False

    def setup_geometry(self):
        """Setup vertex data for particles and lines"""
        try:
            # Setup particle geometry
            self.particle_vao = glGenVertexArrays(1)
            glBindVertexArray(self.particle_vao)
            
            self.particle_vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.particle_vbo)
            
            # Reserve space for particles (6 attributes per particle)
            particle_vertex_size = 6 * 4  # 6 floats * 4 bytes
            glBufferData(GL_ARRAY_BUFFER, self.max_particles * particle_vertex_size, None, GL_DYNAMIC_DRAW)
            
            # Particle attributes
            glEnableVertexAttribArray(0)  # Position
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, particle_vertex_size, ctypes.c_void_p(0))
            glEnableVertexAttribArray(1)  # Color
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, particle_vertex_size, ctypes.c_void_p(2 * 4))
            glEnableVertexAttribArray(2)  # Size
            glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, particle_vertex_size, ctypes.c_void_p(5 * 4))
            glEnableVertexAttribArray(3)  # Age
            glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, particle_vertex_size, ctypes.c_void_p(6 * 4))
            glEnableVertexAttribArray(4)  # Brightness
            glVertexAttribPointer(4, 1, GL_FLOAT, GL_FALSE, particle_vertex_size, ctypes.c_void_p(7 * 4))
            glEnableVertexAttribArray(5)  # Layer
            glVertexAttribPointer(5, 1, GL_FLOAT, GL_FALSE, particle_vertex_size, ctypes.c_void_p(8 * 4))
            
            # Setup line geometry
            self.line_vao = glGenVertexArrays(1)
            glBindVertexArray(self.line_vao)
            
            self.line_vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.line_vbo)
            
            # Reserve space for lines (2 vertices per line, 4 attributes per vertex)
            line_vertex_size = 4 * 4  # 4 floats * 4 bytes
            glBufferData(GL_ARRAY_BUFFER, self.max_connections * 2 * line_vertex_size, None, GL_DYNAMIC_DRAW)
            
            # Line attributes
            glEnableVertexAttribArray(0)  # Position
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, line_vertex_size, ctypes.c_void_p(0))
            glEnableVertexAttribArray(1)  # Color
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, line_vertex_size, ctypes.c_void_p(2 * 4))
            glEnableVertexAttribArray(2)  # Alpha
            glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, line_vertex_size, ctypes.c_void_p(5 * 4))
            glEnableVertexAttribArray(3)  # Layer
            glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, line_vertex_size, ctypes.c_void_p(6 * 4))
            
            # Unbind
            glBindVertexArray(0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            
            logging.debug("Neural network geometry setup complete")
            return True
            
        except Exception as e:
            logging.error(f"Error setting up geometry: {e}")
            return False

    def generate_initial_particles(self):
        """Generate initial set of particles"""
        current_time = time.time() - self.start_time
        
        for _ in range(80):  # Start with some particles
            self.create_particle(current_time)

    def create_particle(self, current_time):
        """Create a new particle"""
        if len(self.particles) >= self.max_particles:
            return
        
        # Random position
        x = random.uniform(-2.0, 2.0)
        y = random.uniform(-2.0, 2.0)
        
        # Random layer for multi-scale effect
        layer = random.uniform(0, self.zoom_layers)
        
        # Color based on mode
        if self.color_mode == 0:  # Cyan/Pink
            if random.random() < 0.6:
                color = (0.2, 0.8, 1.0)  # Cyan
            else:
                color = (1.0, 0.4, 0.8)  # Pink
        elif self.color_mode == 1:  # Blue/White
            if random.random() < 0.7:
                color = (0.3, 0.6, 1.0)  # Blue
            else:
                color = (0.9, 0.95, 1.0)  # White
        else:  # Rainbow
            hue = random.uniform(0, 2 * math.pi)
            color = (
                (math.sin(hue) + 1) * 0.5,
                (math.sin(hue + 2.094) + 1) * 0.5,
                (math.sin(hue + 4.188) + 1) * 0.5
            )
        
        particle = {
            'pos': [x, y],
            'color': color,
            'size': random.uniform(8.0, 20.0),
            'birth_time': current_time,
            'brightness': random.uniform(0.7, 1.0),
            'layer': layer,
            'id': len(self.particles)
        }
        
        self.particles.append(particle)

    def update_particles(self):
        """Update particle system"""
        current_time = time.time() - self.start_time
        
        # Update zoom level for infinite zoom effect
        self.zoom_level = 1.0 + current_time * self.zoom_speed
        
        # Spawn new particles
        if random.random() < self.particle_spawn_rate * 0.1:
            self.create_particle(current_time)
        
        # Remove old particles
        self.particles = [p for p in self.particles 
                         if (current_time - p['birth_time']) < 25.0]
        
        # Update connections
        self.update_connections(current_time)

    def update_connections(self, current_time):
        """Update particle connections"""
        self.connections = []
        
        # Find connections between nearby particles
        for i, particle1 in enumerate(self.particles):
            for j, particle2 in enumerate(self.particles[i+1:], i+1):
                # Only connect particles in similar layers
                if abs(particle1['layer'] - particle2['layer']) > 0.5:
                    continue
                
                # Calculate distance
                dx = particle1['pos'][0] - particle2['pos'][0]
                dy = particle1['pos'][1] - particle2['pos'][1]
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Connect if close enough
                if distance < self.connection_distance:
                    # Connection strength based on distance
                    strength = 1.0 - (distance / self.connection_distance)
                    
                    # Blend colors
                    r = (particle1['color'][0] + particle2['color'][0]) * 0.5
                    g = (particle1['color'][1] + particle2['color'][1]) * 0.5
                    b = (particle1['color'][2] + particle2['color'][2]) * 0.5
                    
                    connection = {
                        'start': particle1['pos'][:],
                        'end': particle2['pos'][:],
                        'color': (r, g, b),
                        'alpha': strength * 0.8,
                        'layer': (particle1['layer'] + particle2['layer']) * 0.5
                    }
                    
                    self.connections.append(connection)
                    
                    if len(self.connections) >= self.max_connections:
                        return

    def update_vertex_data(self):
        """Update vertex buffers"""
        try:
            current_time = time.time() - self.start_time
            
            # Update particles
            particle_vertices = []
            for particle in self.particles:
                age = current_time - particle['birth_time']
                x, y = particle['pos']
                r, g, b = particle['color']
                
                particle_vertices.extend([
                    x, y,  # Position
                    r, g, b,  # Color
                    particle['size'],  # Size
                    age,  # Age
                    particle['brightness'],  # Brightness
                    particle['layer']  # Layer
                ])
            
            if particle_vertices:
                self.particle_vertices = np.array(particle_vertices, dtype=np.float32)
                self.particle_count = len(particle_vertices) // 9
                
                # Upload particle data
                glBindBuffer(GL_ARRAY_BUFFER, self.particle_vbo)
                glBufferSubData(GL_ARRAY_BUFFER, 0, self.particle_vertices.nbytes, self.particle_vertices)
                glBindBuffer(GL_ARRAY_BUFFER, 0)
            else:
                self.particle_count = 0
            
            # Update connections
            line_vertices = []
            for connection in self.connections:
                r, g, b = connection['color']
                alpha = connection['alpha']
                layer = connection['layer']
                
                # Start vertex
                line_vertices.extend([
                    connection['start'][0], connection['start'][1],  # Position
                    r, g, b,  # Color
                    alpha,  # Alpha
                    layer  # Layer
                ])
                
                # End vertex
                line_vertices.extend([
                    connection['end'][0], connection['end'][1],  # Position
                    r, g, b,  # Color
                    alpha,  # Alpha
                    layer  # Layer
                ])
            
            if line_vertices:
                self.line_vertices = np.array(line_vertices, dtype=np.float32)
                self.line_count = len(line_vertices) // 7
                
                # Upload line data
                glBindBuffer(GL_ARRAY_BUFFER, self.line_vbo)
                glBufferSubData(GL_ARRAY_BUFFER, 0, self.line_vertices.nbytes, self.line_vertices)
                glBindBuffer(GL_ARRAY_BUFFER, 0)
            else:
                self.line_count = 0
            
        except Exception as e:
            logging.error(f"Error updating vertex data: {e}")
            self.particle_count = 0
            self.line_count = 0

    def paintGL(self):
        """Render TouchDesigner-quality neural network"""
        try:
            if not self.initialized:
                glClearColor(0.0, 0.0, 0.0, 0.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return

            # Clear with transparent background
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)
            
            # Update system
            self.update_particles()
            self.update_vertex_data()
            
            current_time = time.time() - self.start_time
            
            # Render connections first (behind particles)
            if self.line_count > 0 and self.line_program:
                glUseProgram(self.line_program)
                
                # Update uniforms
                glUniform1f(glGetUniformLocation(self.line_program, "time"), current_time)
                glUniform1f(glGetUniformLocation(self.line_program, "intensity"), self.intensity)
                glUniform1f(glGetUniformLocation(self.line_program, "zoomLevel"), self.zoom_level)
                
                # Draw lines
                glBindVertexArray(self.line_vao)
                glDrawArrays(GL_LINES, 0, self.line_count)
                glBindVertexArray(0)
                
                glUseProgram(0)
            
            # Render particles
            if self.particle_count > 0 and self.particle_program:
                glUseProgram(self.particle_program)
                
                # Update uniforms
                glUniform1f(glGetUniformLocation(self.particle_program, "time"), current_time)
                glUniform1f(glGetUniformLocation(self.particle_program, "intensity"), self.intensity)
                glUniform1f(glGetUniformLocation(self.particle_program, "zoomLevel"), self.zoom_level)
                glUniform2f(glGetUniformLocation(self.particle_program, "resolution"), 1920.0, 1080.0)
                
                # Draw particles
                glBindVertexArray(self.particle_vao)
                glDrawArrays(GL_POINTS, 0, self.particle_count)
                glBindVertexArray(0)
                
                glUseProgram(0)
            
        except Exception as e:
            # Only log errors occasionally
            if not hasattr(self, '_last_error_time') or \
               time.time() - self._last_error_time > 5:
                logging.error(f"TouchDesigner neural network paint error: {e}")
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
            logging.debug("Cleaning up TouchDesigner-quality neural network visualizer")
            
            # Clean up programs
            for program in [getattr(self, 'particle_program', None), getattr(self, 'line_program', None)]:
                if program:
                    try:
                        if glIsProgram(program):
                            glDeleteProgram(program)
                    except:
                        pass
            
            # Clean up VAOs
            for vao in [self.particle_vao, self.line_vao]:
                if vao:
                    try:
                        glDeleteVertexArrays(1, [vao])
                    except:
                        pass
            
            # Clean up VBOs
            for vbo in [self.particle_vbo, self.line_vbo]:
                if vbo:
                    try:
                        glDeleteBuffers(1, [vbo])
                    except:
                        pass
            
            self.initialized = False
            self.particles = []
            self.connections = []
            
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
            "Zoom Speed": {
                "type": "slider",
                "min": 5,
                "max": 100,
                "value": int(self.zoom_speed * 100),
                "default": 30
            },
            "Connection Distance": {
                "type": "slider",
                "min": 10,
                "max": 80,
                "value": int(self.connection_distance * 100),
                "default": 40
            },
            "Spawn Rate": {
                "type": "slider",
                "min": 10,
                "max": 200,
                "value": int(self.particle_spawn_rate * 100),
                "default": 80
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
            elif name == "Zoom Speed":
                self.zoom_speed = value / 100.0
            elif name == "Connection Distance":
                self.connection_distance = value / 100.0
            elif name == "Spawn Rate":
                self.particle_spawn_rate = value / 100.0
            elif name == "Color Mode":
                self.color_mode = int(value)
        except Exception as e:
            logging.error(f"Error updating control {name}: {e}")

    def trigger_action(self, action_name):
        """Handle MIDI triggers"""
        if action_name == "neural" or action_name == "network" or action_name == "zoom":
            current_time = time.time() - self.start_time
            # Create burst of new particles
            for _ in range(20):
                self.create_particle(current_time)
            logging.info("🌌 TouchDesigner NEURAL NETWORK BURST! Triggered via MIDI")