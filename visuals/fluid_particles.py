from PyQt6.QtGui import QOpenGLContext, QSurfaceFormat
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import ctypes
import os
import time

from physics.physics_engine import PhysicsEngine
from .base_visualizer import BaseVisualizer

class FluidParticlesVisualizer(BaseVisualizer):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFormat(QSurfaceFormat())
        self.shader_program = None
        self.VBO = None
        self.VAO = None
        self.num_particles = 1000 # Reduced for testing hang issue
        self.particle_positions = None
        self.particle_colors = None
        self.physics_engine = PhysicsEngine()
        self.last_time = time.time()
        self.point_size = 20.0

    def get_controls(self):
        return {
            "Point Size": {
                "type": "slider",
                "min": 1,
                "max": 30,
                "value": int(self.point_size),
            }
        }

    def update_control(self, name, value):
        if name == "Point Size":
            self.point_size = float(value)

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
        # Initial particle positions from physics engine (placeholder)
        self.particle_positions = np.array(self.physics_engine.create_fluid_particles(self.num_particles), dtype=np.float32)
        self.particle_colors = np.random.rand(self.num_particles, 4).astype(np.float32)

        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        self.VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, self.particle_positions.nbytes + self.particle_colors.nbytes, None, GL_DYNAMIC_DRAW) # Dynamic draw for physics updates
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
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Update physics simulation
        self.physics_engine.step_simulation()
        self.particle_positions = self.physics_engine.get_particle_positions()

        # Update VBO with new positions
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.particle_positions.nbytes, self.particle_positions)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        glUseProgram(self.shader_program)

        # Adjust camera for PyBullet's Z-up coordinate system
        view = self.lookAt(np.array([0.0, -15.0, 15.0]), np.array([0.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0])) # Eye (x,y,z), Center (x,y,z), Up (x,y,z)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 1, GL_FALSE, view)

        model = self.translate(0.0, 0.0, 0.0) # No global model translation for now
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "model"), 1, GL_FALSE, model)

        glPointSize(self.point_size)

        # Debug print for particle positions
        if self.particle_positions is not None and len(self.particle_positions) > 0:
            for i in range(min(5, len(self.particle_positions))):
                print(f"Fluid particle {i} position: {self.particle_positions[i]}")

        glBindVertexArray(self.VAO)
        glDrawArrays(GL_POINTS, 0, self.num_particles)
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
        if self.physics_engine:
            self.physics_engine.disconnect()
