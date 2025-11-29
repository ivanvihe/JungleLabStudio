"""VFX nodes for visual effects"""

import numpy as np
from typing import Any

from nodes.base import VFXNode, NodeOutput, DataType
from nodes.registry import register_node
from presets.base import PresetState


@register_node("glow")
class GlowNode(VFXNode):
    """Add glow effect to geometry"""

    def _setup_ports(self):
        self.add_input("input", [DataType.GEOMETRY, DataType.PARTICLES])
        self.add_input("intensity", DataType.NUMBER, required=False, default=1.0)
        self.add_input("radius", DataType.NUMBER, required=False, default=0.1)
        self.add_output("output", DataType.GEOMETRY)

    def execute(self, state: PresetState) -> NodeOutput:
        input_data = self.get_input_value("input", state)
        if not input_data:
            return NodeOutput(data=None, data_type=DataType.GEOMETRY)

        intensity = self.get_param("intensity", 1.0)
        radius = self.get_param("radius", 0.1)

        # Modulate with audio if specified
        if self.get_param("audio_reactive", False):
            band = self.get_param("audio_band", "high")
            audio_val = getattr(state, band, 0.0)
            intensity *= (1.0 + audio_val)

        result_data = input_data.data.copy()
        result_data["glow_intensity"] = intensity
        result_data["glow_radius"] = radius

        return NodeOutput(
            data=result_data,
            data_type=input_data.data_type,
            metadata={**input_data.metadata, "glow": True}
        )


@register_node("blur")
class BlurNode(VFXNode):
    """Apply blur effect"""

    def _setup_ports(self):
        self.add_input("input", DataType.TEXTURE)
        self.add_input("amount", DataType.NUMBER, required=False, default=1.0)
        self.add_input("direction", DataType.VECTOR2, required=False, default=(1.0, 1.0))
        self.add_output("output", DataType.TEXTURE)

    def execute(self, state: PresetState) -> NodeOutput:
        input_data = self.get_input_value("input", state)
        if not input_data:
            return NodeOutput(data=None, data_type=DataType.TEXTURE)

        amount = self.get_param("amount", 1.0)
        direction = self.get_param("direction", (1.0, 1.0))

        result_data = input_data.data.copy() if isinstance(input_data.data, dict) else {"texture": input_data.data}
        result_data["blur_amount"] = amount
        result_data["blur_direction"] = direction

        return NodeOutput(
            data=result_data,
            data_type=DataType.TEXTURE,
            metadata={**input_data.metadata, "blurred": True}
        )


@register_node("feedback")
class FeedbackNode(VFXNode):
    """Apply feedback/echo effect"""

    def _setup_ports(self):
        self.add_input("input", [DataType.GEOMETRY, DataType.TEXTURE])
        self.add_input("amount", DataType.NUMBER, required=False, default=0.9)
        self.add_input("decay", DataType.NUMBER, required=False, default=0.95)
        self.add_output("output", DataType.TEXTURE)

    def execute(self, state: PresetState) -> NodeOutput:
        input_data = self.get_input_value("input", state)
        if not input_data:
            return NodeOutput(data=None, data_type=DataType.TEXTURE)

        amount = self.get_param("amount", 0.9)
        decay = self.get_param("decay", 0.95)

        result_data = input_data.data.copy() if isinstance(input_data.data, dict) else {"data": input_data.data}
        result_data["feedback_amount"] = amount
        result_data["feedback_decay"] = decay

        return NodeOutput(
            data=result_data,
            data_type=DataType.TEXTURE,
            metadata={**input_data.metadata, "feedback": True}
        )


@register_node("trail")
class TrailNode(VFXNode):
    """Add motion trail effect"""

    def _setup_ports(self):
        self.add_input("input", [DataType.GEOMETRY, DataType.PARTICLES])
        self.add_input("length", DataType.NUMBER, required=False, default=10)
        self.add_input("fade", DataType.NUMBER, required=False, default=0.9)
        self.add_output("output", DataType.GEOMETRY)

    def execute(self, state: PresetState) -> NodeOutput:
        input_data = self.get_input_value("input", state)
        if not input_data:
            return NodeOutput(data=None, data_type=DataType.GEOMETRY)

        length = int(self.get_param("length", 10))
        fade = self.get_param("fade", 0.9)

        result_data = input_data.data.copy()
        result_data["trail_length"] = length
        result_data["trail_fade"] = fade

        return NodeOutput(
            data=result_data,
            data_type=input_data.data_type,
            metadata={**input_data.metadata, "trail": True}
        )


@register_node("chromatic_aberration")
class ChromaticAberrationNode(VFXNode):
    """Apply chromatic aberration effect"""

    def _setup_ports(self):
        self.add_input("input", DataType.TEXTURE)
        self.add_input("amount", DataType.NUMBER, required=False, default=0.01)
        self.add_input("direction", DataType.VECTOR2, required=False, default=(1.0, 0.0))
        self.add_output("output", DataType.TEXTURE)

    def execute(self, state: PresetState) -> NodeOutput:
        input_data = self.get_input_value("input", state)
        if not input_data:
            return NodeOutput(data=None, data_type=DataType.TEXTURE)

        amount = self.get_param("amount", 0.01)
        direction = self.get_param("direction", (1.0, 0.0))

        # Modulate with audio if specified
        if self.get_param("audio_reactive", False):
            band = self.get_param("audio_band", "bass")
            audio_val = getattr(state, band, 0.0)
            amount *= (1.0 + audio_val * 2.0)

        result_data = input_data.data.copy() if isinstance(input_data.data, dict) else {"texture": input_data.data}
        result_data["chroma_amount"] = amount
        result_data["chroma_direction"] = direction

        return NodeOutput(
            data=result_data,
            data_type=DataType.TEXTURE,
            metadata={**input_data.metadata, "chromatic_aberration": True}
        )


@register_node("pixelate")
class PixelateNode(VFXNode):
    """Apply pixelation effect"""

    def _setup_ports(self):
        self.add_input("input", DataType.TEXTURE)
        self.add_input("pixel_size", DataType.NUMBER, required=False, default=8.0)
        self.add_output("output", DataType.TEXTURE)

    def execute(self, state: PresetState) -> NodeOutput:
        input_data = self.get_input_value("input", state)
        if not input_data:
            return NodeOutput(data=None, data_type=DataType.TEXTURE)

        pixel_size = self.get_param("pixel_size", 8.0)

        result_data = input_data.data.copy() if isinstance(input_data.data, dict) else {"texture": input_data.data}
        result_data["pixel_size"] = pixel_size

        return NodeOutput(
            data=result_data,
            data_type=DataType.TEXTURE,
            metadata={**input_data.metadata, "pixelated": True}
        )


@register_node("kaleidoscope")
class KaleidoscopeNode(VFXNode):
    """Apply kaleidoscope effect"""

    def _setup_ports(self):
        self.add_input("input", [DataType.GEOMETRY, DataType.TEXTURE])
        self.add_input("segments", DataType.NUMBER, required=False, default=6)
        self.add_input("rotation", DataType.NUMBER, required=False, default=0.0)
        self.add_output("output", DataType.TEXTURE)

    def execute(self, state: PresetState) -> NodeOutput:
        input_data = self.get_input_value("input", state)
        if not input_data:
            return NodeOutput(data=None, data_type=DataType.TEXTURE)

        segments = int(self.get_param("segments", 6))
        rotation = self.get_param("rotation", 0.0)

        # Auto-rotate with time if enabled
        if self.get_param("auto_rotate", False):
            rotation += state.time * self.get_param("rotation_speed", 0.1)

        result_data = input_data.data.copy() if isinstance(input_data.data, dict) else {"data": input_data.data}
        result_data["kaleidoscope_segments"] = segments
        result_data["kaleidoscope_rotation"] = rotation

        return NodeOutput(
            data=result_data,
            data_type=DataType.TEXTURE,
            metadata={**input_data.metadata, "kaleidoscope": True}
        )
