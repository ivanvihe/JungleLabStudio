"""
Preset system for JungleLabStudio

This module provides the base classes and registry for visual presets.
All presets are now defined using YAML DSL format in the ./presets/ directory.
"""

from presets.base import VisualPreset, PresetState
from presets.media_player import MediaPreset
from presets.graph_preset import GraphPreset

# Empty registry - presets are now loaded from YAML files
PRESET_REGISTRY = {}

__all__ = [
    "VisualPreset",
    "PresetState",
    "PRESET_REGISTRY",
    "MediaPreset",
    "GraphPreset",
]
