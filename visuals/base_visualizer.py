import logging
from typing import Optional

import numpy as np
from OpenGL.GL import glGetError, GL_NO_ERROR
from OpenGL.GLU import gluErrorString


class BaseVisualizer:
    visual_name = "Base Visualizer"

    def __init__(self, *args, **kwargs):
        # Accept any arguments to prevent constructor errors
        # Pure Python class, presets may extend this.
        self.analyzer: Optional[object] = None
        self.audio_level: float = 0.0
        self.audio_fft: np.ndarray = np.array([])
        self.audio_reactive: bool = True

    def _check_gl_error(self, context: str = ""):
        """Checks for OpenGL errors and logs them."""
        error = glGetError()
        if error != GL_NO_ERROR:
            error_str = f"OpenGL Error ({error}) in {context}: {gluErrorString(error).decode()}"
            logging.error(error_str)
            return True
        return False

    def initializeGL(self, backend=None):
        """Initialize OpenGL state.

        If *backend* is provided, use the RenderBackend API. Otherwise legacy
        gl* calls are expected for backwards compatibility."""
        pass

    def resizeGL(self, width: int, height: int, backend=None):
        """Handle resize events."""
        pass

    def paintGL(self, time: float = 0.0, size: tuple[int, int] | None = None, backend=None):
        """Main rendering function."""
        pass

    def cleanup(self):
        """Clean up OpenGL resources."""
        self.set_audio_analyzer(None)

    def get_controls(self):
        """Return dictionary of available controls for this visualizer"""
        return {
            "Audio Reactive": {
                "type": "checkbox",
                "value": self.audio_reactive,
            }
        }

    def update_control(self, name, value):
        """Update a control parameter"""
        if name == "Audio Reactive":
            self.audio_reactive = bool(value)
            return True
        return False

    # ------------------------------------------------------------------
    # Audio handling
    # ------------------------------------------------------------------
    def set_audio_analyzer(self, analyzer: Optional[object]):
        """Attach an audio analyzer to this visualizer.

        The analyzer is expected to expose ``fft_data_ready`` and
        ``level_changed`` Qt signals as provided by ``AudioAnalyzer``.
        """
        if self.analyzer is analyzer:
            return

        # Disconnect from previous analyzer
        if self.analyzer:
            try:
                if hasattr(self.analyzer, "fft_data_ready"):
                    self.analyzer.fft_data_ready.disconnect(self._on_fft_data)
                if hasattr(self.analyzer, "level_changed"):
                    self.analyzer.level_changed.disconnect(self._on_level_changed)
            except Exception:
                pass

        self.analyzer = analyzer

        if analyzer:
            if hasattr(analyzer, "fft_data_ready"):
                analyzer.fft_data_ready.connect(self._on_fft_data)
            if hasattr(analyzer, "level_changed"):
                analyzer.level_changed.connect(self._on_level_changed)

    def _on_fft_data(self, fft: np.ndarray):
        """Store latest FFT data from audio analyzer."""
        self.audio_fft = np.array(fft, copy=True)

    def _on_level_changed(self, level: float):
        """Store latest overall audio level."""
        self.audio_level = float(level)

    def get_frequency_bands(self, bands: int = 3) -> np.ndarray:
        """Return smoothed frequency band values (0-100 range)."""
        if self.analyzer and hasattr(self.analyzer, "get_frequency_bands"):
            try:
                return self.analyzer.get_frequency_bands(bands)
            except Exception:
                return np.zeros(bands)
        return np.zeros(bands)

    def get_audio_bands(self, bands: int = 3) -> np.ndarray:
        """Return normalized frequency bands (0-1) when audio reactivity is enabled."""
        if not self.audio_reactive:
            return np.zeros(bands)
        return self.get_frequency_bands(bands) / 100.0
