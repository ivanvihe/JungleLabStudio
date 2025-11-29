"""Executor to convert VisualGraph to RenderGraph and execute it"""

import moderngl
from typing import Optional
from editor.graph.visual_graph import VisualGraph
from core.graph.graph import RenderGraph
from core.graph.loader import GraphLoader
from editor.dsl.serializer import PresetSerializer


class GraphExecutor:
    """Converts visual graph to executable render graph"""

    def __init__(self, ctx: moderngl.Context, size: tuple):
        self.ctx = ctx
        self.size = size
        self.loader = GraphLoader(ctx, size)
        self.render_graph: Optional[RenderGraph] = None
        self._last_node_count = 0
        self._last_connection_count = 0

    def needs_rebuild(self, visual_graph: VisualGraph) -> bool:
        """Check if render graph needs rebuilding"""
        node_count = len(visual_graph.nodes)
        conn_count = len(visual_graph.connections)

        if self.render_graph is None:
            return True

        if node_count != self._last_node_count:
            return True

        if conn_count != self._last_connection_count:
            return True

        return False

    def rebuild(self, visual_graph: VisualGraph):
        """Rebuild render graph from visual graph"""
        try:
            # Convert visual graph to YAML
            yaml_str = PresetSerializer.serialize(visual_graph)

            print(f"GraphExecutor: Serializing {len(visual_graph.nodes)} nodes, {len(visual_graph.connections)} connections")

            # Load as render graph
            self.render_graph = self.loader.load_from_yaml(yaml_str)

            # Update counters
            self._last_node_count = len(visual_graph.nodes)
            self._last_connection_count = len(visual_graph.connections)

            if self.render_graph:
                print(f"GraphExecutor: ✅ Built render graph with {len(self.render_graph.nodes)} nodes")
            else:
                print("GraphExecutor: ⚠️ Render graph is None")

        except Exception as e:
            print(f"GraphExecutor: ❌ Error building render graph: {e}")
            import traceback
            traceback.print_exc()
            self.render_graph = None

    def update(self, dt: float, fft_bands=None):
        """Update render graph"""
        if self.render_graph:
            self.render_graph.update(dt, fft_bands or [])

    def sync_parameters(self, visual_graph: VisualGraph):
        """Sync parameters from visual graph to render graph (Hot Update)"""
        if not self.render_graph:
            return

        for v_node in visual_graph.nodes.values():
            r_node = self.render_graph.get_node(v_node.id)
            if r_node:
                # Sync params
                for name, value in v_node.params.items():
                    # Check if param exists on render node
                    if name in r_node.params:
                        # Update value
                        # Handle vector types if necessary, but usually they are lists/tuples
                        r_node.params[name].update(value)
                    elif hasattr(r_node, name):
                        # Direct attribute (legacy or specific props like 'blend')
                        setattr(r_node, name, value)
                        
                # Sync custom attributes (like MIDI mapping for Listener)
                if hasattr(v_node, 'midi_mapping') and hasattr(r_node, 'midi_mapping'):
                     # We might need to be careful not to overwrite with None if not set
                     # But VisualNode.midi_mapping is authoritative
                     if v_node.midi_mapping:
                         # If r_node needs a specific object type, we might have issues if we pass a dict?
                         # VisualNode midi_mapping is usually the object or dict depending on deserialization
                         # Let's assume it's compatible or the same object reference (unlikely)
                         # Actually, let's just pass it. The Logic in Listener node should handle updates.
                         # Wait, MIDIListenerNode doesn't have an 'update_mapping' method, it sets 'self.midi_mapping'.
                         # We can just set it.
                         r_node.midi_mapping = v_node.midi_mapping
                
                # Sync Launcher targets
                if hasattr(v_node, 'target_generators') and hasattr(r_node, 'target_generators'):
                    r_node.target_generators = v_node.target_generators
                if hasattr(v_node, 'parameter_mappings') and hasattr(r_node, 'parameter_mappings'):
                    r_node.parameter_mappings = v_node.parameter_mappings

    def render(self):
        """Render the graph"""
        if self.render_graph:
            self.render_graph.render()

    def get_output_texture(self):
        """Get the final output texture"""
        if self.render_graph:
            return self.render_graph.get_final_texture()
        return None

    def has_graph(self) -> bool:
        """Check if we have a valid render graph"""
        return self.render_graph is not None and len(self.render_graph.nodes) > 0
