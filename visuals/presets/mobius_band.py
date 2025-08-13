from OpenGL.GL import *
import numpy as np
import ctypes
import os
import logging
import math
import time

from visuals.base_visualizer import BaseVisualizer

# Import OpenGL safety functions (opcional)
try:
    from opengl_fixes import OpenGLSafety
except ImportError:
    class OpenGLSafety:
        @staticmethod
        def check_gl_errors(context=""):
            try:
                error = glGetError()
                if error != GL_NO_ERROR:
                    logging.warning(f"OpenGL error in {context}: {error}")
                return error
            except Exception:
                return GL_NO_ERROR


def _perspective(fovy_deg: float, aspect: float, znear: float, zfar: float) -> np.ndarray:
    f = 1.0 / math.tan(math.radians(fovy_deg) / 2.0)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (zfar + znear) / (znear - zfar)
    m[2, 3] = (2.0 * zfar * znear) / (znear - zfar)
    m[3, 2] = -1.0
    return m


def _look_at(eye, center, up) -> np.ndarray:
    eye = np.array(eye, dtype=np.float32)
    center = np.array(center, dtype=np.float32)
    up = np.array(up, dtype=np.float32)

    f = center - eye
    f = f / np.linalg.norm(f)
    u = up / np.linalg.norm(up)
    s = np.cross(f, u)
    s = s / np.linalg.norm(s)
    u = np.cross(s, f)

    m = np.identity(4, dtype=np.float32)
    m[0, 0:3] = s
    m[1, 0:3] = u
    m[2, 0:3] = -f
    t = np.identity(4, dtype=np.float32)
    t[0, 3] = -eye[0]
    t[1, 3] = -eye[1]
    t[2, 3] = -eye[2]
    return m @ t


def _rotation_y(theta: float) -> np.ndarray:
    c, s = math.cos(theta), math.sin(theta)
    m = np.identity(4, dtype=np.float32)
    m[0, 0] = c
    m[0, 2] = s
    m[2, 0] = -s
    m[2, 2] = c
    return m


class MobiusBandVisualizer(BaseVisualizer):
    visual_name = "Möbius Band"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shader_program = None
        self.VBO = None
        self.VAO = None
        self.EBO = None

        self.num_segments = 100
        self.num_strips = 24   # algo más suave que 20
        self.vertices = None   # interleaved: x,y,z,r,g,b,a (7 floats)
        self.indices = None

        self.width = 1.0
        self.animation_speed = 1.0
        self.color_mode = 0
        self.surface_offset = 0.0
        self.opacity = 0.9
        self.wireframe = False

        self._last_time = time.time()
        self._proj = np.identity(4, dtype=np.float32)
        self._view = _look_at(eye=(0.0, 0.0, 6.0), center=(0.0, 0.0, 0.0), up=(0.0, 1.0, 0.0))
        self._model = np.identity(4, dtype=np.float32)

        # cache uniform locations
        self._u_projection = None
        self._u_view = None
        self._u_model = None

    # ---------- UI ----------
    def get_controls(self):
        return {
            "Segments": {"type": "slider", "min": 50, "max": 300, "value": int(self.num_segments)},
            "Width": {"type": "slider", "min": 30, "max": 300, "value": int(self.width * 100)},
            "Speed": {"type": "slider", "min": 1, "max": 100, "value": int(self.animation_speed * 10)},
            "Color Mode": {"type": "dropdown",
                           "options": ["Rainbow", "Fire", "Electric", "Ocean", "Plasma"],
                           "value": self.color_mode},
            "Opacity": {"type": "slider", "min": 10, "max": 100, "value": int(self.opacity * 100)},
            "Wireframe": {"type": "checkbox", "value": self.wireframe},
        }

    def update_control(self, name, value):
        if name == "Segments":
            self.num_segments = max(3, int(value))
            self.generate_geometry()
            self._upload_full_vbo()
        elif name == "Width":
            self.width = float(value) / 100.0
            self.generate_geometry()
            self._upload_full_vbo()
        elif name == "Speed":
            self.animation_speed = float(value) / 10.0
        elif name == "Color Mode":
            self.color_mode = int(value)
        elif name == "Opacity":
            self.opacity = float(value) / 100.0
        elif name == "Wireframe":
            self.wireframe = bool(value)

    # ---------- GL lifecycle ----------
    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 0.0)  # fondo transparente
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        if not self.load_shaders():
            print("Failed to initialize Möbius shaders")
            return

        self.generate_geometry()
        self.setup_buffers()
        self._cache_uniforms()
        print("MobiusBand initialized successfully")

    def resizeGL(self, w, h):
        glViewport(0, 0, max(1, w), max(1, h))
        aspect = max(1.0, float(w) / float(h if h > 0 else 1))
        self._proj = _perspective(50.0, aspect, 0.05, 100.0)

    def paintGL(self):
        # delta time
        now = time.time()
        dt = max(0.0, min(0.05, now - self._last_time))  # clamp 50ms
        self._last_time = now

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # animación
        self.surface_offset += dt * 0.7 * self.animation_speed
        self._model = _rotation_y(now * 0.3 * self.animation_speed)

        # actualizar colores (y subir al VBO eficientemente)
        self.update_colors()
        self._upload_colors_only()

        # draw
        glUseProgram(self.shader_program)
        if self._u_projection is not None:
            glUniformMatrix4fv(self._u_projection, 1, GL_FALSE, self._proj)
        if self._u_view is not None:
            glUniformMatrix4fv(self._u_view, 1, GL_FALSE, self._view)
        if self._u_model is not None:
            glUniformMatrix4fv(self._u_model, 1, GL_FALSE, self._model)

        glBindVertexArray(self.VAO)
        polygon_mode = GL_LINE if self.wireframe else GL_FILL
        glPolygonMode(GL_FRONT_AND_BACK, polygon_mode)
        glDrawElements(GL_TRIANGLES, self.indices.size, GL_UNSIGNED_INT, ctypes.c_void_p(0))
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glBindVertexArray(0)
        glUseProgram(0)

        OpenGLSafety.check_gl_errors("paintGL")

    def teardownGL(self):
        # Llama a esto en tu BaseVisualizer si tienes hook de cleanup
        try:
            if self.VAO:
                glDeleteVertexArrays(1, [self.VAO])
                self.VAO = None
            if self.VBO:
                glDeleteBuffers(1, [self.VBO])
                self.VBO = None
            if self.EBO:
                glDeleteBuffers(1, [self.EBO])
                self.EBO = None
            if self.shader_program:
                glDeleteProgram(self.shader_program)
                self.shader_program = None
        except Exception as e:
            print(f"teardownGL error: {e}")

    # ---------- Shaders ----------
    def load_shaders(self):
        try:
            # intenta cargar desde archivo
            script_dir = os.path.dirname(__file__)
            shader_dir = os.path.join(script_dir, '..', '..', 'shaders')

            vertex_src = None
            fragment_src = None
            try:
                with open(os.path.join(shader_dir, 'basic.vert'), 'r', encoding='utf-8') as f:
                    vertex_src = f.read()
                with open(os.path.join(shader_dir, 'basic.frag'), 'r', encoding='utf-8') as f:
                    fragment_src = f.read()
            except FileNotFoundError:
                print("Shader files not found, using fallback shaders")

            if not vertex_src:
                vertex_src = """
                #version 330 core
                layout (location = 0) in vec3 aPos;
                layout (location = 1) in vec4 aColor;
                uniform mat4 projection;
                uniform mat4 view;
                uniform mat4 model;
                out vec4 vColor;
                void main(){
                    gl_Position = projection * view * model * vec4(aPos, 1.0);
                    vColor = aColor;
                }
                """
            if not fragment_src:
                fragment_src = """
                #version 330 core
                in vec4 vColor;
                out vec4 FragColor;
                void main(){
                    FragColor = vColor;
                }
                """

            vs = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vs, vertex_src)
            glCompileShader(vs)
            if not glGetShaderiv(vs, GL_COMPILE_STATUS):
                raise RuntimeError(glGetShaderInfoLog(vs).decode())

            fs = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fs, fragment_src)
            glCompileShader(fs)
            if not glGetShaderiv(fs, GL_COMPILE_STATUS):
                raise RuntimeError(glGetShaderInfoLog(fs).decode())

            self.shader_program = glCreateProgram()
            glAttachShader(self.shader_program, vs)
            glAttachShader(self.shader_program, fs)
            glLinkProgram(self.shader_program)
            if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):
                raise RuntimeError(glGetProgramInfoLog(self.shader_program).decode())

            glDeleteShader(vs)
            glDeleteShader(fs)
            return True
        except Exception as e:
            print(f"Error loading MobiusBand shaders: {e}")
            return False

    def _cache_uniforms(self):
        glUseProgram(self.shader_program)
        self._u_projection = glGetUniformLocation(self.shader_program, "projection")
        self._u_view = glGetUniformLocation(self.shader_program, "view")
        self._u_model = glGetUniformLocation(self.shader_program, "model")
        glUseProgram(0)

    # ---------- Geometría ----------
    def generate_geometry(self):
        vertices = []
        indices = []

        # Parametrización clásica (radio ~2.0) con ancho variable en v
        for i in range(self.num_segments + 1):
            u = i * 2.0 * np.pi / self.num_segments
            for j in range(self.num_strips):
                v = -self.width + (2.0 * self.width * j) / (self.num_strips - 1)

                x = (2.0 + v * math.cos(u * 0.5)) * math.cos(u)
                y = (2.0 + v * math.cos(u * 0.5)) * math.sin(u)
                z = v * math.sin(u * 0.5)

                # pos + color placeholder (se rellena en update_colors)
                vertices.extend([x, y, z, 1.0, 1.0, 1.0, self.opacity])

        # Triángulos
        ring = self.num_strips
        for i in range(self.num_segments):
            for j in range(self.num_strips - 1):
                curr = i * ring + j
                nextu = (i + 1) * ring + j
                indices.extend([curr, nextu, curr + 1])
                indices.extend([nextu, nextu + 1, curr + 1])

        self.vertices = np.array(vertices, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.uint32)
        # inicializa colores una primera vez
        self.update_colors()

    def setup_buffers(self):
        # limpia anteriores
        if self.VAO:
            glDeleteVertexArrays(1, [self.VAO])
        if self.VBO:
            glDeleteBuffers(1, [self.VBO])
        if self.EBO:
            glDeleteBuffers(1, [self.EBO])

        self.VAO = glGenVertexArrays(1)
        self.VBO = glGenBuffers(1)
        self.EBO = glGenBuffers(1)

        glBindVertexArray(self.VAO)

        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_DYNAMIC_DRAW)

        stride = 7 * self.vertices.itemsize
        # aPos (location 0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        # aColor (location 1)
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * self.vertices.itemsize))
        glEnableVertexAttribArray(1)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)

        glBindVertexArray(0)

    # ---------- Actualización de color ----------
    def update_colors(self):
        if self.vertices is None:
            return

        vertex_count = self.vertices.size // 7
        ring = self.num_strips

        for i in range(vertex_count):
            seg = i // ring
            strip = i % ring
            u = seg * 2.0 * np.pi / self.num_segments
            v = strip / (ring - 1) if ring > 1 else 0.0

            sliding_u = u + self.surface_offset

            if self.color_mode == 0:  # Rainbow
                r = 0.5 + 0.5 * math.sin(sliding_u * 3.0)
                g = 0.5 + 0.5 * math.sin(sliding_u * 3.0 + 2 * math.pi / 3)
                b = 0.5 + 0.5 * math.sin(sliding_u * 3.0 + 4 * math.pi / 3)
            elif self.color_mode == 1:  # Fire
                t = 0.5 + 0.5 * math.sin(sliding_u * 4.0 + v * 2.0)
                r, g, b = 0.9 * t, 0.25 + 0.5 * t, 0.05 * t
            elif self.color_mode == 2:  # Electric
                t = 0.3 + 0.7 * max(0.0, math.sin(sliding_u * 8.0))
                r, g, b = 0.25 * t, 0.85 * t, 1.0 * t
            elif self.color_mode == 3:  # Ocean
                w1 = 0.5 + 0.5 * math.sin(sliding_u * 2.0)
                w2 = 0.5 + 0.5 * math.sin(sliding_u * 3.0 + v * 2.5)
                r, g, b = 0.08 * w1, 0.35 + 0.35 * w1, 0.65 + 0.35 * w2
            else:  # Plasma
                p1 = math.sin(sliding_u * 2.0 + v * 3.0)
                p2 = math.sin(sliding_u * 3.0 - v * 2.0)
                p3 = math.sin(sliding_u * 4.0 + v * 4.0)
                r, g, b = 0.5 + 0.5 * p1, 0.5 + 0.5 * p2, 0.5 + 0.5 * p3

            v_factor = 0.8 + 0.2 * math.sin(v * math.pi)
            base = i * 7
            self.vertices[base + 3] = r * v_factor
            self.vertices[base + 4] = g * v_factor
            self.vertices[base + 5] = b * v_factor
            self.vertices[base + 6] = self.opacity  # alpha

    # ---------- Subidas al GPU ----------
    def _upload_full_vbo(self):
        """Re-subir el VBO completo tras regenerar geometría."""
        if not self.VBO:
            self.setup_buffers()
            return
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_DYNAMIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def _upload_colors_only(self):
        """Sube solo la parte de color si la estructura no cambia."""
        if not self.VBO or self.vertices is None:
            return
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        stride = 7 * self.vertices.itemsize
        # Como los colores están intercalados, la forma más simple/robusta
        # es subir el bloque completo. En GPUs modernas esto es OK.
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.vertices.nbytes, self.vertices)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
