import logging
import numpy as np
import ctypes
from OpenGL.GL import (
    glClearColor, glClear, GL_COLOR_BUFFER_BIT,
    glEnable, glBlendFunc, glDisable, GL_BLEND, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
    GL_DEPTH_TEST, glGenVertexArrays, glBindVertexArray,
    glGenBuffers, glBindBuffer, GL_ARRAY_BUFFER, glBufferData, GL_DYNAMIC_DRAW,
    glVertexAttribPointer, glEnableVertexAttribArray, GLfloat,
    glUseProgram,
    glDrawArrays, GL_TRIANGLES, glDeleteBuffers, glDeleteVertexArrays,
    glDeleteProgram
)

from ..base_visualizer import BaseVisualizer


class BuildingMadnessVisualizer(BaseVisualizer):
    """Audio reactive skyline visualizer."""

    visual_name = "Building Madness"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.time = 0.0
        self.building_count = 20
        self.max_height = 1.2
        self.x_positions: np.ndarray | None = None
        self.width = 0.0

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def initializeGL(self):
        """Initialize OpenGL resources."""
        try:
            glClearColor(0.95, 0.98, 1.0, 0.0)  # blueprint style background
            glDisable(GL_DEPTH_TEST)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            if not self._load_shaders():
                logging.error("BuildingMadness: shader compilation failed")
                return
            self._setup_geometry()
        except Exception as exc:  # pragma: no cover - defensive
            logging.error(f"BuildingMadness.initializeGL error: {exc}")

    def _load_shaders(self) -> bool:
        """Compile and link shaders."""
        try:
            vertex_src = """
            #version 330 core
            layout(location = 0) in vec2 aPos;
            layout(location = 1) in vec4 aColor;
            out vec4 vColor;
            void main(){
                gl_Position = vec4(aPos, 0.0, 1.0);
                vColor = aColor;
            }
            """

            fragment_src = """
            #version 330 core
            in vec4 vColor;
            out vec4 FragColor;
            void main(){
                FragColor = vColor;
            }
            """

            vs = glCreateShader(GL_VERTEX_SHADER)  # type: ignore
            glShaderSource(vs, vertex_src)
            glCompileShader(vs)
            if not glGetShaderiv(vs, GL_COMPILE_STATUS):  # type: ignore
                err = glGetShaderInfoLog(vs).decode()
                logging.error(f"BuildingMadness vertex shader error: {err}")
                return False

            fs = glCreateShader(GL_FRAGMENT_SHADER)  # type: ignore
            glShaderSource(fs, fragment_src)
            glCompileShader(fs)
            if not glGetShaderiv(fs, GL_COMPILE_STATUS):  # type: ignore
                err = glGetShaderInfoLog(fs).decode()
                logging.error(f"BuildingMadness fragment shader error: {err}")
                return False

            self.shader_program = glCreateProgram()  # type: ignore
            glAttachShader(self.shader_program, vs)
            glAttachShader(self.shader_program, fs)
            glLinkProgram(self.shader_program)
            if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):  # type: ignore
                err = glGetProgramInfoLog(self.shader_program).decode()
                logging.error(f"BuildingMadness program link error: {err}")
                return False

            glDeleteShader(vs)
            glDeleteShader(fs)
            return True
        except Exception as exc:  # pragma: no cover - defensive
            logging.error(f"BuildingMadness shader load error: {exc}")
            return False

    def _setup_geometry(self):
        """Prepare buffers for building geometry."""
        spacing = 2.0 / self.building_count
        self.width = spacing * 0.8
        # compute left x positions for each building
        self.x_positions = np.linspace(-1.0, 1.0 - self.width, self.building_count)

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        # allocate empty buffer; will be filled each frame
        glBufferData(GL_ARRAY_BUFFER, 0, None, GL_DYNAMIC_DRAW)

        stride = 6 * ctypes.sizeof(GLfloat)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(2 * ctypes.sizeof(GLfloat)))
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)

    # ------------------------------------------------------------------
    # Main rendering
    # ------------------------------------------------------------------
    def paintGL(self):  # pragma: no cover - heavy OpenGL usage
        glClear(GL_COLOR_BUFFER_BIT)
        if not self.shader_program or self.vbo is None or self.vao is None:
            return

        # obtain audio data or generate demo pattern
        if hasattr(self, "analyzer") and self.analyzer and self.analyzer.is_active():
            fft = self.analyzer.get_fft_data().astype(np.float32)
        else:
            # demo sine pattern
            bins = self.building_count
            t = self.time
            fft = (0.5 + 0.5 * np.sin(np.linspace(0, 2*np.pi, bins) + t)) * 50

        # compute heights from FFT bins
        heights = []
        total_bins = len(fft)
        for i in range(self.building_count):
            start = int(i * total_bins / self.building_count)
            end = int((i + 1) * total_bins / self.building_count)
            amp = float(np.mean(fft[start:end])) if end > start else 0.0
            h = 0.1 + np.clip(amp / 50.0, 0.0, 1.0) * self.max_height
            heights.append(h)

        vertex_data = self._build_vertices(heights)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, GL_DYNAMIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        glUseProgram(self.shader_program)
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, len(vertex_data) // 6)
        glBindVertexArray(0)
        glUseProgram(0)

        self.time += 0.016  # assume ~60 FPS for demo mode

    def _build_vertices(self, heights: list[float]) -> np.ndarray:
        """Create vertex data for current building heights."""
        if self.x_positions is None:
            return np.array([], dtype=np.float32)

        data: list[float] = []
        ground = -0.4
        for x, h in zip(self.x_positions, heights):
            x0 = x
            x1 = x + self.width
            y0 = ground
            y1 = ground + h
            r, g, b = 0.2, 0.4, 0.7
            # main building (two triangles)
            data.extend([
                x0, y0, r, g, b, 1.0,
                x1, y0, r, g, b, 1.0,
                x1, y1, r, g, b, 1.0,
                x0, y0, r, g, b, 1.0,
                x1, y1, r, g, b, 1.0,
                x0, y1, r, g, b, 1.0,
            ])
            # reflection
            rf = 0.35
            data.extend([
                x0, y0, r, g, b, rf,
                x1, y0, r, g, b, rf,
                x1, y0 - h, r, g, b, 0.0,
                x0, y0, r, g, b, rf,
                x1, y0 - h, r, g, b, 0.0,
                x0, y0 - h, r, g, b, 0.0,
            ])
        return np.array(data, dtype=np.float32)

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------
    def get_controls(self):
        return {
            "Building Count": {
                "type": "slider",
                "min": 5,
                "max": 50,
                "value": int(self.building_count),
            }
        }

    def update_control(self, name, value):
        if name == "Building Count":
            self.building_count = max(5, int(value))
            self._setup_geometry()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def cleanup(self):  # pragma: no cover - heavy OpenGL usage
        try:
            if self.shader_program:
                glDeleteProgram(self.shader_program)
                self.shader_program = None
            if self.vbo:
                glDeleteBuffers(1, [self.vbo])
                self.vbo = None
            if self.vao:
                glDeleteVertexArrays(1, [self.vao])
                self.vao = None
        except Exception as exc:
            logging.error(f"BuildingMadness.cleanup error: {exc}")

