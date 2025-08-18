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
            ti.sin(ang + ti.random(ti.f32) * 0.5),
            ti.cos(ang + ti.random(ti.f32) * 0.5),
        ]) * 20.0 * dt
        vel[k] *= 0.98
        pos[k] += vel[k] * dt
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
        self.positions = ti.Vector.field(2, dtype=ti.f32, shape=num_particles)
        self.velocities = ti.Vector.field(2, dtype=ti.f32, shape=num_particles)
        self._last_time = time.time()
        super().__init__(*args, **kwargs)
        self._reset_particles()

    def _reset_particles(self):
        w, h = self.renderer.resolution
        pos = np.random.rand(self.num_particles, 2)
        pos[:, 0] *= w
        pos[:, 1] *= h
        self.positions.from_numpy(pos.astype(np.float32))
        self.velocities.fill(0)

    def setup(self):
        self.renderer.add_pass("particles", self._render_pass)

    def _render_pass(self, img):
        dt = ti.cast(self._dt, ti.f32)
        _clear(img)
        _update(self.positions, self.velocities, dt, self.renderer.resolution[0], self.renderer.resolution[1])
        _draw(img, self.positions)

    def render(self):
        now = time.time()
        self._dt = now - self._last_time
        self._last_time = now
        return super().render()

    # Simple control to adjust particle count
    def get_controls(self):
        return {
            "Particle Count": {
                "type": "slider",
                "min": 100,
                "max": 2000,
                "value": self.num_particles,
            }
        }

    def update_control(self, name, value):
        if name == "Particle Count" and int(value) != self.num_particles:
            self.num_particles = int(value)
            self.positions = ti.Vector.field(2, dtype=ti.f32, shape=self.num_particles)
            self.velocities = ti.Vector.field(2, dtype=ti.f32, shape=self.num_particles)
            self._reset_particles()
