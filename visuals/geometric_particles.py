from PyQt6.QtGui import QOpenGLContext, QSurfaceFormat
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import ctypes
import os

from .base_visualizer import BaseVisualizer

class GeometricParticlesVisualizer(BaseVisualizer):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFormat(QSurfaceFormat())
        self.shader_program = None
        self.VBO = None
        self.VAO = None
        self.num_particles = 10000
        self.particle_positions = None
        self.particle_colors = None
        self.time = 0.0

    def get_controls(self):
        return {
            "Particle Count": {
                "type": "slider",
                "min": 1000,
                "max": 20000,
                "value": self.num_particles,
            }
        }

    def update_control(self, name, value):
        if name == "Particle Count":
            self.num_particles = int(value)
            if self.VBO:
                glDeleteBuffers(1, [self.VBO])
                self.VBO = None
            if self.VAO:
                glDeleteVertexArrays(1, [self.VAO])
                self.VAO = None
            self.setup_particles()

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)

        self.load_shaders()
        self.setup_particles()

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

    def setup_particles(self):
        self.particle_positions = np.random.rand(self.num_particles, 3).astype(np.float32) * 2.0 - 1.0
        self.particle_colors = np.random.rand(self.num_particles, 4).astype(np.float32)

        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        self.VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, self.particle_positions.nbytes + self.particle_colors.nbytes, None, GL_STATIC_DRAW)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.particle_positions.nbytes, self.particle_positions)
        glBufferSubData(GL_ARRAY_BUFFER, self.particle_positions.nbytes, self.particle_colors.nbytes, self.particle_colors)

        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(self.particle_positions.nbytes))
        glEnableVertexAttribArray(1)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        projection = self.perspective(45, (width / height) if height > 0 else 1, 0.1, 100.0)
        glUseProgram(self.shader_program)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "projection"), 1, GL_FALSE, projection)

    def paintGL(self):
        print("GeometricParticlesVisualizer: paintGL called") # Debug print
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glUseProgram(self.shader_program)

        view = self.lookAt(np.array([0.0, 0.0, 5.0]), np.array([0.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]))
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 1, GL_FALSE, view)

        # Simple animation: particles move up and down
        self.time += 0.01
        model = self.translate(0.0, np.sin(self.time) * 0.5, 0.0)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "model"), 1, GL_FALSE, model)

        glPointSize(5.0) # Set point size for visibility

        glBindVertexArray(self.VAO)
        glDrawArrays(GL_POINTS, 0, self.num_particles)
        glBindVertexArray(0)

        self.update() # Request continuous updates

    def perspective(self, fov, aspect, near, far):
        # Simple perspective matrix calculation
        f = 1.0 / np.tan(np.radians(fov / 2.0))
        return np.array([
            [f / aspect, 0.0, 0.0, 0.0],
            [0.0, f, 0.0, 0.0],
            [0.0, 0.0, (far + near) / (near - far), -1.0],
            [0.0, 0.0, (2.0 * far * near) / (near - far), 0.0]
        ], dtype=np.float32)

    def lookAt(self, eye, center, up):
        # Simple lookAt matrix calculation
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
