"""midi/midi_visual_mapper.py - dynamic mappings for four decks"""
import logging
import json
from pathlib import Path

class MidiVisualMapper:
    """Generate MIDI mappings for visuals using channel per deck"""

    def __init__(self, visualizer_manager=None):
        self.visualizer_manager = visualizer_manager
        self.config = {}
        self.default_channel = 0
        self.load_visual_mappings_config()
        self.sync_with_available_visuals()
        logging.info("MidiVisualMapper initialized")

    def load_visual_mappings_config(self):
        path = Path(__file__).parent / "visual_mappings_config.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.create_default_visual_config()
            self.save_visual_mappings_config()

    def save_visual_mappings_config(self):
        path = Path(__file__).parent / "visual_mappings_config.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def create_default_visual_config(self):
        self.config = {
            "deck_channels": {"A": 12, "B": 13, "C": 14, "D": 15},
            "start_note": 56,
            "visual_priority_order": []
        }

    def get_available_visuals(self):
        if self.visualizer_manager:
            return self.visualizer_manager.get_visualizer_names()
        return []

    def sync_with_available_visuals(self):
        visuals = self.get_available_visuals()
        self.config["visual_priority_order"] = visuals
        self.save_visual_mappings_config()

    def generate_all_visual_mappings(self):
        visuals = self.get_available_visuals()
        deck_channels = self.config.get("deck_channels", {})
        start_note = self.config.get("start_note", 56)
        mappings = {}
        for i, visual_name in enumerate(visuals):
            note = start_note + i
            for deck, channel in deck_channels.items():
                action_id = f"deck_{deck.lower()}_preset_{i}"
                mappings[action_id] = {
                    "type": "load_preset",
                    "params": {
                        "deck_id": deck,
                        "preset_name": visual_name,
                        "custom_values": ""
                    },
                    "midi": f"note_on_ch{channel}_note{note}"
                }
        clear_note = start_note + len(visuals)
        for deck, channel in deck_channels.items():
            action_id = f"deck_{deck.lower()}_clear"
            mappings[action_id] = {
                "type": "load_preset",
                "params": {
                    "deck_id": deck,
                    "preset_name": None,
                    "custom_values": ""
                },
                "midi": f"note_on_ch{channel}_note{clear_note}"
            }
        return mappings

    def get_note_name(self, note_number):
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (note_number // 12) - 1
        return f"{note_names[note_number % 12]}{octave}"

    def print_current_visual_mappings(self):
        mappings = self.generate_all_visual_mappings()
        for action_id, data in mappings.items():
            midi_key = data.get("midi")
            params = data.get("params", {})
            logging.info(f"{action_id}: {midi_key} -> {params.get('preset_name')}")
