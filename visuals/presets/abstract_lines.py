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
        super().__init__(*args, **kwargs)
        self.spacing = max(1, self.renderer.resolution[0] // self.num_lines)

    def setup(self):
        self.renderer.add_pass("lines", lambda img: _lines(img, self.offset, self.spacing))

    def render(self):
        if self.spacing > 0:
            self.offset = (self.offset + 1) % self.spacing
        return super().render()
