"""Common Taichi visual base class integrated with the OpenGL pipeline."""

from __future__ import annotations

from typing import Tuple

import numpy as np

# ``PyOpenGL`` is an optional dependency.  Importing it eagerly makes any
# module that pulls in :mod:`visuals.base` require a working OpenGL runtime
# which is not available in the headless test environment.  Instead we try to
# import the symbols lazily and fall back to no-op stubs when OpenGL cannot be
# loaded.  This allows the render logic to be exercised without an actual GL
# context (the tests only invoke :meth:`render` and never :meth:`paintGL`).
try:  # pragma: no cover - exercised indirectly in tests
    from OpenGL.GL import (
        GL_FLOAT,
        GL_LUMINANCE,
        GL_UNPACK_ALIGNMENT,
        glDrawPixels,
        glPixelStorei,
    )
except Exception:  # pragma: no cover - gracefully handle missing OpenGL
    GL_FLOAT = GL_LUMINANCE = GL_UNPACK_ALIGNMENT = 0

    def glDrawPixels(*_args, **_kwargs):
        return None

    def glPixelStorei(*_args, **_kwargs):
        return None

from render.taichi_renderer import TaichiRenderer
from .base_visualizer import BaseVisualizer


class TaichiVisual(BaseVisualizer):
    """Base class for Taichi-powered visuals.

    The original project used OpenGL based visualizers.  For the Taichi
    presets to be usable inside the existing application the base class now
    subclasses :class:`BaseVisualizer` and implements the ``initializeGL``,
    ``resizeGL`` and ``paintGL`` methods expected by the UI.  Each render
    call produces a grayscale image which is uploaded using ``glDrawPixels``.
    """

    def __init__(self, resolution: Tuple[int, int] = (640, 480)):
        super().__init__()
        self.resolution = resolution
        self.renderer = TaichiRenderer(resolution)
        self.setup()

    # ------------------------------------------------------------------
    # Life-cycle hooks --------------------------------------------------
    # ------------------------------------------------------------------
    def setup(self) -> None:  # pragma: no cover - meant to be overridden
        """Hook for subclasses to register Taichi render passes."""
        return None

    def initializeGL(self, backend=None):  # pragma: no cover - no GL state
        """No OpenGL resources are required for Taichi visuals."""
        return None

    def resizeGL(self, width: int, height: int, backend=None):
        """Recreate the Taichi renderer on resize."""
        if (width, height) != self.resolution:
            self.resolution = (width, height)
            # Recreate renderer to resize canvas
            self.renderer = TaichiRenderer(self.resolution)
            self.setup()

    def paintGL(self, time: float = 0.0, size: Tuple[int, int] | None = None, backend=None):
        """Render the Taichi frame and blit it using OpenGL."""
        img = self.render()
        # ``TaichiRenderer`` returns an array shaped (width, height)
        h = img.shape[1]
        w = img.shape[0]
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        # Transpose so rows correspond to the Y axis for OpenGL
        glDrawPixels(w, h, GL_LUMINANCE, GL_FLOAT, np.ascontiguousarray(img.T))

    # ------------------------------------------------------------------
    # Rendering ---------------------------------------------------------
    # ------------------------------------------------------------------
    def render(self) -> np.ndarray:
        """Execute registered passes and return the canvas as ``numpy``."""
        return self.renderer.render()

