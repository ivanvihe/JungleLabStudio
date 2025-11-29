"""
MIDI Learn System - Interactive MIDI CC/Note to parameter binding
"""
from typing import Dict, Optional, Callable, List, Tuple
from dataclasses import dataclass
import mido


@dataclass
class MIDIBinding:
    """MIDI control to parameter binding"""
    node_id: str
    param_name: str
    midi_type: str  # "cc" or "note_on"
    midi_channel: int
    midi_number: int  # CC number or note number
    min_value: float = 0.0
    max_value: float = 1.0
    curve: str = "linear"  # linear, exponential, logarithmic
    smoothing: float = 0.0  # 0.0 = no smoothing, 1.0 = max smoothing

    # State
    current_value: float = 0.0
    target_value: float = 0.0


class MIDILearnSystem:
    """
    Manages MIDI Learn mode and parameter bindings
    """

    def __init__(self):
        self.bindings: Dict[str, MIDIBinding] = {}  # key: "{node_id}.{param_name}"
        self.learn_mode: bool = False
        self.learn_target: Optional[Tuple[str, str]] = None  # (node_id, param_name)
        self.learn_callback: Optional[Callable[[str, str, MIDIBinding], None]] = None
        self.last_midi_message: Optional[mido.Message] = None

    def start_learn(self, node_id: str, param_name: str, callback: Optional[Callable] = None):
        """
        Start MIDI Learn mode for a parameter

        Args:
            node_id: Target node ID
            param_name: Target parameter name
            callback: Called when binding is created
        """
        self.learn_mode = True
        self.learn_target = (node_id, param_name)
        self.learn_callback = callback
        print(f"MIDI Learn: Waiting for MIDI input for {node_id}.{param_name}...")

    def stop_learn(self):
        """Stop MIDI Learn mode"""
        self.learn_mode = False
        self.learn_target = None
        self.learn_callback = None
        print("MIDI Learn: Stopped")

    def process_midi_message(self, msg: mido.Message):
        """
        Process incoming MIDI message

        If in learn mode, creates binding.
        Otherwise, updates bound parameters.
        """
        self.last_midi_message = msg

        # Handle learn mode
        if self.learn_mode and self.learn_target:
            if msg.type == "control_change" or msg.type == "note_on":
                node_id, param_name = self.learn_target

                # Create binding
                binding = MIDIBinding(
                    node_id=node_id,
                    param_name=param_name,
                    midi_type="cc" if msg.type == "control_change" else "note_on",
                    midi_channel=msg.channel,
                    midi_number=msg.control if msg.type == "control_change" else msg.note
                )

                # Add binding
                key = f"{node_id}.{param_name}"
                self.bindings[key] = binding

                print(f"MIDI Learn: Bound {key} to {binding.midi_type} {binding.midi_number} on channel {binding.midi_channel}")

                # Callback
                if self.learn_callback:
                    self.learn_callback(node_id, param_name, binding)

                # Exit learn mode
                self.stop_learn()

            return

        # Handle normal operation - update bindings
        for binding in self.bindings.values():
            if self._message_matches_binding(msg, binding):
                # Extract value (0-127 for MIDI)
                if msg.type == "control_change":
                    midi_value = msg.value
                elif msg.type == "note_on":
                    midi_value = msg.velocity
                else:
                    continue

                # Normalize to 0-1
                normalized = midi_value / 127.0

                # Apply curve
                normalized = self._apply_curve(normalized, binding.curve)

                # Map to parameter range
                target_value = binding.min_value + (binding.max_value - binding.min_value) * normalized
                binding.target_value = target_value

    def _message_matches_binding(self, msg: mido.Message, binding: MIDIBinding) -> bool:
        """Check if MIDI message matches a binding"""
        if binding.midi_type == "cc":
            return (msg.type == "control_change" and
                    msg.channel == binding.midi_channel and
                    msg.control == binding.midi_number)
        elif binding.midi_type == "note_on":
            return (msg.type == "note_on" and
                    msg.channel == binding.midi_channel and
                    msg.note == binding.midi_number)
        return False

    def _apply_curve(self, value: float, curve: str) -> float:
        """Apply response curve to normalized value"""
        if curve == "exponential":
            return value ** 2
        elif curve == "logarithmic":
            return value ** 0.5
        else:  # linear
            return value

    def update(self, dt: float) -> Dict[str, Dict[str, float]]:
        """
        Update all bindings with smoothing

        Returns:
            Dict[node_id, Dict[param_name, value]]
        """
        param_values: Dict[str, Dict[str, float]] = {}

        for binding in self.bindings.values():
            # Apply smoothing
            if binding.smoothing > 0.0:
                alpha = 1.0 - binding.smoothing
                binding.current_value += (binding.target_value - binding.current_value) * alpha * dt * 10.0
            else:
                binding.current_value = binding.target_value

            # Build result
            if binding.node_id not in param_values:
                param_values[binding.node_id] = {}

            param_values[binding.node_id][binding.param_name] = binding.current_value

        return param_values

    def add_binding(self, node_id: str, param_name: str, binding: MIDIBinding):
        """Manually add a binding"""
        key = f"{node_id}.{param_name}"
        self.bindings[key] = binding

    def remove_binding(self, node_id: str, param_name: str):
        """Remove a binding"""
        key = f"{node_id}.{param_name}"
        if key in self.bindings:
            del self.bindings[key]

    def get_binding(self, node_id: str, param_name: str) -> Optional[MIDIBinding]:
        """Get binding for a parameter"""
        key = f"{node_id}.{param_name}"
        return self.bindings.get(key)

    def has_binding(self, node_id: str, param_name: str) -> bool:
        """Check if parameter has a binding"""
        key = f"{node_id}.{param_name}"
        return key in self.bindings

    def clear_bindings(self):
        """Clear all bindings"""
        self.bindings.clear()

    def get_bindings_for_node(self, node_id: str) -> List[MIDIBinding]:
        """Get all bindings for a node"""
        return [b for b in self.bindings.values() if b.node_id == node_id]

    def save_bindings(self) -> List[dict]:
        """Serialize bindings to dict format for YAML"""
        return [
            {
                "node_id": b.node_id,
                "param_name": b.param_name,
                "midi_type": b.midi_type,
                "midi_channel": b.midi_channel,
                "midi_number": b.midi_number,
                "min_value": b.min_value,
                "max_value": b.max_value,
                "curve": b.curve,
                "smoothing": b.smoothing
            }
            for b in self.bindings.values()
        ]

    def load_bindings(self, bindings_data: List[dict]):
        """Load bindings from dict format"""
        self.bindings.clear()

        for data in bindings_data:
            binding = MIDIBinding(
                node_id=data["node_id"],
                param_name=data["param_name"],
                midi_type=data["midi_type"],
                midi_channel=data["midi_channel"],
                midi_number=data["midi_number"],
                min_value=data.get("min_value", 0.0),
                max_value=data.get("max_value", 1.0),
                curve=data.get("curve", "linear"),
                smoothing=data.get("smoothing", 0.0)
            )

            key = f"{binding.node_id}.{binding.param_name}"
            self.bindings[key] = binding
