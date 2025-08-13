from PyQt6.QtGui import QOpenGLContext, QSurfaceFormat
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import ctypes
import os
import logging

from visuals.base_visualizer import BaseVisualizer

class GeometricParticlesVisualizer(BaseVisualizer):
    visual_name = "Geometric Particles"
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.shader_program = None
        self.VBO = None
        self.VAO = None
        self.num_particles = 10000
        self.particle_data = None
        self.time = 0.0
        self.point_size = 2.0
        self.shape_type = 0

    def get_controls(self):
        return {
            "Particle Count": {
                "type": "slider", "min": 1000, "max": 50000, "value": self.num_particles
            },
            "Point Size": {
                "type": "slider", "min": 1, "max": 10, "value": int(self.point_size)
            },
            "Shape Type": {
                "type": "dropdown", "options": ["Pulsating Sphere", "Animated Torus", "Abstract Cloud"], "value": self.shape_type
            }
        }

    def update_control(self, name, value):
        if name == "Particle Count":
            self.num_particles = int(value)
            self.setup_particles() # Re-initialize particles
        elif name == "Point Size":
            self.point_size = float(value)
        elif name == "Shape Type":
            self.shape_type = value

    def initializeGL(self):
        # TRANSPARENT BACKGROUND FOR MIXING
        glClearColor(0.0, 0.0, 0.0, 0.0)  # Alpha = 0 for transparency
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_PROGRAM_POINT_SIZE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.load_shaders()
        self.setup_particles()

    def load_shaders(self):
        script_dir = os.path.dirname(__file__)
        shader_dir = os.path.join(script_dir, '..', '..', 'shaders')

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
        # Ensure VBO and VAO are deleted before re-creating
        if self.VBO:
            glDeleteBuffers(1, [self.VBO])
            self.VBO = None # Set to None after deletion
        if self.VAO:
            glDeleteVertexArrays(1, [self.VAO])
            self.VAO = None # Set to None after deletion

        # position (3) + color (4)
        self.particle_data = np.zeros((self.num_particles, 7), dtype=np.float32)

        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        self.VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, self.particle_data.nbytes, self.particle_data, GL_DYNAMIC_DRAW)

        # Position
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 7 * ctypes.sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        # Color
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 7 * ctypes.sizeof(GLfloat), ctypes.c_void_p(3 * ctypes.sizeof(GLfloat)))
        glEnableVertexAttribArray(1)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def update_particles(self):
        self.time += 0.01

        for i in range(self.num_particles):
            # Parametric equations for different shapes
            u = (i / self.num_particles) * 2 * np.pi * 10 # Increase frequency for more complex patterns
            v = np.sin(self.time + i / (self.num_particles / 50.0))

            if self.shape_type == 0:  # Pulsating Sphere
                r = 1.5 + 0.5 * np.sin(self.time * 3.0 + u * 0.5)
                x = r * np.cos(u) * np.sqrt(1 - v**2)
                y = r * np.sin(u) * np.sqrt(1 - v**2)
                z = r * v
            elif self.shape_type == 1:  # Animated Torus
                R = 2.0
                r = 0.5 + 0.2 * np.sin(self.time * 2.0 + u)
                x = (R + r * np.cos(u)) * np.cos(v * 2 * np.pi)
                y = (R + r * np.cos(u)) * np.sin(v * 2 * np.pi)
                z = r * np.sin(u)
            else:  # Abstract "Cloud"
                x = np.sin(u * 3.0 + self.time) * 2.0
                y = np.cos(v * 5.0 - self.time) * 2.0
                z = np.sin(u * 2.0 + v * 3.0 + self.time) * 2.0

            self.particle_data[i, 0:3] = [x, y, z]

            # Color based on position and time with transparency
            r_color = 0.6 + 0.4 * np.sin(x + self.time)
            g_color = 0.6 + 0.4 * np.cos(y + self.time)
            b_color = 0.6 + 0.4 * np.sin(z + self.time)
            # Make particles semi-transparent for better mixing
            alpha = 0.8
            self.particle_data[i, 3:7] = [r_color, g_color, b_color, alpha]

        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.particle_data.nbytes, self.particle_data)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        projection = self.perspective(45, (width / height) if height > 0 else 1, 0.1, 100.0)
        glUseProgram(self.shader_program)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "projection"), 1, GL_FALSE, projection)

    def paintGL(self):
        # CLEAR WITH TRANSPARENT BACKGROUND
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.shader_program)

        self.update_particles()

        view = self.lookAt(np.array([0.0, 0.0, 10.0]), np.array([0.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]))
        model = self.rotate(self.time * 15, 0, 1, 0) @ self.rotate(self.time * 10, 1, 0, 0)

        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 1, GL_FALSE, view)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "model"), 1, GL_FALSE, model)

        glPointSize(self.point_size)

        glBindVertexArray(self.VAO)
        glDrawArrays(GL_POINTS, 0, self.num_particles)
        glBindVertexArray(0)

        

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
        if n == 0: return np.identity(4)
        x, y, z = x/n, y/n, z/n
        return np.array([
            [c+(x**2)*(1-c), x*y*(1-c)-z*s, x*z*(1-c)+y*s, 0],
            [y*x*(1-c)+z*s, c+(y**2)*(1-c), y*z*(1-c)-x*s, 0],
            [z*x*(1-c)-y*s, z*y*(1-c)+x*s, c+(z**2)*(1-c), 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)

    def scale(self, x, y, z):
        return np.array([
            [x, 0, 0, 0],
            [0, y, 0, 0],
            [0, 0, z, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)

    def cleanup(self):
        logging.debug("Cleaning up GeometricParticlesVisualizer")
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