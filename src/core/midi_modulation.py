"""
MIDI Modulation System
Handles modulation of node parameters via MIDI
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass


@dataclass
class ParameterModulation:
    """Defines how a parameter is modulated by a launcher"""
    launcher_id: str  # ID of the launcher node
    parameter_path: str  # Path to the parameter (e.g., "scale", "color.r")
    scale: float = 1.0  # Scale factor
    offset: float = 0.0  # Offset value
    curve_type: str = "linear"  # Curve type: linear, exponential, logarithmic
    invert: bool = False  # Invert the modulation


class MIDIModulationManager:
    """
    Manages MIDI modulation mappings for the entire graph

    This class tracks which launchers modulate which parameters
    on which nodes, and provides the interface to apply modulation.
    """

    def __init__(self):
        # node_id -> [ParameterModulation]
        self.modulations: Dict[str, List[ParameterModulation]] = {}

        # launcher_id -> current_value
        self.launcher_values: Dict[str, float] = {}

        # Callbacks for when modulation changes
        self.modulation_callbacks: List[Callable[[str, str, float], None]] = []

    def add_modulation(self, node_id: str, modulation: ParameterModulation):
        """Add a modulation mapping"""
        if node_id not in self.modulations:
            self.modulations[node_id] = []

        # Check if this modulation already exists
        for existing in self.modulations[node_id]:
            if (existing.launcher_id == modulation.launcher_id and
                existing.parameter_path == modulation.parameter_path):
                # Update existing modulation
                existing.scale = modulation.scale
                existing.offset = modulation.offset
                existing.curve_type = modulation.curve_type
                existing.invert = modulation.invert
                return

        # Add new modulation
        self.modulations[node_id].append(modulation)

    def remove_modulation(self, node_id: str, launcher_id: str, parameter_path: str):
        """Remove a specific modulation mapping"""
        if node_id in self.modulations:
            self.modulations[node_id] = [
                mod for mod in self.modulations[node_id]
                if not (mod.launcher_id == launcher_id and
                       mod.parameter_path == parameter_path)
            ]

    def update_launcher_value(self, launcher_id: str, value: float):
        """Update the current value of a launcher"""
        self.launcher_values[launcher_id] = value

        # Trigger callbacks
        for callback in self.modulation_callbacks:
            callback(launcher_id, "value_changed", value)

    def get_modulated_value(self, node_id: str, parameter_path: str, base_value: float) -> float:
        """
        Get the modulated value for a parameter

        Args:
            node_id: ID of the node
            parameter_path: Path to the parameter
            base_value: The base/original value of the parameter

        Returns:
            The modulated value
        """
        if node_id not in self.modulations:
            return base_value

        # Find all modulations for this parameter
        applicable_mods = [
            mod for mod in self.modulations[node_id]
            if mod.parameter_path == parameter_path
        ]

        if not applicable_mods:
            return base_value

        # Apply modulations (additive for now, could be multiplicative or other modes)
        modulated_value = base_value

        for mod in applicable_mods:
            launcher_value = self.launcher_values.get(mod.launcher_id, 0.0)

            # Apply curve
            launcher_value = self._apply_curve(launcher_value, mod.curve_type)

            # Apply inversion
            if mod.invert:
                launcher_value = 1.0 - launcher_value

            # Apply scale and offset
            modulation_amount = launcher_value * mod.scale + mod.offset

            # Add to base value
            modulated_value += modulation_amount

        return modulated_value

    def _apply_curve(self, value: float, curve_type: str) -> float:
        """Apply a curve to a value"""
        if curve_type == "exponential":
            return value * value
        elif curve_type == "logarithmic":
            return pow(value, 0.5) if value >= 0 else 0.0
        elif curve_type == "smooth_step":
            return value * value * (3.0 - 2.0 * value)
        else:  # linear
            return value

    def get_modulations_for_node(self, node_id: str) -> List[ParameterModulation]:
        """Get all modulations for a specific node"""
        return self.modulations.get(node_id, [])

    def get_modulations_for_launcher(self, launcher_id: str) -> Dict[str, List[ParameterModulation]]:
        """Get all modulations controlled by a specific launcher"""
        result = {}
        for node_id, mods in self.modulations.items():
            launcher_mods = [mod for mod in mods if mod.launcher_id == launcher_id]
            if launcher_mods:
                result[node_id] = launcher_mods
        return result

    def clear_all_modulations(self):
        """Clear all modulation mappings"""
        self.modulations.clear()
        self.launcher_values.clear()

    def clear_modulations_for_node(self, node_id: str):
        """Clear all modulations for a specific node"""
        if node_id in self.modulations:
            del self.modulations[node_id]

    def clear_modulations_for_launcher(self, launcher_id: str):
        """Clear all modulations controlled by a specific launcher"""
        for node_id in list(self.modulations.keys()):
            self.modulations[node_id] = [
                mod for mod in self.modulations[node_id]
                if mod.launcher_id != launcher_id
            ]
            # Remove empty lists
            if not self.modulations[node_id]:
                del self.modulations[node_id]

    def register_callback(self, callback: Callable[[str, str, float], None]):
        """Register a callback for modulation changes"""
        if callback not in self.modulation_callbacks:
            self.modulation_callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[str, str, float], None]):
        """Unregister a callback"""
        if callback in self.modulation_callbacks:
            self.modulation_callbacks.remove(callback)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'modulations': {
                node_id: [
                    {
                        'launcher_id': mod.launcher_id,
                        'parameter_path': mod.parameter_path,
                        'scale': mod.scale,
                        'offset': mod.offset,
                        'curve_type': mod.curve_type,
                        'invert': mod.invert
                    }
                    for mod in mods
                ]
                for node_id, mods in self.modulations.items()
            }
        }

    def from_dict(self, data: Dict[str, Any]):
        """Deserialize from dictionary"""
        self.modulations.clear()

        if 'modulations' in data:
            for node_id, mods_data in data['modulations'].items():
                self.modulations[node_id] = [
                    ParameterModulation(
                        launcher_id=mod_data['launcher_id'],
                        parameter_path=mod_data['parameter_path'],
                        scale=mod_data.get('scale', 1.0),
                        offset=mod_data.get('offset', 0.0),
                        curve_type=mod_data.get('curve_type', 'linear'),
                        invert=mod_data.get('invert', False)
                    )
                    for mod_data in mods_data
                ]


# Global modulation manager instance
_midi_modulation_manager: Optional[MIDIModulationManager] = None


def get_midi_modulation_manager() -> MIDIModulationManager:
    """Get the global MIDI modulation manager"""
    global _midi_modulation_manager
    if _midi_modulation_manager is None:
        _midi_modulation_manager = MIDIModulationManager()
    return _midi_modulation_manager
