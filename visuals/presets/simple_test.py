# visuals/simple_test.py
from OpenGL.GL import *
import numpy as np
import time
import math
import logging
import ctypes

from visuals.base_visualizer import BaseVisualizer

class SimpleTestVisualizer(BaseVisualizer):
    visual_name = "Simple Test"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time_start = time.time()
        self.brightness = 1.0
        self.speed = 1.0
        self.pattern = 0  # 0: circles, 1: squares, 2: triangles
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.initialized = False
        logging.info("🎨 SimpleTestVisualizer created")

    def get_controls(self):
        return {
            "Brightness": {
                "type": "slider",
                "min": 0,
                "max": 200,
                "value": int(self.brightness * 100)
            },
            "Speed": {
                "type": "slider",
                "min": 0,
                "max": 300,
                "value": int(self.speed * 100)
            },
            "Pattern": {
                "type": "dropdown",
                "options": ["Circles", "Squares", "Triangles"],
                "value": self.pattern
            }
        }

    def update_control(self, name, value):
        if name == "Brightness":
            self.brightness = float(value) / 100.0
        elif name == "Speed":
            self.speed = float(value) / 100.0
        elif name == "Pattern":
            self.pattern = int(value)

    def initializeGL(self):
        """Initialize OpenGL state"""
        logging.info("🔧 SimpleTestVisualizer.initializeGL called")
        
        try:
            # Set clear color to transparent for proper mixing
            glClearColor(0.0, 0.0, 0.0, 0.0)
            
            # Enable blending for transparency
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            # Disable depth testing for 2D
            glDisable(GL_DEPTH_TEST)
            
            # Create shaders
            self.create_shaders()
            
            # Create geometry buffers
            self.create_buffers()
            
            self.initialized = True
            logging.info("✅ SimpleTestVisualizer initialized")
            
        except Exception as e:
            logging.error(f"❌ Error in SimpleTestVisualizer.initializeGL: {e}")
            import traceback
            traceback.print_exc()

    def create_shaders(self):
        """Create and compile shaders"""
        # Vertex shader for 2D shapes
        vertex_shader_src = """
        #version 330 core
        layout(location = 0) in vec2 aPos;
        layout(location = 1) in vec3 aColor;
        
        out vec3 fragColor;
        
        uniform mat4 transform;
        
        void main() {
            gl_Position = transform * vec4(aPos, 0.0, 1.0);
            fragColor = aColor;
        }
        """
        
        # Fragment shader
        fragment_shader_src = """
        #version 330 core
        in vec3 fragColor;
        out vec4 FragColor;
        
        uniform float brightness;
        
        void main() {
            FragColor = vec4(fragColor * brightness, 0.9);
        }
        """
        
        # Compile vertex shader
        vertex_shader = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vertex_shader, vertex_shader_src)
        glCompileShader(vertex_shader)
        
        if not glGetShaderiv(vertex_shader, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(vertex_shader).decode()
            raise Exception(f"Vertex shader compilation failed: {error}")
        
        # Compile fragment shader
        fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragment_shader, fragment_shader_src)
        glCompileShader(fragment_shader)
        
        if not glGetShaderiv(fragment_shader, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(fragment_shader).decode()
            raise Exception(f"Fragment shader compilation failed: {error}")
        
        # Link shader program
        self.shader_program = glCreateProgram()
        glAttachShader(self.shader_program, vertex_shader)
        glAttachShader(self.shader_program, fragment_shader)
        glLinkProgram(self.shader_program)
        
        if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):
            error = glGetProgramInfoLog(self.shader_program).decode()
            raise Exception(f"Shader program linking failed: {error}")
        
        # Clean up shaders
        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)
        
        logging.info("✅ Shaders created successfully")

    def create_buffers(self):
        """Create vertex buffers"""
        # Create VAO and VBO
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        
        # We'll update the buffer dynamically in paintGL
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        
        # Pre-allocate buffer for max vertices (e.g., 1000 vertices * 5 floats each)
        max_vertices = 1000
        buffer_size = max_vertices * 5 * ctypes.sizeof(GLfloat)
        glBufferData(GL_ARRAY_BUFFER, buffer_size, None, GL_DYNAMIC_DRAW)
        
        # Setup vertex attributes
        # Position (2 floats)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 5 * ctypes.sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        # Color (3 floats)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 5 * ctypes.sizeof(GLfloat), ctypes.c_void_p(2 * ctypes.sizeof(GLfloat)))
        glEnableVertexAttribArray(1)
        
        glBindVertexArray(0)
        
        logging.info("✅ Buffers created")

    def create_identity_matrix(self):
        """Create an identity matrix"""
        return np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)

    def resizeGL(self, width, height):
        """Handle resize"""
        logging.debug(f"📐 SimpleTestVisualizer.resizeGL: {width}x{height}")
        glViewport(0, 0, width, height)

    def paintGL(self):
        """Main rendering function"""
        try:
            if not self.initialized or not self.shader_program:
                # Just clear to a color if not initialized
                glClearColor(0.1, 0.0, 0.1, 1.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return
            
            # Clear with transparent background
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)
            
            # Calculate time for animation
            t = (time.time() - self.time_start) * self.speed
            
            # Use shader program
            glUseProgram(self.shader_program)
            
            # Set uniforms
            glUniform1f(glGetUniformLocation(self.shader_program, "brightness"), self.brightness)
            
            # Identity transform (NDC coordinates)
            transform = self.create_identity_matrix()
            glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "transform"), 1, GL_FALSE, transform)
            
            # Choose pattern to draw
            if self.pattern == 0:
                self.draw_circles_modern(t)
            elif self.pattern == 1:
                self.draw_squares_modern(t)
            else:
                self.draw_triangles_modern(t)
            
            # Clean up
            glUseProgram(0)
            
        except Exception as e:
            logging.error(f"❌ Error in SimpleTestVisualizer.paintGL: {e}")
            # Fallback: just clear to a color
            glClearColor(0.2, 0.0, 0.2, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def draw_circles_modern(self, t):
        """Draw circles using modern OpenGL"""
        num_circles = 8
        segments = 32
        
        vertices = []
        
        for i in range(num_circles):
            angle_offset = (2 * math.pi * i) / num_circles
            
            # Pulsating radius
            radius = 0.15 + 0.05 * math.sin(t * 2 + angle_offset)
            
            # Position
            cx = 0.5 * math.cos(t + angle_offset)
            cy = 0.5 * math.sin(t + angle_offset)
            
            # Color cycling
            r = 0.5 + 0.5 * math.sin(t + angle_offset)
            g = 0.5 + 0.5 * math.sin(t + angle_offset + 2.094)
            b = 0.5 + 0.5 * math.sin(t + angle_offset + 4.189)
            
            # Create circle vertices (as triangle fan)
            # Center vertex
            vertices.extend([cx, cy, r, g, b])
            
            for j in range(segments + 1):
                angle = 2 * math.pi * j / segments
                x = cx + radius * math.cos(angle)
                y = cy + radius * math.sin(angle)
                vertices.extend([x, y, r, g, b])
        
        # Upload vertices to GPU
        vertices_array = np.array(vertices, dtype=np.float32)
        
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, vertices_array.nbytes, vertices_array)
        
        # Draw circles
        vertex_offset = 0
        for i in range(num_circles):
            num_vertices = segments + 2  # center + perimeter + 1 to close
            glDrawArrays(GL_TRIANGLE_FAN, vertex_offset, num_vertices)
            vertex_offset += num_vertices
        
        glBindVertexArray(0)

    def draw_squares_modern(self, t):
        """Draw squares using modern OpenGL"""
        num_squares = 6
        vertices = []
        
        for i in range(num_squares):
            angle = (2 * math.pi * i) / num_squares + t * 0.5
            
            # Size pulsation
            size = 0.08 + 0.04 * math.sin(t * 3 + i)
            
            # Position
            dist = 0.4 + 0.1 * math.sin(t + i)
            cx = dist * math.cos(angle)
            cy = dist * math.sin(angle)
            
            # Color
            hue = (t * 0.2 + i * 0.3) % 1.0
            r, g, b = self.hsv_to_rgb(hue, 0.8, 1.0)
            
            # Rotation
            rot = t * 0.5 + i * 0.785  # radians
            cos_r = math.cos(rot)
            sin_r = math.sin(rot)
            
            # Square vertices (as two triangles)
            corners = [
                [-size, -size],
                [size, -size],
                [size, size],
                [-size, size]
            ]
            
            # Apply rotation and translation
            for j in range(4):
                x = corners[j][0]
                y = corners[j][1]
                # Rotate
                rx = x * cos_r - y * sin_r
                ry = x * sin_r + y * cos_r
                # Translate
                corners[j] = [rx + cx, ry + cy]
            
            # First triangle
            vertices.extend([corners[0][0], corners[0][1], r, g, b])
            vertices.extend([corners[1][0], corners[1][1], r, g, b])
            vertices.extend([corners[2][0], corners[2][1], r, g, b])
            
            # Second triangle
            vertices.extend([corners[0][0], corners[0][1], r, g, b])
            vertices.extend([corners[2][0], corners[2][1], r, g, b])
            vertices.extend([corners[3][0], corners[3][1], r, g, b])
        
        # Upload and draw
        vertices_array = np.array(vertices, dtype=np.float32)
        
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, vertices_array.nbytes, vertices_array)
        
        glDrawArrays(GL_TRIANGLES, 0, num_squares * 6)
        
        glBindVertexArray(0)

    def draw_triangles_modern(self, t):
        """Draw triangles using modern OpenGL"""
        num_triangles = 10
        vertices = []
        
        for i in range(num_triangles):
            angle = (2 * math.pi * i) / num_triangles
            
            # Wave motion
            wave = math.sin(t * 2 + angle * 3)
            
            # Position
            cx = 0.4 * math.cos(angle) * (1 + 0.3 * wave)
            cy = 0.4 * math.sin(angle) * (1 + 0.3 * wave)
            
            # Size
            size = 0.12 + 0.04 * wave
            
            # Color with rainbow effect
            hue = (angle / (2 * math.pi) + t * 0.1) % 1.0
            r, g, b = self.hsv_to_rgb(hue, 1.0, 1.0)
            
            # Rotation
            rot = t * 0.7 + i * 1.047  # radians
            
            # Triangle vertices
            v1 = [0, size]
            v2 = [-size * 0.866, -size * 0.5]
            v3 = [size * 0.866, -size * 0.5]
            
            # Apply rotation
            cos_r = math.cos(rot)
            sin_r = math.sin(rot)
            
            for v in [v1, v2, v3]:
                x = v[0] * cos_r - v[1] * sin_r + cx
                y = v[0] * sin_r + v[1] * cos_r + cy
                vertices.extend([x, y, r, g, b])
        
        # Upload and draw
        vertices_array = np.array(vertices, dtype=np.float32)
        
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, vertices_array.nbytes, vertices_array)
        
        glDrawArrays(GL_TRIANGLES, 0, num_triangles * 3)
        
        glBindVertexArray(0)

    def hsv_to_rgb(self, h, s, v):
        """Convert HSV to RGB color space"""
        c = v * s
        x = c * (1 - abs((h * 6) % 2 - 1))
        m = v - c
        
        if h < 1/6:
            r, g, b = c, x, 0
        elif h < 2/6:
            r, g, b = x, c, 0
        elif h < 3/6:
            r, g, b = 0, c, x
        elif h < 4/6:
            r, g, b = 0, x, c
        elif h < 5/6:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
            
        return r + m, g + m, b + m

    def cleanup(self):
        """Clean up resources"""
        logging.info("🧹 Cleaning up SimpleTestVisualizer")
        
        try:
            if self.shader_program:
                glDeleteProgram(self.shader_program)
                self.shader_program = None
            
            if self.vbo:
                glDeleteBuffers(1, [self.vbo])
                self.vbo = None
            
            if self.vao:
                glDeleteVertexArrays(1, [self.vao])
                self.vao = None
                
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")