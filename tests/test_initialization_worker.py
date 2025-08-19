from pathlib import Path
import sys
import types
import importlib

from PySide6.QtCore import QCoreApplication, QThread


repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root))

# Stub heavy dependencies before importing the module under test
midi_pkg = types.ModuleType('midi')
midi_pkg.__path__ = []
midi_engine_mod = types.ModuleType('midi.midi_engine')
midi_pkg.midi_engine = midi_engine_mod

visuals_pkg = types.ModuleType('visuals')
visuals_pkg.__path__ = []
visualizer_mod = types.ModuleType('visuals.visualizer_manager')
visuals_pkg.visualizer_manager = visualizer_mod

audio_pkg = types.ModuleType('audio')
audio_pkg.__path__ = []
audio_analyzer_mod = types.ModuleType('audio.audio_analyzer')
audio_pkg.audio_analyzer = audio_analyzer_mod

utils_pkg = types.ModuleType('utils')
utils_pkg.__path__ = []
settings_mod = types.ModuleType('utils.settings_manager')
utils_pkg.settings_manager = settings_mod

stub_modules = {
    'midi': midi_pkg,
    'midi.midi_engine': midi_engine_mod,
    'visuals': visuals_pkg,
    'visuals.visualizer_manager': visualizer_mod,
    'audio': audio_pkg,
    'audio.audio_analyzer': audio_analyzer_mod,
    'utils': utils_pkg,
    'utils.settings_manager': settings_mod,

    'ui.mixer_window': types.ModuleType('ui.mixer_window'),
    'ui.control_panel_window': types.ModuleType('ui.control_panel_window'),
}


class _FailOnCall:
    """Sentinel that fails if instantiated."""

    def __init__(self, *args, **kwargs):  # pragma: no cover - should never run
        raise AssertionError("Hardware classes should not be instantiated in worker")


class DummyVisualizerManager:
    pass


stub_modules['midi.midi_engine'].MidiEngine = _FailOnCall
stub_modules['midi.midi_engine'].DummyMidiEngine = _FailOnCall
stub_modules['visuals.visualizer_manager'].VisualizerManager = DummyVisualizerManager
stub_modules['audio.audio_analyzer'].AudioAnalyzer = _FailOnCall
stub_modules['audio.audio_analyzer'].DummyAudioAnalyzer = _FailOnCall

stub_modules['utils.settings_manager'].SettingsManager = object
stub_modules['ui.mixer_window'].MixerWindow = object
stub_modules['ui.control_panel_window'].ControlPanelWindow = object

for name, module in stub_modules.items():
    sys.modules[name] = module

from ui.main_application import InitializationWorker


def test_initialization_worker_emits_visualizer_manager(monkeypatch):
    # Avoid actual module reloading and thread sleeping
    monkeypatch.setattr(importlib, 'reload', lambda m: m)
    monkeypatch.setattr(QThread, 'msleep', staticmethod(lambda ms: None))

    app = QCoreApplication.instance() or QCoreApplication([])

    worker = InitializationWorker(object())
    received = []
    worker.initialization_complete.connect(received.append)

    worker.run()

    assert len(received) == 1
    assert isinstance(received[0], DummyVisualizerManager)


