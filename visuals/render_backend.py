"""Simplified rendering backend using Taichi.

This module replaces the previous OpenGL/ModernGL based implementation with a
minimal Taichi powered backend.  The goal is to provide a lightweight and
Pythonic API that existing visualizers can gradually migrate to.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple

import numpy as np
import taichi as ti


class RenderBackend:
    """Abstract rendering backend interface."""

    def ensure_context(self) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def begin_frame(self, size: Tuple[int, int]) -> None:  # pragma: no cover
        raise NotImplementedError

    def end_frame(self) -> np.ndarray:  # pragma: no cover
        raise NotImplementedError

    def clear(self, r: float, g: float, b: float, a: float) -> None:  # pragma: no cover
        raise NotImplementedError


@dataclass
class Pass:
    name: str
    compute: Callable[[ti.Field], None]


class TaichiBackend(RenderBackend):
    """Basic Taichi based renderer.

    The backend maintains a list of passes that operate on an RGBA canvas.  Each
    pass is a callable accepting the canvas field.  After all passes run the
    resulting image can be retrieved as a numpy array.
    """

    def __init__(self, resolution: Tuple[int, int] = (640, 480)) -> None:
        ti.init(arch=ti.cpu)
        self.resolution = resolution
        self.canvas = ti.Vector.field(4, dtype=ti.f32, shape=resolution)
        self._passes: List[Pass] = []

    # ------------------------------------------------------------------
    # RenderBackend API
    # ------------------------------------------------------------------
    def ensure_context(self) -> None:
        """Taichi initializes on construction, nothing extra required."""
        return None

    def begin_frame(self, size: Tuple[int, int]) -> None:
        if size != self.resolution:
            self.resolution = size
            self.canvas = ti.Vector.field(4, dtype=ti.f32, shape=size)
        self._passes.clear()

    def add_pass(self, name: str, compute: Callable[[ti.Field], None]) -> None:
        self._passes.append(Pass(name, compute))

    def clear(self, r: float, g: float, b: float, a: float) -> None:
        @ti.kernel
        def _clear(canvas: ti.types.ndarray()):
            for i, j in ti.ndrange(canvas.shape[0], canvas.shape[1]):
                canvas[i, j] = ti.Vector([r, g, b, a])

        def compute(field: ti.Field) -> None:
            _clear(field)

        self.add_pass("clear", compute)

    def end_frame(self) -> np.ndarray:
        for p in self._passes:
            p.compute(self.canvas)
        return self.canvas.to_numpy()

    # ------------------------------------------------------------------
    # Compatibility helpers
    # ------------------------------------------------------------------
    def begin_target(self, size: Tuple[int, int]) -> None:
        """Alias of :meth:`begin_frame` for legacy callers."""
        self.begin_frame(size)

    def end_target(self) -> np.ndarray:
        """Alias of :meth:`end_frame` for legacy callers."""
        return self.end_frame()

    # Compatibility stubs ------------------------------------------------
    # Simple data containers used by legacy presets expecting an OpenGL style API
    @dataclass
    class _DummyProgram:
        vertex_shader: str = ""
        fragment_shader: str = ""
        uniforms: Dict[str, Any] = None

        def __post_init__(self) -> None:  # pragma: no cover - simple container
            if self.uniforms is None:
                self.uniforms = {}

    class _DummyBuffer:
        def __init__(self, data: bytes | None = None) -> None:  # pragma: no cover - simple container
            self.data = data

        def release(self) -> None:  # pragma: no cover - simple container
            self.data = None

    class _DummyVertexArray:
        def __init__(self, program: "TaichiBackend._DummyProgram", buffers: Tuple[Any, ...]):  # pragma: no cover - simple container
            self.program = program
            self.buffers = buffers

        def render(self) -> None:  # pragma: no cover - no-op
            return None

        def release(self) -> None:  # pragma: no cover - simple container
            self.program = None
            self.buffers = ()

    def program(self, vertex_shader: str = "", fragment_shader: str = "", *_, **__) -> Any:
        """Return a minimal shader program container."""
        return TaichiBackend._DummyProgram(vertex_shader, fragment_shader)

    def buffer(self, data: bytes) -> Any:
        """Return a minimal buffer container."""
        return TaichiBackend._DummyBuffer(data)

    def vertex_array(self, program: Any, buffers: Tuple[Any, ...] = tuple()) -> Any:
        """Return a minimal vertex array container."""
        return TaichiBackend._DummyVertexArray(program, buffers)

    def set_viewport(self, *args, **kwargs) -> None:  # pragma: no cover - stub
        return None

    def uniform(self, program: Any, name: str, value: Any) -> None:  # pragma: no cover - simple setter
        if isinstance(program, TaichiBackend._DummyProgram):
            program.uniforms[name] = value

    def create_framebuffer(self, *args, **kwargs) -> Any:  # pragma: no cover - stub
        raise NotImplementedError("Framebuffers are not supported in TaichiBackend")


# Legacy compatibility wrappers -------------------------------------------------

class GLBackend(TaichiBackend):
    """Alias of :class:`TaichiBackend` for legacy OpenGL code."""

    def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - simple wrapper
        super().__init__()


class ModernGLBackend(GLBackend):
    """Alias of :class:`TaichiBackend` representing a ModernGL backend."""

    def __init__(self, device_index: int = 0, share_context: Any = None, *args, **kwargs) -> None:  # pragma: no cover - simple wrapper
        super().__init__(*args, **kwargs)
        self.device_index = device_index
        self.share_context = share_context


# ----------------------------------------------------------------------
# Backend factory helpers
# ----------------------------------------------------------------------
def create_backend(backend_type: str = "taichi", device_index: int = 0) -> RenderBackend:
    """Factory function returning a Taichi backend regardless of type."""
    return TaichiBackend()


def get_available_backends() -> list[str]:
    """Return the list of available backends."""
    return ["taichi"]


def test_backend(backend_type: str, device_index: int = 0) -> bool:
    """Simple health check for the Taichi backend."""
    try:
        backend = create_backend(backend_type, device_index)
        backend.ensure_context()
        backend.begin_frame((32, 32))
        backend.clear(0.0, 0.0, 0.0, 1.0)
        img = backend.end_frame()
        return isinstance(img, np.ndarray)
    except Exception:
        return False

