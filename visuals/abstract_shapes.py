from PyQt6.QtGui import QOpenGLContext, QSurfaceFormat
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import ctypes
import os
import logging

from .base_visualizer import BaseVisualizer

class AbstractShapesVisualizer(BaseVisualizer):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFormat(QSurfaceFormat())
        self.shader_program = None
        self.VBO = None
        self.VAO = None
        self.num_shapes = 10
        self.shape_data = None
        self.time = 0.0
        self.rotation_speed = 0.0
        self.shape_type = 0

    def get_controls(self):
        return {
            "Rotation Speed": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.rotation_speed * 100),
            },
            "Shape Type": {
                "type": "dropdown",
                "options": ["Triangle", "Quad", "Cube"],
                "value": self.shape_type,
            },
            "Number of Shapes": {
                "type": "slider",
                "min": 1,
                "max": 100,
                "value": self.num_shapes,
            }
        }

    def update_control(self, name, value):
        if name == "Rotation Speed":
            self.rotation_speed = float(value) / 100.0
        elif name == "Shape Type":
            self.shape_type = value
            self.setup_shapes()
        elif name == "Number of Shapes":
            self.num_shapes = int(value)
            self.setup_shapes()

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)

        self.load_shaders()
        self.setup_shapes()

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

    def setup_shapes(self):
        if self.VBO:
            glDeleteBuffers(1, [self.VBO])
        if self.VAO:
            glDeleteVertexArrays(1, [self.VAO])

        vertices = []
        indices = []
        
        if self.shape_type == 0: # Triangle
            base_vertices = np.array([
                -0.5, -0.5, 0.0, 1.0, 0.0, 0.0, 1.0, # Vertex 1 (pos, color)
                 0.5, -0.5, 0.0, 0.0, 1.0, 0.0, 1.0, # Vertex 2
                 0.0,  0.5, 0.0, 0.0, 0.0, 1.0, 1.0  # Vertex 3
            ], dtype=np.float32)
            base_indices = np.array([0, 1, 2], dtype=np.uint32)
            num_verts_per_shape = 3
            num_indices_per_shape = 3
        elif self.shape_type == 1: # Quad
            base_vertices = np.array([
                -0.5, -0.5, 0.0, 1.0, 0.0, 0.0, 1.0, # Vertex 1
                 0.5, -0.5, 0.0, 0.0, 1.0, 0.0, 1.0, # Vertex 2
                 0.5,  0.5, 0.0, 0.0, 0.0, 1.0, 1.0, # Vertex 3
                -0.5,  0.5, 0.0, 1.0, 1.0, 0.0, 1.0  # Vertex 4
            ], dtype=np.float32)
            base_indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)
            num_verts_per_shape = 4
            num_indices_per_shape = 6
        else: # Cube
            base_vertices = np.array([
                # Front face
                -0.5, -0.5,  0.5,  1.0, 0.0, 0.0, 1.0,
                 0.5, -0.5,  0.5,  1.0, 0.0, 0.0, 1.0,
                 0.5,  0.5,  0.5,  1.0, 0.0, 0.0, 1.0,
                -0.5,  0.5,  0.5,  1.0, 0.0, 0.0, 1.0,
                # Back face
                -0.5, -0.5, -0.5,  0.0, 1.0, 0.0, 1.0,
                 0.5, -0.5, -0.5,  0.0, 1.0, 0.0, 1.0,
                 0.5,  0.5, -0.5,  0.0, 1.0, 0.0, 1.0,
                -0.5,  0.5, -0.5,  0.0, 1.0, 0.0, 1.0,
                # Top face
                -0.5,  0.5,  0.5,  0.0, 0.0, 1.0, 1.0,
                 0.5,  0.5,  0.5,  0.0, 0.0, 1.0, 1.0,
                 0.5,  0.5, -0.5,  0.0, 0.0, 1.0, 1.0,
                -0.5,  0.5, -0.5,  0.0, 0.0, 1.0, 1.0,
                # Bottom face
                -0.5, -0.5,  0.5,  1.0, 1.0, 0.0, 1.0,
                 0.5, -0.5,  0.5,  1.0, 1.0, 0.0, 1.0,
                 0.5, -0.5, -0.5,  1.0, 1.0, 0.0, 1.0,
                -0.5, -0.5, -0.5,  1.0, 1.0, 0.0, 1.0,
                # Right face
                 0.5, -0.5,  0.5,  0.0, 1.0, 1.0, 1.0,
                 0.5,  0.5,  0.5,  0.0, 1.0, 1.0, 1.0,
                 0.5,  0.5, -0.5,  0.0, 1.0, 1.0, 1.0,
                 0.5, -0.5, -0.5,  0.0, 1.0, 1.0, 1.0,
                # Left face
                -0.5, -0.5,  0.5,  1.0, 0.0, 1.0, 1.0,
                -0.5,  0.5,  0.5,  1.0, 0.0, 1.0, 1.0,
                -0.5,  0.5, -0.5,  1.0, 0.0, 1.0, 1.0,
                -0.5, -0.5, -0.5,  1.0, 0.0, 1.0, 1.0
            ], dtype=np.float32)
            base_indices = np.array([
                0, 1, 2, 2, 3, 0,  # Front face
                4, 5, 6, 6, 7, 4,  # Back face
                8, 9, 10, 10, 11, 8,  # Top face
                12, 13, 14, 14, 15, 12,  # Bottom face
                16, 17, 18, 18, 19, 16,  # Right face
                20, 21, 22, 22, 23, 20   # Left face
            ], dtype=np.uint32)
            num_verts_per_shape = 24
            num_indices_per_shape = 36

        for i in range(self.num_shapes):
            # Simple translation for each shape
            offset_x = (i % 10 - 5) * 1.5
            offset_y = (i // 10 - 5) * 1.5
            offset_z = 0.0

            # Apply offset to base vertices
            translated_vertices = base_vertices.copy()
            translated_vertices[::7] += offset_x
            translated_vertices[1::7] += offset_y
            translated_vertices[2::7] += offset_z
            vertices.extend(translated_vertices.tolist())

            # Apply offset to indices
            indices.extend((base_indices + i * num_verts_per_shape).tolist())

        self.shape_data = np.array(vertices, dtype=np.float32)
        self.index_data = np.array(indices, dtype=np.uint32)

        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        self.VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, self.shape_data.nbytes, self.shape_data, GL_STATIC_DRAW)

        # Position attribute
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 7 * ctypes.sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # Color attribute
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 7 * ctypes.sizeof(GLfloat), ctypes.c_void_p(3 * ctypes.sizeof(GLfloat)))
        glEnableVertexAttribArray(1)

        self.EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.index_data.nbytes, self.index_data, GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        projection = self.perspective(45, (width / height) if height > 0 else 1, 0.1, 100.0)
        glUseProgram(self.shader_program)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "projection"), 1, GL_FALSE, projection)

    def paintGL(self):
        print("AbstractShapesVisualizer: paintGL called") # Debug print
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glUseProgram(self.shader_program)

        view = self.lookAt(np.array([0.0, 0.0, 5.0]), np.array([0.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]))
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 1, GL_FALSE, view)

        self.time += self.rotation_speed
        model = self.rotate_z(self.time)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "model"), 1, GL_FALSE, model)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, len(self.index_data), GL_UNSIGNED_INT, None)
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

    def rotate_z(self, angle):
        c = np.cos(angle)
        s = np.sin(angle)
        return np.array([
            [c, -s, 0.0, 0.0],
            [s,  c, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=np.float32)

    def cleanup(self):
        self.makeCurrent()
        try:
            if self.shader_program:
                glDeleteProgram(self.shader_program)
                self.shader_program = None
        except Exception as e:
            logging.error(f"Error deleting shader program: {e}")
        try:
            if self.VBO:
                glDeleteBuffers(1, [self.VBO])
                self.VBO = None
        except Exception as e:
            logging.error(f"Error deleting VBO: {e}")
        try:
            if self.VAO:
                glDeleteVertexArrays(1, [self.VAO])
                self.VAO = None
        except Exception as e:
            logging.error(f"Error deleting VAO: {e}")
        self.doneCurrent()