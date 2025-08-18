# TODO: migrate to RenderBackend (ModernGL)
# visuals/presets/infinite_neural_network.py
import logging
import numpy as np
import ctypes
import time
import math
import random
from OpenGL.GL import *
try:
    from OpenGL.GL import (
        GL_SRC_ALPHA,
        GL_ONE,
        GL_ONE_MINUS_SRC_ALPHA,
        GL_NO_ERROR,
        GL_ALIASED_LINE_WIDTH_RANGE,
    )
except Exception:  # pragma: no cover - fallback for minimal GL stubs
    GL_SRC_ALPHA = 0x0302
    GL_ONE = 1
    GL_ONE_MINUS_SRC_ALPHA = 0x0303
    GL_NO_ERROR = 0
    GL_ALIASED_LINE_WIDTH_RANGE = 0x846E
from ..base_visualizer import BaseVisualizer

class InfiniteNeuralNetworkVisualizer(BaseVisualizer):
    """Ultra-high quality infinite zoom neural network with seamless travel through the network"""
    
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

        # Enhanced network state
        self.nodes = []
        self.connections = []
        self.max_nodes = 300
        self.max_connections = 800
        
        # Visual parameters for premium quality
        self.intensity = 1.2
        self.travel_speed = 0.8
        self.connection_distance = 0.6
        self.node_spawn_rate = 1.2
        self.color_scheme = 0  # 0=neural_blue, 1=cyber_purple, 2=matrix_green, 3=fire_orange
        
        # Infinite zoom system
        self.camera_z = 0.0
        self.zoom_layers = 5  # More layers for smoother transition
        self.layer_spacing = 4.0
        self.fov_factor = 1.0
        
        # Node generation
        self.node_id_counter = 0
        self.last_spawn_time = 0.0
        
        # Pre-allocated buffers
        self.node_vertices = None
        self.connection_vertices = None
        self.node_count = 0
        self.connection_count = 0
        
        logging.info("🧠 Ultra-high quality Infinite Neural Network created")
        
        # Initialize the network
        self.generate_initial_network()

    def initializeGL(self):
        """Initialize OpenGL with premium settings"""
        try:
            logging.debug("InfiniteNeuralNetworkVisualizer.initializeGL called")
            
            # Clear any existing GL errors
            while glGetError() != GL_NO_ERROR:
                pass
            
            # Premium OpenGL setup
            glClearColor(0.0, 0.0, 0.0, 0.0)  # Transparent background
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # Additive blending for premium glow
            glDisable(GL_DEPTH_TEST)
            glEnable(GL_PROGRAM_POINT_SIZE)

            # Ensure line width is within supported range to avoid GL_INVALID_VALUE errors
            try:
                min_width, max_width = glGetFloatv(GL_ALIASED_LINE_WIDTH_RANGE)
                safe_width = float(np.clip(2.0, min_width, max_width))
                glLineWidth(safe_width)
                logging.debug(
                    f"Line width set to {safe_width:.1f} (supported range {min_width}-{max_width})"
                )
            except Exception:
                # Fallback to default line width when querying fails
                glLineWidth(1.0)
            
            # Anti-aliasing hints
            glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
            glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)
            
            # Load enhanced shaders
            if not self.load_enhanced_shaders():
                logging.error("Failed to load enhanced shaders")
                return
            
            # Setup premium geometry
            if not self.setup_enhanced_geometry():
                logging.error("Failed to setup enhanced geometry")
                return
            
            self.initialized = True
            logging.info("🚀 Ultra-premium infinite neural network initialized")
            
        except Exception as e:
            logging.error(f"Error in initialization: {e}")
            import traceback
            traceback.print_exc()

    def load_enhanced_shaders(self):
        """Load premium quality neural network shaders"""
        try:
            # Enhanced node vertex shader
            node_vertex_shader = """
            #version 330 core
            layout (location = 0) in vec3 aPos;
            layout (location = 1) in vec3 aColor;
            layout (location = 2) in float aSize;
            layout (location = 3) in float aActivity;
            layout (location = 4) in float aPulse;
            layout (location = 5) in float aLayer;
            
            uniform float time;
            uniform float intensity;
            uniform float cameraZ;
            uniform float fovFactor;
            uniform vec2 resolution;
            
            out vec3 color;
            out float alpha;
            out float activity;
            out vec2 screenPos;
            
            void main()
            {
                // Calculate 3D position with infinite zoom
                vec3 worldPos = aPos;
                worldPos.z += aLayer * 4.0;  // Layer spacing
                
                // Apply camera movement (traveling into the network)
                worldPos.z -= cameraZ;
                
                // Perspective projection
                float w = 1.0 + worldPos.z * 0.1;
                vec2 projected = worldPos.xy / max(w, 0.1);
                
                gl_Position = vec4(projected * fovFactor, 0.0, 1.0);
                screenPos = projected;
                
                // Enhanced size calculation with perspective and pulsing
                float distance = length(worldPos);
                float perspectiveScale = 50.0 / max(w, 0.1);
                float pulse = sin(time * 8.0 + aPulse) * 0.4 + 0.6;
                float activityPulse = sin(time * 15.0 + aActivity * 10.0) * 0.3 + 0.7;
                
                gl_PointSize = aSize * perspectiveScale * pulse * activityPulse * intensity;
                
                color = aColor;
                activity = aActivity;
                
                // Distance-based alpha for smooth fade in/out
                float fadeIn = smoothstep(-2.0, 0.0, worldPos.z);
                float fadeOut = 1.0 - smoothstep(8.0, 12.0, worldPos.z);
                alpha = fadeIn * fadeOut * intensity;
            }
            """
            
            # Enhanced node fragment shader
            node_fragment_shader = """
            #version 330 core
            in vec3 color;
            in float alpha;
            in float activity;
            in vec2 screenPos;
            
            uniform float time;
            uniform vec2 resolution;
            
            out vec4 FragColor;
            
            void main()
            {
                vec2 coord = gl_PointCoord - vec2(0.5);
                float dist = length(coord);
                
                // Multi-layer node with core, ring, and outer glow
                float core = exp(-pow(dist / 0.15, 2.0));
                float ring = exp(-pow((dist - 0.3) / 0.1, 2.0)) * 0.8;
                float outerGlow = exp(-pow(dist / 0.5, 1.2)) * 0.4;
                
                // Activity-based pulsing
                float activityGlow = sin(time * 12.0 + activity * 20.0) * 0.3 + 0.7;
                float finalIntensity = (core + ring + outerGlow) * activityGlow;
                
                // Discard weak fragments for performance
                if (finalIntensity < 0.02) discard;
                
                // Enhanced color with activity influence
                vec3 finalColor = color * (1.0 + activity * 0.5);
                
                FragColor = vec4(finalColor, finalIntensity * alpha);
            }
            """
            
            # Enhanced connection vertex shader
            connection_vertex_shader = """
            #version 330 core
            layout (location = 0) in vec3 aPos;
            layout (location = 1) in vec3 aColor;
            layout (location = 2) in float aAlpha;
            layout (location = 3) in float aActivity;
            layout (location = 4) in float aLayer;
            
            uniform float time;
            uniform float intensity;
            uniform float cameraZ;
            uniform float fovFactor;
            
            out vec3 color;
            out float alpha;
            out float activity;
            
            void main()
            {
                // Calculate 3D position
                vec3 worldPos = aPos;
                worldPos.z += aLayer * 4.0;
                worldPos.z -= cameraZ;
                
                // Perspective projection
                float w = 1.0 + worldPos.z * 0.1;
                vec2 projected = worldPos.xy / max(w, 0.1);
                
                gl_Position = vec4(projected * fovFactor, 0.0, 1.0);
                
                color = aColor;
                activity = aActivity;
                
                // Distance-based alpha
                float fadeIn = smoothstep(-2.0, 0.0, worldPos.z);
                float fadeOut = 1.0 - smoothstep(8.0, 12.0, worldPos.z);
                alpha = aAlpha * fadeIn * fadeOut * intensity * 0.8;
            }
            """
            
            # Enhanced connection fragment shader
            connection_fragment_shader = """
            #version 330 core
            in vec3 color;
            in float alpha;
            in float activity;
            
            uniform float time;
            
            out vec4 FragColor;
            
            void main()
            {
                // Animated connection with data flow effect
                float flow = sin(time * 6.0 + activity * 15.0) * 0.4 + 0.6;
                vec3 finalColor = color * flow;
                
                FragColor = vec4(finalColor, alpha);
            }
            """
            
            # Compile node shaders
            node_vs = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(node_vs, node_vertex_shader)
            glCompileShader(node_vs)
            
            if not glGetShaderiv(node_vs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(node_vs).decode()
                logging.error(f"Node vertex shader compilation failed: {error}")
                return False
            
            node_fs = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(node_fs, node_fragment_shader)
            glCompileShader(node_fs)
            
            if not glGetShaderiv(node_fs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(node_fs).decode()
                logging.error(f"Node fragment shader compilation failed: {error}")
                return False
            
            self.node_program = glCreateProgram()
            glAttachShader(self.node_program, node_vs)
            glAttachShader(self.node_program, node_fs)
            glLinkProgram(self.node_program)
            
            if not glGetProgramiv(self.node_program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(self.node_program).decode()
                logging.error(f"Node shader program linking failed: {error}")
                return False
            
            # Compile connection shaders
            conn_vs = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(conn_vs, connection_vertex_shader)
            glCompileShader(conn_vs)
            
            if not glGetShaderiv(conn_vs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(conn_vs).decode()
                logging.error(f"Connection vertex shader compilation failed: {error}")
                return False
            
            conn_fs = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(conn_fs, connection_fragment_shader)
            glCompileShader(conn_fs)
            
            if not glGetShaderiv(conn_fs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(conn_fs).decode()
                logging.error(f"Connection fragment shader compilation failed: {error}")
                return False
            
            self.connection_program = glCreateProgram()
            glAttachShader(self.connection_program, conn_vs)
            glAttachShader(self.connection_program, conn_fs)
            glLinkProgram(self.connection_program)
            
            if not glGetProgramiv(self.connection_program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(self.connection_program).decode()
                logging.error(f"Connection shader program linking failed: {error}")
                return False
            
            # Clean up
            glDeleteShader(node_vs)
            glDeleteShader(node_fs)
            glDeleteShader(conn_vs)
            glDeleteShader(conn_fs)
            
            logging.debug("Enhanced neural network shaders compiled successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error loading enhanced shaders: {e}")
            return False

    def setup_enhanced_geometry(self):
        """Setup enhanced vertex data for nodes and connections"""
        try:
            # Setup node geometry with more attributes
            self.node_vao = glGenVertexArrays(1)
            glBindVertexArray(self.node_vao)
            
            self.node_vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.node_vbo)
            
            # Node attributes: pos(3) + color(3) + size(1) + activity(1) + pulse(1) + layer(1) = 10 floats
            node_vertex_size = 10 * 4
            glBufferData(GL_ARRAY_BUFFER, self.max_nodes * node_vertex_size, None, GL_DYNAMIC_DRAW)
            
            # Node attributes
            glEnableVertexAttribArray(0)  # Position (3D)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, node_vertex_size, ctypes.c_void_p(0))
            glEnableVertexAttribArray(1)  # Color
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, node_vertex_size, ctypes.c_void_p(3 * 4))
            glEnableVertexAttribArray(2)  # Size
            glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, node_vertex_size, ctypes.c_void_p(6 * 4))
            glEnableVertexAttribArray(3)  # Activity
            glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, node_vertex_size, ctypes.c_void_p(7 * 4))
            glEnableVertexAttribArray(4)  # Pulse
            glVertexAttribPointer(4, 1, GL_FLOAT, GL_FALSE, node_vertex_size, ctypes.c_void_p(8 * 4))
            glEnableVertexAttribArray(5)  # Layer
            glVertexAttribPointer(5, 1, GL_FLOAT, GL_FALSE, node_vertex_size, ctypes.c_void_p(9 * 4))
            
            # Setup connection geometry
            self.connection_vao = glGenVertexArrays(1)
            glBindVertexArray(self.connection_vao)
            
            self.connection_vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.connection_vbo)
            
            # Connection attributes: pos(3) + color(3) + alpha(1) + activity(1) + layer(1) = 9 floats
            conn_vertex_size = 9 * 4
            glBufferData(GL_ARRAY_BUFFER, self.max_connections * 2 * conn_vertex_size, None, GL_DYNAMIC_DRAW)
            
            # Connection attributes
            glEnableVertexAttribArray(0)  # Position (3D)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, conn_vertex_size, ctypes.c_void_p(0))
            glEnableVertexAttribArray(1)  # Color
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, conn_vertex_size, ctypes.c_void_p(3 * 4))
            glEnableVertexAttribArray(2)  # Alpha
            glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, conn_vertex_size, ctypes.c_void_p(6 * 4))
            glEnableVertexAttribArray(3)  # Activity
            glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, conn_vertex_size, ctypes.c_void_p(7 * 4))
            glEnableVertexAttribArray(4)  # Layer
            glVertexAttribPointer(4, 1, GL_FLOAT, GL_FALSE, conn_vertex_size, ctypes.c_void_p(8 * 4))
            
            # Unbind
            glBindVertexArray(0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            
            logging.debug("Enhanced neural network geometry setup complete")
            return True
            
        except Exception as e:
            logging.error(f"Error setting up enhanced geometry: {e}")
            return False

    def generate_initial_network(self):
        """Generate initial neural network structure"""
        current_time = time.time() - self.start_time
        
        # Create nodes in multiple layers
        for layer in range(self.zoom_layers):
            nodes_in_layer = 40 + layer * 10
            for _ in range(nodes_in_layer):
                self.create_node(current_time, layer)

    def create_node(self, current_time, layer=None):
        """Create a new neural node"""
        if len(self.nodes) >= self.max_nodes:
            return
        
        if layer is None:
            layer = random.randint(0, self.zoom_layers - 1)
        
        # 3D position with proper spacing
        angle_xy = random.uniform(0, 2 * math.pi)
        angle_z = random.uniform(0, 2 * math.pi)
        radius = random.uniform(0.5, 3.0)
        
        x = radius * math.cos(angle_xy) * math.cos(angle_z)
        y = radius * math.sin(angle_xy) * math.cos(angle_z)
        z = radius * math.sin(angle_z)
        
        # Enhanced color schemes
        color_schemes = {
            0: [(0.2, 0.7, 1.0), (0.1, 0.9, 1.0), (0.0, 0.6, 0.9)],  # Neural blue
            1: [(0.8, 0.2, 1.0), (1.0, 0.4, 0.8), (0.6, 0.1, 0.9)],  # Cyber purple
            2: [(0.2, 1.0, 0.3), (0.4, 0.9, 0.2), (0.1, 0.8, 0.4)],  # Matrix green
            3: [(1.0, 0.6, 0.2), (1.0, 0.8, 0.1), (0.9, 0.4, 0.0)]   # Fire orange
        }
        
        colors = color_schemes.get(self.color_scheme, color_schemes[0])
        color = random.choice(colors)
        
        node = {
            'id': self.node_id_counter,
            'pos': [x, y, z],
            'color': color,
            'size': random.uniform(15.0, 35.0),
            'activity': random.uniform(0.0, 1.0),
            'pulse': random.uniform(0.0, 2 * math.pi),
            'layer': layer,
            'birth_time': current_time,
            'connections': []
        }
        
        self.nodes.append(node)
        self.node_id_counter += 1

    def update_network(self):
        """Update the entire neural network system"""
        current_time = time.time() - self.start_time
        
        # Update camera for infinite zoom effect
        speed = getattr(self, 'current_travel_speed', self.travel_speed)
        self.camera_z += speed * 0.1
        
        # Spawn new nodes in front layers
        if current_time - self.last_spawn_time > (1.0 / self.node_spawn_rate):
            front_layer = int(self.camera_z / self.layer_spacing) + self.zoom_layers
            self.create_node(current_time, front_layer % self.zoom_layers)
            self.last_spawn_time = current_time
        
        # Remove nodes that are too far behind
        max_distance = self.layer_spacing * (self.zoom_layers + 2)
        self.nodes = [node for node in self.nodes 
                     if (node['layer'] * self.layer_spacing - self.camera_z) > -max_distance]
        
        # Update node activities (neural firing simulation)
        for node in self.nodes:
            node['activity'] = max(0.0, node['activity'] + random.uniform(-0.1, 0.1))
            node['activity'] = min(1.0, node['activity'])
        
        # Update connections
        self.update_connections(current_time)

    def update_connections(self, current_time):
        """Update neural network connections with activity propagation"""
        self.connections = []
        
        # Create connections between nearby nodes
        for i, node1 in enumerate(self.nodes):
            for j, node2 in enumerate(self.nodes[i+1:], i+1):
                # Only connect nodes in similar layers
                if abs(node1['layer'] - node2['layer']) > 1:
                    continue
                
                # Calculate 3D distance
                dx = node1['pos'][0] - node2['pos'][0]
                dy = node1['pos'][1] - node2['pos'][1]
                dz = node1['pos'][2] - node2['pos'][2]
                distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                
                # Connect if within range
                if distance < self.connection_distance:
                    # Connection strength based on distance and activity
                    strength = (1.0 - distance / self.connection_distance)
                    activity = (node1['activity'] + node2['activity']) * 0.5
                    
                    # Blend colors based on activity
                    blend_factor = activity
                    r = node1['color'][0] * (1-blend_factor) + node2['color'][0] * blend_factor
                    g = node1['color'][1] * (1-blend_factor) + node2['color'][1] * blend_factor
                    b = node1['color'][2] * (1-blend_factor) + node2['color'][2] * blend_factor
                    
                    connection = {
                        'start': node1['pos'][:],
                        'end': node2['pos'][:],
                        'color': (r, g, b),
                        'alpha': strength * activity * 0.9,
                        'activity': activity,
                        'layer': (node1['layer'] + node2['layer']) * 0.5
                    }
                    
                    self.connections.append(connection)
                    
                    if len(self.connections) >= self.max_connections:
                        return

    def update_vertex_data(self):
        """Update vertex buffers with enhanced data"""
        try:
            current_time = time.time() - self.start_time
            
            # Update nodes
            node_vertices = []
            for node in self.nodes:
                x, y, z = node['pos']
                r, g, b = node['color']
                
                node_vertices.extend([
                    x, y, z,                    # Position (3D)
                    r, g, b,                    # Color
                    node['size'],               # Size
                    node['activity'],           # Activity
                    node['pulse'],              # Pulse offset
                    float(node['layer'])        # Layer
                ])
            
            if node_vertices:
                self.node_vertices = np.array(node_vertices, dtype=np.float32)
                self.node_count = len(node_vertices) // 10
                
                # Upload node data
                glBindBuffer(GL_ARRAY_BUFFER, self.node_vbo)
                glBufferSubData(GL_ARRAY_BUFFER, 0, self.node_vertices.nbytes, self.node_vertices)
                glBindBuffer(GL_ARRAY_BUFFER, 0)
            else:
                self.node_count = 0
            
            # Update connections
            connection_vertices = []
            for conn in self.connections:
                r, g, b = conn['color']
                alpha = conn['alpha']
                activity = conn['activity']
                layer = conn['layer']
                
                # Start vertex
                x1, y1, z1 = conn['start']
                connection_vertices.extend([
                    x1, y1, z1,         # Position
                    r, g, b,            # Color
                    alpha,              # Alpha
                    activity,           # Activity
                    layer               # Layer
                ])
                
                # End vertex
                x2, y2, z2 = conn['end']
                connection_vertices.extend([
                    x2, y2, z2,         # Position
                    r, g, b,            # Color
                    alpha,              # Alpha
                    activity,           # Activity
                    layer               # Layer
                ])
            
            if connection_vertices:
                self.connection_vertices = np.array(connection_vertices, dtype=np.float32)
                self.connection_count = len(connection_vertices) // 9
                
                # Upload connection data
                glBindBuffer(GL_ARRAY_BUFFER, self.connection_vbo)
                glBufferSubData(GL_ARRAY_BUFFER, 0, self.connection_vertices.nbytes, self.connection_vertices)
                glBindBuffer(GL_ARRAY_BUFFER, 0)
            else:
                self.connection_count = 0
            
        except Exception as e:
            logging.error(f"Error updating enhanced vertex data: {e}")
            self.node_count = 0
            self.connection_count = 0

    def paintGL(self):
        """Render ultra-high quality infinite neural network"""
        try:
            if not self.initialized:
                glClearColor(0.0, 0.0, 0.0, 0.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return

            # Clear with transparent background
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)

            # Audio-reactive parameters
            bass, mid, treble = self.get_audio_bands()
            self.current_travel_speed = self.travel_speed * (0.5 + bass)
            current_intensity = self.intensity * (0.5 + treble)

            # Update the network
            self.update_network()
            self.update_vertex_data()

            current_time = time.time() - self.start_time
            
            # Render connections first (behind nodes)
            if self.connection_count > 0 and self.connection_program:
                glUseProgram(self.connection_program)
                
                # Update uniforms
                glUniform1f(glGetUniformLocation(self.connection_program, "time"), current_time)
                glUniform1f(glGetUniformLocation(self.connection_program, "intensity"), current_intensity)
                glUniform1f(glGetUniformLocation(self.connection_program, "cameraZ"), self.camera_z)
                glUniform1f(glGetUniformLocation(self.connection_program, "fovFactor"), self.fov_factor)
                
                # Draw connections
                glBindVertexArray(self.connection_vao)
                glDrawArrays(GL_LINES, 0, self.connection_count)
                glBindVertexArray(0)
                
                glUseProgram(0)
            
            # Render nodes
            if self.node_count > 0 and self.node_program:
                glUseProgram(self.node_program)
                
                # Update uniforms
                glUniform1f(glGetUniformLocation(self.node_program, "time"), current_time)
                glUniform1f(glGetUniformLocation(self.node_program, "intensity"), current_intensity)
                glUniform1f(glGetUniformLocation(self.node_program, "cameraZ"), self.camera_z)
                glUniform1f(glGetUniformLocation(self.node_program, "fovFactor"), self.fov_factor)
                glUniform2f(glGetUniformLocation(self.node_program, "resolution"), 1920.0, 1080.0)
                
                # Draw nodes
                glBindVertexArray(self.node_vao)
                glDrawArrays(GL_POINTS, 0, self.node_count)
                glBindVertexArray(0)
                
                glUseProgram(0)
            
        except Exception as e:
            # Only log errors occasionally
            if not hasattr(self, '_last_error_time') or \
               time.time() - self._last_error_time > 5:
                logging.error(f"Ultra neural network paint error: {e}")
                self._last_error_time = time.time()

            # Fallback rendering
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def resizeGL(self, width, height):
        """Handle resize with enhanced viewport"""
        glViewport(0, 0, width, height)
        # Update FOV factor based on aspect ratio
        if height > 0:
            self.fov_factor = max(1.0, width / height)

    def cleanup(self):
        """Clean up OpenGL resources"""
        try:
            logging.debug("Cleaning up ultra neural network visualizer")
            
            # Clean up programs
            for program in [getattr(self, 'node_program', None), getattr(self, 'connection_program', None)]:
                if program:
                    try:
                        if glIsProgram(program):
                            glDeleteProgram(program)
                    except:
                        pass
            
            # Clean up VAOs
            for vao in [self.node_vao, self.connection_vao]:
                if vao:
                    try:
                        glDeleteVertexArrays(1, [vao])
                    except:
                        pass
            
            # Clean up VBOs
            for vbo in [self.node_vbo, self.connection_vbo]:
                if vbo:
                    try:
                        glDeleteBuffers(1, [vbo])
                    except:
                        pass
            
            self.initialized = False
            self.nodes = []
            self.connections = []
            
        except Exception as e:
            logging.debug(f"Cleanup error (non-critical): {e}")

    def get_controls(self):
        """Return enhanced controls"""
        controls = super().get_controls()
        controls.update({
            "Intensity": {
                "type": "slider",
                "min": 20,
                "max": 300,
                "value": int(self.intensity * 100),
                "default": 120
            },
            "Travel Speed": {
                "type": "slider",
                "min": 10,
                "max": 200,
                "value": int(self.travel_speed * 100),
                "default": 80
            },
            "Connection Range": {
                "type": "slider",
                "min": 20,
                "max": 150,
                "value": int(self.connection_distance * 100),
                "default": 60
            },
            "Node Spawn Rate": {
                "type": "slider",
                "min": 20,
                "max": 300,
                "value": int(self.node_spawn_rate * 100),
                "default": 120
            },
            "Color Scheme": {
                "type": "slider",
                "min": 0,
                "max": 3,
                "value": self.color_scheme,
                "default": 0
            },
            "FOV Factor": {
                "type": "slider",
                "min": 50,
                "max": 200,
                "value": int(self.fov_factor * 100),
                "default": 100
            }
        })
        return controls

    def update_control(self, name, value):
        """Update enhanced control values"""
        try:
            if super().update_control(name, value):
                return
            if name == "Intensity":
                self.intensity = value / 100.0
            elif name == "Travel Speed":
                self.travel_speed = value / 100.0
            elif name == "Connection Range":
                self.connection_distance = value / 100.0
            elif name == "Node Spawn Rate":
                self.node_spawn_rate = value / 100.0
            elif name == "Color Scheme":
                self.color_scheme = int(value)
                # Regenerate colors for existing nodes
                self.update_node_colors()
            elif name == "FOV Factor":
                self.fov_factor = value / 100.0
        except Exception as e:
            logging.error(f"Error updating control {name}: {e}")

    def update_node_colors(self):
        """Update colors of existing nodes when color scheme changes"""
        color_schemes = {
            0: [(0.2, 0.7, 1.0), (0.1, 0.9, 1.0), (0.0, 0.6, 0.9)],  # Neural blue
            1: [(0.8, 0.2, 1.0), (1.0, 0.4, 0.8), (0.6, 0.1, 0.9)],  # Cyber purple
            2: [(0.2, 1.0, 0.3), (0.4, 0.9, 0.2), (0.1, 0.8, 0.4)],  # Matrix green
            3: [(1.0, 0.6, 0.2), (1.0, 0.8, 0.1), (0.9, 0.4, 0.0)]   # Fire orange
        }
        
        colors = color_schemes.get(self.color_scheme, color_schemes[0])
        
        for node in self.nodes:
            node['color'] = random.choice(colors)

    def trigger_action(self, action_name):
        """Handle enhanced MIDI triggers"""
        if action_name in ["neural", "network", "zoom", "brain", "synapse"]:
            current_time = time.time() - self.start_time
            
            # Create neural burst effect
            burst_count = random.randint(15, 30)
            burst_layer = random.randint(0, self.zoom_layers - 1)
            
            for _ in range(burst_count):
                self.create_node(current_time, burst_layer)
            
            # Increase activity of existing nodes
            for node in self.nodes:
                node['activity'] = min(1.0, node['activity'] + random.uniform(0.3, 0.7))
            
            # Temporarily boost travel speed for dramatic effect
            original_speed = self.travel_speed
            self.travel_speed = min(2.0, self.travel_speed * 1.5)
            
            # Reset speed after a short time (this would need a timer in a real implementation)
            logging.info(f"🧠 NEURAL BURST ACTIVATED! {burst_count} nodes spawned via MIDI trigger")
        
        elif action_name in ["pulse", "fire", "activate"]:
            # Pulse all nodes simultaneously
            current_time = time.time() - self.start_time
            pulse_phase = random.uniform(0, 2 * math.pi)
            
            for node in self.nodes:
                node['pulse'] = pulse_phase
                node['activity'] = min(1.0, node['activity'] + 0.5)
            
            logging.info("⚡ NEURAL PULSE! All nodes synchronized via MIDI")
        
        elif action_name in ["reset", "clear", "restart"]:
            # Clear network and restart
            self.nodes = []
            self.connections = []
            self.camera_z = 0.0
            self.node_id_counter = 0
            
            # Regenerate initial network
            self.generate_initial_network()
            
            logging.info("🔄 NEURAL NETWORK RESET! Starting fresh journey")

    def get_visual_info(self):
        """Return information about this visualizer"""
        return {
            "name": self.visual_name,
            "description": "Ultra-high quality infinite zoom neural network with seamless 3D travel through interconnected nodes",
            "features": [
                "Infinite zoom with seamless layer transitions",
                "3D perspective projection",
                "Dynamic neural activity simulation", 
                "Multiple premium color schemes",
                "Enhanced particle effects with multi-layer glow",
                "Activity-based connection pulsing",
                "Transparent background support",
                "Real-time network generation and cleanup",
                "MIDI-triggered neural bursts and effects"
            ],
            "controls": len(self.get_controls()),
            "performance": "Optimized for 60+ FPS with up to 300 nodes and 800 connections"
        }