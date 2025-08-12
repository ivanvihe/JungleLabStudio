from OpenGL.GL import *
import numpy as np
import ctypes
import os
import logging

from .base_visualizer import BaseVisualizer

class AbstractLinesVisualizer(BaseVisualizer):
    visual_name = "Abstract Lines"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shader_program = None
        self.VBO = None
        self.VAO = None
        self.num_lines = 1000
        self.line_data = None
        self.time = 0.0
        self.line_width = 1.0
        self.pulsation_speed = 2.0

    def get_controls(self):
        return {
            "Line Width": {
                "type": "slider",
                "min": 1,
                "max": 10,
                "value": int(self.line_width),
            },
            "Number of Lines": {
                "type": "slider",
                "min": 100,
                "max": 5000,
                "value": self.num_lines,
            },
            "Pulsation Speed": {
                "type": "slider",
                "min": 1,
                "max": 100,
                "value": int(self.pulsation_speed * 10),
            }
        }

    def update_control(self, name, value):
        if name == "Line Width":
            self.line_width = float(value)
        elif name == "Number of Lines":
            old_lines = self.num_lines
            self.num_lines = int(value)
            if old_lines != self.num_lines:
                self.setup_lines()
        elif name == "Pulsation Speed":
            self.pulsation_speed = float(value) / 10.0

    def initializeGL(self):
        print("AbstractLinesVisualizer.initializeGL called")
        # TRANSPARENT BACKGROUND FOR MIXING
        glClearColor(0.0, 0.0, 0.0, 0.0)  # Alpha = 0 for transparency
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.load_shaders()
        self.setup_lines()

    def load_shaders(self):
        script_dir = os.path.dirname(__file__)
        shader_dir = os.path.join(script_dir, '..', 'shaders')

        try:
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
            print("AbstractLines shaders loaded successfully")
        except Exception as e:
            print(f"AbstractLines shader loading error: {e}")

    def setup_lines(self):
        try:
            # Clean up old buffers
            if self.VBO:
                glDeleteBuffers(1, [self.VBO])
            if self.VAO:
                glDeleteVertexArrays(1, [self.VAO])
                
            self.line_data = np.zeros((self.num_lines * 2, 7), dtype=np.float32)

            self.VAO = glGenVertexArrays(1)
            glBindVertexArray(self.VAO)

            self.VBO = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
            glBufferData(GL_ARRAY_BUFFER, self.line_data.nbytes, self.line_data, GL_DYNAMIC_DRAW)

            # Position attribute
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 7 * ctypes.sizeof(GLfloat), ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)

            # Color attribute
            glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 7 * ctypes.sizeof(GLfloat), ctypes.c_void_p(3 * ctypes.sizeof(GLfloat)))
            glEnableVertexAttribArray(1)

            glBindVertexArray(0)
            print(f"AbstractLines setup complete with {self.num_lines} lines")
        except Exception as e:
            print(f"Error setting up lines: {e}")

    def update_lines(self):
        if self.line_data is None:
            return
            
        try:
            for i in range(self.num_lines):
                angle = i * (2 * np.pi / self.num_lines)
                
                # Pulsating effect
                pulsation = 0.5 + 0.5 * np.sin(self.time * self.pulsation_speed)

                # Endpoint 1
                x1 = np.cos(angle) * (1.0 + 0.5 * np.sin(self.time + angle)) * pulsation
                y1 = np.sin(angle) * (1.0 + 0.5 * np.cos(self.time + angle)) * pulsation
                z1 = np.sin(self.time + i / 10.0) * 0.5
                
                # Endpoint 2
                x2 = np.cos(angle + np.pi/self.num_lines * 10) * (1.0 - 0.5 * np.sin(self.time + angle)) * pulsation
                y2 = np.sin(angle + np.pi/self.num_lines * 10) * (1.0 - 0.5 * np.cos(self.time + angle)) * pulsation
                z2 = np.cos(self.time + i / 10.0) * 0.5

                self.line_data[i * 2, :3] = [x1, y1, z1]
                self.line_data[i * 2 + 1, :3] = [x2, y2, z2]

                # Color based on position and time
                r = 0.6 + 0.4 * np.sin(self.time + angle)
                g = 0.6 + 0.4 * np.cos(self.time / 2.0 + angle)
                b = 0.6 + 0.4 * np.sin(self.time / 3.0 + angle)
                alpha = 0.8  # Semi-transparent for mixing
                
                self.line_data[i * 2, 3:7] = [r, g, b, alpha]
                self.line_data[i * 2 + 1, 3:7] = [r, g, b, alpha]

            # Update buffer
            glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
            glBufferSubData(GL_ARRAY_BUFFER, 0, self.line_data.nbytes, self.line_data)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
        except Exception as e:
            print(f"Error updating lines: {e}")

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)

    def paintGL(self):
        # CLEAR WITH TRANSPARENT BACKGROUND
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        if not self.shader_program or not self.VAO:
            return
            
        try:
            glUseProgram(self.shader_program)

            self.time += 0.01
            self.update_lines()

            # Set up matrices
            projection = self.perspective(45, 1.0, 0.1, 100.0)
            view = self.lookAt(np.array([0.0, 0.0, 5.0]), np.array([0.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]))
            model = self.rotate(self.time * 20, 1, 0, 0) @ self.rotate(self.time * 15, 0, 1, 0)

            glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "projection"), 1, GL_FALSE, projection)
            glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 1, GL_FALSE, view)
            glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "model"), 1, GL_FALSE, model)

            glLineWidth(self.line_width)
            glBindVertexArray(self.VAO)
            glDrawArrays(GL_LINES, 0, self.num_lines * 2)
            glBindVertexArray(0)
        except Exception as e:
            print(f"Error in paintGL: {e}")

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
        print("Cleaning up AbstractLinesVisualizer")
        try:
            if self.shader_program:
                glDeleteProgram(self.shader_program)
                self.shader_program = None
            if self.VBO:
                glDeleteBuffers(1, [self.VBO])
                self.VBO = None
            if self.VAO:
                glDeleteVertexArrays(1, [self.VAO])
                self.VAO = None
        except Exception as e:
            print(f"Error during cleanup: {e}")