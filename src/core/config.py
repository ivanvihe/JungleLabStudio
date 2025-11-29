import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Optional

PREF_PATH = Path("prefs/preferences.json")


@dataclass
class Preferences:
    audio_device: Optional[str] = None
    midi_device: Optional[str] = None
    preset: str = "test_simple"  # Changed to a working preset
    orientation: str = "vertical"  # Changed default to vertical
    midi_trigger_note: Optional[int] = None
    midi_actions: Dict[str, int] = field(default_factory=dict)
    preset_action_map: Dict[str, Dict[str, int]] = field(default_factory=dict)
    fx_assignments: Dict[str, int] = field(default_factory=dict)
    midi_filters: Dict[str, Any] = field(default_factory=lambda: {"channel": None, "note": None})
    params: Dict[str, Any] = field(default_factory=dict)
    resolution: Optional[list] = None  # [width, height]


def load_preferences() -> Preferences:
    if PREF_PATH.exists():
        try:
            data = json.loads(PREF_PATH.read_text())
            return Preferences(**data)
        except Exception:
            # Fall back to defaults if anything looks wrong
            return Preferences()
    PREF_PATH.parent.mkdir(parents=True, exist_ok=True)
    return Preferences()


def save_preferences(prefs: Preferences) -> None:
    PREF_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(prefs)
    PREF_PATH.write_text(json.dumps(data, indent=2))
