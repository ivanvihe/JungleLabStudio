from pathlib import Path
import sys
import types

repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root))

# Stub out heavy dependencies before importing the module under test
stub_modules = {
    'midi': types.ModuleType('midi'),
    'midi.midi_engine': types.ModuleType('midi.midi_engine'),
    'visuals': types.ModuleType('visuals'),
    'visuals.visualizer_manager': types.ModuleType('visuals.visualizer_manager'),
    'audio': types.ModuleType('audio'),
    'audio.audio_analyzer': types.ModuleType('audio.audio_analyzer'),
    'utils': types.ModuleType('utils'),
    'utils.settings_manager': types.ModuleType('utils.settings_manager'),
    'ui.mixer_window': types.ModuleType('ui.mixer_window'),
    'ui.control_panel_window': types.ModuleType('ui.control_panel_window'),
}

stub_modules['midi.midi_engine'].MidiEngine = object
stub_modules['midi.midi_engine'].DummyMidiEngine = object
stub_modules['visuals.visualizer_manager'].VisualizerManager = object
stub_modules['audio.audio_analyzer'].AudioAnalyzer = object
stub_modules['audio.audio_analyzer'].DummyAudioAnalyzer = object
stub_modules['utils.settings_manager'].SettingsManager = object
stub_modules['ui.mixer_window'].MixerWindow = object
stub_modules['ui.control_panel_window'].ControlPanelWindow = object

for name, module in stub_modules.items():
    sys.modules[name] = module

from ui.main_application import InitializationWorker


class DummySettings:
    pass


def test_initialization_complete_emits_visualizer_manager():
    worker = InitializationWorker(DummySettings())
    received = []
    worker.initialization_complete.connect(lambda vm: received.append(vm))
    sentinel = object()
    worker.initialization_complete.emit(sentinel)
    assert received == [sentinel]
