"""Simplified rendering backend using Taichi.

This module replaces the previous OpenGL/ModernGL based implementation with a
minimal Taichi powered backend.  The goal is to provide a lightweight and
Pythonic API that existing visualizers can gradually migrate to.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List, Tuple

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

    # Compatibility stubs ------------------------------------------------
    def program(self, *args, **kwargs) -> Any:  # pragma: no cover - stub
        raise NotImplementedError("Shader programs are not supported in TaichiBackend")

    def buffer(self, *args, **kwargs) -> Any:  # pragma: no cover - stub
        raise NotImplementedError("Buffer objects are not supported in TaichiBackend")

    def vertex_array(self, *args, **kwargs) -> Any:  # pragma: no cover - stub
        raise NotImplementedError("Vertex arrays are not supported in TaichiBackend")

    def set_viewport(self, *args, **kwargs) -> None:  # pragma: no cover - stub
        return None

    def uniform(self, *args, **kwargs) -> None:  # pragma: no cover - stub
        return None

    def create_framebuffer(self, *args, **kwargs) -> Any:  # pragma: no cover - stub
        raise NotImplementedError("Framebuffers are not supported in TaichiBackend")


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

