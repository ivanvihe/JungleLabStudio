# TODO: migrate to RenderBackend (ModernGL)
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
    """TouchDesigner-quality electric flow visualization"""
    
    visual_name = "Oneshot Circuit Signal"
    
    def __init__(self):
        super().__init__()
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.start_time = time.time()
        self.initialized = False
        
        # Electric flow state
        self.active_flows = []
        self.max_flows = 3
        
        # Visual parameters
        self.flow_speed = 1.0
        self.electric_intensity = 1.0
        self.flow_mode = 0  # 0=blue, 1=cyan, 2=multicolor
        
        # High-quality flow paths
        self.flow_paths = [
            [(-1.5, -0.8), (-0.6, -0.2), (0.3, 0.4), (1.0, 0.9)],
            [(-1.2, 0.7), (-0.3, 0.1), (0.4, -0.3), (1.3, -0.6)],
            [(-1.4, 0.0), (-0.7, 0.5), (0.0, 0.3), (0.6, -0.2), (1.2, 0.1)],
            [(-1.0, -0.5), (-0.2, -0.8), (0.5, -0.4), (0.8, 0.2), (1.5, 0.6)],
        ]
        
        # Pre-generate data
        self.vertices = None
        self.vertex_count = 0
        
        logging.info("TouchDesigner Circuit Signal created")
        
        # Auto-trigger on creation
        self.create_electric_flow()

    def initializeGL(self):
        """Initialize OpenGL resources"""
        try:
            logging.debug("TouchDesigner Circuit Signal initializing")
            
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
            logging.info("TouchDesigner electric flow initialized")
            
        except Exception as e:
            logging.error(f"Error in initialization: {e}")
            import traceback
            traceback.print_exc()

    def load_shaders(self):
        """Load TouchDesigner-quality electric flow shaders"""
        try:
            # Vertex shader
            vertex_shader_source = """
            #version 330 core
            layout (location = 0) in vec2 aPos;
            layout (location = 1) in vec2 aTexCoord;
            layout (location = 2) in float aProgress;
            layout (location = 3) in float aAge;
            layout (location = 4) in vec3 aColor;
            layout (location = 5) in vec2 aDirection;
            layout (location = 6) in float aIntensity;
            
            uniform float time;
            uniform float globalIntensity;
            
            out vec2 texCoord;
            out vec3 color;
            out float alpha;
            out float progress;
            out vec2 direction;
            out float intensity;
            out float age;
            
            void main()
            {
                vec2 pos = aPos;
                
                // Electric jitter
                float jitterFreq = 80.0;
                float jitterAmp = 0.008;
                vec2 jitter = vec2(
                    sin(time * jitterFreq + aProgress * 50.0) * jitterAmp,
                    cos(time * jitterFreq * 1.3 + aProgress * 60.0) * jitterAmp * 0.7
                );
                
                pos += jitter * aIntensity;
                
                gl_Position = vec4(pos, 0.0, 1.0);
                texCoord = aTexCoord;
                color = aColor;
                progress = aProgress;
                direction = aDirection;
                intensity = aIntensity;
                age = aAge;
                
                // Smooth fade with electric pulsing
                float baseFade = 1.0 - smoothstep(0.0, 4.0, aAge);
                float pulse = sin(time * 15.0 + aProgress * 20.0) * 0.2 + 0.8;
                alpha = baseFade * pulse * globalIntensity;
            }
            """
            
            # Fragment shader
            fragment_shader_source = """
            #version 330 core
            in vec2 texCoord;
            in vec3 color;
            in float alpha;
            in float progress;
            in vec2 direction;
            in float intensity;
            in float age;
            
            uniform float time;
            
            out vec4 FragColor;
            
            // Noise functions
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
                for (int i = 0; i < 5; i++) {
                    value += amplitude * noise(p);
                    p *= 2.0;
                    amplitude *= 0.5;
                }
                return value;
            }
            
            // Electric flow
            float electricFlow(vec2 uv) {
                vec2 center = uv - vec2(0.5);
                
                // Main flow channel
                float flowWidth = 0.015;
                float mainFlow = 1.0 - smoothstep(0.0, flowWidth, abs(center.y));
                
                // Electric branching
                float branchNoise = fbm(vec2(uv.x * 60.0, time * 8.0));
                float branches = sin(uv.x * 150.0 + branchNoise * 10.0) * 0.002;
                mainFlow *= 1.0 - smoothstep(0.0, flowWidth * 2.0, abs(center.y + branches));
                
                // Moving pulse
                float pulsePos = fract(time * 3.0 + progress * 2.0);
                float pulseWidth = 0.08;
                float pulse = exp(-pow((uv.x - pulsePos) / pulseWidth, 2.0));
                
                // Core energy
                float coreEnergy = mainFlow * (0.6 + pulse * 0.4);
                
                // Electric disturbance
                float disturbance = noise(vec2(uv.x * 200.0, time * 25.0)) * 0.3;
                coreEnergy *= (0.8 + disturbance);
                
                // Electric arcs
                float arcFreq = 40.0;
                float arcNoise = fbm(vec2(uv.x * arcFreq, time * 6.0));
                float arcs = 0.0;
                
                for (int i = 0; i < 3; i++) {
                    float arcOffset = float(i + 1) * 0.03;
                    float arcIntensity = 1.0 / float(i + 2);
                    float arc = exp(-pow((center.y + arcOffset * sin(uv.x * arcFreq + arcNoise * 5.0)) / (flowWidth * 3.0), 2.0));
                    arcs += arc * arcIntensity * 0.4;
                    
                    arc = exp(-pow((center.y - arcOffset * sin(uv.x * arcFreq * 1.2 + arcNoise * 4.0)) / (flowWidth * 3.0), 2.0));
                    arcs += arc * arcIntensity * 0.4;
                }
                
                // Electric glow
                float glowRadius = 0.04;
                float glow = exp(-pow(abs(center.y) / glowRadius, 1.5)) * 0.3;
                
                // Combine effects
                float totalElectric = coreEnergy + arcs + glow;
                
                // Electric crackling
                float crackle = noise(vec2(uv.x * 100.0 + time * 20.0, uv.y * 80.0));
                totalElectric *= (0.85 + crackle * 0.15);
                
                return clamp(totalElectric, 0.0, 1.0);
            }
            
            // Electric sparks
            float electricSparks(vec2 uv) {
                float sparks = 0.0;
                
                for (int i = 0; i < 8; i++) {
                    float sparkPos = float(i) / 7.0;
                    float sparkOffset = sin(time * 10.0 + sparkPos * 20.0) * 0.02;
                    vec2 sparkCenter = vec2(sparkPos, 0.5 + sparkOffset);
                    
                    float sparkDist = length(uv - sparkCenter);
                    float sparkRadius = 0.008 + sin(time * 30.0 + sparkPos * 50.0) * 0.003;
                    float spark = exp(-pow(sparkDist / sparkRadius, 2.0));
                    
                    float flicker = sin(time * 40.0 + sparkPos * 100.0) * 0.5 + 0.5;
                    sparks += spark * flicker * 0.6;
                }
                
                return sparks;
            }
            
            void main()
            {
                // Calculate electric effects
                float flow = electricFlow(texCoord);
                float sparks = electricSparks(texCoord);
                
                // Combine effects
                float totalEffect = flow + sparks;
                
                // Enhanced color
                vec3 finalColor = color;
                
                // Core brightness
                if (totalEffect > 0.5) {
                    float brightness = (totalEffect - 0.5) * 2.0;
                    finalColor = mix(color, vec3(1.0), brightness * 0.6);
                }
                
                // Electric tinting
                if (flow > 0.3) {
                    vec3 electricTint = mix(vec3(0.3, 0.9, 1.0), vec3(1.0), flow);
                    finalColor = mix(finalColor, electricTint, flow * 0.5);
                }
                
                // Spark effect
                if (sparks > 0.2) {
                    finalColor = mix(finalColor, vec3(1.0, 1.0, 0.9), sparks * 0.8);
                }
                
                FragColor = vec4(finalColor, totalEffect * alpha * intensity);
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
            
            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            
            logging.debug("TouchDesigner electric flow shaders compiled")
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
            
            # Reserve space
            max_elements = 100
            vertex_size = 13 * 4  # 13 floats per vertex
            glBufferData(GL_ARRAY_BUFFER, max_elements * vertex_size * 6, None, GL_DYNAMIC_DRAW)
            
            # Set vertex attributes
            stride = 13 * 4
            
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
            # Direction (2 floats)
            glEnableVertexAttribArray(5)
            glVertexAttribPointer(5, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(9 * 4))
            # Intensity (1 float)
            glEnableVertexAttribArray(6)
            glVertexAttribPointer(6, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(11 * 4))
            
            # Unbind
            glBindVertexArray(0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            
            logging.debug("Electric flow geometry setup complete")
            return True
            
        except Exception as e:
            logging.error(f"Error setting up geometry: {e}")
            return False

    def create_electric_flow(self, path_index=None):
        """Create electric flow"""
        current_time = time.time() - self.start_time
        
        # Remove old flows
        self.active_flows = [flow for flow in self.active_flows 
                            if (current_time - flow['start_time']) < 5.0]
        
        # Don't create if at max
        if len(self.active_flows) >= self.max_flows:
            self.active_flows.pop(0)
        
        # Choose random path
        if path_index is None:
            path_index = random.randint(0, len(self.flow_paths) - 1)
        
        path = self.flow_paths[path_index]
        
        # Get colors based on mode
        if self.flow_mode == 0:  # Blue electric
            flow_color = (0.2, 0.7, 1.0)
        elif self.flow_mode == 1:  # Cyan electric
            flow_color = (0.0, 1.0, 0.8)
        else:  # Multicolor electric
            colors = [(1.0, 0.4, 0.0), (0.0, 1.0, 0.3), (0.8, 0.0, 1.0), (1.0, 1.0, 0.0)]
            flow_color = random.choice(colors)
        
        # Create flow data
        flow = {
            'path': path,
            'start_time': current_time,
            'speed': 0.8 * self.flow_speed,
            'color': flow_color,
            'intensity': 1.0 + random.uniform(-0.2, 0.3)
        }
        
        self.active_flows.append(flow)
        logging.info(f"Electric flow created on path {path_index}")

    def interpolate_path(self, path, progress):
        """Interpolate position along path"""
        if progress <= 0:
            return path[0]
        if progress >= 1:
            return path[-1]
        
        # Find segment
        total_segments = len(path) - 1
        segment_progress = progress * total_segments
        segment_index = int(segment_progress)
        local_progress = segment_progress - segment_index
        
        if segment_index >= total_segments:
            return path[-1]
        
        # Linear interpolation
        start = path[segment_index]
        end = path[segment_index + 1]
        
        x = start[0] + (end[0] - start[0]) * local_progress
        y = start[1] + (end[1] - start[1]) * local_progress
        
        return (x, y)

    def get_path_direction(self, path, progress):
        """Get direction vector at a point on the path"""
        eps = 0.01
        p1 = self.interpolate_path(path, max(0, progress - eps))
        p2 = self.interpolate_path(path, min(1, progress + eps))
        
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.sqrt(dx*dx + dy*dy)
        
        if length > 0:
            return (dx / length, dy / length)
        return (1.0, 0.0)

    def update_vertex_data(self):
        """Update vertex buffer"""
        try:
            current_time = time.time() - self.start_time
            vertices = []
            
            for flow in self.active_flows:
                flow_age = current_time - flow['start_time']
                
                if flow_age > 5.0:
                    continue
                
                path = flow['path']
                r, g, b = flow['color']
                flow_intensity = flow['intensity']
                
                # Create segments for smooth flow
                num_segments = 20
                for i in range(num_segments):
                    segment_progress = float(i) / (num_segments - 1)
                    
                    # Get position and direction
                    pos = self.interpolate_path(path, segment_progress)
                    direction = self.get_path_direction(path, segment_progress)
                    
                    # Create quad for this segment
                    thickness = 0.08
                    
                    # Calculate perpendicular vector
                    perpx = -direction[1] * thickness
                    perpy = direction[0] * thickness
                    
                    # Vary intensity
                    segment_intensity = flow_intensity * (0.8 + 0.2 * math.sin(segment_progress * 6.28))
                    
                    # Create quad vertices
                    vertices.extend([
                        pos[0] - perpx, pos[1] - perpy, 0.0, 0.0, segment_progress, flow_age, r, g, b, direction[0], direction[1], segment_intensity, 0.0,
                        pos[0] + perpx, pos[1] + perpy, 1.0, 0.0, segment_progress, flow_age, r, g, b, direction[0], direction[1], segment_intensity, 0.0,
                        pos[0] - perpx, pos[1] - perpy, 0.0, 1.0, segment_progress, flow_age, r, g, b, direction[0], direction[1], segment_intensity, 0.0,
                        
                        pos[0] + perpx, pos[1] + perpy, 1.0, 0.0, segment_progress, flow_age, r, g, b, direction[0], direction[1], segment_intensity, 0.0,
                        pos[0] + perpx, pos[1] + perpy, 1.0, 1.0, segment_progress, flow_age, r, g, b, direction[0], direction[1], segment_intensity, 0.0,
                        pos[0] - perpx, pos[1] - perpy, 0.0, 1.0, segment_progress, flow_age, r, g, b, direction[0], direction[1], segment_intensity, 0.0
                    ])
            
            if vertices:
                self.vertices = np.array(vertices, dtype=np.float32)
                self.vertex_count = len(vertices) // 13
                
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
        """Render electric flows"""
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
                glUniform1f(glGetUniformLocation(self.shader_program, "globalIntensity"), self.electric_intensity)
                
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
                logging.error(f"Electric flow paint error: {e}")
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
            logging.debug("Cleaning up electric flow")
            
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
            self.active_flows = []
            
        except Exception as e:
            logging.debug(f"Cleanup error (non-critical): {e}")

    def get_controls(self):
        """Return available controls"""
        return {
            "Flow Speed": {
                "type": "slider",
                "min": 20,
                "max": 300,
                "value": int(self.flow_speed * 100),
                "default": 100
            },
            "Electric Intensity": {
                "type": "slider",
                "min": 10,
                "max": 300,
                "value": int(self.electric_intensity * 100),
                "default": 100
            },
            "Flow Mode": {
                "type": "slider",
                "min": 0,
                "max": 2,
                "value": self.flow_mode,
                "default": 0
            }
        }

    def update_control(self, name, value):
        """Update control values"""
        try:
            if name == "Flow Speed":
                self.flow_speed = value / 100.0
            elif name == "Electric Intensity":
                self.electric_intensity = value / 100.0
            elif name == "Flow Mode":
                self.flow_mode = int(value)
        except Exception as e:
            logging.error(f"Error updating control {name}: {e}")

    def trigger_action(self, action_name):
        """Handle MIDI triggers"""
        if action_name == "flow" or action_name == "electric" or action_name == "signal":
            self.create_electric_flow()
            logging.info("Electric flow triggered via MIDI")