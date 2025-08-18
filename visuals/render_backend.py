from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Tuple
import ctypes

from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_BLEND,
    GL_MULTISAMPLE,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_FALSE,
    GL_FLOAT,
    GL_FRAGMENT_SHADER,
    GL_COMPILE_STATUS,
    GL_LINK_STATUS,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
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
    glGetError,
    GL_NO_ERROR,
)


class RenderBackend:
    """Abstract rendering backend."""

    def ensure_context(self) -> None:  # pragma: no cover - interface
        pass

    def begin_frame(self, size: Tuple[int, int]) -> None:  # pragma: no cover - interface
        pass

    def end_frame(self) -> None:  # pragma: no cover - interface
        pass

    def begin_target(self, target: Any) -> None:  # pragma: no cover - interface
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

    def create_framebuffer(self, width: int, height: int) -> Any:  # pragma: no cover - interface
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
    """Backend that forwards to classic OpenGL calls - FIXED."""

    def __init__(self):
        self.context_initialized = False
        logging.debug("🎮 GLBackend initialized")

    def ensure_context(self) -> None:
        """Ensure OpenGL context is properly configured"""
        if not self.context_initialized:
            try:
                # Clear any existing errors
                while glGetError() != GL_NO_ERROR:
                    pass
                    
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                glDisable(GL_DEPTH_TEST)
                
                # Try to enable multisampling if available
                try:
                    glEnable(GL_MULTISAMPLE)
                except Exception:
                    pass  # Multisampling might not be available
                
                self.context_initialized = True
                logging.debug("✅ GLBackend context initialized")
                
            except Exception as e:
                logging.error(f"❌ Error initializing GLBackend context: {e}")

    def begin_target(self, size: Tuple[int, int]) -> None:
        self.set_viewport(0, 0, size[0], size[1])

    def end_target(self) -> None:
        pass

    def clear(self, r: float, g: float, b: float, a: float) -> None:
        glClearColor(r, g, b, a)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def program(self, vertex_src: str, fragment_src: str, **kwargs) -> int:
        """Compile and link a shader program"""
        try:
            # Compile vertex shader
            vs = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vs, vertex_src)
            glCompileShader(vs)

            if not glGetShaderiv(vs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(vs).decode()
                glDeleteShader(vs)
                raise RuntimeError(f"Vertex shader compilation failed: {error}")

            # Compile fragment shader
            fs = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fs, fragment_src)
            glCompileShader(fs)

            if not glGetShaderiv(fs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(fs).decode()
                glDeleteShader(vs)
                glDeleteShader(fs)
                raise RuntimeError(f"Fragment shader compilation failed: {error}")

            # Link program
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

            # Clean up individual shaders
            glDeleteShader(vs)
            glDeleteShader(fs)

            return program

        except Exception as e:
            logging.error(f"❌ GLBackend program compilation failed: {e}")
            raise

    def buffer(self, data: bytes) -> GLBuffer:
        """Create a buffer object"""
        try:
            buf = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, buf)
            glBufferData(GL_ARRAY_BUFFER, len(data), data, GL_STATIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            return GLBuffer(buf, len(data))
        except Exception as e:
            logging.error(f"❌ GLBackend buffer creation failed: {e}")
            raise

    def vertex_array(
        self, program: int, content: Any, index_buffer: Any | None = None
    ) -> GLVertexArray:
        """Create a vertex array object"""
        try:
            vao = glGenVertexArrays(1)
            glBindVertexArray(vao)

            buf, fmt, *attrs = content[0]
            stride = 0
            comps = []
            
            # Parse format string (e.g., "2f 2f" -> positions and texcoords)
            for part in fmt.split():
                num = int(part[:-1])
                stride += num * 4  # 4 bytes per float
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
            
        except Exception as e:
            logging.error(f"❌ GLBackend vertex array creation failed: {e}")
            raise

    def set_viewport(self, x: int, y: int, w: int, h: int) -> None:
        glViewport(x, y, w, h)

    def uniform(self, program: int, name: str, value: Any) -> None:
        """Set a uniform value ensuring the program is bound."""
        try:
            loc = glGetUniformLocation(program, name)
            if loc < 0:
                return  # Uniform not found or optimized out

            # glUniform* calls require the program to be currently bound.
            glUseProgram(program)

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
                    # For arrays
                    import numpy as np
                    glUniform1fv(loc, len(value), np.array(value, dtype=np.float32))
                    
        except Exception as e:
            logging.error(f"❌ GLBackend uniform setting failed for {name}: {e}")


class ModernGLBackend(RenderBackend):
    """Backend using moderngl - ENHANCED WITH BETTER ERROR HANDLING."""

    def __init__(self, device_index: int = 0, share_context: Any = None) -> None:
        self.ctx = None
        self.mgl = None
        self.device_index = device_index
        self.share_context = share_context  # Store the context to share with
        self.context_initialized = False
        logging.debug(f"🎮 ModernGLBackend initialized with device_index={device_index}, share_context={share_context is not None}")

    def ensure_context(self) -> None:
        """Ensure ModernGL context is created and configured.

        The original implementation attempted a number of different context
        creation strategies every time the method was called.  This patch
        simplifies the logic, performs a fast early return when a context is
        already available and provides clearer logging for each attempt.  The
        behaviour is otherwise unchanged but avoids repeated work on subsequent
        calls.
        """

        if self.ctx is not None:
            # Context already exists – nothing to do.
            return

        try:
            import moderngl
            self.mgl = moderngl

            if self.share_context:
                logging.debug("🔧 Creating ModernGL context by sharing existing GL context")
                try:
                    self.ctx = moderngl.create_context(share=self.share_context)
                    logging.info("✅ ModernGL context created by sharing")
                except Exception as exc:
                    logging.error(f"❌ Failed to create ModernGL context by sharing: {exc}")
                    raise
            else:
                logging.debug(
                    f"🔧 Creating ModernGL context for device {self.device_index}"
                )

                creation_attempts = [
                    {"require": 330, "standalone": True, "device_index": self.device_index},
                    {"require": 330, "standalone": True, "backend": "egl", "device_index": self.device_index},
                    {"require": 330},  # Fallback
                ]

                for kwargs in creation_attempts:
                    try:
                        self.ctx = moderngl.create_context(**kwargs)
                        logging.info(
                            f"✅ ModernGL context created ({kwargs})"
                        )
                        break
                    except Exception as exc:  # pragma: no cover - logging path
                        logging.debug(f"ModernGL context creation failed {kwargs}: {exc}")

                if self.ctx is None:
                    raise RuntimeError("All ModernGL context creation methods failed")

            # Configure context
            self.ctx.enable(moderngl.BLEND)

            # Log context info once for diagnostics
            try:
                info = self.ctx.info
                renderer = info.get("GL_RENDERER", "Unknown")
                vendor = info.get("GL_VENDOR", "Unknown")
                version = info.get("GL_VERSION", "Unknown")
                logging.info("🎮 ModernGL Context Info:")
                logging.info(f"   Renderer: {renderer}")
                logging.info(f"   Vendor: {vendor}")
                logging.info(f"   Version: {version}")
            except Exception as info_exc:  # pragma: no cover - logging path
                logging.warning(f"Could not get ModernGL context info: {info_exc}")

            self.context_initialized = True

        except ImportError:  # pragma: no cover - dependency issue
            logging.error("❌ ModernGL not available! Install with: pip install moderngl")
            raise
        except Exception as e:  # pragma: no cover - logging path
            logging.error(f"❌ Failed to create ModernGL context: {e}")
            raise

    def begin_target(self, size: Tuple[int, int]) -> None:
        if self.ctx:
            self.set_viewport(0, 0, size[0], size[1])

    def end_target(self) -> None:
        pass

    def clear(self, r: float, g: float, b: float, a: float) -> None:
        if self.ctx:
            self.ctx.clear(r, g, b, a)

    def program(self, vertex_src: str, fragment_src: str, **kwargs) -> Any:
        """Create a ModernGL program"""
        if not self.ctx:
            raise RuntimeError("ModernGL context not available")
        
        try:
            return self.ctx.program(
                vertex_shader=vertex_src, 
                fragment_shader=fragment_src, 
                **kwargs
            )
        except Exception as e:
            logging.error(f"❌ ModernGL program creation failed: {e}")
            raise

    def buffer(self, data: bytes) -> Any:
        if not self.ctx:
            raise RuntimeError("ModernGL context not available")
        
        try:
            return self.ctx.buffer(data)
        except Exception as e:
            logging.error(f"❌ ModernGL buffer creation failed: {e}")
            raise

    def vertex_array(
        self, program: Any, content: Any, index_buffer: Any | None = None
    ) -> Any:
        if not self.ctx:
            raise RuntimeError("ModernGL context not available")
        
        try:
            return self.ctx.vertex_array(program, content, index_buffer=index_buffer)
        except Exception as e:
            logging.error(f"❌ ModernGL vertex array creation failed: {e}")
            raise

    def set_viewport(self, x: int, y: int, w: int, h: int) -> None:
        if self.ctx:
            self.ctx.viewport = (x, y, w, h)

    def uniform(self, program: Any, name: str, value: Any) -> None:
        """Set uniform value in ModernGL program"""
        try:
            if name not in program:
                return  # Uniform not found or optimized out
            
            uniform = program[name]
            
            if isinstance(value, (list, tuple)) and len(value) > 4:
                # Large arrays need to be written as bytes
                import numpy as np
                uniform.write(np.array(value, dtype="f4").tobytes())
            else:
                uniform.value = value
                
        except Exception as e:
            logging.error(f"❌ ModernGL uniform setting failed for {name}: {e}")

    def cleanup(self):
        """Clean up ModernGL resources"""
        try:
            if self.ctx:
                self.ctx.release()
                self.ctx = None
                self.context_initialized = False
                logging.debug("✅ ModernGL context released")
        except Exception as e:
            logging.error(f"❌ Error cleaning up ModernGL context: {e}")


def create_backend(backend_type: str = "OpenGL", device_index: int = 0) -> RenderBackend:
    """Factory function to create the appropriate backend"""
    try:
        if backend_type.lower() == "moderngl":
            return ModernGLBackend(device_index)
        else:
            return GLBackend()
    except Exception as e:
        logging.error(f"❌ Failed to create {backend_type} backend: {e}")
        logging.info("🔄 Falling back to OpenGL backend")
        return GLBackend()


def get_available_backends() -> list[str]:
    """Get list of available backends"""
    backends = ["OpenGL"]
    
    try:
        import moderngl
        backends.append("ModernGL")
    except ImportError:
        pass
    
    return backends


def test_backend(backend_type: str, device_index: int = 0) -> bool:
    """Test if a backend can be created successfully"""
    try:
        backend = create_backend(backend_type, device_index)
        backend.ensure_context()

        if hasattr(backend, "cleanup"):
            backend.cleanup()

        return True
    except Exception as e:
        logging.debug(f"Backend {backend_type} test failed: {e}")
        return False
