import logging
from typing import Optional

import numpy as np


class BaseVisualizer:
    visual_name = "Base Visualizer"

    def __init__(self, *args, **kwargs):
        # Accept any arguments to prevent constructor errors
        # Pure Python class, presets may extend this.
        self.analyzer: Optional[object] = None
        self.audio_level: float = 0.0
        self.audio_fft: np.ndarray = np.array([])
        self.audio_reactive: bool = True
        # Generic audio sensitivity factor (0-100)
        self.audio_sensitivity: float = 50.0
        # How smoothly audio values change (0-100, higher = smoother)
        self.audio_smoothness: float = 50.0
        self._smoothed_bands: np.ndarray | None = None

    def _check_gl_error(self, context: str = ""):
        """Placeholder for legacy OpenGL error checks."""
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
                "description": "Enable or disable audio-driven effects",
            },
            "Audio Sensitivity": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.audio_sensitivity),
                "description": "Adjust how strongly the visual reacts to audio",
            },
            "Smoothness": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.audio_smoothness),
                "description": "Higher values smooth out rapid audio changes",
            },
        }

    def update_control(self, name, value):
        """Update a control parameter"""
        if name == "Audio Reactive":
            self.audio_reactive = bool(value)
            return True
        elif name == "Audio Sensitivity":
            try:
                self.audio_sensitivity = float(value)
            except Exception:
                self.audio_sensitivity = 50.0
            return True
        elif name == "Smoothness":
            try:
                self.audio_smoothness = float(value)
            except Exception:
                self.audio_smoothness = 50.0
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
        bands_vals = self.get_frequency_bands(bands) / 100.0
        sensitivity = max(self.audio_sensitivity, 0.0) / 50.0
        raw = np.clip(bands_vals * sensitivity, 0.0, 1.0)
        smooth_factor = np.clip(self.audio_smoothness, 0.0, 100.0) / 100.0
        if self._smoothed_bands is None or len(self._smoothed_bands) != bands:
            self._smoothed_bands = raw
        else:
            self._smoothed_bands = (
                self._smoothed_bands * smooth_factor + raw * (1.0 - smooth_factor)
            )
        return self._smoothed_bands
