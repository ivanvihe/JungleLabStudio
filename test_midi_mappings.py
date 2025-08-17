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

    mappings = settings_manager.load_midi_mappings()
    assert mappings, "No MIDI mappings loaded"
    sample_visual, sample_note = next(iter(mappings.items()))

    for channel in range(4):
        logging.info(
            f"\n🎵 Testing {sample_visual} on channel {channel+1}: note {sample_note}"
        )
        midi_engine.test_midi_mapping(sample_note, channel=channel)
        time.sleep(0.2)

    logging.info("\n✅ MIDI mapping tests completed")


def test_preset_names():
    from visuals.visualizer_manager import VisualizerManager
    from utils.settings_manager import SettingsManager

    visualizer_manager = VisualizerManager()
    available_presets = set(visualizer_manager.get_visualizer_names())
    settings_manager = SettingsManager()
    mappings = settings_manager.load_midi_mappings()

    mapping_presets = set(mappings.keys())

    missing = mapping_presets - available_presets
    extra = available_presets - mapping_presets
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
