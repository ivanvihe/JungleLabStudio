"""Visual node representation"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid

class NodeCategory(Enum):
    GENERATOR = "generator"
    MODIFIER = "modifier"
    VFX = "vfx"
    ANIMATION = "animation"
    TRIGGER = "trigger"
    ROUTING = "routing"
    OUTPUT = "output"

@dataclass
class Vector2:
    x: float
    y: float

    def __add__(self, other): return Vector2(self.x + other.x, self.y + other.y)
    def __sub__(self, other): return Vector2(self.x - other.x, self.y - other.y)
    def __mul__(self, scalar): return Vector2(self.x * scalar, self.y * scalar)

@dataclass
class Color:
    r: float
    g: float
    b: float
    a: float = 1.0

    def as_tuple(self): return (self.r, self.g, self.b, self.a)

@dataclass
class InputPort:
    name: str
    data_type: str
    required: bool = True
    connected: bool = False

@dataclass
class OutputPort:
    name: str
    data_type: str

@dataclass
class AnimationBlock:
    """Animation definition for a parameter"""
    id: str
    target_param: str
    animation_type: str  # lfo, envelope, noise_walk, keyframe

    # LFO
    lfo_frequency: float = 1.0
    lfo_waveform: str = "sine"  # sine, square, saw, triangle
    lfo_amplitude: float = 1.0
    lfo_offset: float = 0.0
    lfo_phase: float = 0.0

    # Envelope (ADSR)
    envelope_attack: float = 0.1
    envelope_decay: float = 0.2
    envelope_sustain: float = 0.7
    envelope_release: float = 0.3
    envelope_triggered: bool = False
    envelope_trigger_time: float = 0.0

    # Noise walk
    noise_scale: float = 1.0
    noise_speed: float = 0.5
    noise_octaves: int = 3

    # Keyframes
    keyframes: List[Dict[str, Any]] = field(default_factory=list)

    # State
    is_active: bool = True
    current_value: float = 0.0

@dataclass
class TriggerBinding:
    """Trigger action binding"""
    id: str
    trigger_type: str  # midi_note, midi_cc, fft_band, timer, bpm_sync
    action_mode: str  # trigger, set, impulse, animate
    target_param: str

    # MIDI
    midi_note: Optional[int] = None
    midi_cc: Optional[int] = None
    midi_channel: int = 1
    midi_velocity_min: int = 0
    midi_velocity_max: int = 127

    # Audio
    fft_band: Optional[str] = None  # bass, mid, high
    fft_threshold: float = 0.5

    # Timer
    timer_interval: Optional[float] = None
    timer_last_trigger: float = 0.0

    # BPM
    bpm_multiple: Optional[float] = None  # 1.0 = every beat, 0.5 = every half beat

    # Action
    action_value: Any = None
    action_duration: float = 1.0

    # Impulse
    impulse_amount: float = 1.0
    impulse_decay: float = 2.0
    impulse_current: float = 0.0

@dataclass
class VisualNode:
    """Complete visual node representation"""
    id: str
    node_type: str
    category: NodeCategory

    # Visual properties
    position: Vector2
    size: Vector2 = field(default_factory=lambda: Vector2(120, 80))
    color: Color = field(default_factory=lambda: Color(0.3, 0.3, 0.3, 1.0))

    # Ports
    inputs: List[InputPort] = field(default_factory=list)
    outputs: List[OutputPort] = field(default_factory=list)

    # Data
    params: Dict[str, Any] = field(default_factory=dict)
    animations: List[AnimationBlock] = field(default_factory=list)
    triggers: List[TriggerBinding] = field(default_factory=list)

    # State
    selected: bool = False
    hovered: bool = False
    thumbnail: Optional[Any] = None  # Texture for preview

    # Metadata
    display_name: str = ""
    description: str = ""

    def __post_init__(self):
        if not self.display_name:
            self.display_name = self.node_type.replace("_", " ").title()

    def get_bounds(self) -> tuple:
        """Get node bounds (x, y, width, height)"""
        return (self.position.x, self.position.y, self.size.x, self.size.y)

    def contains_point(self, point: Vector2) -> bool:
        """Check if point is inside node"""
        x, y, w, h = self.get_bounds()
        return x <= point.x <= x + w and y <= point.y <= y + h

    def get_input_port_position(self, port_name: str) -> Vector2:
        """Get world position of input port"""
        idx = next((i for i, p in enumerate(self.inputs) if p.name == port_name), 0)
        port_y = self.position.y + 30 + idx * 20
        return Vector2(self.position.x, port_y)

    def get_output_port_position(self, port_name: str) -> Vector2:
        """Get world position of output port"""
        idx = next((i for i, p in enumerate(self.outputs) if p.name == port_name), 0)
        port_y = self.position.y + 30 + idx * 20
        return Vector2(self.position.x + self.size.x, port_y)

def create_node(node_type: str, position: Vector2, custom_id: Optional[str] = None) -> VisualNode:
    """Factory function to create nodes with proper configuration"""
    from core.graph.registry import NodeRegistry

    node_id = custom_id if custom_id else f"{node_type}_{uuid.uuid4().hex[:8]}"

    # Static configuration for known node types
    # This avoids needing to instantiate RenderNodes which require ctx
    node_configs = {
        # Generators
        "shader": {
            "category": NodeCategory.GENERATOR,
            "inputs": [InputPort("texture", "texture"), InputPort("ctrl", "data", required=False)],
            "outputs": [OutputPort("output", "texture")]
        },
        "particles": {
            "category": NodeCategory.GENERATOR,
            "inputs": [InputPort("ctrl", "data", required=False)],
            "outputs": [OutputPort("output", "texture")]
        },
        "video": {
            "category": NodeCategory.GENERATOR,
            "inputs": [InputPort("ctrl", "data", required=False)],
            "outputs": [OutputPort("output", "texture")]
        },
        "geometry": {
            "category": NodeCategory.GENERATOR,
            "inputs": [InputPort("ctrl", "data", required=False)],
            "outputs": [OutputPort("output", "texture")]
        },

        # Effects
        "effect.distort": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "effect.blur": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "effect.color": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "effect.feedback": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "effect.kaleidoscope": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "effect.mirror": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "effect.glow": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "effect.vignette": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "effect.color_gradient": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "effect.advanced_bloom": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "effect.pixelate": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "effect.edge_detect": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "effect.posterize": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "effect.transform": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },

        # VFX / Glitch Effects
        "vfx.glitch.vhs": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "vfx.glitch.rgb": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "vfx.glitch.scanlines": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "vfx.glitch.noise": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "vfx.glitch.blocks": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "vfx.glitch.displacement": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "vfx.crt": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "vfx.datamosh": {
            "category": NodeCategory.VFX,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },

        # Generators (additional)
        "shadertoy": {
            "category": NodeCategory.GENERATOR,
            "inputs": [],
            "outputs": [OutputPort("output", "texture")]
        },
        "generator.noise": {
            "category": NodeCategory.GENERATOR,
            "inputs": [],
            "outputs": [OutputPort("output", "texture")]
        },
        "generator.checkerboard": {
            "category": NodeCategory.GENERATOR,
            "inputs": [],
            "outputs": [OutputPort("output", "texture")]
        },

        # MIDI
        "midi.listener": {
            "category": NodeCategory.TRIGGER,
            "inputs": [],
            "outputs": [OutputPort("value", "data")]
        },
        "midi.launcher": {
            "category": NodeCategory.TRIGGER,
            "inputs": [InputPort("midi_value", "data")],
            "outputs": [OutputPort("value", "data")]
        },

        # Compositing
        "composite": {
            "category": NodeCategory.ROUTING,
            "inputs": [InputPort("input0", "texture"), InputPort("input1", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "blend": {
            "category": NodeCategory.ROUTING,
            "inputs": [InputPort("input0", "texture"), InputPort("input1", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "math.operation": {
            "category": NodeCategory.MODIFIER,
            "inputs": [InputPort("input0", "texture"), InputPort("input1", "texture", required=False)],
            "outputs": [OutputPort("output", "texture")]
        },
        "mask": {
            "category": NodeCategory.ROUTING,
            "inputs": [InputPort("input0", "texture"), InputPort("mask", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "utility.buffer": {
            "category": NodeCategory.ROUTING,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },

        # Output
        "output": {
            "category": NodeCategory.OUTPUT,
            "inputs": [InputPort("input0", "texture")],
            "outputs": [OutputPort("output", "texture")]
        },
        "preview": {
            "category": NodeCategory.OUTPUT,
            "inputs": [InputPort("input0", "texture")],
            "outputs": []
        },
        "init": {
            "category": NodeCategory.ROUTING,
            "inputs": [],
            "outputs": [OutputPort("config", "data")]
        }
    }

    # Use config if available, otherwise use defaults
    if node_type in node_configs:
        config = node_configs[node_type]
        category = config["category"]
        inputs = config["inputs"]
        outputs = config["outputs"]
    else:
        # Default configuration for unknown types
        category = NodeCategory.GENERATOR
        inputs = []
        outputs = [OutputPort(name="output", data_type="texture")]

    # Category colors
    colors = {
        NodeCategory.GENERATOR: Color(0.2, 0.6, 1.0, 1.0),
        NodeCategory.MODIFIER: Color(0.3, 0.8, 0.3, 1.0),
        NodeCategory.VFX: Color(0.9, 0.5, 0.2, 1.0),
        NodeCategory.ANIMATION: Color(0.8, 0.3, 0.8, 1.0),
        NodeCategory.TRIGGER: Color(1.0, 0.8, 0.2, 1.0),
        NodeCategory.ROUTING: Color(0.7, 0.7, 0.7, 1.0),
        NodeCategory.OUTPUT: Color(1.0, 0.3, 0.3, 1.0),
    }
    
    node = VisualNode(
        id=node_id,
        node_type=node_type,
        category=category,
        position=position,
        color=colors.get(category, Color(0.5, 0.5, 0.5, 1.0)),
        inputs=inputs,
        outputs=outputs
    )
    
    if node_type == "init":
        node.params["aspect_ratio"] = "horizontal"
        node.params["project_name"] = "New Project"
        
    return node
