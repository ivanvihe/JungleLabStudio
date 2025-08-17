import json
from pathlib import Path
import logging

CONFIG_PATH = Path("config/visual_properties.json")

def _load_all():
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception as e:
        logging.error(f"Error loading visual properties: {e}")
    return {}

def load_visual_properties(visual_name):
    """Load saved properties for a visual."""
    return _load_all().get(visual_name, {})

def save_visual_properties(visual_name, properties):
    """Save properties for a visual."""
    data = _load_all()
    data[visual_name] = properties
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error saving visual properties: {e}")
