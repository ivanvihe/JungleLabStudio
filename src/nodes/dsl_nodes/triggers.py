"""Trigger and animation nodes for controlling parameters"""

import numpy as np
from typing import Any

from nodes.base import TriggerNode, NodeOutput, DataType
from nodes.registry import register_node
from presets.base import PresetState


@register_node("audio_trigger")
class AudioTriggerNode(TriggerNode):
    """Trigger based on audio input"""

    def _setup_ports(self):
        self.add_input("band", DataType.NUMBER, required=False, default=0)  # 0=bass, 1=mid, 2=high
        self.add_input("threshold", DataType.NUMBER, required=False, default=0.5)
        self.add_output("output", DataType.NUMBER)

    def evaluate(self, state: PresetState) -> float:
        band_idx = int(self.get_param("band", 0))
        threshold = self.get_param("threshold", 0.5)

        # Get audio value
        if band_idx == 0:
            value = state.bass
        elif band_idx == 1:
            value = state.mid
        else:
            value = state.high

        # Apply threshold
        if value >= threshold:
            return (value - threshold) / (1.0 - threshold)
        return 0.0

    def execute(self, state: PresetState) -> NodeOutput:
        value = self.evaluate(state)
        return NodeOutput(
            data=value,
            data_type=DataType.NUMBER,
            metadata={"trigger": "audio"}
        )


@register_node("midi_trigger")
class MidiTriggerNode(TriggerNode):
    """Trigger based on MIDI input"""

    def __init__(self, node_id: str, params: dict = None):
        super().__init__(node_id, params)
        self.last_value = 0.0

    def _setup_ports(self):
        self.add_input("note", DataType.NUMBER, required=False, default=60)
        self.add_input("channel", DataType.NUMBER, required=False, default=0)
        self.add_output("output", DataType.NUMBER)

    def evaluate(self, state: PresetState) -> float:
        # This would interface with MIDI system
        # For now, return stored value
        return self.last_value

    def execute(self, state: PresetState) -> NodeOutput:
        value = self.evaluate(state)
        return NodeOutput(
            data=value,
            data_type=DataType.NUMBER,
            metadata={"trigger": "midi"}
        )


@register_node("timer")
class TimerNode(TriggerNode):
    """Timer-based trigger"""

    def _setup_ports(self):
        self.add_input("frequency", DataType.NUMBER, required=False, default=1.0)
        self.add_input("phase", DataType.NUMBER, required=False, default=0.0)
        self.add_output("output", DataType.NUMBER)

    def evaluate(self, state: PresetState) -> float:
        frequency = self.get_param("frequency", 1.0)
        phase = self.get_param("phase", 0.0)

        # Generate oscillating value
        value = np.sin(state.time * frequency * 2.0 * np.pi + phase)
        return (value + 1.0) / 2.0  # Normalize to 0-1

    def execute(self, state: PresetState) -> NodeOutput:
        value = self.evaluate(state)
        return NodeOutput(
            data=value,
            data_type=DataType.NUMBER,
            metadata={"trigger": "timer"}
        )


@register_node("lfo")
class LFONode(TriggerNode):
    """Low Frequency Oscillator"""

    def _setup_ports(self):
        self.add_input("frequency", DataType.NUMBER, required=False, default=1.0)
        self.add_input("phase", DataType.NUMBER, required=False, default=0.0)
        self.add_input("waveform", DataType.NUMBER, required=False, default=0)  # 0=sine, 1=square, 2=saw, 3=triangle
        self.add_output("output", DataType.NUMBER)

    def evaluate(self, state: PresetState) -> float:
        frequency = self.get_param("frequency", 1.0)
        phase = self.get_param("phase", 0.0)
        waveform = int(self.get_param("waveform", 0))

        t = (state.time * frequency + phase) % 1.0

        if waveform == 0:  # Sine
            return (np.sin(t * 2.0 * np.pi) + 1.0) / 2.0
        elif waveform == 1:  # Square
            return 1.0 if t < 0.5 else 0.0
        elif waveform == 2:  # Saw
            return t
        else:  # Triangle
            return 1.0 - abs(t * 2.0 - 1.0)

    def execute(self, state: PresetState) -> NodeOutput:
        value = self.evaluate(state)
        return NodeOutput(
            data=value,
            data_type=DataType.NUMBER,
            metadata={"trigger": "lfo"}
        )


@register_node("envelope")
class EnvelopeNode(TriggerNode):
    """ADSR Envelope"""

    def __init__(self, node_id: str, params: dict = None):
        super().__init__(node_id, params)
        self.trigger_time = 0.0
        self.is_triggered = False

    def _setup_ports(self):
        self.add_input("trigger", DataType.NUMBER, required=False, default=0.0)
        self.add_input("attack", DataType.NUMBER, required=False, default=0.1)
        self.add_input("decay", DataType.NUMBER, required=False, default=0.2)
        self.add_input("sustain", DataType.NUMBER, required=False, default=0.7)
        self.add_input("release", DataType.NUMBER, required=False, default=0.3)
        self.add_output("output", DataType.NUMBER)

    def evaluate(self, state: PresetState) -> float:
        trigger = self.get_param("trigger", 0.0)
        attack = self.get_param("attack", 0.1)
        decay = self.get_param("decay", 0.2)
        sustain = self.get_param("sustain", 0.7)
        release = self.get_param("release", 0.3)

        # Check for trigger
        if trigger > 0.5 and not self.is_triggered:
            self.is_triggered = True
            self.trigger_time = state.time
        elif trigger < 0.5 and self.is_triggered:
            self.is_triggered = False

        if not self.is_triggered and self.trigger_time == 0.0:
            return 0.0

        elapsed = state.time - self.trigger_time

        if self.is_triggered:
            # Attack phase
            if elapsed < attack:
                return elapsed / attack
            # Decay phase
            elif elapsed < attack + decay:
                t = (elapsed - attack) / decay
                return 1.0 - t * (1.0 - sustain)
            # Sustain phase
            else:
                return sustain
        else:
            # Release phase
            release_start = state.time - self.trigger_time
            if elapsed < release:
                return sustain * (1.0 - elapsed / release)
            else:
                return 0.0

    def execute(self, state: PresetState) -> NodeOutput:
        value = self.evaluate(state)
        return NodeOutput(
            data=value,
            data_type=DataType.NUMBER,
            metadata={"trigger": "envelope"}
        )


@register_node("random")
class RandomNode(TriggerNode):
    """Random value generator"""

    def __init__(self, node_id: str, params: dict = None):
        super().__init__(node_id, params)
        self.last_value = np.random.rand()
        self.last_change_time = 0.0

    def _setup_ports(self):
        self.add_input("frequency", DataType.NUMBER, required=False, default=1.0)
        self.add_input("min", DataType.NUMBER, required=False, default=0.0)
        self.add_input("max", DataType.NUMBER, required=False, default=1.0)
        self.add_output("output", DataType.NUMBER)

    def evaluate(self, state: PresetState) -> float:
        frequency = self.get_param("frequency", 1.0)
        min_val = self.get_param("min", 0.0)
        max_val = self.get_param("max", 1.0)

        # Change value at specified frequency
        if state.time - self.last_change_time >= 1.0 / frequency:
            self.last_value = np.random.rand()
            self.last_change_time = state.time

        return min_val + self.last_value * (max_val - min_val)

    def execute(self, state: PresetState) -> NodeOutput:
        value = self.evaluate(state)
        return NodeOutput(
            data=value,
            data_type=DataType.NUMBER,
            metadata={"trigger": "random"}
        )
