from __future__ import annotations
from typing import Type, Tuple
from .base import TaichiVisual

class VisualizerManager:
    """Minimal manager that instantiates and renders a visual."""
    def __init__(self, visual_cls: Type[TaichiVisual], resolution: Tuple[int, int] = (640, 480)):
        self.visual = visual_cls(resolution)

    def render(self):
        return self.visual.render()
