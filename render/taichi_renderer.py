import taichi as ti
from .graph import Layer, Pass

class TaichiRenderer:
    """Simple Taichi-based renderer with a pass graph."""

    _ti_initialized = False

    def __init__(self, resolution=(640, 480)):
        if not TaichiRenderer._ti_initialized:
            ti.init(arch=ti.cpu)
            TaichiRenderer._ti_initialized = True
        self.resolution = resolution
        self.canvas = ti.field(dtype=ti.f32, shape=resolution)
        self.layer = Layer()

    def add_pass(self, name: str, compute):
        self.layer.add_pass(Pass(name, compute))

    def render(self):
        self.layer.run(self.canvas)
        return self.canvas.to_numpy()
