from PyQt6.QtGui import QOpenGLContext, QSurfaceFormat
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import ctypes
import os

from .base_visualizer import BaseVisualizer

class MobiusBandVisualizer(BaseVisualizer):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFormat(QSurfaceFormat())
        self.shader_program = None
        self.VBO = None
        self.VAO = None
        self.num_segments = 100
        self.num_slices = 20
        self.band_data = None
        self.time = 0.0

    def get_controls(self):
        return {
            "Segments": {
                "type": "slider",
                "min": 10,
                "max": 200,
                "value": self.num_segments,
            }
        }

    def update_control(self, name, value):
        if name == "Segments":
            self.num_segments = int(value)
            if self.VBO:
                glDeleteBuffers(1, [self.VBO])
                self.VBO = None
            if self.VAO:
                glDeleteVertexArrays(1, [self.VAO])
                self.VAO = None
            self.setup_band()

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)

        self.load_shaders()
        self.setup_band()

    def load_shaders(self):
        script_dir = os.path.dirname(__file__)
        shader_dir = os.path.join(script_dir, '..', 'shaders')

        with open(os.path.join(shader_dir, 'basic.vert'), 'r') as f:
            vertex_shader_source = f.read()
        with open(os.path.join(shader_dir, 'basic.frag'), 'r') as f:
            fragment_shader_source = f.read()

        vertex_shader = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vertex_shader, vertex_shader_source)
        glCompileShader(vertex_shader)
        if not glGetShaderiv(vertex_shader, GL_COMPILE_STATUS):
            print("Vertex Shader Compile Error:", glGetShaderInfoLog(vertex_shader).decode())

        fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragment_shader, fragment_shader_source)
        glCompileShader(fragment_shader)
        if not glGetShaderiv(fragment_shader, GL_COMPILE_STATUS):
            print("Fragment Shader Compile Error:", glGetShaderInfoLog(fragment_shader).decode())

        self.shader_program = glCreateProgram()
        glAttachShader(self.shader_program, vertex_shader)
        glAttachShader(self.shader_program, fragment_shader)
        glLinkProgram(self.shader_program)
        if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):
            print("Shader Program Link Error:", glGetProgramInfoLog(self.shader_program).decode())

        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

    def setup_band(self):
        vertices = []
        colors = []

        for i in range(self.num_segments):
            theta = i * 2.0 * np.pi / self.num_segments
            for j in range(self.num_slices):
                phi = j * 2.0 * np.pi / self.num_slices

                # Mobius band equations (simplified)
                x = (1 + 0.5 * np.cos(phi / 2.0)) * np.cos(theta)
                y = (1 + 0.5 * np.cos(phi / 2.0)) * np.sin(theta)
                z = 0.5 * np.sin(phi / 2.0)

                vertices.extend([x, y, z])
                colors.extend([np.random.rand(), np.random.rand(), np.random.rand(), 1.0])

        self.band_data = np.array(vertices + colors, dtype=np.float32)

        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        self.VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, self.band_data.nbytes, self.band_data, GL_STATIC_DRAW)

        # Position attribute
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # Color attribute (assuming colors are interleaved after positions for now)
        # This needs to be adjusted if positions and colors are separate buffers
        # For now, just a placeholder, will need proper setup for complex geometry
        # glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(len(vertices) * ctypes.sizeof(GLfloat)))
        # glEnableVertexAttribArray(1)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        projection = self.perspective(45, (width / height) if height > 0 else 1, 0.1, 100.0)
        glUseProgram(self.shader_program)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "projection"), 1, GL_FALSE, projection)

    def paintGL(self):
        print("MobiusBandVisualizer: paintGL called") # Debug print
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glUseProgram(self.shader_program)

        view = self.lookAt(np.array([0.0, 0.0, 5.0]), np.array([0.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]))
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 1, GL_FALSE, view)

        self.time += 0.01
        model = self.translate(0.0, 0.0, 0.0) # No animation for now
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "model"), 1, GL_FALSE, model)

        glBindVertexArray(self.VAO)
        glDrawArrays(GL_POINTS, 0, self.num_segments * self.num_slices) # Drawing as points for now
        glBindVertexArray(0)

        self.update() # Request continuous updates

    def perspective(self, fov, aspect, near, far):
        f = 1.0 / np.tan(np.radians(fov / 2.0))
        return np.array([
            [f / aspect, 0.0, 0.0, 0.0],
            [0.0, f, 0.0, 0.0],
            [0.0, 0.0, (far + near) / (near - far), -1.0],
            [0.0, 0.0, (2.0 * far * near) / (near - far), 0.0]
        ], dtype=np.float32)

    def lookAt(self, eye, center, up):
        f = (center - eye) / np.linalg.norm(center - eye)
        s = np.cross(f, up) / np.linalg.norm(np.cross(f, up))
        u = np.cross(s, f)

        return np.array([
            [s[0], u[0], -f[0], 0.0],
            [s[1], u[1], -f[1], 0.0],
            [s[2], u[2], -f[2], 0.0],
            [-np.dot(s, eye), -np.dot(u, eye), np.dot(f, eye), 1.0]
        ], dtype=np.float32).T

    def translate(self, x, y, z):
        return np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [x, y, z, 1.0]
        ], dtype=np.float32)

    def cleanup(self):
        if self.shader_program:
            glDeleteProgram(self.shader_program)
        if self.VBO:
            glDeleteBuffers(1, [self.VBO])
        if self.VAO:
            glDeleteVertexArrays(1, [self.VAO])
