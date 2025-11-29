import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional, List, Union, Tuple, Any

import moderngl
import numpy as np

# --- Parameter System ---

@dataclass
class AudioModulation:
    """Configuration for audio-reactive parameter modulation"""
    band: int = 0  # Which FFT band to use (0=bass, 1=mids, 2=highs)
    min_value: float = 0.0  # Min output value
    max_value: float = 1.0  # Max output value
    smoothing: float = 0.5  # Smoothing factor (0=instant, 1=very smooth)

    _smoothed_value: float = 0.0

    def update(self, fft_bands: List[float], dt: float) -> float:
        """Update and return modulated value based on FFT band"""
        if not fft_bands or self.band >= len(fft_bands):
            return 0.0

        # Get raw FFT value for this band (0.0-1.0)
        raw_value = fft_bands[self.band]

        # Apply smoothing
        alpha = 1.0 - self.smoothing
        self._smoothed_value += (raw_value - self._smoothed_value) * alpha

        # Map to output range
        return self.min_value + self._smoothed_value * (self.max_value - self.min_value)

class Parameter:
    """
    A value that can be controlled by static config, LFOs, MIDI, or Audio.
    Supports float, vec2, vec3, vec4, color types.
    """
    def __init__(self, name: str, value: Union[float, List[float]] = 0.0,
                 min_val: Union[float, List[float]] = 0.0,
                 max_val: Union[float, List[float]] = 1.0):
        self.name = name
        self.base_value = value if isinstance(value, (list, tuple)) else float(value)
        self.min_val = min_val if isinstance(min_val, (list, tuple)) else float(min_val)
        self.max_val = max_val if isinstance(max_val, (list, tuple)) else float(max_val)

        # Modifiers (always scalar for simplicity, applied uniformly to vectors)
        self.midi_offset = 0.0
        self.lfo_offset = 0.0
        self.audio_offset = 0.0

        # Audio modulation config
        self.audio_mod: Optional['AudioModulation'] = None

    @property
    def value(self) -> Union[float, List[float]]:
        """Get final value with modifiers applied"""
        if isinstance(self.base_value, (list, tuple)):
            # Vector parameter - apply offsets uniformly
            offset = self.midi_offset + self.lfo_offset + self.audio_offset
            result = [v + offset for v in self.base_value]
            # Clamp each component
            if isinstance(self.min_val, (list, tuple)):
                result = [max(mn, min(mx, v)) for v, mn, mx in zip(result, self.min_val, self.max_val)]
            else:
                result = [max(self.min_val, min(self.max_val, v)) for v in result]
            return result
        else:
            # Scalar parameter
            val = self.base_value + self.midi_offset + self.lfo_offset + self.audio_offset
            return max(self.min_val, min(self.max_val, val))

    def update(self, val: Union[float, List[float]]):
        """Direct update from logic"""
        self.base_value = val

    def set_midi_value(self, normalized: float):
        """Set from MIDI (0.0-1.0)"""
        if isinstance(self.base_value, (list, tuple)):
            # For vectors, offset is applied uniformly
            self.midi_offset = normalized * 0.5 - 0.25  # Small offset range
        else:
            # Map MIDI 0-1 to parameter range
            self.midi_offset = (self.max_val - self.min_val) * normalized + self.min_val - self.base_value

# --- Animation Modifiers ---

@dataclass
class LFO:
    """Low-Frequency Oscillator for parameter animation"""
    type: str = "sine"  # sine, triangle, square, noise, random_walk
    freq: float = 1.0
    amp: float = 1.0
    phase: float = 0.0

    # Random walk state
    _walk_value: float = 0.0
    _walk_target: float = 0.0
    _walk_timer: float = 0.0

    def update(self, dt: float) -> float:
        """Update and return current value"""
        self.phase += dt * self.freq

        if self.type == "sine":
            return math.sin(self.phase * 6.283185307) * self.amp
        elif self.type == "triangle":
            t = (self.phase % 1.0)
            return (abs(t - 0.5) * 4.0 - 1.0) * self.amp
        elif self.type == "square":
            return (1.0 if (self.phase % 1.0) < 0.5 else -1.0) * self.amp
        elif self.type == "noise":
            # Per-frame noise (fast flickering)
            return (random.random() * 2.0 - 1.0) * self.amp
        elif self.type == "random_walk":
            # Smooth random walk
            self._walk_timer -= dt
            if self._walk_timer <= 0.0:
                self._walk_target = (random.random() * 2.0 - 1.0) * self.amp
                self._walk_timer = 1.0 / max(self.freq, 0.01)
            # Interpolate towards target
            alpha = dt * self.freq * 2.0
            self._walk_value += (self._walk_target - self._walk_value) * min(alpha, 1.0)
            return self._walk_value

        return 0.0

@dataclass
class Envelope:
    """ADSR Envelope for triggered parameter animation"""
    attack: float = 0.1
    decay: float = 0.2
    sustain: float = 0.7
    release: float = 0.3

    _time: float = 0.0
    _state: str = "idle"  # idle, attack, decay, sustain, release
    _value: float = 0.0

    def trigger(self):
        """Trigger the envelope"""
        self._state = "attack"
        self._time = 0.0

    def release_trigger(self):
        """Release the envelope"""
        if self._state in ("attack", "decay", "sustain"):
            self._state = "release"
            self._time = 0.0

    def update(self, dt: float) -> float:
        """Update and return current value (0.0-1.0)"""
        self._time += dt

        if self._state == "attack":
            if self._time >= self.attack:
                self._state = "decay"
                self._time = 0.0
                self._value = 1.0
            else:
                self._value = self._time / self.attack

        elif self._state == "decay":
            if self._time >= self.decay:
                self._state = "sustain"
                self._time = 0.0
                self._value = self.sustain
            else:
                self._value = 1.0 - (1.0 - self.sustain) * (self._time / self.decay)

        elif self._state == "sustain":
            self._value = self.sustain

        elif self._state == "release":
            if self._time >= self.release:
                self._state = "idle"
                self._value = 0.0
            else:
                self._value = self.sustain * (1.0 - self._time / self.release)

        else:  # idle
            self._value = 0.0

        return self._value

# --- Base Node ---

class RenderNode(ABC):
    """
    Base class for all graph nodes.
    Each node renders to its own FBO and can take inputs from other nodes.
    """
    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        self.ctx = ctx
        self.id = node_id
        self.resolution = resolution

        # FBO for this node (Output texture)
        self.texture = self.ctx.texture(resolution, 4, dtype="f1")
        self.texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.texture.repeat_x = False
        self.texture.repeat_y = False
        self.fbo = self.ctx.framebuffer(color_attachments=[self.texture])

        # Inputs (Keys are input slot names, Values are RenderNode objects)
        self.input_nodes: Dict[str, 'RenderNode'] = {}

        # Parameters (float, vec2, vec3, vec4, color)
        self.params: Dict[str, Parameter] = {}

        # Animators (LFOs, Envelopes)
        self.animators: Dict[str, LFO] = {}
        self.envelopes: Dict[str, Envelope] = {}

        # Shared fullscreen quad VBO (pos_x, pos_y, uv_x, uv_y)
        self.quad_vbo = self.ctx.buffer(np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype="f4").tobytes())

        # Time accumulator
        self.time = 0.0

    def add_param(self, name: str, value: Union[float, List[float]],
                  min_v: Union[float, List[float]] = 0.0,
                  max_v: Union[float, List[float]] = 1.0):
        """Add a parameter to this node"""
        self.params[name] = Parameter(name, value, min_v, max_v)

    def add_input(self, slot_name: str):
        """Add an input slot to this node"""
        # Input slots are stored in input_nodes dict, initialized to None
        if slot_name not in self.input_nodes:
            self.input_nodes[slot_name] = None

    def set_input(self, slot_name: str, node: 'RenderNode'):
        """Connect an input node to this node"""
        self.input_nodes[slot_name] = node

    def get_input(self, slot_name: str) -> Optional['RenderNode']:
        """Get connected input node"""
        return self.input_nodes.get(slot_name)

    def get_input_texture(self, slot_name: str, default=None) -> Optional[moderngl.Texture]:
        """Get input texture from connected node"""
        node = self.input_nodes.get(slot_name)
        return node.get_texture() if node else default

    def update(self, dt: float, fft_bands: Optional[List[float]] = None):
        """Update logic, animations, and parameters"""
        self.time += dt

        # Update LFO Animators
        for param_name, lfo in self.animators.items():
            if param_name in self.params:
                offset = lfo.update(dt)
                self.params[param_name].lfo_offset = offset

        # Update Envelopes
        for param_name, env in self.envelopes.items():
            if param_name in self.params:
                offset = env.update(dt)
                self.params[param_name].lfo_offset = offset

        # Update Audio Modulations
        if fft_bands:
            for param_name, param in self.params.items():
                if param.audio_mod:
                    modulated_value = param.audio_mod.update(fft_bands, dt)
                    # Calculate offset from base value
                    param.audio_offset = modulated_value - param.base_value if isinstance(param.base_value, (int, float)) else 0.0

    @abstractmethod
    def render(self):
        """Execute rendering to self.fbo"""
        pass

    def get_texture(self) -> moderngl.Texture:
        """Get output texture"""
        return self.texture

    def get_param_value(self, name: str, default: Any = 0.0) -> Any:
        """Get parameter value with fallback"""
        return self.params[name].value if name in self.params else default


# --- Specialized Node Base Classes ---

class GeneratorNode(RenderNode):
    """
    Base class for generator nodes.
    Generators create imagery from scratch (no inputs required).
    """
    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)


class EffectNode(RenderNode):
    """
    Base class for effect nodes.
    Effects process one or more input textures.
    """
    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

    def has_input(self) -> bool:
        """Check if node has at least one input"""
        return len(self.input_nodes) > 0


class CompositeNode(RenderNode):
    """
    Base class for composite nodes.
    Compositors blend/mix multiple inputs.
    """
    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)


class OutputNode(RenderNode):
    """
    Base class for output nodes.
    Output nodes are terminal nodes (final render targets).
    """
    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)
