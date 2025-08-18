import taichi as ti
from visuals.base import TaichiVisual

@ti.kernel
def _gradient(img: ti.template()):
    for i, j in img:
        img[i, j] = j / img.shape[1]

class GradientVisual(TaichiVisual):
    """Simple visual that renders a horizontal gradient."""
    # Advertise this visual so ``VisualizerManager`` can discover it
    # just like the other Taichi-based presets.
    visual_name = "Gradient"

    def setup(self):
        # Register a single rendering pass that fills the framebuffer with
        # a horizontal gradient.  Without ``visual_name`` the manager skips
        # this module which caused the runtime warning seen by users.
        self.renderer.add_pass("gradient", _gradient)
