# visuals/presets/test_visualizer.py
#
# Simple test visualizer that renders basic shapes using modern OpenGL calls.
# The previous version used immediate mode (glBegin/glEnd) which caused
# GL_INVALID_OPERATION errors on drivers that expose a core profile without
# legacy support. This rewrite uses a small shader program and vertex buffers
# for portability.

from __future__ import annotations

import ctypes
import math
import time
from dataclasses import dataclass

import numpy as np
from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_BLEND,
    GL_COLOR_BUFFER_BIT,
    GL_FLOAT,
    GL_STATIC_DRAW,
    GL_TRIANGLES,
    GL_TRIANGLE_FAN,
    GL_FALSE,
    glBindBuffer,
    glBindVertexArray,
    glBlendFunc,
    glBufferData,
    glClear,
    glClearColor,
    glCreateProgram,
    glCreateShader,
    glDeleteBuffers,
    glDeleteProgram,
    glDeleteShader,
    glDeleteVertexArrays,
    glDrawArrays,
    glEnable,
    glEnableVertexAttribArray,
    glLinkProgram,
    glShaderSource,
    glUseProgram,
    glVertexAttribPointer,
    glViewport,
    glAttachShader,
    glGetProgramiv,
    glGetShaderiv,
    glGetUniformLocation,
    glUniform1f,
    glUniform2f,
    glUniform3f,
    glCompileShader,
    glGetProgramInfoLog,
    glGetShaderInfoLog,
    GL_LINK_STATUS,
    GL_COMPILE_STATUS,
    GL_VERTEX_SHADER,
    GL_FRAGMENT_SHADER,
)

from visuals.base_visualizer import BaseVisualizer


@dataclass
class Shape:
    vao: int
    vbo: int
    count: int
    mode: int


class TestVisualizer(BaseVisualizer):
    """Render a simple animated shape for testing purposes."""

    visual_name = "Test Pattern"

    def __init__(self) -> None:
        super().__init__()
        self.time = 0.0
        self.color_r = 1.0
        self.color_g = 0.5
        self.color_b = 0.0
        self.speed = 1.0
        self.pattern = 0  # 0 = circle, 1 = square, 2 = triangle

        # Shader / geometry handles
        self.program: int | None = None
        self.offset_loc = -1
        self.size_loc = -1
        self.color_loc = -1
        self.shapes: dict[str, Shape] = {}

    # ------------------------------------------------------------------
    # OpenGL setup
    # ------------------------------------------------------------------
    def initializeGL(self) -> None:
        glClearColor(0.0, 0.0, 0.0, 0.0)  # Transparent background
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.program = self._create_program()
        self.offset_loc = glGetUniformLocation(self.program, "offset")
        self.size_loc = glGetUniformLocation(self.program, "size")
        self.color_loc = glGetUniformLocation(self.program, "color")

        # Pre-build geometry for the supported shapes
        self.shapes = {
            "circle": self._create_circle(),
            "square": self._create_square(),
            "triangle": self._create_triangle(),
        }
        print("TestVisualizer initialized")

    def resizeGL(self, w: int, h: int) -> None:
        glViewport(0, 0, w, h)
        print(f"TestVisualizer resized to {w}x{h}")

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def paintGL(self) -> None:
        self.time += 0.016 * self.speed  # Assume ~60 FPS

        glClear(GL_COLOR_BUFFER_BIT)

        # Animated position/size
        x = math.sin(self.time) * 0.5
        y = math.cos(self.time * 0.7) * 0.3
        size = 0.2 + 0.1 * math.sin(self.time * 2)

        shape_key = "circle" if self.pattern == 0 else "square" if self.pattern == 1 else "triangle"
        self._draw_shape(shape_key, x, y, size)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _create_program(self) -> int:
        vertex_src = """
        #version 330 core
        layout (location = 0) in vec2 aPos;
        uniform vec2 offset;
        uniform float size;
        void main() {
            vec2 pos = aPos * size + offset;
            gl_Position = vec4(pos, 0.0, 1.0);
        }
        """

        fragment_src = """
        #version 330 core
        uniform vec3 color;
        out vec4 FragColor;
        void main() {
            FragColor = vec4(color, 0.8);
        }
        """

        def compile_shader(src: str, shader_type: int) -> int:
            shader = glCreateShader(shader_type)
            glShaderSource(shader, src)
            glCompileShader(shader)
            if not glGetShaderiv(shader, GL_COMPILE_STATUS):
                err = glGetShaderInfoLog(shader).decode()
                glDeleteShader(shader)
                raise RuntimeError(err)
            return shader

        vs = compile_shader(vertex_src, GL_VERTEX_SHADER)
        fs = compile_shader(fragment_src, GL_FRAGMENT_SHADER)

        program = glCreateProgram()
        glAttachShader(program, vs)
        glAttachShader(program, fs)
        glLinkProgram(program)

        if not glGetProgramiv(program, GL_LINK_STATUS):
            err = glGetProgramInfoLog(program).decode()
            glDeleteShader(vs)
            glDeleteShader(fs)
            glDeleteProgram(program)
            raise RuntimeError(err)

        glDeleteShader(vs)
        glDeleteShader(fs)
        return program

    def _create_circle(self) -> Shape:
        verts = [(0.0, 0.0)]
        for i in range(33):
            angle = 2.0 * math.pi * i / 32.0
            verts.append((math.cos(angle), math.sin(angle)))
        return self._create_shape(verts, GL_TRIANGLE_FAN)

    def _create_square(self) -> Shape:
        verts = [
            (-1.0, -1.0),
            (1.0, -1.0),
            (1.0, 1.0),
            (-1.0, -1.0),
            (1.0, 1.0),
            (-1.0, 1.0),
        ]
        return self._create_shape(verts, GL_TRIANGLES)

    def _create_triangle(self) -> Shape:
        verts = [(0.0, 1.0), (-1.0, -1.0), (1.0, -1.0)]
        return self._create_shape(verts, GL_TRIANGLES)

    def _create_shape(self, vertices: list[tuple[float, float]], mode: int) -> Shape:
        arr = np.array(vertices, dtype=np.float32)
        vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)
        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, arr.nbytes, arr, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        return Shape(vao=vao, vbo=vbo, count=len(arr) // 2, mode=mode)

    def _draw_shape(self, key: str, x: float, y: float, size: float) -> None:
        if self.program is None:
            return
        shape = self.shapes[key]
        glUseProgram(self.program)
        glUniform2f(self.offset_loc, x, y)
        glUniform1f(self.size_loc, size)
        glUniform3f(self.color_loc, self.color_r, self.color_g, self.color_b)
        glBindVertexArray(shape.vao)
        glDrawArrays(shape.mode, 0, shape.count)
        glBindVertexArray(0)
        glUseProgram(0)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def get_controls(self) -> dict:
        return {
            "Red": {"type": "slider", "min": 0, "max": 100, "value": int(self.color_r * 100)},
            "Green": {"type": "slider", "min": 0, "max": 100, "value": int(self.color_g * 100)},
            "Blue": {"type": "slider", "min": 0, "max": 100, "value": int(self.color_b * 100)},
            "Speed": {"type": "slider", "min": 0, "max": 300, "value": int(self.speed * 100)},
            "Pattern": {"type": "dropdown", "options": ["Circle", "Square", "Triangle"], "value": self.pattern},
        }

    def update_control(self, name: str, value: float) -> None:
        print(f"TestVisualizer: updating {name} to {value}")
        if name == "Red":
            self.color_r = value / 100.0
        elif name == "Green":
            self.color_g = value / 100.0
        elif name == "Blue":
            self.color_b = value / 100.0
        elif name == "Speed":
            self.speed = value / 100.0
        elif name == "Pattern":
            self.pattern = int(value)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def cleanup(self) -> None:
        for shape in self.shapes.values():
            glDeleteBuffers(1, [shape.vbo])
            glDeleteVertexArrays(1, [shape.vao])
        if self.program:
            glDeleteProgram(self.program)
        print("TestVisualizer cleaned up")

