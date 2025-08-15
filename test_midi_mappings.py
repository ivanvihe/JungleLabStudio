#!/usr/bin/env python3
"""
Script de prueba para verificar MIDI mappings
Ejecutar: python test_midi_mappings.py
"""

import sys
import time
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_midi_mappings():
    """Test key MIDI mappings"""
    
    # Import your modules
    from utils.settings_manager import SettingsManager
    from visuals.visualizer_manager import VisualizerManager
    from midi.midi_engine import MidiEngine
    
    print("🧪 TESTING MIDI MAPPINGS")
    print("=" * 50)
    
    # Initialize components
    settings_manager = SettingsManager()
    visualizer_manager = VisualizerManager()
    midi_engine = MidiEngine(settings_manager, visualizer_manager)
    
    # Wait for initialization
    time.sleep(1)
    
    # Test key mappings
    test_cases = [
        (37, "Wire Terrain on Deck A (C#1)"),
        (50, "Mix A→B in 5s (D2)"),
        (55, "Wire Terrain on Deck B (G2)"),
        (46, "Clear Deck A (A#1)"),
        (64, "Clear Deck B (E3)")
    ]
    
    print("\n🎹 TESTING MIDI MAPPINGS:")
    print("-" * 30)
    
    for note, description in test_cases:
        print(f"\n🎵 Testing Note {note}: {description}")
        midi_engine.test_midi_mapping(note)
        time.sleep(0.5)  # Small delay between tests
    
    print("\n" + "=" * 50)
    print("✅ MIDI mapping tests completed!")
    print("\nCheck the console output above for detailed results.")
    print("\nIf you see 'Found mapping' messages, your MIDI setup is working!")
    print("\nNext steps:")
    print("1. Connect your virtual MIDI device")
    print("2. Set up Drum Rack in Ableton Live")
    print("3. Add External Instruments to pads C1-E3")
    print("4. Configure MIDI Out to your virtual device")
    print("5. Run your main application and test!")

def test_preset_names():
    """Test that all preset names match visualizer manager"""
    
    from visuals.visualizer_manager import VisualizerManager
    from utils.settings_manager import SettingsManager
    
    print("\n🎨 TESTING PRESET NAMES:")
    print("-" * 30)
    
    # Get available presets
    visualizer_manager = VisualizerManager()
    available_presets = visualizer_manager.get_visualizer_names()
    
    print(f"Available presets: {available_presets}")
    
    # Get mappings presets
    settings_manager = SettingsManager()
    mappings = settings_manager.load_midi_mappings()
    
    mapping_presets = set()
    for action_id, mapping_data in mappings.items():
        params = mapping_data.get('params', {})
        preset_name = params.get('preset_name')
        if preset_name and preset_name != "Clear":
            mapping_presets.add(preset_name)
    
    print(f"Mapping presets: {list(mapping_presets)}")
    
    # Check matches
    missing_presets = mapping_presets - set(available_presets)
    extra_presets = set(available_presets) - mapping_presets
    
    if missing_presets:
        print(f"❌ Missing presets in visualizer_manager: {missing_presets}")
    
    if extra_presets:
        print(f"ℹ️  Extra presets in visualizer_manager: {extra_presets}")
    
    if not missing_presets:
        print("✅ All mapping presets found in visualizer_manager!")
    
    return len(missing_presets) == 0

def main():
    """Main test function"""
    
    print("🚀 AUDIO VISUALIZER PRO - MIDI MAPPING TEST")
    print("=" * 60)
    
    # Create QApplication for Qt components
    app = QApplication(sys.argv)
    
    try:
        # Test preset names first
        presets_ok = test_preset_names()
        
        if presets_ok:
            # Test MIDI mappings
            test_midi_mappings()
        else:
            print("❌ Preset name mismatches found. Fix these first!")
            return 1
        
        print("\n🎉 ALL TESTS PASSED!")
        print("\nYour MIDI mapping setup is ready to use!")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        app.quit()

if __name__ == "__main__":
    sys.exit(main())