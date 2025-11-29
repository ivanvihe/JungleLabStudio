"""YAML-based preset that uses the node graph system"""

import moderngl
from pathlib import Path
from typing import Dict, Any

from presets.base import VisualPreset, PresetState
from nodes.yaml_loader import YAMLPresetLoader
from nodes.graph import NodeGraph
import nodes.dsl_nodes  # Import to register all DSL nodes


class YAMLPreset(VisualPreset):
    """Visual preset defined by YAML DSL"""

    def __init__(self, ctx: moderngl.Context, yaml_path: Path = None, yaml_data: Dict[str, Any] = None):
        self.ctx = ctx
        self.loader = YAMLPresetLoader()
        self.graph: NodeGraph = None
        self.metadata: Dict[str, Any] = {}
        self.controls: Dict[str, Dict[str, Any]] = {}
        self.name = "YAML Preset"

        if yaml_path:
            self.load_from_file(yaml_path)
        elif yaml_data:
            self.load_from_data(yaml_data)

    def load_from_file(self, path: Path):
        """Load preset from YAML file"""
        preset_data = self.loader.load_from_file(path)
        self._build_from_data(preset_data)

    def load_from_data(self, data: Dict[str, Any]):
        """Load preset from data dict"""
        self._build_from_data(data)

    def _build_from_data(self, data: Dict[str, Any]):
        """Build the preset from validated data"""
        self.metadata = self.loader.get_metadata(data)
        self.controls = self.loader.get_controls(data)
        self.name = self.metadata.get('name', 'YAML Preset')

        try:
            self.graph = self.loader.build_graph(data)
            print(f"✓ Loaded YAML preset: {self.name}")
            print(f"  Nodes: {len(self.graph.nodes)}")
            print(f"  Controls: {len(self.controls)}")
        except Exception as e:
            print(f"✗ Error loading YAML preset: {e}")
            raise

    def get_controls(self) -> Dict[str, Dict[str, Any]]:
        """Return UI controls for this preset"""
        return self.controls

    def update_parameter(self, param_name: str, value: Any):
        """Update a parameter value and propagate to nodes"""
        # Find nodes that use this parameter
        for node in self.graph.nodes.values():
            if param_name in node.params or hasattr(node, param_name):
                node.set_param(param_name, value)

    def render(self, state: PresetState, fbo=None):
        """Render the preset using the node graph"""
        target = fbo if fbo else self.ctx.screen
        target.use()

        if not self.graph:
            self.ctx.clear(0.0, 0.0, 0.0)
            return

        try:
            # Execute the graph
            output = self.graph.execute(state)

            if output and output.data:
                self._render_output(output, state, target)
        except Exception as e:
            print(f"Error rendering YAML preset: {e}")
            self.ctx.clear(0.1, 0.0, 0.0)  # Red tint for errors

    def _render_output(self, output, state: PresetState, target):
        """Render the output from the graph"""
        # This is a simplified renderer - in practice, you'd have more sophisticated rendering
        from nodes.base import DataType

        self.ctx.clear(0.0, 0.0, 0.0)

        if output.data_type == DataType.GEOMETRY:
            self._render_geometry(output.data, state)
        elif output.data_type == DataType.PARTICLES:
            self._render_particles(output.data, state)
        elif output.data_type == DataType.TEXTURE:
            self._render_texture(output.data, state)

    def _render_geometry(self, data: Dict[str, Any], state: PresetState):
        """Render geometry data"""
        if "vertices" not in data:
            return

        vertices = data["vertices"]
        primitive = data.get("primitive", "lines")

        # Get color
        color = data.get("color", (1.0, 1.0, 1.0, 1.0))

        # Apply glow if present
        if data.get("glow_intensity"):
            # Apply glow effect (simplified - would use shaders in practice)
            pass

        # Simple rendering using ModernGL
        # In practice, you'd use proper shaders here
        # For now, just demonstrate the data flow is working
        print(f"Rendering geometry: {len(vertices)} vertices, primitive={primitive}")

    def _render_particles(self, data: Dict[str, Any], state: PresetState):
        """Render particle system"""
        if "positions" not in data:
            return

        positions = data["positions"]
        size = data.get("size", 2.0)

        print(f"Rendering particles: {len(positions)} particles, size={size}")

    def _render_texture(self, data: Dict[str, Any], state: PresetState):
        """Render texture/post-processing effects"""
        print(f"Rendering texture with effects: {list(data.keys())}")

    def __repr__(self):
        return f"YAMLPreset(name={self.name}, nodes={len(self.graph.nodes) if self.graph else 0})"
