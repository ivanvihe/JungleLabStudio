import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QSurfaceFormat

from utils.settings_manager import SettingsManager
from midi.midi_engine import MidiEngine
from visuals.visualizer_manager import VisualizerManager
from audio.audio_analyzer import AudioAnalyzer
from .mixer_window import MixerWindow
from .control_panel_window import ControlPanelWindow

# Force reload of visualizer_manager to ensure fresh loading
import importlib
import visuals.visualizer_manager
importlib.reload(visuals.visualizer_manager)
from visuals.visualizer_manager import VisualizerManager

logging.basicConfig(level=logging.DEBUG)

class MainApplication:
    def __init__(self):
        self.app = QApplication(sys.argv)
        
        # Set up OpenGL format
        format = QSurfaceFormat()
        format.setVersion(3, 3)
        format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        format.setDepthBufferSize(24)
        format.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
        QSurfaceFormat.setDefaultFormat(format)

        # Initialize components
        self.settings_manager = SettingsManager()
        self.midi_engine = MidiEngine()
        self.visualizer_manager = VisualizerManager()
        self.audio_analyzer = AudioAnalyzer()

        # Check if visualizers were loaded
        visualizer_names = self.visualizer_manager.get_visualizer_names()
        if not visualizer_names:
            logging.error("No visualizers found! Check your visuals directory.")
            sys.exit(1)
        else:
            logging.info(f"Loaded visualizers: {visualizer_names}")
            
        # List all visualizer classes for debugging
        for name in visualizer_names:
            visualizer_class = self.visualizer_manager.get_visualizer_class(name)
            logging.info(f"Visualizer '{name}' -> {visualizer_class}")

        # Create windows
        self.mixer_window = MixerWindow(self.visualizer_manager)
        self.control_panel = ControlPanelWindow(
            self.mixer_window, 
            self.settings_manager, 
            self.midi_engine, 
            self.visualizer_manager,
            self.audio_analyzer
        )
        
        # Auto-connect saved devices
        self.auto_connect_devices()

    def auto_connect_devices(self):
        """Auto-connect previously saved devices"""
        # Auto-connect MIDI device
        last_midi_device = self.settings_manager.get_setting("last_midi_device", "")
        if last_midi_device and last_midi_device != "":
            available_midi = self.midi_engine.get_midi_input_ports()
            if last_midi_device in available_midi:
                self.midi_engine.open_midi_input_port(last_midi_device)
                logging.info(f"Auto-connected to MIDI device: {last_midi_device}")
        
        # Auto-connect audio device
        last_audio_device = self.settings_manager.get_setting("audio_settings.input_device", "")
        if last_audio_device and last_audio_device != "":
            available_audio = self.audio_analyzer.get_available_devices()
            for device in available_audio:
                device_text = f"{device['name']} ({device['channels']} ch)"
                if device_text == last_audio_device:
                    self.audio_analyzer.set_input_device(device['index'])
                    self.audio_analyzer.start_analysis()
                    logging.info(f"Auto-connected to audio device: {last_audio_device}")
                    break

    def show_windows(self):
        """Show both windows"""
        self.mixer_window.show()
        self.control_panel.show()

    def run(self):
        """Run the application"""
        self.show_windows()
        return self.app.exec()