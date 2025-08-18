import sys
import logging
logging.basicConfig(level=logging.DEBUG)
logging.debug("EXECUTING main_test.py - THIS IS THE CORRECT FILE")

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QSlider,
    QPushButton,
    QComboBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QSurfaceFormat

from visuals.presets.geometric_particles import GeometricParticlesVisualizer
from visuals.presets.evolutive_particles import EvolutiveParticlesVisualizer
from visuals.presets.abstract_lines import AbstractLinesVisualizer
from visuals.presets.mobius_band import MobiusBandVisualizer
from visuals.presets.abstract_shapes import AbstractShapesVisualizer
from visuals.presets.building_madness import BuildingMadnessVisualizer # New import
from utils.settings_manager import SettingsManager
from midi.midi_engine import MidiEngine

class VisualEngineWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logging.debug("VisualEngineWindow.__init__")
        self.setWindowTitle("Audio Visualizer Pro - Visual Engine")
        self.setGeometry(100, 100, 800, 600)
        self.visualizer = None
        self.set_visualizer("Geometric Particles") # Default visualizer

    def set_visualizer(self, visualizer_name):
        logging.debug(f"Setting visualizer to: {visualizer_name}")
        if self.visualizer:
            if hasattr(self.visualizer, 'cleanup'):
                logging.debug(f"Cleaning up old visualizer: {self.visualizer.__class__.__name__}")
                self.visualizer.cleanup()
            old_visualizer = self.visualizer
            self.centralWidget().setParent(None) # Remove old visualizer from layout
            old_visualizer.deleteLater() # Schedule old visualizer for deletion
            self.visualizer = None

        if visualizer_name == "Geometric Particles":
            self.visualizer = GeometricParticlesVisualizer()
        elif visualizer_name == "Evolutive Particles":
            self.visualizer = EvolutiveParticlesVisualizer()
        elif visualizer_name == "Abstract Lines":
            self.visualizer = AbstractLinesVisualizer()
        elif visualizer_name == "Mobius Band":
            self.visualizer = MobiusBandVisualizer()
        elif visualizer_name == "Abstract Shapes":
            self.visualizer = AbstractShapesVisualizer()
        elif visualizer_name == "Building Madness": # New visualizer
            self.visualizer = BuildingMadnessVisualizer()
        else:
            self.visualizer = QLabel("Select a Visualizer")
            self.visualizer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setCentralWidget(self.visualizer)
        logging.debug("Visualizer set")

class ControlPanelWindow(QMainWindow):
    def __init__(self, visual_engine_window, settings_manager, midi_engine):
        super().__init__()
        logging.debug("ControlPanelWindow.__init__")
        self.visual_engine_window = visual_engine_window
        self.settings_manager = settings_manager
        self.midi_engine = midi_engine
        self.midi_engine.midi_message_received.connect(self.on_midi_message)
        self.setWindowTitle("Audio Visualizer Pro - Control Panel")
        self.setGeometry(950, 100, 400, 600)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        layout.addWidget(QLabel("<h2>Control Panel</h2>"))

        # Preset Selector
        layout.addWidget(QLabel("Visual Preset:"))
        self.preset_selector = QComboBox()
        self.preset_selector.addItem("Geometric Particles")
        self.preset_selector.addItem("Evolutive Particles") # Added new preset
        self.preset_selector.addItem("Abstract Lines")
        self.preset_selector.addItem("Mobius Band")
        self.preset_selector.addItem("Abstract Shapes")
        self.preset_selector.addItem("Building Madness") # New visualizer
        self.preset_selector.currentIndexChanged.connect(self.on_preset_selected)
        layout.addWidget(self.preset_selector)

        # MIDI Device Selection
        layout.addWidget(QLabel("MIDI Input Device:"))
        self.midi_device_selector = QComboBox()
        self.populate_midi_devices()
        self.midi_device_selector.currentIndexChanged.connect(self.on_midi_device_selected)
        layout.addWidget(self.midi_device_selector)

        # Dynamic controls container
        self.controls_layout = QVBoxLayout()
        layout.addLayout(self.controls_layout)

        # Placeholder for MIDI mapping button
        midi_button = QPushButton("Open MIDI Mapping")
        layout.addWidget(midi_button)

        layout.addStretch()

        # Load and set last selected MIDI device
        last_midi_device = self.settings_manager.get_setting('last_midi_device')
        if last_midi_device:
            index = self.midi_device_selector.findText(last_midi_device)
            if index != -1:
                self.midi_device_selector.setCurrentIndex(index)
                self.midi_engine.open_input_port(last_midi_device)

        # Create controls for default preset
        self.create_controls()
        logging.debug("ControlPanelWindow.__init__ finished")

    def populate_midi_devices(self):
        logging.debug("Populating MIDI devices")
        self.midi_device_selector.clear()
        ports = self.midi_engine.list_input_ports()
        if not ports:
            self.midi_device_selector.addItem("No MIDI devices found")
            self.midi_device_selector.setEnabled(False)
        else:
            self.midi_device_selector.setEnabled(True)
            for port in ports:
                self.midi_device_selector.addItem(port)
        logging.debug("MIDI devices populated")

    def on_midi_device_selected(self, index):
        selected_device = self.midi_device_selector.currentText()
        logging.debug(f"MIDI device selected: {selected_device}")
        if selected_device and selected_device != "No MIDI devices found":
            self.midi_engine.open_input_port(selected_device)
            self.settings_manager.set_setting('last_midi_device', selected_device)

    def on_preset_selected(self, index):
        selected_preset = self.preset_selector.currentText()
        logging.debug(f"Selected preset: {selected_preset}")
        self.visual_engine_window.set_visualizer(selected_preset)
        self.create_controls()

    def create_controls(self):
        logging.debug("Creating controls")
        # Remove existing controls
        while self.controls_layout.count():
            item = self.controls_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        visualizer = self.visual_engine_window.visualizer
        if not hasattr(visualizer, "get_controls"):
            logging.debug("Visualizer has no controls")
            return

        controls = visualizer.get_controls()
        for name, cfg in controls.items():
            self.controls_layout.addWidget(QLabel(name))
            if cfg.get("type") == "slider":
                slider = QSlider(Qt.Orientation.Horizontal)
                slider.setRange(cfg.get("min", 0), cfg.get("max", 100))
                slider.setValue(cfg.get("value", 0))
                slider.valueChanged.connect(
                    lambda value, n=name: self.on_control_changed(n, value)
                )
                self.controls_layout.addWidget(slider)
            elif cfg.get("type") == "dropdown":
                dropdown = QComboBox()
                dropdown.addItems(cfg.get("options", []))
                dropdown.setCurrentIndex(cfg.get("value", 0))
                dropdown.currentIndexChanged.connect(
                    lambda index, n=name: self.on_control_changed(n, index)
                )
                self.controls_layout.addWidget(dropdown)

    def on_control_changed(self, name, value):
        logging.debug(f"Control changed: {name}, {value}")
        visualizer = self.visual_engine_window.visualizer
        if hasattr(visualizer, "update_control"):
            visualizer.update_control(name, value)

    def on_midi_message(self, message):
        # This method receives the raw MIDI message (list of bytes)
        # Further parsing and action can be done here
        logging.debug(f"Raw MIDI Message Received in Control Panel: {message}")

if __name__ == "__main__":
    logging.debug("Application starting")
    # Set OpenGL format before QApplication is created
    format = QSurfaceFormat()
    format.setVersion(3, 3) # Request OpenGL 3.3
    format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile) # Use core profile
    format.setDepthBufferSize(24)
    QSurfaceFormat.setDefaultFormat(format)
    logging.debug("QSurfaceFormat set")

    app = QApplication(sys.argv)
    logging.debug("QApplication created")

    settings_manager = SettingsManager()
    logging.debug("SettingsManager created")

    class DummyVisualizerManager:
        def get_visualizer_names(self):
            return []

    visualizer_manager = DummyVisualizerManager()
    midi_engine = MidiEngine(settings_manager, visualizer_manager)
    logging.debug("MidiEngine created")

    visual_engine = VisualEngineWindow()
    logging.debug("VisualEngineWindow created")
    visual_engine.move(50, 50) # Set a fixed position
    visual_engine.show()
    visual_engine.raise_() # Bring to front
    visual_engine.activateWindow() # Activate window
    logging.debug("VisualEngineWindow shown")

    control_panel = ControlPanelWindow(visual_engine, settings_manager, midi_engine)

    logging.debug("ControlPanelWindow created")
    control_panel.move(900, 50) # Set a fixed position
    control_panel.show()
    control_panel.raise_() # Bring to front
    control_panel.activateWindow() # Activate window
    logging.debug("ControlPanelWindow shown")

    logging.debug("Starting app.exec()")
    exit_code = app.exec()
    logging.debug(f"app.exec() finished with exit code: {exit_code}")
    sys.exit(exit_code)