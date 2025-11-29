"""
InitNode - Initialization and Configuration Node
"""
import moderngl
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("init")
class InitNode(RenderNode):
    """
    Init node - Configuration point for the graph.
    Does not render visual output, but exists in the graph to avoid connection errors.
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)
        # It doesn't need to draw anything
    
    def render(self):
        # No-op
        pass
