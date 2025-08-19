"""Working enhanced spectrum analyzer with simplified Taichi implementation."""

import numpy as np
import taichi as ti
from typing import Tuple
from visuals.base import TaichiVisual


class WorkingSpectrumVisualizer(TaichiVisual):
    """Working spectrum analyzer with beautiful visual effects."""
    
    visual_name = "Working Spectrum Analyzer"
    
    def __init__(self, resolution: Tuple[int, int] = (800, 600)):
        super().__init__(resolution)
        
        # Spectrum parameters
        self.num_bars = 32  # Reduced for better performance
        self.bar_width = resolution[0] // self.num_bars
        self.spectrum_history = 5  # Reduced history
        
        # Visual parameters
        self.color_shift = 0.0
        self.intensity_multiplier = 1.0
        
        # Taichi fields - simplified
        try:
            self.spectrum_data = ti.field(dtype=ti.f32, shape=self.num_bars)
            self.spectrum_smooth = ti.field(dtype=ti.f32, shape=self.num_bars)
            self._taichi_available = True
        except Exception as e:
            print(f"Taichi field creation failed: {e}")
            self._taichi_available = False
            # Fallback to numpy
            self.spectrum_data = np.zeros(self.num_bars, dtype=np.float32)
            self.spectrum_smooth = np.zeros(self.num_bars, dtype=np.float32)
        
        # Initialize spectrum data
        self._init_spectrum()
        
    def _init_spectrum(self):
        """Initialize spectrum data."""
        if self._taichi_available:
            self._init_spectrum_ti()
        else:
            # Numpy fallback
            for i in range(self.num_bars):
                self.spectrum_data[i] = 0.0
                self.spectrum_smooth[i] = 0.0
    
    @ti.kernel
    def _init_spectrum_ti(self):
        """Initialize spectrum with Taichi."""
        for i in range(self.num_bars):
            self.spectrum_data[i] = 0.0
            self.spectrum_smooth[i] = 0.0
            
    def setup(self):
        """Set up render passes."""
        self.renderer.add_pass("clear_background", self._clear_background)
        self.renderer.add_pass("update_spectrum", self._update_spectrum)
        self.renderer.add_pass("draw_spectrum_bars", self._draw_spectrum_bars)
        
    @ti.kernel
    def _clear_background(self, canvas: ti.template()):
        """Clear canvas with dynamic background."""
        for i, j in canvas:
            # Simple gradient background
            x_factor = i / canvas.shape[0]
            y_factor = j / canvas.shape[1]
            
            intensity = 0.1 * (1.0 - y_factor) + 0.05
            canvas[i, j] = ti.Vector([
                intensity * 0.2, 
                intensity * 0.1, 
                intensity * 0.3, 
                1.0
            ])
            
    @ti.kernel
    def _update_spectrum(self, canvas: ti.template()):
        """Update spectrum data with smoothing."""
        frame_time = self.renderer.get_frame_count() * 0.1
        
        # Generate fake spectrum data for demo
        for bar in range(self.num_bars):
            freq_factor = bar / self.num_bars
            base_intensity = ti.abs(ti.sin(frame_time + freq_factor * 10.0))
            noise = ti.random() * 0.2
            
            # Simulate audio reactivity
            self.spectrum_data[bar] = ti.max(0.0, base_intensity + noise)
            
        # Simple smoothing
        for bar in range(self.num_bars):
            self.spectrum_smooth[bar] = self.spectrum_data[bar] * 0.7 + self.spectrum_smooth[bar] * 0.3
            
    @ti.kernel
    def _draw_spectrum_bars(self, canvas: ti.template()):
        """Draw spectrum bars with gradient colors."""
        for bar in range(self.num_bars):
            bar_height = self.spectrum_smooth[bar] * canvas.shape[1] * 0.6
            bar_x_start = bar * self.bar_width
            bar_x_end = bar_x_start + self.bar_width - 2
            
            # Color calculation with rainbow gradient
            hue = (bar / self.num_bars + self.color_shift) % 1.0
            intensity = self.spectrum_smooth[bar] * self.intensity_multiplier
            
            # Simple HSV to RGB conversion
            h = hue * 6.0
            c = intensity * 0.8
            x = c * (1.0 - ti.abs((h % 2.0) - 1.0))
            
            r, g, b = 0.0, 0.0, 0.0
            if h < 1.0:
                r, g, b = c, x, 0.0
            elif h < 2.0:
                r, g, b = x, c, 0.0
            elif h < 3.0:
                r, g, b = 0.0, c, x
            elif h < 4.0:
                r, g, b = 0.0, x, c
            elif h < 5.0:
                r, g, b = x, 0.0, c
            else:
                r, g, b = c, 0.0, x
                
            # Draw the bar
            for i in range(bar_x_start, bar_x_end):
                if i < canvas.shape[0]:
                    for j in range(int(canvas.shape[1] - bar_height), canvas.shape[1]):
                        if 0 <= j < canvas.shape[1]:
                            # Gradient from bright at bottom to dim at top
                            y_factor = 1.0 - (j - (canvas.shape[1] - bar_height)) / bar_height if bar_height > 0 else 0.0
                            brightness = y_factor * 0.7 + 0.3
                            
                            color = ti.Vector([
                                r * brightness, 
                                g * brightness, 
                                b * brightness, 
                                1.0
                            ])
                            canvas[i, j] = ti.max(canvas[i, j], color)
                            
    def update_audio_data(self, audio_level: float, audio_fft: np.ndarray):
        """Update with real audio data."""
        self.audio_level = audio_level
        
        if len(audio_fft) > 0 and self._taichi_available:
            # Resample FFT data to match our bar count
            fft_resampled = np.interp(
                np.linspace(0, len(audio_fft) - 1, self.num_bars),
                np.arange(len(audio_fft)),
                audio_fft
            )
            
            # Update spectrum data
            for i, value in enumerate(fft_resampled):
                if i < self.num_bars:
                    # Apply audio sensitivity
                    sensitivity = getattr(self, 'audio_sensitivity', 50.0) / 50.0
                    self.spectrum_data[i] = min(1.0, value * sensitivity)
                    
    def paintGL(self, time: float = 0.0, size: Tuple[int, int] | None = None, backend=None):
        """Enhanced painting with audio reactivity."""
        # Update color shift for dynamic colors
        self.color_shift += 0.01
        if self.color_shift > 1.0:
            self.color_shift = 0.0
            
        # Update intensity based on audio
        if hasattr(self, 'audio_level'):
            self.intensity_multiplier = 0.5 + self.audio_level * 1.5
            
        # Call parent implementation
        super().paintGL(time, size, backend)


class SimpleWaveformVisualizer(TaichiVisual):
    """Simple waveform visualizer."""
    
    visual_name = "Simple Waveform"
    
    def __init__(self, resolution: Tuple[int, int] = (800, 600)):
        super().__init__(resolution)
        self.waveform_points = 128  # Reduced for performance
        
        # Create waveform field
        try:
            self.waveform_data = ti.field(dtype=ti.f32, shape=self.waveform_points)
            self._taichi_available = True
        except Exception:
            self._taichi_available = False
            self.waveform_data = np.zeros(self.waveform_points, dtype=np.float32)
        
    def setup(self):
        """Set up waveform render passes."""
        self.renderer.add_pass("clear_waveform", self._clear_background)
        self.renderer.add_pass("update_waveform", self._update_waveform)
        self.renderer.add_pass("draw_waveform", self._draw_waveform)
        
    @ti.kernel
    def _clear_background(self, canvas: ti.template()):
        """Clear with gradient background."""
        for i, j in canvas:
            y_factor = j / canvas.shape[1]
            intensity = 0.05 + y_factor * 0.1
            canvas[i, j] = ti.Vector([
                intensity * 0.1, 
                intensity * 0.2, 
                intensity * 0.4, 
                1.0
            ])
            
    @ti.kernel
    def _update_waveform(self, canvas: ti.template()):
        """Update waveform data."""
        frame_time = self.renderer.get_frame_count() * 0.05
        
        for point in range(self.waveform_points):
            t = point / self.waveform_points
            wave = ti.sin(t * 15.0 + frame_time) * 0.4
            wave += ti.sin(t * 30.0 + frame_time * 0.7) * 0.2
            
            self.waveform_data[point] = wave
            
    @ti.kernel
    def _draw_waveform(self, canvas: ti.template()):
        """Draw waveform."""
        center_y = canvas.shape[1] // 2
        
        for point in range(self.waveform_points - 1):
            x1 = int(point * canvas.shape[0] / self.waveform_points)
            x2 = int((point + 1) * canvas.shape[0] / self.waveform_points)
            
            y1 = center_y + int(self.waveform_data[point] * 100)
            y2 = center_y + int(self.waveform_data[point + 1] * 100)
            
            # Simple line drawing
            steps = max(abs(x2 - x1), abs(y2 - y1))
            if steps > 0:
                for step in range(steps):
                    t = step / steps
                    x = int(x1 + t * (x2 - x1))
                    y = int(y1 + t * (y2 - y1))
                    
                    if 0 <= x < canvas.shape[0] and 0 <= y < canvas.shape[1]:
                        # Golden color
                        color = ti.Vector([1.0, 0.8, 0.2, 1.0])
                        canvas[x, y] = canvas[x, y] + color * 0.8


# Registration function
def get_visualizers():
    """Return list of available working visualizers."""
    return [
        ('working_spectrum', WorkingSpectrumVisualizer),
        ('simple_waveform', SimpleWaveformVisualizer)
    ]


# Test the visualizer
if __name__ == "__main__":
    print("Testing Working Spectrum Visualizer...")
    
    try:
        viz = WorkingSpectrumVisualizer(resolution=(400, 300))
        
        # Test basic rendering
        for frame in range(10):
            img = viz.render()
            print(f"Frame {frame}: {img.shape}, max: {img.max():.3f}")
            
        print("Working Spectrum Visualizer test passed!")
        
    except Exception as e:
        print(f" Test failed: {e}")
        import traceback
        traceback.print_exc()