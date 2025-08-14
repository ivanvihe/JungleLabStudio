# visuals/presets/kaleido_tunney.py
import os  # ← FIX: Add missing import
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
        self.start_time = time.time()
        
        # Parameters
        self.rotation_speed = 50
        self.tunnel_depth = 80
        self.color_intensity = 100
        self.pattern_complexity = 60
        
        # Geometry
        self.vertices = None
        self.vertex_count = 0

    def get_controls(self):
        return {
            "Rotation Speed": {"type": "slider", "min": 10, "max": 200, "value": self.rotation_speed},
            "Tunnel Depth": {"type": "slider", "min": 20, "max": 150, "value": self.tunnel_depth},
            "Color Intensity": {"type": "slider", "min": 30, "max": 200, "value": self.color_intensity},
            "Pattern Complexity": {"type": "slider", "min": 20, "max": 120, "value": self.pattern_complexity}
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

    def load_shaders(self):
        """Load shaders from files or use fallback"""
        script_dir = os.path.dirname(__file__)  # Now os is properly imported
        vert_path = os.path.join(script_dir, "../../shaders/basic.vert")
        frag_path = os.path.join(script_dir, "../../shaders/basic.frag")
        
        # Try to load from files
        vs_src = None
        fs_src = None
        
        try:
            if os.path.exists(vert_path):
                with open(vert_path, 'r') as f:
                    vs_src = f.read()
            if os.path.exists(frag_path):
                with open(frag_path, 'r') as f:
                    fs_src = f.read()
        except Exception as e:
            logging.warning(f"Could not load shader files: {e}")
        
        # Fallback shaders
        if not vs_src:
            vs_src = """
            #version 330 core
            layout (location = 0) in vec3 aPos;
            layout (location = 1) in vec4 aColor;
            uniform mat4 model;
            uniform mat4 view;
            uniform mat4 projection;
            uniform float time;
            out vec4 vColor;
            void main()
            {
                vec3 pos = aPos;
                pos.z += sin(time + aPos.x * 0.5) * 0.2;
                gl_Position = projection * view * model * vec4(pos, 1.0);
                vColor = aColor;
            }
            """
        
        if not fs_src:
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
        """Generate tunnel geometry"""
        try:
            segments = max(8, self.pattern_complexity // 10)
            rings = max(10, self.tunnel_depth // 8)
            
            vertices = []
            
            for ring in range(rings):
                z = -ring * 0.5
                radius = 1.0 + ring * 0.1
                
                for seg in range(segments):
                    angle = (seg / segments) * 2 * math.pi
                    x = radius * math.cos(angle)
                    y = radius * math.sin(angle)
                    
                    # Color based on position
                    r = 0.5 + 0.5 * math.sin(angle + ring * 0.2)
                    g = 0.5 + 0.5 * math.cos(angle * 1.5 + ring * 0.1)
                    b = 0.5 + 0.5 * math.sin(angle * 2 + ring * 0.3)
                    a = 0.8
                    
                    vertices.extend([x, y, z, r, g, b, a])
            
            self.vertices = np.array(vertices, dtype=np.float32)
            self.vertex_count = len(vertices) // 7
            
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
            
            # Create new buffers
            self.vao = glGenVertexArrays(1)
            self.vbo = glGenBuffers(1)
            
            glBindVertexArray(self.vao)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
            
            # Position attribute
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 7 * 4, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            
            # Color attribute
            glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 7 * 4, ctypes.c_void_p(3 * 4))
            glEnableVertexAttribArray(1)
            
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
            
            # Model matrix (rotation)
            model = np.eye(4, dtype=np.float32)
            rotation_angle = current_time * self.rotation_speed * 0.01
            cos_a, sin_a = math.cos(rotation_angle), math.sin(rotation_angle)
            model[0, 0] = cos_a
            model[0, 1] = -sin_a
            model[1, 0] = sin_a
            model[1, 1] = cos_a
            
            # View matrix
            view = self.look_at(
                np.array([0, 0, 3]), 
                np.array([0, 0, 0]), 
                np.array([0, 1, 0])
            )
            
            # Projection matrix
            projection = self.perspective(45, 1.0, 0.1, 100.0)
            
            # Set uniforms
            glUniformMatrix4fv(glGetUniformLocation(self.program, "model"), 1, GL_TRUE, model)
            glUniformMatrix4fv(glGetUniformLocation(self.program, "view"), 1, GL_TRUE, view)
            glUniformMatrix4fv(glGetUniformLocation(self.program, "projection"), 1, GL_TRUE, projection)
            glUniform1f(glGetUniformLocation(self.program, "time"), current_time)
            
            # Draw
            glBindVertexArray(self.vao)
            glDrawArrays(GL_POINTS, 0, self.vertex_count)
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
            logging.info("KaleidoTunnel: Cleaned up")
        except Exception as e:
            logging.error(f"KaleidoTunnel cleanup error: {e}")