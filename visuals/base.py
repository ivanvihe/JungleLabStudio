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
        GL_RED,
        GL_TEXTURE_2D,
        GL_UNPACK_ALIGNMENT,
        GL_TEXTURE_MIN_FILTER,
        GL_TEXTURE_MAG_FILTER,
        GL_LINEAR,
        GL_TRIANGLE_STRIP,
        glDrawPixels,
        glPixelStorei,
        glGenTextures,
        glBindTexture,
        glTexImage2D,
        glTexParameteri,
        glBegin,
        glEnd,
        glTexCoord2f,
        glVertex2f,
        glEnable,
        glDisable,
    )
except Exception:  # pragma: no cover - gracefully handle missing OpenGL
    GL_FLOAT = GL_LUMINANCE = GL_RED = GL_TEXTURE_2D = GL_UNPACK_ALIGNMENT = 0
    GL_TEXTURE_MIN_FILTER = GL_TEXTURE_MAG_FILTER = GL_LINEAR = GL_TRIANGLE_STRIP = 0

    def glDrawPixels(*_args, **_kwargs):
        return None

    def glPixelStorei(*_args, **_kwargs):
        return None

    def glGenTextures(*_args, **_kwargs):
        return 0

    def glBindTexture(*_args, **_kwargs):
        return None

    def glTexImage2D(*_args, **_kwargs):
        return None

    def glTexParameteri(*_args, **_kwargs):
        return None

    def glBegin(*_args, **_kwargs):
        return None

    def glEnd(*_args, **_kwargs):
        return None

    def glTexCoord2f(*_args, **_kwargs):
        return None

    def glVertex2f(*_args, **_kwargs):
        return None

    def glEnable(*_args, **_kwargs):
        return None

    def glDisable(*_args, **_kwargs):
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
        # Texture handle used when ``glDrawPixels`` is unavailable.  Created
        # lazily to avoid requiring an active GL context during construction.
        self._texture_id: int | None = None

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
        """Render the Taichi frame and upload it to the current target."""
        img = self.render()
        # ``TaichiRenderer`` returns an array shaped (width, height)
        h = img.shape[1]
        w = img.shape[0]
        data = np.ascontiguousarray(img.T)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        try:  # First try the simple legacy path.
            glDrawPixels(w, h, GL_LUMINANCE, GL_FLOAT, data)
            return
        except Exception:
            # ``glDrawPixels`` is not supported in modern core contexts.  Fall
            # back to uploading the image to a temporary texture and drawing a
            # screen-aligned quad.  This keeps Taichi visuals working on
            # systems where deprecated functionality has been removed.
            pass

        if self._texture_id is None:
            self._texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self._texture_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        else:
            glBindTexture(GL_TEXTURE_2D, self._texture_id)

        # Upload the grayscale buffer as a single channel texture.
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RED, w, h, 0, GL_RED, GL_FLOAT, data
        )

        glEnable(GL_TEXTURE_2D)
        glBegin(GL_TRIANGLE_STRIP)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(-1.0, -1.0)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(1.0, -1.0)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(-1.0, 1.0)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(1.0, 1.0)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, 0)

    # ------------------------------------------------------------------
    # Rendering ---------------------------------------------------------
    # ------------------------------------------------------------------
    def render(self) -> np.ndarray:
        """Execute registered passes and return the canvas as ``numpy``."""
        return self.renderer.render()

