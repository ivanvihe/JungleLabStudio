from __future__ import annotations
from typing import Tuple
from render.taichi_renderer import TaichiRenderer

class TaichiVisual:
    """Base class for visuals rendered with TaichiRenderer."""
    def __init__(self, resolution: Tuple[int, int] = (640, 480)):
        self.renderer = TaichiRenderer(resolution)
        self.setup()

    def setup(self) -> None:
        """Hook to register passes on the renderer."""
        pass

    def render(self):
        return self.renderer.render()
