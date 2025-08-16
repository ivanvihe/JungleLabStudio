# visuals/presets/oneshot_circuit_signal.py
import logging
import numpy as np
import ctypes
import time
import math
import random
from OpenGL.GL import *
from ..base_visualizer import BaseVisualizer

class OneshotCircuitSignalVisualizer(BaseVisualizer):
    """One-shot electric circuit signal visualization for robotic sounds"""
    
    visual_name = "Oneshot Circuit Signal"
    
    def __init__(self):
        super().__init__()
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.start_time = time.time()
        self.initialized = False
        
        # Circuit signal state
        self.active_signals = []
        self.max_signals = 4
        
        # Visual parameters
        self.signal_speed = 1.0
        self.pulse_intensity = 1.0
        self.circuit_mode = 0  # 0=green, 1=blue, 2=multicolor
        
        # Circuit patterns
        self.circuit_paths = [
            # Horizontal circuits
            [(-1.2, 0.3), (-0.4, 0.3), (-0.4, 0.0), (0.4, 0.0), (0.4, -0.3), (1.2, -0.3)],
            [(-1.2, -0.2), (-0.2, -0.2), (-0.2, 0.4), (0.6, 0.4), (0.6, 0.1), (1.2, 0.1)],
            # Vertical circuits
            [(0.0, -1.0), (0.0, -0.3), (0.5, -0.3), (0.5, 0.3), (-0.3, 0.3), (-0.3, 1.0)],
            [(-0.6, -1.0), (-0.6, 0.2), (0.2, 0.2), (0.2, -0.5), (0.8, -0.5), (0.8, 1.0)]
        ]
        
        # Pre-generate data
        self.vertices = None
        self.vertex_count = 0
        
        logging.info("OneshotCircuitSignalVisualizer created")
        
        # Auto-trigger the signal on creation
        self.create_circuit_signal()

    def initializeGL(self):
        """Initialize OpenGL resources"""
        try:
            logging.debug("OneshotCircuitSignalVisualizer.initializeGL called")
            
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
            logging.info("🔌 OneshotCircuitSignalVisualizer initialized successfully")
            
        except Exception as e:
            logging.error(f"Error in OneshotCircuitSignalVisualizer.initializeGL: {e}")
            import traceback
            traceback.print_exc()

    def load_shaders(self):
        """Load and compile circuit signal shaders"""
        try:
            # Circuit signal vertex shader
            vertex_shader_source = """
            #version 330 core
            layout (location = 0) in vec2 aPos;
            layout (location = 1) in vec2 aTexCoord;
            layout (location = 2) in float aProgress; // 0-1 along path
            layout (location = 3) in float aAge;
            layout (location = 4) in vec3 aColor;
            layout (location = 5) in float aType; // 0=signal, 1=circuit_path, 2=node
            
            uniform float time;
            uniform float intensity;
            
            out vec2 texCoord;
            out vec3 color;
            out float alpha;
            out float effectType;
            out float progress;
            out float age;
            
            void main()
            {
                vec2 pos = aPos;
                
                // Add circuit board jitter for active signals
                if (aType < 0.5) { // Active signal
                    float jitter = sin(time * 60.0 + aProgress * 100.0) * 0.005;
                    pos += vec2(jitter, jitter * 0.5);
                }
                
                gl_Position = vec4(pos, 0.0, 1.0);
                texCoord = aTexCoord;
                color = aColor;
                effectType = aType;
                progress = aProgress;
                age = aAge;
                
                // Different fade patterns for different effects
                if (aType < 0.5) { // Signal pulse - bright and quick
                    alpha = (1.0 - smoothstep(0.0, 3.0, aAge)) * intensity;
                } else if (aType < 1.5) { // Circuit path - dim and persistent
                    alpha = 0.3 * intensity;
                } else { // Node - pulsing
                    float pulse = sin(time * 4.0 + aProgress * 10.0) * 0.3 + 0.7;
                    alpha = pulse * 0.6 * intensity;
                }
            }
            """
            
            # Circuit signal fragment shader
            fragment_shader_source = """
            #version 330 core
            in vec2 texCoord;
            in vec3 color;
            in float alpha;
            in float effectType;
            in float progress;
            in float age;
            
            uniform float time;
            
            out vec4 FragColor;
            
            // Digital noise for circuit effects
            float digitalNoise(vec2 uv, float scale) {
                vec2 p = floor(uv * scale);
                return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
            }
            
            // Signal pulse effect
            float signalPulse(vec2 uv) {
                vec2 center = uv - vec2(0.5);
                float dist = length(center);
                
                // Moving pulse along the signal
                float pulse_pos = fract(time * 2.0 + progress * 3.0);
                float pulse = 1.0 - smoothstep(0.0, 0.2, abs(dist - pulse_pos * 0.4));
                
                // Core signal line
                float line = 1.0 - smoothstep(0.0, 0.1, abs(center.y));
                line *= 1.0 - smoothstep(0.4, 0.5, abs(center.x));
                
                // Digital glitch effect
                float glitch = digitalNoise(uv * 50.0 + time * 10.0, 1.0);
                line *= 0.8 + glitch * 0.2;
                
                return max(pulse, line * 0.7);
            }
            
            // Circuit path (dim traces)
            float circuitPath(vec2 uv) {
                vec2 center = uv - vec2(0.5);
                
                // Thin circuit line
                float line = 1.0 - smoothstep(0.0, 0.02, abs(center.y));
                line *= 1.0 - smoothstep(0.4, 0.5, abs(center.x));
                
                // Add circuit board texture
                float texture = digitalNoise(uv * 20.0, 1.0) * 0.3 + 0.7;
                line *= texture;
                
                return line;
            }
            
            // Circuit node (connection points)
            float circuitNode(vec2 uv) {
                vec2 center = uv - vec2(0.5);
                float dist = length(center);
                
                // Circular node
                float node = 1.0 - smoothstep(0.1, 0.2, dist);
                
                // Pulsing core
                float pulse = sin(time * 8.0 + progress * 20.0) * 0.4 + 0.6;
                float core = 1.0 - smoothstep(0.0, 0.05, dist);
                
                // Digital ring pattern
                float rings = 0.0;
                for (int i = 1; i <= 3; i++) {
                    float ring_dist = float(i) * 0.03;
                    rings += (1.0 - smoothstep(ring_dist - 0.005, ring_dist + 0.005, dist)) * 0.3;
                }
                
                return node * 0.6 + core * pulse + rings;
            }
            
            void main()
            {
                float effect = 0.0;
                
                if (effectType < 0.5) { // Signal pulse
                    effect = signalPulse(texCoord);
                } else if (effectType < 1.5) { // Circuit path
                    effect = circuitPath(texCoord);
                } else { // Circuit node
                    effect = circuitNode(texCoord);
                }
                
                // Enhance colors based on effect type
                vec3 finalColor = color;
                if (effectType < 0.5) { // Signal - bright glow
                    finalColor = mix(color, vec3(1.0), effect * 0.4);
                } else if (effectType >= 1.5) { // Node - electric glow
                    finalColor = mix(color, color * 1.5, effect * 0.5);
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
            
            logging.debug("Circuit signal shaders compiled successfully")
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
            
            # Reserve space for circuit signals
            max_elements = 300  # More elements for complex circuits
            vertex_size = 11 * 4  # 11 floats per vertex * 4 bytes
            glBufferData(GL_ARRAY_BUFFER, max_elements * vertex_size * 6, None, GL_DYNAMIC_DRAW)
            
            # Set vertex attributes
            stride = 11 * 4  # 11 floats per vertex
            
            # Position (2 floats)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
            # Texture coordinates (2 floats)
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(2 * 4))
            # Progress (1 float)
            glEnableVertexAttribArray(2)
            glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(4 * 4))
            # Age (1 float)
            glEnableVertexAttribArray(3)
            glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(5 * 4))
            # Color (3 floats)
            glEnableVertexAttribArray(4)
            glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(6 * 4))
            # Effect type (1 float)
            glEnableVertexAttribArray(5)
            glVertexAttribPointer(5, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(9 * 4))
            
            # Unbind
            glBindVertexArray(0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            
            logging.debug("Circuit signal geometry setup complete")
            return True
            
        except Exception as e:
            logging.error(f"Error setting up geometry: {e}")
            return False

    def create_circuit_signal(self, path_index=None):
        """Create a new circuit signal traveling through a path"""
        current_time = time.time() - self.start_time
        
        # Remove old signals
        self.active_signals = [signal for signal in self.active_signals 
                              if (current_time - signal['start_time']) < 4.0]
        
        # Don't create if at max
        if len(self.active_signals) >= self.max_signals:
            self.active_signals.pop(0)
        
        # Choose random path if not specified
        if path_index is None:
            path_index = random.randint(0, len(self.circuit_paths) - 1)
        
        path = self.circuit_paths[path_index]
        
        # Get colors based on mode
        if self.circuit_mode == 0:  # Green circuit
            signal_color = (0.0, 1.0, 0.3)
            path_color = (0.0, 0.5, 0.1)
            node_color = (0.2, 0.8, 0.3)
        elif self.circuit_mode == 1:  # Blue circuit
            signal_color = (0.2, 0.8, 1.0)
            path_color = (0.1, 0.3, 0.5)
            node_color = (0.3, 0.6, 1.0)
        else:  # Multicolor circuit
            colors = [(1.0, 0.3, 0.0), (0.0, 1.0, 0.5), (0.8, 0.0, 1.0), (1.0, 1.0, 0.0)]
            signal_color = random.choice(colors)
            path_color = tuple(c * 0.3 for c in signal_color)
            node_color = tuple(c * 0.8 for c in signal_color)
        
        # Create signal data
        signal = {
            'path': path,
            'start_time': current_time,
            'speed': 1.2 * self.signal_speed,
            'signal_color': signal_color,
            'path_color': path_color,
            'node_color': node_color
        }
        
        self.active_signals.append(signal)
        logging.info(f"🔌 Created CIRCUIT signal on path {path_index}")

    def interpolate_path(self, path, progress):
        """Interpolate position along a path"""
        if progress <= 0:
            return path[0]
        if progress >= 1:
            return path[-1]
        
        # Find which segment we're on
        total_segments = len(path) - 1
        segment_progress = progress * total_segments
        segment_index = int(segment_progress)
        local_progress = segment_progress - segment_index
        
        if segment_index >= total_segments:
            return path[-1]
        
        # Interpolate between two points
        start = path[segment_index]
        end = path[segment_index + 1]
        
        x = start[0] + (end[0] - start[0]) * local_progress
        y = start[1] + (end[1] - start[1]) * local_progress
        
        return (x, y)

    def update_vertex_data(self):
        """Update vertex buffer with circuit signals"""
        try:
            current_time = time.time() - self.start_time
            vertices = []
            
            for signal in self.active_signals:
                signal_age = current_time - signal['start_time']
                signal_progress = (signal_age * signal['speed']) % 1.0  # Loop the signal
                
                path = signal['path']
                signal_color = signal['signal_color']
                path_color = signal['path_color']
                node_color = signal['node_color']
                
                # 1. Draw circuit path (dim background)
                for i in range(len(path) - 1):
                    start = path[i]
                    end = path[i + 1]
                    
                    # Create line segment as thin quad
                    thickness = 0.01
                    
                    # Calculate perpendicular vector
                    dx = end[0] - start[0]
                    dy = end[1] - start[1]
                    length = math.sqrt(dx*dx + dy*dy)
                    if length > 0:
                        perpx = -dy / length * thickness
                        perpy = dx / length * thickness
                    else:
                        continue
                    
                    segment_progress = float(i) / (len(path) - 1)
                    r, g, b = path_color
                    
                    # Create quad for path segment
                    vertices.extend([
                        start[0] - perpx, start[1] - perpy, 0.0, 0.0, segment_progress, signal_age, r, g, b, 0.0, 1.0,
                        start[0] + perpx, start[1] + perpy, 1.0, 0.0, segment_progress, signal_age, r, g, b, 0.0, 1.0,
                        end[0] - perpx, end[1] - perpy, 0.0, 1.0, segment_progress, signal_age, r, g, b, 0.0, 1.0,
                        
                        start[0] + perpx, start[1] + perpy, 1.0, 0.0, segment_progress, signal_age, r, g, b, 0.0, 1.0,
                        end[0] + perpx, end[1] + perpy, 1.0, 1.0, segment_progress, signal_age, r, g, b, 0.0, 1.0,
                        end[0] - perpx, end[1] - perpy, 0.0, 1.0, segment_progress, signal_age, r, g, b, 0.0, 1.0
                    ])
                
                # 2. Draw circuit nodes (connection points)
                for i, point in enumerate(path):
                    if i == 0 or i == len(path) - 1:  # Only start and end nodes
                        node_progress = float(i) / max(1, len(path) - 1)
                        size = 0.03
                        r, g, b = node_color
                        
                        # Create quad for node
                        vertices.extend([
                            point[0] - size, point[1] - size, 0.0, 0.0, node_progress, signal_age, r, g, b, 0.0, 2.0,
                            point[0] + size, point[1] - size, 1.0, 0.0, node_progress, signal_age, r, g, b, 0.0, 2.0,
                            point[0] - size, point[1] + size, 0.0, 1.0, node_progress, signal_age, r, g, b, 0.0, 2.0,
                            
                            point[0] + size, point[1] - size, 1.0, 0.0, node_progress, signal_age, r, g, b, 0.0, 2.0,
                            point[0] + size, point[1] + size, 1.0, 1.0, node_progress, signal_age, r, g, b, 0.0, 2.0,
                            point[0] - size, point[1] + size, 0.0, 1.0, node_progress, signal_age, r, g, b, 0.0, 2.0
                        ])
                
                # 3. Draw moving signal pulse
                signal_pos = self.interpolate_path(path, signal_progress)
                size = 0.08
                r, g, b = signal_color
                
                # Create quad for signal pulse
                vertices.extend([
                    signal_pos[0] - size, signal_pos[1] - size, 0.0, 0.0, signal_progress, signal_age, r, g, b, 0.0, 0.0,
                    signal_pos[0] + size, signal_pos[1] - size, 1.0, 0.0, signal_progress, signal_age, r, g, b, 0.0, 0.0,
                    signal_pos[0] - size, signal_pos[1] + size, 0.0, 1.0, signal_progress, signal_age, r, g, b, 0.0, 0.0,
                    
                    signal_pos[0] + size, signal_pos[1] - size, 1.0, 0.0, signal_progress, signal_age, r, g, b, 0.0, 0.0,
                    signal_pos[0] + size, signal_pos[1] + size, 1.0, 1.0, signal_progress, signal_age, r, g, b, 0.0, 0.0,
                    signal_pos[0] - size, signal_pos[1] + size, 0.0, 1.0, signal_progress, signal_age, r, g, b, 0.0, 0.0
                ])
            
            if vertices:
                self.vertices = np.array(vertices, dtype=np.float32)
                self.vertex_count = len(vertices) // 11
                
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
        """Render circuit signals"""
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
                glUniform1f(glGetUniformLocation(self.shader_program, "intensity"), self.pulse_intensity)
                
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
                logging.error(f"CircuitSignal paint error: {e}")
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
            logging.debug("Cleaning up OneshotCircuitSignalVisualizer")
            
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
            self.active_signals = []
            
        except Exception as e:
            logging.debug(f"Cleanup error (non-critical): {e}")

    def get_controls(self):
        """Return available controls"""
        return {
            "Signal Speed": {
                "type": "slider",
                "min": 20,
                "max": 300,
                "value": int(self.signal_speed * 100),
                "default": 100
            },
            "Pulse Intensity": {
                "type": "slider",
                "min": 10,
                "max": 300,
                "value": int(self.pulse_intensity * 100),
                "default": 100
            },
            "Circuit Mode": {
                "type": "slider",
                "min": 0,
                "max": 2,
                "value": self.circuit_mode,
                "default": 0
            }
        }

    def update_control(self, name, value):
        """Update control values"""
        try:
            if name == "Signal Speed":
                self.signal_speed = value / 100.0
            elif name == "Pulse Intensity":
                self.pulse_intensity = value / 100.0
            elif name == "Circuit Mode":
                self.circuit_mode = int(value)
        except Exception as e:
            logging.error(f"Error updating control {name}: {e}")

    def trigger_action(self, action_name):
        """Handle MIDI triggers"""
        if action_name == "signal" or action_name == "circuit" or action_name == "electric":
            self.create_circuit_signal()
            logging.info("🔌 CIRCUIT SIGNAL! Triggered via MIDI")