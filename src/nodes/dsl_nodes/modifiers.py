"""Modifier nodes for transforming geometry and data"""

import numpy as np
from typing import Any

from nodes.base import ModifierNode, NodeOutput, DataType
from nodes.registry import register_node
from presets.base import PresetState


@register_node("transform")
class TransformNode(ModifierNode):
    """Apply transformation to geometry"""

    def _setup_ports(self):
        self.add_input("input", [DataType.GEOMETRY, DataType.PARTICLES])
        self.add_input("position", DataType.VECTOR3, required=False, default=(0.0, 0.0, 0.0))
        self.add_input("rotation", DataType.VECTOR3, required=False, default=(0.0, 0.0, 0.0))
        self.add_input("scale", [DataType.NUMBER, DataType.VECTOR3], required=False, default=1.0)
        self.add_output("output", DataType.GEOMETRY)

    def execute(self, state: PresetState) -> NodeOutput:
        input_data = self.get_input_value("input", state)
        if not input_data:
            return NodeOutput(data=None, data_type=DataType.GEOMETRY)

        position = self.get_param("position", (0.0, 0.0, 0.0))
        rotation = self.get_param("rotation", (0.0, 0.0, 0.0))
        scale = self.get_param("scale", 1.0)

        # Get vertices
        if input_data.data_type == DataType.GEOMETRY:
            vertices = input_data.data["vertices"].copy()
        elif input_data.data_type == DataType.PARTICLES:
            vertices = input_data.data["positions"].copy()
        else:
            return input_data

        # Apply scale
        if isinstance(scale, (int, float)):
            vertices *= scale
        else:
            vertices *= np.array(scale)

        # Apply rotation (simple Z-axis rotation for now)
        if rotation[2] != 0:
            angle = rotation[2]
            cos_a = np.cos(angle)
            sin_a = np.sin(angle)
            rot_matrix = np.array([
                [cos_a, -sin_a, 0],
                [sin_a, cos_a, 0],
                [0, 0, 1]
            ])
            vertices = vertices @ rot_matrix.T

        # Apply translation
        vertices += np.array(position)

        # Return modified data
        result_data = input_data.data.copy()
        if input_data.data_type == DataType.GEOMETRY:
            result_data["vertices"] = vertices
        else:
            result_data["positions"] = vertices

        return NodeOutput(
            data=result_data,
            data_type=input_data.data_type,
            metadata={**input_data.metadata, "transformed": True}
        )


@register_node("displace")
class DisplaceNode(ModifierNode):
    """Displace geometry using noise or field"""

    def _setup_ports(self):
        self.add_input("input", [DataType.GEOMETRY, DataType.PARTICLES])
        self.add_input("field", DataType.FIELD, required=False)
        self.add_input("amount", DataType.NUMBER, required=False, default=0.1)
        self.add_input("frequency", DataType.NUMBER, required=False, default=1.0)
        self.add_output("output", DataType.GEOMETRY)

    def execute(self, state: PresetState) -> NodeOutput:
        input_data = self.get_input_value("input", state)
        if not input_data:
            return NodeOutput(data=None, data_type=DataType.GEOMETRY)

        amount = self.get_param("amount", 0.1)
        frequency = self.get_param("frequency", 1.0)

        # Modulate with audio if specified
        if self.get_param("audio_reactive", False):
            band = self.get_param("audio_band", "mid")
            audio_val = getattr(state, band, 0.0)
            amount *= (1.0 + audio_val)

        # Get vertices
        if input_data.data_type == DataType.GEOMETRY:
            vertices = input_data.data["vertices"].copy()
        elif input_data.data_type == DataType.PARTICLES:
            vertices = input_data.data["positions"].copy()
        else:
            return input_data

        # Apply noise displacement
        time_offset = state.time * 0.5
        noise_x = np.sin(vertices[:, 0] * frequency + time_offset) * amount
        noise_y = np.cos(vertices[:, 1] * frequency - time_offset) * amount
        noise_z = np.sin(vertices[:, 2] * frequency + time_offset * 0.5) * amount

        vertices[:, 0] += noise_x
        vertices[:, 1] += noise_y
        vertices[:, 2] += noise_z

        # Return modified data
        result_data = input_data.data.copy()
        if input_data.data_type == DataType.GEOMETRY:
            result_data["vertices"] = vertices
        else:
            result_data["positions"] = vertices

        return NodeOutput(
            data=result_data,
            data_type=input_data.data_type,
            metadata={**input_data.metadata, "displaced": True}
        )


@register_node("repeat")
class RepeatNode(ModifierNode):
    """Repeat geometry multiple times"""

    def _setup_ports(self):
        self.add_input("input", DataType.GEOMETRY)
        self.add_input("count", DataType.NUMBER, required=False, default=5)
        self.add_input("offset", DataType.VECTOR3, required=False, default=(0.1, 0.0, 0.0))
        self.add_input("rotation_step", DataType.NUMBER, required=False, default=0.0)
        self.add_output("output", DataType.GEOMETRY)

    def execute(self, state: PresetState) -> NodeOutput:
        input_data = self.get_input_value("input", state)
        if not input_data or input_data.data_type != DataType.GEOMETRY:
            return NodeOutput(data=None, data_type=DataType.GEOMETRY)

        count = int(self.get_param("count", 5))
        offset = np.array(self.get_param("offset", (0.1, 0.0, 0.0)))
        rotation_step = self.get_param("rotation_step", 0.0)

        original_vertices = input_data.data["vertices"]
        all_vertices = []

        for i in range(count):
            vertices = original_vertices.copy()

            # Apply rotation
            if rotation_step != 0:
                angle = rotation_step * i
                cos_a = np.cos(angle)
                sin_a = np.sin(angle)
                rot_matrix = np.array([
                    [cos_a, -sin_a, 0],
                    [sin_a, cos_a, 0],
                    [0, 0, 1]
                ])
                vertices = vertices @ rot_matrix.T

            # Apply offset
            vertices += offset * i

            all_vertices.append(vertices)

        # Concatenate all vertices
        combined_vertices = np.vstack(all_vertices)

        return NodeOutput(
            data={"vertices": combined_vertices, "primitive": input_data.data.get("primitive", "lines")},
            data_type=DataType.GEOMETRY,
            metadata={"repeated": count}
        )


@register_node("color")
class ColorNode(ModifierNode):
    """Apply color to geometry"""

    def _setup_ports(self):
        self.add_input("input", [DataType.GEOMETRY, DataType.PARTICLES])
        self.add_input("color", DataType.COLOR, required=False, default=(1.0, 1.0, 1.0, 1.0))
        self.add_input("hue_shift", DataType.NUMBER, required=False, default=0.0)
        self.add_output("output", DataType.GEOMETRY)

    def execute(self, state: PresetState) -> NodeOutput:
        input_data = self.get_input_value("input", state)
        if not input_data:
            return NodeOutput(data=None, data_type=input_data.data_type if input_data else DataType.GEOMETRY)

        color = self.get_param("color", (1.0, 1.0, 1.0, 1.0))
        hue_shift = self.get_param("hue_shift", 0.0)

        # Modulate hue with audio if specified
        if self.get_param("audio_reactive", False):
            band = self.get_param("audio_band", "high")
            audio_val = getattr(state, band, 0.0)
            hue_shift += audio_val * self.get_param("audio_intensity", 0.5)

        # Create color array for all vertices
        result_data = input_data.data.copy()
        result_data["color"] = np.array(color, dtype=np.float32)
        result_data["hue_shift"] = hue_shift

        return NodeOutput(
            data=result_data,
            data_type=input_data.data_type,
            metadata={**input_data.metadata, "colored": True}
        )


@register_node("twist")
class TwistNode(ModifierNode):
    """Apply twisting deformation to geometry"""

    def _setup_ports(self):
        self.add_input("input", DataType.GEOMETRY)
        self.add_input("amount", DataType.NUMBER, required=False, default=1.0)
        self.add_input("axis", DataType.NUMBER, required=False, default=2)  # 0=X, 1=Y, 2=Z
        self.add_output("output", DataType.GEOMETRY)

    def execute(self, state: PresetState) -> NodeOutput:
        input_data = self.get_input_value("input", state)
        if not input_data or input_data.data_type != DataType.GEOMETRY:
            return NodeOutput(data=None, data_type=DataType.GEOMETRY)

        amount = self.get_param("amount", 1.0)
        axis = int(self.get_param("axis", 2))

        vertices = input_data.data["vertices"].copy()

        # Apply twist based on distance along axis
        if axis == 2:  # Z-axis
            for i, v in enumerate(vertices):
                angle = v[2] * amount
                cos_a = np.cos(angle)
                sin_a = np.sin(angle)
                x_new = v[0] * cos_a - v[1] * sin_a
                y_new = v[0] * sin_a + v[1] * cos_a
                vertices[i, 0] = x_new
                vertices[i, 1] = y_new

        result_data = input_data.data.copy()
        result_data["vertices"] = vertices

        return NodeOutput(
            data=result_data,
            data_type=DataType.GEOMETRY,
            metadata={**input_data.metadata, "twisted": True}
        )
