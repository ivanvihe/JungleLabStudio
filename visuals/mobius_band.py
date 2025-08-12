from PyQt6.QtGui import QOpenGLContext, QSurfaceFormat
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import ctypes
import os
import logging

from .base_visualizer import BaseVisualizer

class MobiusBandVisualizer(BaseVisualizer):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFormat(QSurfaceFormat())
        self.shader_program = None
        self.VBO = None
        self.VAO = None
        self.EBO = None
        self.num_segments = 100
        self.num_strips = 20
        self.vertices = None
        self.indices = None
        self.time = 0.0
        self.width = 1.0
        self.animation_speed = 1.0
        self.color_mode = 0

    def get_controls(self):
        return {
            "Segments": {
                "type": "slider",
                "min": 50,
                "max": 300,
                "value": self.num_segments,
            },
            "Width": {
                "type": "slider",
                "min": 50,
                "max": 200,
                "value": int(self.width * 100),
            },
            "Speed": {
                "type": "slider",
                "min": 1,
                "max": 50,
                "value": int(self.animation_speed * 10),
            },
            "Color Mode": {
                "type": "dropdown",
                "options": ["Rainbow", "Fire", "Electric", "Ocean", "Plasma"],
                "value": self.color_mode,
            }
        }

    def update_control(self, name, value):
        if name == "Segments":
            self.num_segments = int(value)
            self.generate_geometry()
        elif name == "Width":
            self.width = float(value) / 100.0
            self.generate_geometry()
        elif name == "Speed":
            self.animation_speed = float(value) / 10.0
        elif name == "Color Mode":
            self.color_mode = int(value)

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.load_shaders()
        self.generate_geometry()
        self.setup_buffers()

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

        fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragment_shader, fragment_shader_source)
        glCompileShader(fragment_shader)

        self.shader_program = glCreateProgram()
        glAttachShader(self.shader_program, vertex_shader)
        glAttachShader(self.shader_program, fragment_shader)
        glLinkProgram(self.shader_program)

        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

    def generate_geometry(self):
        vertices = []
        indices = []

        # Generate Möbius strip
        for i in range(self.num_segments + 1):
            u = i * 2.0 * np.pi / self.num_segments
            
            for j in range(self.num_strips):
                v = -self.width + (2 * self.width * j) / (self.num_strips - 1)
                
                # Möbius strip equations
                x = (2.0 + v * np.cos(u/2)) * np.cos(u)
                y = (2.0 + v * np.cos(u/2)) * np.sin(u)
                z = v * np.sin(u/2)
                
                # Add vertex with position and initial color
                vertices.extend([x, y, z, 1.0, 1.0, 1.0, 1.0])

        # Generate triangle indices
        for i in range(self.num_segments):
            for j in range(self.num_strips - 1):
                idx = i * self.num_strips + j
                next_i = ((i + 1) % (self.num_segments + 1)) * self.num_strips + j
                
                # Two triangles per quad
                indices.extend([idx, next_i, idx + 1])
                indices.extend([next_i, next_i + 1, idx + 1])

        self.vertices = np.array(vertices, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.uint32)

    def setup_buffers(self):
        if self.VAO:
            glDeleteVertexArrays(1, [self.VAO])
        if self.VBO:
            glDeleteBuffers(1, [self.VBO])
        if self.EBO:
            glDeleteBuffers(1, [self.EBO])

        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        self.VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_DYNAMIC_DRAW)

        # Position
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 7 * ctypes.sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        # Color
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 7 * ctypes.sizeof(GLfloat), ctypes.c_void_p(3 * ctypes.sizeof(GLfloat)))
        glEnableVertexAttribArray(1)

        self.EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)

        glBindVertexArray(0)

    def update_colors(self):
        vertex_count = len(self.vertices) // 7
        
        for i in range(vertex_count):
            idx = i * 7
            
            # Get parametric coordinates
            segment = i // self.num_strips
            strip = i % self.num_strips
            u = segment * 2.0 * np.pi / self.num_segments
            v = strip / (self.num_strips - 1)
            
            # Color based on mode
            if self.color_mode == 0:  # Rainbow
                r = 0.5 + 0.5 * np.sin(u * 2 + self.time * self.animation_speed)
                g = 0.5 + 0.5 * np.sin(u * 2 + self.time * self.animation_speed + 2*np.pi/3)
                b = 0.5 + 0.5 * np.sin(u * 2 + self.time * self.animation_speed + 4*np.pi/3)
            elif self.color_mode == 1:  # Fire
                r = 0.9
                g = 0.3 + 0.4 * np.sin(u * 3 + self.time * self.animation_speed * 2)
                b = 0.1
            elif self.color_mode == 2:  # Electric
                intensity = 0.5 + 0.5 * np.sin(u * 5 + self.time * self.animation_speed * 3)
                r = 0.3 * intensity
                g = 0.8 * intensity
                b = 1.0 * intensity
            elif self.color_mode == 3:  # Ocean
                r = 0.1
                g = 0.4 + 0.3 * np.sin(u * 4 + self.time * self.animation_speed)
                b = 0.8 + 0.2 * np.sin(u * 6 + self.time * self.animation_speed * 1.5)
            else:  # Plasma
                r = 0.5 + 0.5 * np.sin(u * 3 + v * 5 + self.time * self.animation_speed * 2)
                g = 0.5 + 0.5 * np.sin(u * 4 - v * 3 + self.time * self.animation_speed * 1.5)
                b = 0.5 + 0.5 * np.sin(u * 5 + v * 4 + self.time * self.animation_speed * 2.5)
            
            self.vertices[idx + 3] = r
            self.vertices[idx + 4] = g
            self.vertices[idx + 5] = b
            self.vertices[idx + 6] = 1.0

        # Update buffer
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.vertices.nbytes, self.vertices)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.shader_program)

        self.time += 0.016 * self.animation_speed
        self.update_colors()

        # Set matrices
        projection = self.perspective(45, 1.0, 0.1, 100.0)
        view = self.lookAt(np.array([0, 0, 8]), np.array([0, 0, 0]), np.array([0, 1, 0]))
        model = self.rotate(self.time * 15, 0, 1, 0) @ self.rotate(self.time * 10, 1, 0, 0)

        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "projection"), 1, GL_FALSE, projection)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 1, GL_FALSE, view)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "model"), 1, GL_FALSE, model)

        # Draw
        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

        self.update()

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

    def rotate(self, angle, x, y, z):
        angle = np.radians(angle)
        c, s = np.cos(angle), np.sin(angle)
        n = np.sqrt(x*x + y*y + z*z)
        if n == 0: 
            return np.identity(4, dtype=np.float32)
        x, y, z = x/n, y/n, z/n
        return np.array([
            [c+(x**2)*(1-c), x*y*(1-c)-z*s, x*z*(1-c)+y*s, 0],
            [y*x*(1-c)+z*s, c+(y**2)*(1-c), y*z*(1-c)-x*s, 0],
            [z*x*(1-c)-y*s, z*y*(1-c)+x*s, c+(z**2)*(1-c), 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)

    def cleanup(self):
        self.makeCurrent()
        if self.shader_program:
            glDeleteProgram(self.shader_program)
        if self.VBO:
            glDeleteBuffers(1, [self.VBO])
        if self.VAO:
            glDeleteVertexArrays(1, [self.VAO])
        if self.EBO:
            glDeleteBuffers(1, [self.EBO])
        self.doneCurrent()