"""Generator nodes for the YAML DSL system"""

import numpy as np
import moderngl
from typing import Any

from nodes.base import GeneratorNode, NodeOutput, DataType
from nodes.registry import register_node
from presets.base import PresetState


@register_node("circle")
class CircleNode(GeneratorNode):
    """Generate a circle shape"""

    def _setup_ports(self):
        self.add_input("radius", DataType.NUMBER, required=False, default=0.5)
        self.add_input("segments", DataType.NUMBER, required=False, default=64)
        self.add_input("position", DataType.VECTOR2, required=False, default=(0.0, 0.0))
        self.add_output("output", DataType.GEOMETRY)

    def execute(self, state: PresetState) -> NodeOutput:
        radius = self.get_param("radius", 0.5)
        segments = int(self.get_param("segments", 64))
        position = self.get_param("position", (0.0, 0.0))

        # Modulate radius with audio if specified
        if self.get_param("audio_reactive", False):
            band = self.get_param("audio_band", "bass")
            intensity = self.get_param("audio_intensity", 0.5)
            audio_val = getattr(state, band, 0.0)
            radius *= (1.0 + audio_val * intensity)

        # Generate circle vertices
        angles = np.linspace(0, 2 * np.pi, segments, endpoint=False)
        vertices = []
        for angle in angles:
            x = position[0] + radius * np.cos(angle)
            y = position[1] + radius * np.sin(angle)
            vertices.append([x, y, 0.0])

        vertices = np.array(vertices, dtype=np.float32)

        return NodeOutput(
            data={"vertices": vertices, "primitive": "line_loop"},
            data_type=DataType.GEOMETRY,
            metadata={"shape": "circle", "radius": radius}
        )


@register_node("rect")
class RectNode(GeneratorNode):
    """Generate a rectangle shape"""

    def _setup_ports(self):
        self.add_input("width", DataType.NUMBER, required=False, default=1.0)
        self.add_input("height", DataType.NUMBER, required=False, default=1.0)
        self.add_input("position", DataType.VECTOR2, required=False, default=(0.0, 0.0))
        self.add_output("output", DataType.GEOMETRY)

    def execute(self, state: PresetState) -> NodeOutput:
        width = self.get_param("width", 1.0)
        height = self.get_param("height", 1.0)
        position = self.get_param("position", (0.0, 0.0))

        # Modulate size with audio if specified
        if self.get_param("audio_reactive", False):
            band = self.get_param("audio_band", "bass")
            intensity = self.get_param("audio_intensity", 0.5)
            audio_val = getattr(state, band, 0.0)
            scale = 1.0 + audio_val * intensity
            width *= scale
            height *= scale

        half_w = width / 2
        half_h = height / 2
        x, y = position

        vertices = np.array([
            [x - half_w, y - half_h, 0.0],
            [x + half_w, y - half_h, 0.0],
            [x + half_w, y + half_h, 0.0],
            [x - half_w, y + half_h, 0.0],
        ], dtype=np.float32)

        return NodeOutput(
            data={"vertices": vertices, "primitive": "line_loop"},
            data_type=DataType.GEOMETRY,
            metadata={"shape": "rect", "width": width, "height": height}
        )


@register_node("line")
class LineNode(GeneratorNode):
    """Generate a line"""

    def _setup_ports(self):
        self.add_input("start", DataType.VECTOR2, required=False, default=(-1.0, 0.0))
        self.add_input("end", DataType.VECTOR2, required=False, default=(1.0, 0.0))
        self.add_output("output", DataType.GEOMETRY)

    def execute(self, state: PresetState) -> NodeOutput:
        start = self.get_param("start", (-1.0, 0.0))
        end = self.get_param("end", (1.0, 0.0))

        vertices = np.array([
            [start[0], start[1], 0.0],
            [end[0], end[1], 0.0],
        ], dtype=np.float32)

        return NodeOutput(
            data={"vertices": vertices, "primitive": "lines"},
            data_type=DataType.GEOMETRY,
            metadata={"shape": "line"}
        )


@register_node("particles")
class ParticlesNode(GeneratorNode):
    """Generate a particle system"""

    def _setup_ports(self):
        self.add_input("count", DataType.NUMBER, required=False, default=1000)
        self.add_input("size", DataType.NUMBER, required=False, default=2.0)
        self.add_input("spread", DataType.NUMBER, required=False, default=1.0)
        self.add_output("output", DataType.PARTICLES)

    def execute(self, state: PresetState) -> NodeOutput:
        count = int(self.get_param("count", 1000))
        size = self.get_param("size", 2.0)
        spread = self.get_param("spread", 1.0)

        # Modulate with audio if specified
        if self.get_param("audio_reactive", False):
            band = self.get_param("audio_band", "mid")
            intensity = self.get_param("audio_intensity", 0.5)
            audio_val = getattr(state, band, 0.0)
            count = int(count * (1.0 + audio_val * intensity * 0.5))

        # Generate random particle positions
        positions = np.random.randn(count, 3).astype(np.float32) * spread
        velocities = np.random.randn(count, 3).astype(np.float32) * 0.01
        ages = np.random.rand(count).astype(np.float32)

        return NodeOutput(
            data={
                "positions": positions,
                "velocities": velocities,
                "ages": ages,
                "size": size,
            },
            data_type=DataType.PARTICLES,
            metadata={"count": count}
        )


@register_node("noise_field")
class NoiseFieldNode(GeneratorNode):
    """Generate a noise-based vector field"""

    def _setup_ports(self):
        self.add_input("resolution", DataType.NUMBER, required=False, default=32)
        self.add_input("scale", DataType.NUMBER, required=False, default=1.0)
        self.add_input("octaves", DataType.NUMBER, required=False, default=4)
        self.add_output("output", DataType.FIELD)

    def execute(self, state: PresetState) -> NodeOutput:
        resolution = int(self.get_param("resolution", 32))
        scale = self.get_param("scale", 1.0)
        octaves = int(self.get_param("octaves", 4))

        # Simple Perlin-like noise approximation
        def noise_func(x, y, t):
            return np.sin(x * scale + t) * np.cos(y * scale - t)

        # Generate field grid
        x = np.linspace(-1, 1, resolution)
        y = np.linspace(-1, 1, resolution)
        xx, yy = np.meshgrid(x, y)

        # Calculate vector field using noise
        time_offset = state.time * 0.1
        field_x = noise_func(xx, yy, time_offset)
        field_y = noise_func(xx + 100, yy + 100, time_offset + 100)

        field = np.stack([field_x, field_y], axis=-1)

        return NodeOutput(
            data={"field": field, "grid": (xx, yy)},
            data_type=DataType.FIELD,
            metadata={"resolution": resolution}
        )


@register_node("grid")
class GridNode(GeneratorNode):
    """Generate a grid of lines"""

    def _setup_ports(self):
        self.add_input("rows", DataType.NUMBER, required=False, default=10)
        self.add_input("cols", DataType.NUMBER, required=False, default=10)
        self.add_input("spacing", DataType.NUMBER, required=False, default=0.1)
        self.add_output("output", DataType.GEOMETRY)

    def execute(self, state: PresetState) -> NodeOutput:
        rows = int(self.get_param("rows", 10))
        cols = int(self.get_param("cols", 10))
        spacing = self.get_param("spacing", 0.1)

        vertices = []

        # Horizontal lines
        for i in range(rows + 1):
            y = (i - rows / 2) * spacing
            vertices.append([cols / 2 * spacing, y, 0.0])
            vertices.append([-cols / 2 * spacing, y, 0.0])

        # Vertical lines
        for i in range(cols + 1):
            x = (i - cols / 2) * spacing
            vertices.append([x, -rows / 2 * spacing, 0.0])
            vertices.append([x, rows / 2 * spacing, 0.0])

        vertices = np.array(vertices, dtype=np.float32)

        return NodeOutput(
            data={"vertices": vertices, "primitive": "lines"},
            data_type=DataType.GEOMETRY,
            metadata={"rows": rows, "cols": cols}
        )
