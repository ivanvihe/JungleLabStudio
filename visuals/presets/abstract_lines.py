import taichi as ti
from visuals.base import TaichiVisual

@ti.kernel
def _lines(img: ti.template(), offset: ti.i32, spacing: ti.i32):
    for i, j in img:
        img[i, j] = 1.0 if (i + offset) % spacing == 0 else 0.0

class AbstractLinesVisualizer(TaichiVisual):
    """Simple vertical lines animation using Taichi."""
    visual_name = "Abstract Lines"

    def __init__(self, *args, **kwargs):
        self.offset = 0
        self.num_lines = 20
        # ``TaichiVisual`` will call ``setup`` which computes the initial spacing
        # based on the renderer's resolution.
        super().__init__(*args, **kwargs)

    def setup(self):
        # Derive the spacing from the current renderer resolution so that a
        # resize triggers an updated line layout when ``setup`` is invoked again.
        self.spacing = max(1, self.renderer.resolution[0] // self.num_lines)
        self.renderer.add_pass("lines", lambda img: _lines(img, self.offset, self.spacing))

    def render(self):
        img = super().render()
        if self.spacing > 0:
            self.offset = (self.offset + 1) % self.spacing
        return img
