from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple
import ctypes

from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_BLEND,
    GL_MULTISAMPLE,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_FALSE,
    GL_FLOAT,
    GL_FRAGMENT_SHADER,
    GL_LINK_STATUS,
    GL_STATIC_DRAW,
    GL_TRIANGLES,
    GL_VERTEX_SHADER,
    glAttachShader,
    glBindBuffer,
    glBindVertexArray,
    glBlendFunc,
    glBufferData,
    glClear,
    glClearColor,
    glCompileShader,
    glCreateProgram,
    glCreateShader,
    glDeleteProgram,
    glDeleteShader,
    glDisable,
    glDrawArrays,
    glEnable,
    glEnableVertexAttribArray,
    glGenBuffers,
    glGenVertexArrays,
    glGetProgramInfoLog,
    glGetProgramiv,
    glGetShaderInfoLog,
    glGetShaderiv,
    glGetUniformLocation,
    glLinkProgram,
    glShaderSource,
    glUniform1f,
    glUniform1fv,
    glUniform2f,
    glUniform3f,
    glUniform4f,
    glUseProgram,
    glVertexAttribPointer,
    glViewport,
)


class RenderBackend:
    """Abstract rendering backend."""

    def ensure_context(self) -> None:  # pragma: no cover - interface
        pass

    def begin_target(self, size: Tuple[int, int]) -> None:  # pragma: no cover - interface
        pass

    def end_target(self) -> None:  # pragma: no cover - interface
        pass

    def clear(self, r: float, g: float, b: float, a: float) -> None:  # pragma: no cover - interface
        pass

    def program(self, vertex_src: str, fragment_src: str, **kwargs) -> Any:  # pragma: no cover
        pass

    def buffer(self, data: bytes) -> Any:  # pragma: no cover
        pass

    def vertex_array(
        self, program: Any, content: Any, index_buffer: Any | None = None
    ) -> Any:  # pragma: no cover
        pass

    def set_viewport(self, x: int, y: int, w: int, h: int) -> None:  # pragma: no cover
        pass

    def uniform(self, program: Any, name: str, value: Any) -> None:  # pragma: no cover
        pass


@dataclass
class GLBuffer:
    buffer_id: int
    size: int


class GLVertexArray:
    def __init__(self, program: int, vao: int, count: int) -> None:
        self.program = program
        self.vao = vao
        self.count = count

    def render(self, mode: int = GL_TRIANGLES) -> None:
        glUseProgram(self.program)
        glBindVertexArray(self.vao)
        glDrawArrays(mode, 0, self.count)
        glBindVertexArray(0)
        glUseProgram(0)


class GLBackend(RenderBackend):
    """Backend that forwards to classic OpenGL calls."""

    def ensure_context(self) -> None:
        glEnable(GL_BLEND)
        glEnable(GL_MULTISAMPLE)
        glBlendFunc(1, 771)  # GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA
        glDisable(0x0B71)  # GL_DEPTH_TEST

    def begin_target(self, size: Tuple[int, int]) -> None:
        self.set_viewport(0, 0, size[0], size[1])

    def end_target(self) -> None:
        pass

    def clear(self, r: float, g: float, b: float, a: float) -> None:
        glClearColor(r, g, b, a)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def program(self, vertex_src: str, fragment_src: str, **kwargs) -> int:
        vs = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vs, vertex_src)
        glCompileShader(vs)
        if not glGetShaderiv(vs, 0x8B81):
            error = glGetShaderInfoLog(vs).decode()
            glDeleteShader(vs)
            raise RuntimeError(f"Vertex shader compilation failed: {error}")

        fs = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fs, fragment_src)
        glCompileShader(fs)
        if not glGetShaderiv(fs, 0x8B81):
            error = glGetShaderInfoLog(fs).decode()
            glDeleteShader(vs)
            glDeleteShader(fs)
            raise RuntimeError(f"Fragment shader compilation failed: {error}")

        program = glCreateProgram()
        glAttachShader(program, vs)
        glAttachShader(program, fs)
        glLinkProgram(program)
        if not glGetProgramiv(program, GL_LINK_STATUS):
            error = glGetProgramInfoLog(program).decode()
            glDeleteShader(vs)
            glDeleteShader(fs)
            glDeleteProgram(program)
            raise RuntimeError(f"Program link failed: {error}")

        glDeleteShader(vs)
        glDeleteShader(fs)
        return program

    def buffer(self, data: bytes) -> GLBuffer:
        buf = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, buf)
        glBufferData(GL_ARRAY_BUFFER, len(data), data, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        return GLBuffer(buf, len(data))

    def vertex_array(
        self, program: int, content: Any, index_buffer: Any | None = None
    ) -> GLVertexArray:
        vao = glGenVertexArrays(1)
        glBindVertexArray(vao)

        buf, fmt, *attrs = content[0]
        stride = 0
        comps = []
        for part in fmt.split():
            num = int(part[:-1])
            stride += num * 4
            comps.append(num)

        glBindBuffer(GL_ARRAY_BUFFER, buf.buffer_id)
        offset = 0
        for idx, num in enumerate(comps):
            glEnableVertexAttribArray(idx)
            glVertexAttribPointer(
                idx, num, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset)
            )
            offset += num * 4

        glBindVertexArray(0)
        count = buf.size // stride
        return GLVertexArray(program, vao, count)

    def set_viewport(self, x: int, y: int, w: int, h: int) -> None:
        glViewport(x, y, w, h)

    def uniform(self, program: int, name: str, value: Any) -> None:
        loc = glGetUniformLocation(program, name)
        if loc < 0:
            return
        if isinstance(value, (float, int)):
            glUniform1f(loc, float(value))
        elif isinstance(value, (list, tuple)):
            if len(value) == 2:
                glUniform2f(loc, *value)
            elif len(value) == 3:
                glUniform3f(loc, *value)
            elif len(value) == 4:
                glUniform4f(loc, *value)
            else:
                glUniform1fv(loc, len(value), value)


class ModernGLBackend(RenderBackend):
    """Backend using moderngl. Context is created on demand."""

    def __init__(self, device_index: int = 0) -> None:
        self.ctx = None
        self.mgl = None
        self.device_index = device_index

    def ensure_context(self) -> None:
        if self.ctx is None:
            import moderngl

            self.mgl = moderngl
            try:
                self.ctx = moderngl.create_context(
                    require=330, standalone=True, backend="egl", device_index=self.device_index
                )
            except Exception:
                self.ctx = moderngl.create_context(require=330)
            self.ctx.enable(moderngl.BLEND)

    def begin_target(self, size: Tuple[int, int]) -> None:
        if self.ctx:
            self.set_viewport(0, 0, size[0], size[1])

    def end_target(self) -> None:
        pass

    def clear(self, r: float, g: float, b: float, a: float) -> None:
        self.ctx.clear(r, g, b, a)

    def program(self, vertex_src: str, fragment_src: str, **kwargs) -> Any:
        return self.ctx.program(
            vertex_shader=vertex_src, fragment_shader=fragment_src, **kwargs
        )

    def buffer(self, data: bytes) -> Any:
        return self.ctx.buffer(data)

    def vertex_array(
        self, program: Any, content: Any, index_buffer: Any | None = None
    ) -> Any:
        return self.ctx.vertex_array(program, content, index_buffer=index_buffer)

    def set_viewport(self, x: int, y: int, w: int, h: int) -> None:
        self.ctx.viewport = (x, y, w, h)

    def uniform(self, program: Any, name: str, value: Any) -> None:
        if name not in program:
            return
        uniform = program[name]
        if isinstance(value, (list, tuple)) and len(value) > 4:
            import numpy as np

            uniform.write(np.array(value, dtype="f4").tobytes())
        else:
            uniform.value = value

