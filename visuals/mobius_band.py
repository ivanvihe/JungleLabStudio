from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import ctypes
import os
import logging

from .base_visualizer import BaseVisualizer

class MobiusBandVisualizer(BaseVisualizer):
    visual_name = "Möbius Band"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        self.surface_offset = 0.0  # Para el deslizamiento de la superficie

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
        print("MobiusBandVisualizer.initializeGL called")
        # TRANSPARENT BACKGROUND FOR MIXING
        glClearColor(0.0, 0.0, 0.0, 0.0)  # Alpha = 0 for transparency
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.load_shaders()
        self.generate_geometry()
        self.setup_buffers()

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

            fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fragment_shader, fragment_shader_source)
            glCompileShader(fragment_shader)

            self.shader_program = glCreateProgram()
            glAttachShader(self.shader_program, vertex_shader)
            glAttachShader(self.shader_program, fragment_shader)
            glLinkProgram(self.shader_program)

            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            print("MobiusBand shaders loaded successfully")
        except Exception as e:
            print(f"MobiusBand shader loading error: {e}")

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
                
                # Add vertex with position and initial color (semi-transparent)
                vertices.extend([x, y, z, 1.0, 1.0, 1.0, 0.8])

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
            
            # SUPERFICIE DESLIZANTE: añadir offset que se mueve a lo largo de la banda
            # Esto hace que los patrones de color se deslicen siguiendo la superficie
            sliding_u = u + self.surface_offset
            
            # Color based on mode con superficie deslizante
            if self.color_mode == 0:  # Rainbow - deslizante
                r = 0.5 + 0.5 * np.sin(sliding_u * 3)
                g = 0.5 + 0.5 * np.sin(sliding_u * 3 + 2*np.pi/3)
                b = 0.5 + 0.5 * np.sin(sliding_u * 3 + 4*np.pi/3)
            elif self.color_mode == 1:  # Fire - efecto llama deslizante
                flame_intensity = 0.5 + 0.5 * np.sin(sliding_u * 4)
                r = 0.9 * flame_intensity
                g = 0.3 + 0.4 * flame_intensity
                b = 0.1 * flame_intensity
            elif self.color_mode == 2:  # Electric - pulsos eléctricos
                electric_pulse = 0.3 + 0.7 * np.sin(sliding_u * 8)
                r = 0.3 * electric_pulse
                g = 0.8 * electric_pulse
                b = 1.0 * electric_pulse
            elif self.color_mode == 3:  # Ocean - ondas de agua
                wave1 = 0.5 + 0.5 * np.sin(sliding_u * 2)
                wave2 = 0.5 + 0.5 * np.sin(sliding_u * 3 + v * 2)
                r = 0.1 * wave1
                g = 0.4 + 0.3 * wave1
                b = 0.7 + 0.3 * wave2
            else:  # Plasma - patrón ondulatorio complejo
                plasma1 = np.sin(sliding_u * 2 + v * 3)
                plasma2 = np.sin(sliding_u * 3 - v * 2)
                plasma3 = np.sin(sliding_u * 4 + v * 4)
                r = 0.5 + 0.5 * plasma1
                g = 0.5 + 0.5 * plasma2
                b = 0.5 + 0.5 * plasma3
            
            # Añadir variación basada en la posición v para mayor riqueza visual
            v_factor = 0.8 + 0.2 * np.sin(v * np.pi)
            
            self.vertices[idx + 3] = r * v_factor
            self.vertices[idx + 4] = g * v_factor
            self.vertices[idx + 5] = b * v_factor
            self.vertices[idx + 6] = 0.8  # Semi-transparente para mezclas

        # Update buffer
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.vertices.nbytes, self.vertices)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)

    def paintGL(self):
        # CLEAR WITH TRANSPARENT BACKGROUND
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        if not self.shader_program:
            return
            
        glUseProgram(self.shader_program)

        # Actualizar tiempo y offset de superficie deslizante
        self.time += 0.016 * self.animation_speed
        # El surface_offset hace que la superficie se deslice a lo largo de la banda
        self.surface_offset += 0.05 * self.animation_speed
        
        self.update_colors()

        # Set matrices - BANDA FIJA EN EL ESPACIO
        projection = self.perspective(45, 1.0, 0.1, 100.0)
        # FIXED: Camera más alejada para ver toda la banda
        view = self.lookAt(np.array([0, 3, 12]), np.array([0, 0, 0]), np.array([0, 1, 0]))
        
        # MODELO FIJO - sin rotación, solo una ligera inclinación para mejor visualización
        model = self.rotate(15, 1, 0, 0) @ self.rotate(30, 0, 1, 0)  # Inclinación fija

        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "projection"), 1, GL_FALSE, projection)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 1, GL_FALSE, view)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "model"), 1, GL_FALSE, model)

        # Draw
        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
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
        print("Cleaning up MobiusBandVisualizer")
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
            if self.EBO:
                glDeleteBuffers(1, [self.EBO])
                self.EBO = None
        except Exception as e:
            print(f"Error during cleanup: {e}")