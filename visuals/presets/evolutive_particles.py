import time
import numpy as np
import taichi as ti

from visuals.base import TaichiVisual


@ti.kernel
def _clear(img: ti.template()):
    for i, j in img:
        img[i, j] *= 0.9  # slight trail for motion


@ti.kernel
def _update(pos: ti.template(), vel: ti.template(), dt: ti.f32, w: ti.i32, h: ti.i32):
    for k in pos:
        ang = (pos[k].x + pos[k].y) * 0.01
        vel[k] += ti.Vector([
            ti.sin(ang + ti.random() * 0.5),  # Fixed: removed ti.f32 from ti.random()
            ti.cos(ang + ti.random() * 0.5),  # Fixed: removed ti.f32 from ti.random()
        ]) * 20.0 * dt
        vel[k] *= 0.98
        pos[k] += vel[k] * dt
        
        # Handle boundary wrapping
        if pos[k].x < 0:
            pos[k].x += w
        if pos[k].x >= w:
            pos[k].x -= w
        if pos[k].y < 0:
            pos[k].y += h
        if pos[k].y >= h:
            pos[k].y -= h


@ti.kernel
def _draw(img: ti.template(), pos: ti.template()):
    for k in pos:
        x = int(pos[k].x)
        y = int(pos[k].y)
        if 0 <= x < img.shape[0] and 0 <= y < img.shape[1]:
            img[x, y] = 1.0


class EvolutiveParticlesVisualizer(TaichiVisual):
    """Taichi implementation of an evolving particle system."""

    visual_name = "Evolutive Particles"

    def __init__(self, *args, num_particles: int = 800, **kwargs):
        self.num_particles = num_particles
        self._last_time = time.time()
        self._dt = 0.016  # Default delta time
        
        # Initialize parent first to get renderer
        super().__init__(*args, **kwargs)
        
        # Initialize Taichi fields after parent initialization
        self._init_fields()
        self._reset_particles()

    def _init_fields(self):
        """Initialize Taichi fields"""
        self.positions = ti.Vector.field(2, dtype=ti.f32, shape=self.num_particles)
        self.velocities = ti.Vector.field(2, dtype=ti.f32, shape=self.num_particles)

    def _reset_particles(self):
        """Reset particle positions and velocities"""
        w, h = self.renderer.resolution
        pos = np.random.rand(self.num_particles, 2)
        pos[:, 0] *= w
        pos[:, 1] *= h
        self.positions.from_numpy(pos.astype(np.float32))
        
        # Initialize velocities to zero
        vel = np.zeros((self.num_particles, 2), dtype=np.float32)
        self.velocities.from_numpy(vel)

    def setup(self):
        """Setup render passes"""
        # Clear any existing passes
        self.renderer.clear_passes()
        self.renderer.add_pass("particles", self._render_pass)

    def _render_pass(self, img):
        """Main render pass for particles"""
        try:
            # Fixed: Convert dt to proper Taichi scalar
            dt_scalar = float(self._dt)  # Ensure it's a Python float first
            
            _clear(img)
            _update(self.positions, self.velocities, dt_scalar, 
                   self.renderer.resolution[0], self.renderer.resolution[1])
            _draw(img, self.positions)
        except Exception as e:
            print(f"Error in particles render pass: {e}")
            # Fallback: just clear the image
            for i, j in img:
                img[i, j] = 0.0

    def render(self):
        """Update time and render"""
        now = time.time()
        self._dt = min(now - self._last_time, 0.033)  # Cap at ~30fps for stability
        self._last_time = now
        return super().render()

    def resizeGL(self, width: int, height: int, backend=None):
        """Handle resize events"""
        super().resizeGL(width, height, backend)
        # Reset particles when resolution changes
        self._reset_particles()

    def get_controls(self):
        """Get available controls"""
        controls = super().get_controls() if hasattr(super(), 'get_controls') else {}
        controls.update({
            "Particle Count": {
                "type": "slider",
                "min": 100,
                "max": 2000,
                "value": self.num_particles,
                "description": "Number of particles in the system"
            }
        })
        return controls

    def update_control(self, name, value):
        """Handle control updates"""
        if hasattr(super(), 'update_control') and super().update_control(name, value):
            return True
            
        if name == "Particle Count" and int(value) != self.num_particles:
            self.num_particles = int(value)
            # Reinitialize fields with new particle count
            self._init_fields()
            self._reset_particles()
            return True
        return False