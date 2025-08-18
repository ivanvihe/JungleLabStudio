import taichi as ti
from visuals.base import TaichiVisual

@ti.kernel
def _gradient(img: ti.template()):
    for i, j in img:
        img[i, j] = j / img.shape[1]

class GradientVisual(TaichiVisual):
    """Simple visual that renders a horizontal gradient."""
    def setup(self):
        self.renderer.add_pass("gradient", _gradient)
