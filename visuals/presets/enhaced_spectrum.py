"""Enhanced spectrum analyzer with modern visual effects and audio reactivity."""

import numpy as np
import taichi as ti
from typing import Tuple
from visuals.base import TaichiVisual


@ti.data_oriented
class EnhancedSpectrumVisualizer(TaichiVisual):
    """Enhanced spectrum analyzer with beautiful visual effects.
    
    Features:
    - Smooth spectrum bars with gradient colors
    - Particle effects that react to audio
    - Background waves and ripples
    - Dynamic color palettes
    - Audio-reactive intensity and movement
    """
    
    visual_name = "Enhanced Spectrum Analyzer"
    
    def __init__(self, resolution: Tuple[int, int] = (800, 600)):
        super().__init__(resolution)
        
        # Spectrum parameters
        self.num_bars = 64
        self.bar_width = resolution[0] // self.num_bars
        self.spectrum_history = 10
        
        # Visual parameters
        self.color_shift = 0.0
        self.intensity_multiplier = 1.0
        self.background_alpha = 0.1
        
        # Taichi fields
        self.spectrum_data = ti.field(dtype=ti.f32, shape=(self.num_bars, self.spectrum_history))
        self.spectrum_smooth = ti.field(dtype=ti.f32, shape=self.num_bars)
        self.particles = ti.Vector.field(4, dtype=ti.f32, shape=1000)  # x, y, vx, vy
        self.particle_colors = ti.Vector.field(3, dtype=ti.f32, shape=1000)
        self.background_field = ti.Vector.field(3, dtype=ti.f32, shape=resolution)
        
        # Initialize particles
        self._init_particles()
        
    @ti.kernel
    def _init_particles(self):
        """Initialize particle system."""
        for i in range(1000):
            self.particles[i] = ti.Vector([
                ti.random() * self.resolution[0],  # x
                ti.random() * self.resolution[1],  # y
                (ti.random() - 0.5) * 2.0,         # vx
                (ti.random() - 0.5) * 2.0          # vy
            ])
            
    def setup(self):
        """Set up render passes."""
        self.renderer.add_pass("clear_background", self._clear_background)
        self.renderer.add_pass("draw_background_waves", self._draw_background_waves)
        self.renderer.add_pass("update_spectrum", self._update_spectrum)
        self.renderer.add_pass("draw_spectrum_bars", self._draw_spectrum_bars)
        self.renderer.add_pass("update_particles", self._update_particles)
        self.renderer.add_pass("draw_particles", self._draw_particles)
        self.renderer.add_pass("add_glow_effect", self._add_glow_effect)
        
    @ti.kernel
    def _clear_background(self, canvas: ti.template()):
        """Clear canvas with dynamic background."""
        for i, j in canvas:
            # Dynamic background color based on audio and time
            time_factor = ti.sin(self._frame_count * 0.01) * 0.1
            audio_factor = 0.0
            if hasattr(self, 'audio_level'):
                audio_factor = self.audio_level * 0.3
            
            bg_intensity = 0.05 + time_factor + audio_factor
            canvas[i, j] = ti.Vector([bg_intensity * 0.2, bg_intensity * 0.1, bg_intensity * 0.3, 1.0])
            
    @ti.kernel
    def _draw_background_waves(self, canvas: ti.template()):
        """Draw animated background waves."""
        for i, j in canvas:
            x = i / self.resolution[0]
            y = j / self.resolution[1]
            time = self._frame_count * 0.02
            
            # Create wave patterns
            wave1 = ti.sin(x * 10.0 + time) * ti.sin(y * 8.0 + time * 0.7)
            wave2 = ti.sin(x * 6.0 - time * 1.5) * ti.sin(y * 12.0 + time)
            wave_intensity = (wave1 + wave2) * 0.02
            
            # Add to background
            current = canvas[i, j]
            wave_color = ti.Vector([
                wave_intensity * 0.3,
                wave_intensity * 0.5,
                wave_intensity * 0.8,
                0.0
            ])
            canvas[i, j] = current + wave_color
            
    @ti.kernel
    def _update_spectrum(self, canvas: ti.template()):
        """Update spectrum data with smoothing."""
        # Shift history
        for bar in range(self.num_bars):
            for hist in range(self.spectrum_history - 1, 0, -1):
                self.spectrum_data[bar, hist] = self.spectrum_data[bar, hist - 1]
                
        # Add new data (would come from audio analyzer)
        for bar in range(self.num_bars):
            # Simulate spectrum data for now
            freq_factor = bar / self.num_bars
            base_intensity = ti.sin(self._frame_count * 0.1 + freq_factor * 20.0)
            noise = ti.random() * 0.3
            audio_reactive = 1.0
            if hasattr(self, 'audio_level'):
                audio_reactive = 0.3 + self.audio_level * 0.7
                
            self.spectrum_data[bar, 0] = ti.max(0.0, base_intensity + noise) * audio_reactive
            
        # Smooth the spectrum data
        for bar in range(self.num_bars):
            total = 0.0
            for hist in range(self.spectrum_history):
                weight = 1.0 - (hist / self.spectrum_history) * 0.7
                total += self.spectrum_data[bar, hist] * weight
            self.spectrum_smooth[bar] = total / self.spectrum_history
            
    @ti.kernel
    def _draw_spectrum_bars(self, canvas: ti.template()):
        """Draw spectrum bars with gradient colors and effects."""
        for bar in range(self.num_bars):
            bar_height = self.spectrum_smooth[bar] * self.resolution[1] * 0.7
            bar_x_start = bar * self.bar_width
            bar_x_end = bar_x_start + self.bar_width - 2
            
            # Color calculation with rainbow gradient
            hue = (bar / self.num_bars + self.color_shift) % 1.0
            intensity = self.spectrum_smooth[bar] * self.intensity_multiplier
            
            # HSV to RGB conversion
            h = hue * 6.0
            c = intensity
            x = c * (1.0 - ti.abs((h % 2.0) - 1.0))
            
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
                if i < self.resolution[0]:
                    for j in range(int(self.resolution[1] - bar_height), self.resolution[1]):
                        if 0 <= j < self.resolution[1]:
                            # Gradient from bright at bottom to dim at top
                            y_factor = (self.resolution[1] - j) / bar_height if bar_height > 0 else 0.0
                            brightness = y_factor * 0.8 + 0.2
                            
                            color = ti.Vector([r * brightness, g * brightness, b * brightness, 1.0])
                            canvas[i, j] = ti.max(canvas[i, j], color)
                            
    @ti.kernel
    def _update_particles(self, canvas: ti.template()):
        """Update particle physics with audio reactivity."""
        audio_force = 1.0
        if hasattr(self, 'audio_level'):
            audio_force = 0.5 + self.audio_level * 1.5
            
        for i in range(1000):
            # Get current particle state
            pos_x = self.particles[i][0]
            pos_y = self.particles[i][1]
            vel_x = self.particles[i][2]
            vel_y = self.particles[i][3]
            
            # Apply forces based on spectrum
            nearest_bar = int((pos_x / self.resolution[0]) * self.num_bars)
            if 0 <= nearest_bar < self.num_bars:
                spectrum_force = self.spectrum_smooth[nearest_bar] * audio_force
                vel_y -= spectrum_force * 5.0  # Upward force
                
            # Apply gravity and damping
            vel_y += 0.1  # Gravity
            vel_x *= 0.99  # Damping
            vel_y *= 0.99
            
            # Update position
            pos_x += vel_x
            pos_y += vel_y
            
            # Boundary conditions
            if pos_x < 0.0 or pos_x >= self.resolution[0]:
                vel_x = -vel_x * 0.8
                pos_x = ti.max(0.0, ti.min(float(self.resolution[0] - 1), pos_x))
                
            if pos_y < 0.0:
                vel_y = -vel_y * 0.8
                pos_y = 0.0
            elif pos_y >= self.resolution[1]:
                # Reset particle at top when it hits bottom
                pos_x = ti.random() * self.resolution[0]
                pos_y = 0.0
                vel_x = (ti.random() - 0.5) * 4.0
                vel_y = ti.random() * -2.0
                
            # Update particle
            self.particles[i] = ti.Vector([pos_x, pos_y, vel_x, vel_y])
            
            # Update particle color based on position and spectrum
            bar_index = int((pos_x / self.resolution[0]) * self.num_bars)
            if 0 <= bar_index < self.num_bars:
                spectrum_val = self.spectrum_smooth[bar_index]
                hue = (bar_index / self.num_bars + self.color_shift) % 1.0
                
                # HSV to RGB for particle color
                h = hue * 6.0
                s = 0.8
                v = spectrum_val * 0.8 + 0.2
                
                c = v * s
                x = c * (1.0 - ti.abs((h % 2.0) - 1.0))
                
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
                    
                self.particle_colors[i] = ti.Vector([r, g, b])
                
    @ti.kernel
    def _draw_particles(self, canvas: ti.template()):
        """Draw particles with bloom effect."""
        for i in range(1000):
            x = int(self.particles[i][0])
            y = int(self.particles[i][1])
            
            if 0 <= x < self.resolution[0] and 0 <= y < self.resolution[1]:
                color = self.particle_colors[i]
                
                # Draw particle with small bloom
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        px = x + dx
                        py = y + dy
                        if 0 <= px < self.resolution[0] and 0 <= py < self.resolution[1]:
                            distance = ti.sqrt(dx * dx + dy * dy)
                            alpha = ti.max(0.0, 1.0 - distance * 0.5)
                            
                            particle_color = ti.Vector([
                                color[0] * alpha,
                                color[1] * alpha, 
                                color[2] * alpha,
                                alpha * 0.5
                            ])
                            
                            current = canvas[px, py]
                            canvas[px, py] = current + particle_color
                            
    @ti.kernel
    def _add_glow_effect(self, canvas: ti.template()):
        """Add subtle glow effect to bright areas."""
        # Simple box blur for glow
        for i, j in canvas:
            if canvas[i, j][0] > 0.5 or canvas[i, j][1] > 0.5 or canvas[i, j][2] > 0.5:
                # Add glow around bright pixels
                for di in range(-2, 3):
                    for dj in range(-2, 3):
                        ni, nj = i + di, j + dj
                        if 0 <= ni < self.resolution[0] and 0 <= nj < self.resolution[1]:
                            distance = ti.sqrt(di * di + dj * dj)
                            if distance > 0:
                                glow_strength = 0.1 / distance
                                glow_color = canvas[i, j] * glow_strength
                                canvas[ni, nj] = canvas[ni, nj] + glow_color * 0.3
                                
    def update_audio_data(self, audio_level: float, audio_fft: np.ndarray):
        """Update with real audio data."""
        self.audio_level = audio_level
        
        if len(audio_fft) > 0:
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
                    self.spectrum_data[i, 0] = min(1.0, value * sensitivity)
                    
    def update_visual_effects(self, effects: dict):
        """Update visual effect parameters."""
        if 'intensity' in effects:
            self.intensity_multiplier = effects['intensity']
            
        if 'color_shift' in effects:
            # Auto color shift based on time if not manually set
            self.color_shift += 0.005
            if self.color_shift > 1.0:
                self.color_shift = 0.0
                
        # Update visual effects in parent class
        if hasattr(super(), 'set_visual_effect'):
            for effect, value in effects.items():
                super().set_visual_effect(effect, value)
                
    def paintGL(self, time: float = 0.0, size: Tuple[int, int] | None = None, backend=None):
        """Enhanced painting with audio reactivity."""
        # Update color shift for dynamic colors
        self.color_shift += 0.005
        if self.color_shift > 1.0:
            self.color_shift = 0.0
            
        # Update intensity based on audio
        if hasattr(self, 'audio_level'):
            self.intensity_multiplier = 0.5 + self.audio_level * 1.5
            
        # Call parent implementation
        super().paintGL(time, size, backend)
        

class EnhancedWaveformVisualizer(TaichiVisual):
    """Enhanced waveform visualizer with 3D-like effects."""
    
    visual_name = "Enhanced Waveform"
    
    def __init__(self, resolution: Tuple[int, int] = (800, 600)):
        super().__init__(resolution)
        
        # Waveform parameters
        self.waveform_points = 512
        self.waveform_history = 5
        
        # Taichi fields
        self.waveform_data = ti.field(dtype=ti.f32, shape=(self.waveform_points, self.waveform_history))
        self.waveform_smooth = ti.field(dtype=ti.f32, shape=self.waveform_points)
        
    def setup(self):
        """Set up waveform render passes."""
        self.renderer.add_pass("clear_waveform", self._clear_background)
        self.renderer.add_pass("update_waveform", self._update_waveform)
        self.renderer.add_pass("draw_waveform_3d", self._draw_waveform_3d)
        self.renderer.add_pass("draw_waveform_reflection", self._draw_reflection)
        
    @ti.kernel
    def _clear_background(self, canvas: ti.template()):
        """Clear with gradient background."""
        for i, j in canvas:
            y_factor = j / self.resolution[1]
            intensity = 0.05 + y_factor * 0.1
            canvas[i, j] = ti.Vector([intensity * 0.1, intensity * 0.2, intensity * 0.4, 1.0])
            
    @ti.kernel
    def _update_waveform(self, canvas: ti.template()):
        """Update waveform data."""
        # Shift history
        for point in range(self.waveform_points):
            for hist in range(self.waveform_history - 1, 0, -1):
                self.waveform_data[point, hist] = self.waveform_data[point, hist - 1]
                
        # Generate new waveform data (would come from audio)
        for point in range(self.waveform_points):
            t = point / self.waveform_points
            wave = ti.sin(t * 20.0 + self._frame_count * 0.1) * 0.3
            wave += ti.sin(t * 40.0 + self._frame_count * 0.05) * 0.2
            
            audio_reactive = 1.0
            if hasattr(self, 'audio_level'):
                audio_reactive = 0.2 + self.audio_level * 0.8
                
            self.waveform_data[point, 0] = wave * audio_reactive
            
        # Smooth the data
        for point in range(self.waveform_points):
            total = 0.0
            for hist in range(self.waveform_history):
                weight = 1.0 - hist * 0.2
                total += self.waveform_data[point, hist] * weight
            self.waveform_smooth[point] = total / self.waveform_history
            
    @ti.kernel
    def _draw_waveform_3d(self, canvas: ti.template()):
        """Draw 3D-style waveform with multiple layers."""
        center_y = self.resolution[1] // 2
        
        for layer in range(3):
            layer_offset = layer * 20
            layer_alpha = 1.0 - layer * 0.3
            
            for point in range(self.waveform_points - 1):
                x1 = int(point * self.resolution[0] / self.waveform_points)
                x2 = int((point + 1) * self.resolution[0] / self.waveform_points)
                
                y1 = center_y + int(self.waveform_smooth[point] * 100) - layer_offset
                y2 = center_y + int(self.waveform_smooth[point + 1] * 100) - layer_offset
                
                # Draw line between points
                self._draw_line(canvas, x1, y1, x2, y2, layer_alpha, layer)
                
    @ti.func
    def _draw_line(self, canvas: ti.template(), x1: int, y1: int, x2: int, y2: int, alpha: float, layer: int):
        """Draw anti-aliased line."""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        steps = max(dx, dy)
        
        if steps > 0:
            x_step = (x2 - x1) / steps
            y_step = (y2 - y1) / steps
            
            for i in range(steps):
                x = int(x1 + i * x_step)
                y = int(y1 + i * y_step)
                
                if 0 <= x < self.resolution[0] and 0 <= y < self.resolution[1]:
                    # Color based on layer
                    if layer == 0:
                        color = ti.Vector([1.0, 0.8, 0.2, alpha])  # Golden
                    elif layer == 1:
                        color = ti.Vector([0.8, 0.4, 1.0, alpha])  # Purple
                    else:
                        color = ti.Vector([0.2, 0.8, 1.0, alpha])  # Cyan
                        
                    current = canvas[x, y]
                    canvas[x, y] = current + color * 0.7
                    
    @ti.kernel
    def _draw_reflection(self, canvas: ti.template()):
        """Draw reflection effect."""
        center_y = self.resolution[1] // 2
        
        for i, j in canvas:
            if j > center_y:
                reflection_y = 2 * center_y - j
                if 0 <= reflection_y < self.resolution[1]:
                    reflection_alpha = 0.3 * (1.0 - (j - center_y) / center_y)
                    reflection_color = canvas[i, reflection_y] * reflection_alpha
                    canvas[i, j] = canvas[i, j] + reflection_color


class EnhancedParticleSystemVisualizer(TaichiVisual):
    """Enhanced particle system with advanced physics and visual effects."""
    
    visual_name = "Enhanced Particle System"
    
    def __init__(self, resolution: Tuple[int, int] = (800, 600)):
        super().__init__(resolution)
        
        # Particle system parameters
        self.num_particles = 2000
        self.num_emitters = 4
        
        # Taichi fields
        self.particles = ti.Vector.field(6, dtype=ti.f32, shape=self.num_particles)  # x, y, vx, vy, life, age
        self.particle_colors = ti.Vector.field(4, dtype=ti.f32, shape=self.num_particles)  # r, g, b, a
        self.emitters = ti.Vector.field(4, dtype=ti.f32, shape=self.num_emitters)  # x, y, strength, phase
        
        # Initialize system
        self._init_particle_system()
        
    @ti.kernel
    def _init_particle_system(self):
        """Initialize particle system."""
        # Initialize emitters
        for i in range(self.num_emitters):
            angle = (i / self.num_emitters) * 2.0 * 3.14159
            radius = min(self.resolution[0], self.resolution[1]) * 0.3
            center_x = self.resolution[0] * 0.5
            center_y = self.resolution[1] * 0.5
            
            self.emitters[i] = ti.Vector([
                center_x + ti.cos(angle) * radius,
                center_y + ti.sin(angle) * radius,
                1.0,  # strength
                i * 1.57  # phase offset
            ])
            
        # Initialize particles
        for i in range(self.num_particles):
            self.particles[i] = ti.Vector([
                ti.random() * self.resolution[0],  # x
                ti.random() * self.resolution[1],  # y
                0.0,  # vx
                0.0,  # vy
                0.0,  # life (0 = dead)
                0.0   # age
            ])
            
    def setup(self):
        """Set up particle system render passes."""
        self.renderer.add_pass("clear_particles", self._clear_background)
        self.renderer.add_pass("update_emitters", self._update_emitters)
        self.renderer.add_pass("update_particles", self._update_particles)
        self.renderer.add_pass("spawn_particles", self._spawn_particles)
        self.renderer.add_pass("draw_particles", self._draw_particles)
        self.renderer.add_pass("draw_emitters", self._draw_emitters)
        
    @ti.kernel
    def _clear_background(self, canvas: ti.template()):
        """Clear with fading effect."""
        for i, j in canvas:
            # Fade previous frame
            current = canvas[i, j]
            fade_factor = 0.95
            canvas[i, j] = current * fade_factor
            
    @ti.kernel
    def _update_emitters(self, canvas: ti.template()):
        """Update emitter positions and properties."""
        time = self._frame_count * 0.05
        
        for i in range(self.num_emitters):
            # Circular motion
            base_angle = (i / self.num_emitters) * 2.0 * 3.14159
            orbit_radius = min(self.resolution[0], self.resolution[1]) * 0.2
            center_x = self.resolution[0] * 0.5
            center_y = self.resolution[1] * 0.5
            
            angle = base_angle + time + self.emitters[i][3]
            
            self.emitters[i][0] = center_x + ti.cos(angle) * orbit_radius
            self.emitters[i][1] = center_y + ti.sin(angle) * orbit_radius
            
            # Audio reactive strength
            audio_strength = 1.0
            if hasattr(self, 'audio_level'):
                audio_strength = 0.5 + self.audio_level * 1.5
                
            self.emitters[i][2] = audio_strength
            
    @ti.kernel
    def _spawn_particles(self, canvas: ti.template()):
        """Spawn new particles from emitters."""
        spawn_rate = 5  # particles per frame per emitter
        
        for emitter_idx in range(self.num_emitters):
            emitter_x = self.emitters[emitter_idx][0]
            emitter_y = self.emitters[emitter_idx][1]
            strength = self.emitters[emitter_idx][2]
            
            for spawn in range(spawn_rate):
                # Find dead particle to reuse
                particle_idx = (emitter_idx * spawn_rate + spawn + self._frame_count * spawn_rate) % self.num_particles
                
                if self.particles[particle_idx][4] <= 0:  # if dead
                    # Spawn new particle
                    angle = ti.random() * 2.0 * 3.14159
                    speed = ti.random() * 3.0 + 1.0
                    life = ti.random() * 60.0 + 30.0  # 30-90 frames life
                    
                    self.particles[particle_idx] = ti.Vector([
                        emitter_x + (ti.random() - 0.5) * 10.0,  # x with small offset
                        emitter_y + (ti.random() - 0.5) * 10.0,  # y with small offset
                        ti.cos(angle) * speed * strength,        # vx
                        ti.sin(angle) * speed * strength,        # vy
                        life,                                     # life
                        0.0                                       # age
                    ])
                    
    @ti.kernel
    def _update_particles(self, canvas: ti.template()):
        """Update particle physics."""
        for i in range(self.num_particles):
            if self.particles[i][4] > 0:  # if alive
                # Get particle state
                x = self.particles[i][0]
                y = self.particles[i][1]
                vx = self.particles[i][2]
                vy = self.particles[i][3]
                life = self.particles[i][4]
                age = self.particles[i][5]
                
                # Apply forces
                # Gravity towards center
                center_x = self.resolution[0] * 0.5
                center_y = self.resolution[1] * 0.5
                dx = center_x - x
                dy = center_y - y
                dist = ti.sqrt(dx * dx + dy * dy)
                
                if dist > 0:
                    gravity_strength = 0.1
                    vx += (dx / dist) * gravity_strength
                    vy += (dy / dist) * gravity_strength
                
                # Damping
                vx *= 0.98
                vy *= 0.98
                
                # Update position
                x += vx
                y += vy
                
                # Boundary wrapping
                if x < 0:
                    x = self.resolution[0]
                elif x >= self.resolution[0]:
                    x = 0
                if y < 0:
                    y = self.resolution[1]
                elif y >= self.resolution[1]:
                    y = 0
                
                # Update age and check life
                age += 1.0
                if age >= life:
                    life = 0.0  # kill particle
                
                # Update particle
                self.particles[i] = ti.Vector([x, y, vx, vy, life, age])
                
                # Update color based on age and position
                life_factor = age / life if life > 0 else 0
                hue = (x / self.resolution[0] + self.color_shift) % 1.0
                
                # HSV to RGB
                h = hue * 6.0
                s = 0.8
                v = (1.0 - life_factor) * 0.8 + 0.2
                
                c = v * s
                x_color = c * (1.0 - ti.abs((h % 2.0) - 1.0))
                
                if h < 1.0:
                    r, g, b = c, x_color, 0.0
                elif h < 2.0:
                    r, g, b = x_color, c, 0.0
                elif h < 3.0:
                    r, g, b = 0.0, c, x_color
                elif h < 4.0:
                    r, g, b = 0.0, x_color, c
                elif h < 5.0:
                    r, g, b = x_color, 0.0, c
                else:
                    r, g, b = c, 0.0, x_color
                
                alpha = 1.0 - life_factor
                self.particle_colors[i] = ti.Vector([r, g, b, alpha])
                
    @ti.kernel
    def _draw_particles(self, canvas: ti.template()):
        """Draw particles with trails and glow."""
        for i in range(self.num_particles):
            if self.particles[i][4] > 0:  # if alive
                x = int(self.particles[i][0])
                y = int(self.particles[i][1])
                
                if 0 <= x < self.resolution[0] and 0 <= y < self.resolution[1]:
                    color = self.particle_colors[i]
                    
                    # Draw particle with glow
                    for dx in range(-2, 3):
                        for dy in range(-2, 3):
                            px = x + dx
                            py = y + dy
                            if 0 <= px < self.resolution[0] and 0 <= py < self.resolution[1]:
                                distance = ti.sqrt(dx * dx + dy * dy)
                                if distance <= 2.0:
                                    glow = ti.max(0.0, 1.0 - distance * 0.3)
                                    particle_color = ti.Vector([
                                        color[0] * glow,
                                        color[1] * glow,
                                        color[2] * glow,
                                        color[3] * glow * 0.7
                                    ])
                                    
                                    current = canvas[px, py]
                                    canvas[px, py] = current + particle_color
                                    
    @ti.kernel
    def _draw_emitters(self, canvas: ti.template()):
        """Draw emitter positions."""
        for i in range(self.num_emitters):
            x = int(self.emitters[i][0])
            y = int(self.emitters[i][1])
            strength = self.emitters[i][2]
            
            if 0 <= x < self.resolution[0] and 0 <= y < self.resolution[1]:
                # Draw emitter glow
                radius = int(strength * 15.0)
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        px = x + dx
                        py = y + dy
                        if 0 <= px < self.resolution[0] and 0 <= py < self.resolution[1]:
                            distance = ti.sqrt(dx * dx + dy * dy)
                            if distance <= radius:
                                glow = ti.max(0.0, 1.0 - distance / radius)
                                emitter_color = ti.Vector([
                                    1.0 * glow * strength,
                                    0.5 * glow * strength,
                                    0.2 * glow * strength,
                                    glow * 0.3
                                ])
                                
                                current = canvas[px, py]
                                canvas[px, py] = current + emitter_color


class EnhancedKaleidoscopeVisualizer(TaichiVisual):
    """Enhanced kaleidoscope visualizer with symmetrical patterns."""
    
    visual_name = "Enhanced Kaleidoscope"
    
    def __init__(self, resolution: Tuple[int, int] = (800, 600)):
        super().__init__(resolution)
        
        # Kaleidoscope parameters
        self.num_segments = 8
        self.center_x = resolution[0] // 2
        self.center_y = resolution[1] // 2
        self.max_radius = min(resolution[0], resolution[1]) // 2
        
        # Pattern fields
        self.pattern_field = ti.Vector.field(4, dtype=ti.f32, shape=resolution)
        self.source_field = ti.Vector.field(4, dtype=ti.f32, shape=(resolution[0] // 4, resolution[1] // 4))
        
    def setup(self):
        """Set up kaleidoscope render passes."""
        self.renderer.add_pass("clear_kaleidoscope", self._clear_background)
        self.renderer.add_pass("generate_source_pattern", self._generate_source_pattern)
        self.renderer.add_pass("apply_kaleidoscope", self._apply_kaleidoscope)
        self.renderer.add_pass("add_center_glow", self._add_center_glow)
        
    @ti.kernel
    def _clear_background(self, canvas: ti.template()):
        """Clear with radial gradient."""
        for i, j in canvas:
            dx = i - self.center_x
            dy = j - self.center_y
            distance = ti.sqrt(dx * dx + dy * dy)
            
            # Radial gradient
            radius_factor = distance / self.max_radius
            intensity = ti.max(0.0, 1.0 - radius_factor) * 0.1
            
            canvas[i, j] = ti.Vector([intensity * 0.2, intensity * 0.1, intensity * 0.3, 1.0])
            
    @ti.kernel
    def _generate_source_pattern(self, canvas: ti.template()):
        """Generate source pattern for kaleidoscope."""
        time = self._frame_count * 0.03
        
        for i, j in self.source_field:
            x = i / self.source_field.shape[0]
            y = j / self.source_field.shape[1]
            
            # Create flowing patterns
            pattern1 = ti.sin(x * 15.0 + time) * ti.cos(y * 12.0 + time * 0.8)
            pattern2 = ti.sin((x + y) * 8.0 - time * 1.2) * 0.7
            pattern3 = ti.sin(x * y * 30.0 + time * 2.0) * 0.5
            
            combined = pattern1 + pattern2 + pattern3
            
            # Audio reactive intensity
            audio_multiplier = 1.0
            if hasattr(self, 'audio_level'):
                audio_multiplier = 0.5 + self.audio_level * 1.5
                
            intensity = ti.abs(combined) * audio_multiplier
            
            # Color based on position and pattern
            hue = (x + y + combined * 0.1 + self.color_shift) % 1.0
            
            # HSV to RGB
            h = hue * 6.0
            s = 0.9
            v = ti.min(1.0, intensity * 0.8)
            
            c = v * s
            x_color = c * (1.0 - ti.abs((h % 2.0) - 1.0))
            
            if h < 1.0:
                r, g, b = c, x_color, 0.0
            elif h < 2.0:
                r, g, b = x_color, c, 0.0
            elif h < 3.0:
                r, g, b = 0.0, c, x_color
            elif h < 4.0:
                r, g, b = 0.0, x_color, c
            elif h < 5.0:
                r, g, b = x_color, 0.0, c
            else:
                r, g, b = c, 0.0, x_color
                
            self.source_field[i, j] = ti.Vector([r, g, b, v])
            
    @ti.kernel
    def _apply_kaleidoscope(self, canvas: ti.template()):
        """Apply kaleidoscope symmetry."""
        segment_angle = 2.0 * 3.14159 / self.num_segments
        
        for i, j in canvas:
            dx = i - self.center_x
            dy = j - self.center_y
            distance = ti.sqrt(dx * dx + dy * dy)
            
            if distance < self.max_radius and distance > 0:
                # Convert to polar coordinates
                angle = ti.atan2(dy, dx)
                if angle < 0:
                    angle += 2.0 * 3.14159
                    
                # Map to first segment
                segment_angle_norm = angle % segment_angle
                
                # Mirror every other segment
                segment_idx = int(angle / segment_angle)
                if segment_idx % 2 == 1:
                    segment_angle_norm = segment_angle - segment_angle_norm
                    
                # Map back to cartesian in source space
                source_x = ti.cos(segment_angle_norm) * distance
                source_y = ti.sin(segment_angle_norm) * distance
                
                # Scale to source field size
                src_i = int((source_x / self.max_radius + 1.0) * 0.5 * self.source_field.shape[0])
                src_j = int((source_y / self.max_radius + 1.0) * 0.5 * self.source_field.shape[1])
                
                # Bounds check
                if (0 <= src_i < self.source_field.shape[0] and 
                    0 <= src_j < self.source_field.shape[1]):
                    
                    source_color = self.source_field[src_i, src_j]
                    
                    # Apply distance fade
                    fade = 1.0 - (distance / self.max_radius) * 0.3
                    
                    color = ti.Vector([
                        source_color[0] * fade,
                        source_color[1] * fade,
                        source_color[2] * fade,
                        source_color[3] * fade
                    ])
                    
                    canvas[i, j] = canvas[i, j] + color
                    
    @ti.kernel
    def _add_center_glow(self, canvas: ti.template()):
        """Add center glow effect."""
        glow_radius = 50
        
        for i, j in canvas:
            dx = i - self.center_x
            dy = j - self.center_y
            distance = ti.sqrt(dx * dx + dy * dy)
            
            if distance < glow_radius:
                glow_strength = 1.0 - distance / glow_radius
                glow_intensity = glow_strength * glow_strength
                
                # Audio reactive glow
                audio_glow = 1.0
                if hasattr(self, 'audio_level'):
                    audio_glow = 0.3 + self.audio_level * 0.7
                    
                glow_color = ti.Vector([
                    1.0 * glow_intensity * audio_glow,
                    0.8 * glow_intensity * audio_glow,
                    0.6 * glow_intensity * audio_glow,
                    glow_intensity * 0.5
                ])
                
                canvas[i, j] = canvas[i, j] + glow_color


# Registration function for the visualizer manager
def get_visualizers():
    """Return list of available enhanced visualizers."""
    return [
        ('enhanced_spectrum', EnhancedSpectrumVisualizer),
        ('enhanced_waveform', EnhancedWaveformVisualizer),
        ('enhanced_particles', EnhancedParticleSystemVisualizer),
        ('enhanced_kaleidoscope', EnhancedKaleidoscopeVisualizer)
    ]


# Example usage and testing
if __name__ == "__main__":
    import time
    
    # Test the enhanced spectrum visualizer
    print("Testing Enhanced Spectrum Visualizer...")
    
    viz = EnhancedSpectrumVisualizer(resolution=(400, 300))
    
    # Simulate some frames
    for frame in range(100):
        # Simulate audio data
        fake_audio_level = 0.5 + 0.3 * np.sin(frame * 0.1)
        fake_fft = np.random.random(64) * fake_audio_level
        
        viz.update_audio_data(fake_audio_level, fake_fft)
        
        # Render frame
        img = viz.render()
        
        if frame % 20 == 0:
            print(f"Frame {frame}: rendered {img.shape} image, max value: {img.max():.3f}")
            
        time.sleep(0.016)  # ~60 FPS
    
    print("Test completed successfully!")