"""
Node Package
Auto-registers all node types with the NodeRegistry.
"""

# Import all node modules here to trigger registration
# Generators
from nodes.generators.shader_node import ShaderNode as ShaderGenNode
from nodes.generators.noise_node import NoiseNode
from nodes.generators.checkerboard_node import CheckerboardNode

# Effects
from nodes.blur_node import BlurNode
from nodes.feedback_node import FeedbackNode
from nodes.kaleidoscope_node import KaleidoscopeNode
from nodes.mirror_node import MirrorNode
from nodes.color_adjust_node import ColorAdjustNode
from nodes.glow_node import GlowNode
from nodes.vignette_node import VignetteNode
from nodes.color_gradient_node import ColorGradientNode
# New effects
from nodes.pixelate_node import PixelateNode
from nodes.edge_detect_node import EdgeDetectNode
from nodes.posterize_node import PosterizeNode
from nodes.distort_node import DistortNode
from nodes.transform_node import TransformNode
from nodes.bloom_node import AdvancedBloomNode

# Compositing
from nodes.blend_node import BlendNode
from nodes.blend_modes_node import BlendModesNode
from nodes.math_nodes import MathNode

# Other
from nodes.buffer_node import BufferNode
from nodes.particles_node import ParticlesNode
from nodes.geometry_node import GeometryNode
from nodes.output_node import OutputNode
from nodes.preview_node import PreviewNode
from nodes.init_node import InitNode

# MIDI nodes
from nodes.midi.midi_listener_node import MIDIListenerNode
from nodes.midi.launcher_node import LauncherNode

# Shadertoy nodes
from nodes.shadertoy.shadertoy_node import ShadertoyNode

# VFX / Glitch nodes
from nodes.vfx.glitch_vhs_node import GlitchVHSNode
from nodes.vfx.glitch_rgb_node import GlitchRGBNode
from nodes.vfx.glitch_scanlines_node import GlitchScanlinesNode
from nodes.vfx.glitch_noise_node import GlitchNoiseNode
from nodes.vfx.glitch_blocks_node import GlitchBlocksNode
from nodes.vfx.glitch_displacement_node import GlitchDisplacementNode
from nodes.vfx.crt_node import CRTNode
from nodes.vfx.datamosh_node import DatamoshNode

# Try to import optional nodes
try:
    from nodes.input import VideoNode, ShaderNode as ShaderInputNode
    from nodes.composite import CompositeNode
    from nodes.effect import DistortNode as DistortEffectNode
except ImportError:
    pass

print(f"DEBUG: Nodes package loaded, registering nodes...")

__all__ = [
    # Generators
    'ShaderGenNode',
    'NoiseNode',
    'CheckerboardNode',
    # Effects
    'BlurNode',
    'FeedbackNode',
    'KaleidoscopeNode',
    'MirrorNode',
    'ColorAdjustNode',
    'GlowNode',
    'VignetteNode',
    'ColorGradientNode',
    'PixelateNode',
    'EdgeDetectNode',
    'PosterizeNode',
    'DistortNode',
    'TransformNode',
    'AdvancedBloomNode',
    # Compositing
    'BlendNode',
    'BlendModesNode',
    'MathNode',
    # Other
    'BufferNode',
    'ParticlesNode',
    'GeometryNode',
    'OutputNode',
    'PreviewNode',
    'InitNode',
    # MIDI
    'MIDIListenerNode',
    'LauncherNode',
    # Shadertoy
    'ShadertoyNode',
    # VFX / Glitch
    'GlitchVHSNode',
    'GlitchRGBNode',
    'GlitchScanlinesNode',
    'GlitchNoiseNode',
    'GlitchBlocksNode',
    'GlitchDisplacementNode',
    'CRTNode',
    'DatamoshNode',
]
