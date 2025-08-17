#!/usr/bin/env python3
"""
Script de prueba para verificar MIDI mappings para cuatro decks
Ejecutar: python test_midi_mappings.py
"""

import sys
import time
import logging
from PyQt6.QtWidgets import QApplication

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def test_midi_mappings():
    """Test key MIDI mappings for all decks"""
    from utils.settings_manager import SettingsManager
    from visuals.visualizer_manager import VisualizerManager
    from midi.midi_engine import MidiEngine

    settings_manager = SettingsManager()
    visualizer_manager = VisualizerManager()
    midi_engine = MidiEngine(settings_manager, visualizer_manager)
    time.sleep(1)

    start_note = 56
    visuals = visualizer_manager.get_visualizer_names()
    clear_note = start_note + len(visuals)

    test_cases = [
        (start_note, 0, "Primer visual en Deck A"),
        (start_note, 1, "Primer visual en Deck B"),
        (start_note, 2, "Primer visual en Deck C"),
        (clear_note, 3, "Clear Deck D"),
    ]

    for note, channel, description in test_cases:
        logging.info(f"\n🎵 Testing {description}: note {note} ch{channel+1}")
        midi_engine.test_midi_mapping(note, channel=channel)
        time.sleep(0.2)

    logging.info("\n✅ MIDI mapping tests completed")


def test_preset_names():
    from visuals.visualizer_manager import VisualizerManager
    from utils.settings_manager import SettingsManager

    visualizer_manager = VisualizerManager()
    available_presets = visualizer_manager.get_visualizer_names()
    settings_manager = SettingsManager()
    mappings = settings_manager.load_midi_mappings()

    mapping_presets = set()
    for mapping_data in mappings.values():
        params = mapping_data.get('params', {})
        preset_name = params.get('preset_name')
        if preset_name:
            mapping_presets.add(preset_name)

    missing = mapping_presets - set(available_presets)
    extra = set(available_presets) - mapping_presets
    if missing:
        logging.warning(f"Presets missing in visualizer_manager: {missing}")
    if extra:
        logging.warning(f"Presets without mapping: {extra}")
    return not missing and not extra


def main():
    app = QApplication(sys.argv)
    ok = test_preset_names()
    if ok:
        test_midi_mappings()
    else:
        logging.error("Preset name mismatches detected")
    app.quit()


if __name__ == "__main__":
    main()
