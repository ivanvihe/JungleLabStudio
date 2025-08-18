# TODO: migrate to RenderBackend (ModernGL)
# visuals/presets/kaleido_tunney.py
import os
import logging
import numpy as np
import ctypes
import time
import math
from OpenGL.GL import *
from visuals.base_visualizer import BaseVisualizer

# Import OpenGL safety functions
try:
    from opengl_fixes import OpenGLSafety
except ImportError:
    class OpenGLSafety:
        @staticmethod
        def safe_line_width(width):
            try:
                glLineWidth(max(1.0, min(width, 10.0)))
            except:
                glLineWidth(1.0)
        
        @staticmethod
        def check_gl_errors(context=""):
            pass

class KaleidoTunnelVisualizer(BaseVisualizer):
    visual_name = "Kaleido Tunnel"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.program = None
        self.vao = None
        self.vbo = None
        self.ebo = None
        self.start_time = time.time()
        
        # Parameters
        self.rotation_speed = 50
        self.tunnel_depth = 80
        self.color_intensity = 100
        self.pattern_complexity = 60
        self.tunnel_radius = 3.0
        self.segments_per_ring = 32
        self.rings = 50
        
        # Geometry
        self.vertices = None
        self.indices = None
        self.vertex_count = 0

    def get_controls(self):
        return {
            "Rotation Speed": {"type": "slider", "min": 10, "max": 200, "value": self.rotation_speed},
            "Tunnel Depth": {"type": "slider", "min": 20, "max": 150, "value": self.tunnel_depth},
            "Color Intensity": {"type": "slider", "min": 30, "max": 200, "value": self.color_intensity},
            "Pattern Complexity": {"type": "slider", "min": 20, "max": 120, "value": self.pattern_complexity},
            "Tunnel Radius": {"type": "slider", "min": 50, "max": 200, "value": int(self.tunnel_radius * 50)}
        }

    def update_control(self, name, value):
        if name == "Rotation Speed":
            self.rotation_speed = value
        elif name == "Tunnel Depth":
            self.tunnel_depth = value
            self.generate_tunnel_geometry()
            self.setup_buffers()
        elif name == "Color Intensity":
            self.color_intensity = value
        elif name == "Pattern Complexity":
            self.pattern_complexity = value
            self.generate_tunnel_geometry()
            self.setup_buffers()
        elif name == "Tunnel Radius":
            self.tunnel_radius = float(value) / 50.0
            self.generate_tunnel_geometry()
            self.setup_buffers()

    def load_shaders(self):
        """Load shaders with inline fallback"""
        vs_src = """
        #version 330 core
        layout (location = 0) in vec3 aPos;
        layout (location = 1) in vec4 aColor;
        uniform mat4 model;
        uniform mat4 view;
        uniform mat4 projection;
        uniform float time;
        uniform float intensity;
        out vec4 vColor;
        
        void main()
        {
            vec3 pos = aPos;
            
            // Add kaleidoscope wave effects
            float wave1 = sin(time * 2.0 + pos.z * 0.5 + atan(pos.y, pos.x) * 6.0);
            float wave2 = cos(time * 1.5 + pos.z * 0.3 + length(pos.xy) * 4.0);
            
            // Slight position displacement for hypnotic effect
            pos.x += wave1 * 0.05 * intensity;
            pos.y += wave2 * 0.05 * intensity;
            
            gl_Position = projection * view * model * vec4(pos, 1.0);
            
            // Color modulation based on waves
            vec4 modColor = aColor;
            modColor.rgb *= (0.8 + 0.2 * wave1) * (0.8 + 0.2 * wave2);
            modColor.rgb *= intensity;
            
            vColor = modColor;
        }
        """
        
        fs_src = """
        #version 330 core
        in vec4 vColor;
        out vec4 FragColor;
        
        void main()
        {
            FragColor = vec4(vColor.rgb, 0.8);  // Semi-transparent for mixing
        }
        """
        
        return self.compile_shader_program(vs_src, fs_src)

    def compile_shader_program(self, vs_src, fs_src):
        """Compile shader program"""
        try:
            # Vertex shader
            vs = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vs, vs_src)
            glCompileShader(vs)
            
            if not glGetShaderiv(vs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(vs).decode()
                logging.error(f"Vertex shader error: {error}")
                return None
            
            # Fragment shader
            fs = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fs, fs_src)
            glCompileShader(fs)
            
            if not glGetShaderiv(fs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(fs).decode()
                logging.error(f"Fragment shader error: {error}")
                return None
            
            # Program
            program = glCreateProgram()
            glAttachShader(program, vs)
            glAttachShader(program, fs)
            glLinkProgram(program)
            
            if not glGetProgramiv(program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(program).decode()
                logging.error(f"Shader program error: {error}")
                return None
            
            glDeleteShader(vs)
            glDeleteShader(fs)
            
            return program
            
        except Exception as e:
            logging.error(f"Error compiling shaders: {e}")
            return None

    def generate_tunnel_geometry(self):
        """Generate improved tunnel geometry with triangles"""
        try:
            # Adjusted parameters based on controls
            self.segments_per_ring = max(12, int(self.pattern_complexity / 5))
            self.rings = max(20, int(self.tunnel_depth / 2))
            
            vertices = []
            indices = []
            
            # Generate tunnel rings
            for ring in range(self.rings):
                z = -ring * 0.5  # Move backwards into the tunnel
                
                # Variable radius for interesting tunnel shape
                radius_variation = 1.0 + 0.3 * math.sin(ring * 0.2)
                current_radius = self.tunnel_radius * radius_variation
                
                for seg in range(self.segments_per_ring):
                    angle = (seg / self.segments_per_ring) * 2 * math.pi
                    
                    x = current_radius * math.cos(angle)
                    y = current_radius * math.sin(angle)
                    
                    # Kaleidoscope colors based on position and ring
                    hue_base = (angle / (2 * math.pi)) + (ring * 0.1)
                    r = 0.5 + 0.5 * math.sin(hue_base * 6.0)
                    g = 0.5 + 0.5 * math.sin(hue_base * 6.0 + 2.0)
                    b = 0.5 + 0.5 * math.sin(hue_base * 6.0 + 4.0)
                    
                    # Distance-based alpha fading
                    alpha = 0.9 * (1.0 - ring / self.rings)
                    
                    vertices.extend([x, y, z, r, g, b, alpha])
            
            # Generate indices for triangular mesh
            for ring in range(self.rings - 1):
                for seg in range(self.segments_per_ring):
                    # Current ring vertices
                    current = ring * self.segments_per_ring + seg
                    next_seg = ring * self.segments_per_ring + ((seg + 1) % self.segments_per_ring)
                    
                    # Next ring vertices
                    next_ring = (ring + 1) * self.segments_per_ring + seg
                    next_ring_next_seg = (ring + 1) * self.segments_per_ring + ((seg + 1) % self.segments_per_ring)
                    
                    # Two triangles per quad
                    indices.extend([current, next_ring, next_seg])
                    indices.extend([next_seg, next_ring, next_ring_next_seg])
            
            self.vertices = np.array(vertices, dtype=np.float32)
            self.indices = np.array(indices, dtype=np.uint32)
            self.vertex_count = len(self.vertices) // 7
            
            print(f"Generated tunnel: {self.rings} rings x {self.segments_per_ring} segments = {self.vertex_count} vertices")
            
        except Exception as e:
            logging.error(f"Error generating tunnel geometry: {e}")

    def setup_buffers(self):
        """Setup OpenGL buffers"""
        try:
            if self.vertices is None:
                return
            
            # Cleanup old buffers
            if self.vao:
                glDeleteVertexArrays(1, [self.vao])
            if self.vbo:
                glDeleteBuffers(1, [self.vbo])
            if self.ebo:
                glDeleteBuffers(1, [self.ebo])
            
            # Create new buffers
            self.vao = glGenVertexArrays(1)
            self.vbo = glGenBuffers(1)
            self.ebo = glGenBuffers(1)
            
            glBindVertexArray(self.vao)
            
            # Vertex buffer
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
            
            # Position attribute
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 7 * 4, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            
            # Color attribute
            glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 7 * 4, ctypes.c_void_p(3 * 4))
            glEnableVertexAttribArray(1)
            
            # Index buffer
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)
            
            glBindVertexArray(0)
            
        except Exception as e:
            logging.error(f"Error setting up buffers: {e}")

    def initializeGL(self):
        """Initialize OpenGL state"""
        logging.info("KaleidoTunnel: Initializing...")
        
        # TRANSPARENT BACKGROUND FOR MIXING
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)
        
        # Load shaders
        self.program = self.load_shaders()
        if not self.program:
            logging.error("KaleidoTunnel: Failed to load shaders")
            return
        
        # Generate geometry
        self.generate_tunnel_geometry()
        self.setup_buffers()
        
        logging.info("KaleidoTunnel: Initialized successfully")

    def paintGL(self):
        """Render the kaleidoscope tunnel"""
        try:
            if not self.program or not self.vao:
                return
            
            # CLEAR WITH TRANSPARENT BACKGROUND
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            glUseProgram(self.program)
            
            # Set up matrices
            current_time = time.time() - self.start_time
            
            # Model matrix (rotation around Z axis for kaleidoscope effect)
            model = np.eye(4, dtype=np.float32)
            rotation_angle = current_time * self.rotation_speed * 0.01
            cos_a, sin_a = math.cos(rotation_angle), math.sin(rotation_angle)
            model[0, 0] = cos_a
            model[0, 1] = -sin_a
            model[1, 0] = sin_a
            model[1, 1] = cos_a
            
            # View matrix - camera moving forward through tunnel
            forward_movement = (current_time * 2.0) % 1.0  # Cycle every 0.5 seconds
            eye_z = 5.0 - forward_movement * 1.0
            view = self.look_at(
                np.array([0, 0, eye_z]), 
                np.array([0, 0, 0]), 
                np.array([0, 1, 0])
            )
            
            # Projection matrix
            projection = self.perspective(60, 1.0, 0.1, 100.0)
            
            # Set uniforms
            glUniformMatrix4fv(glGetUniformLocation(self.program, "model"), 1, GL_FALSE, model)
            glUniformMatrix4fv(glGetUniformLocation(self.program, "view"), 1, GL_FALSE, view)
            glUniformMatrix4fv(glGetUniformLocation(self.program, "projection"), 1, GL_FALSE, projection)
            glUniform1f(glGetUniformLocation(self.program, "time"), current_time)
            glUniform1f(glGetUniformLocation(self.program, "intensity"), self.color_intensity / 100.0)
            
            # Draw tunnel
            glBindVertexArray(self.vao)
            glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
            glBindVertexArray(0)
            
            glUseProgram(0)
            
        except Exception as e:
            logging.error(f"KaleidoTunnel paint error: {e}")

    def look_at(self, eye, center, up):
        """Create look-at matrix"""
        f = center - eye
        f = f / np.linalg.norm(f)
        u = up / np.linalg.norm(up)
        s = np.cross(f, u)
        s = s / np.linalg.norm(s)
        u = np.cross(s, f)
        
        return np.array([
            [s[0], u[0], -f[0], 0],
            [s[1], u[1], -f[1], 0],
            [s[2], u[2], -f[2], 0],
            [-np.dot(s, eye), -np.dot(u, eye), np.dot(f, eye), 1]
        ], dtype=np.float32)

    def perspective(self, fovy, aspect, near, far):
        """Create perspective matrix"""
        f = 1.0 / math.tan(math.radians(fovy) / 2.0)
        return np.array([
            [f/aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far+near)/(near-far), (2*far*near)/(near-far)],
            [0, 0, -1, 0]
        ], dtype=np.float32)

    def resizeGL(self, w, h):
        """Handle resize"""
        glViewport(0, 0, w, h)

    def cleanup(self):
        """Clean up resources"""
        try:
            if self.program:
                glDeleteProgram(self.program)
                self.program = None
            if self.vao:
                glDeleteVertexArrays(1, [self.vao])
                self.vao = None
            if self.vbo:
                glDeleteBuffers(1, [self.vbo])
                self.vbo = None
            if self.ebo:
                glDeleteBuffers(1, [self.ebo])
                self.ebo = None
            logging.info("KaleidoTunnel: Cleaned up")
        except Exception as e:
            logging.error(f"KaleidoTunnel cleanup error: {e}")