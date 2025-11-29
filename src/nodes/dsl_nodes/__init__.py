"""DSL node implementations for YAML-based presets"""

# Import all DSL nodes to register them
from nodes.dsl_nodes.generators import (
    CircleNode,
    RectNode,
    LineNode,
    ParticlesNode,
    NoiseFieldNode,
    GridNode,
)

from nodes.dsl_nodes.modifiers import (
    TransformNode,
    DisplaceNode,
    RepeatNode,
    ColorNode,
    TwistNode,
)

from nodes.dsl_nodes.vfx import (
    GlowNode,
    BlurNode,
    FeedbackNode,
    TrailNode,
    ChromaticAberrationNode,
    PixelateNode,
    KaleidoscopeNode,
)

from nodes.dsl_nodes.triggers import (
    AudioTriggerNode,
    MidiTriggerNode,
    TimerNode,
    LFONode,
    EnvelopeNode,
    RandomNode,
)

__all__ = [
    # Generators
    "CircleNode",
    "RectNode",
    "LineNode",
    "ParticlesNode",
    "NoiseFieldNode",
    "GridNode",
    # Modifiers
    "TransformNode",
    "DisplaceNode",
    "RepeatNode",
    "ColorNode",
    "TwistNode",
    # VFX
    "GlowNode",
    "BlurNode",
    "FeedbackNode",
    "TrailNode",
    "ChromaticAberrationNode",
    "PixelateNode",
    "KaleidoscopeNode",
    # Triggers
    "AudioTriggerNode",
    "MidiTriggerNode",
    "TimerNode",
    "LFONode",
    "EnvelopeNode",
    "RandomNode",
]
