import sys
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QComboBox, QTabWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QSurfaceFormat
from OpenGL.GL import *
import numpy as np
import ctypes

from utils.settings_manager import SettingsManager
from midi.midi_engine import MidiEngine
from visuals.visualizer_manager import VisualizerManager
from visuals.deck import Deck

logging.basicConfig(level=logging.DEBUG)

class MixerWindow(QMainWindow):
    def __init__(self, visualizer_manager):
        super().__init__()
        self.setWindowTitle("Audio Visualizer Pro - Mixer Output")
        self.setGeometry(100, 100, 800, 600)
        self.visualizer_manager = visualizer_manager

        self.deck_a = Deck(visualizer_manager)
        self.deck_b = Deck(visualizer_manager)
        self.mix_value = 0.5

        self.gl_widget = QOpenGLWidget(self)
        self.setCentralWidget(self.gl_widget)

        self.gl_widget.initializeGL = self.initializeGL
        self.gl_widget.paintGL = self.paintGL
        self.gl_widget.resizeGL = self.resizeGL

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        self.load_shaders()
        self.setup_quad()
        self.deck_a.resize(self.size())
        self.deck_b.resize(self.size())

        # Initial setup
        if self.visualizer_manager.get_visualizer_names():
            logging.debug("Calling on_preset_selected for initial setup")
            # Call on_preset_selected to initialize visualizers for both decks
            self.on_preset_selected('A', self.preset_selector_a.currentIndex())
            self.on_preset_selected('B', self.preset_selector_b.currentIndex())
        else:
            logging.warning("No visualizers found to load for initial setup.")

    def load_shaders(self):
        # Shader for mixing the two deck textures
        with open("shaders/mix.vert", 'r') as f:
            vs_src = f.read()
        with open("shaders/mix.frag", 'r') as f:
            fs_src = f.read()

        vs = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vs, vs_src)
        glCompileShader(vs)

        fs = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fs, fs_src)
        glCompileShader(fs)

        self.shader_program = glCreateProgram()
        glAttachShader(self.shader_program, vs)
        glAttachShader(self.shader_program, fs)
        glLinkProgram(self.shader_program)

        glDeleteShader(vs)
        glDeleteShader(fs)

    def setup_quad(self):
        quad_vertices = np.array([
            # positions   # texCoords
            -1.0,  1.0,  0.0, 1.0,
            -1.0, -1.0,  0.0, 0.0,
             1.0, -1.0,  1.0, 0.0,

            -1.0,  1.0,  0.0, 1.0,
             1.0, -1.0,  1.0, 0.0,
             1.0,  1.0,  1.0, 1.0
        ], dtype=np.float32)

        self.quad_vao = glGenVertexArrays(1)
        self.quad_vbo = glGenBuffers(1)
        glBindVertexArray(self.quad_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.quad_vbo)
        glBufferData(GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(2 * 4))

    def paintGL(self):
        logging.debug("MixerWindow.paintGL start")
        self.gl_widget.makeCurrent()
        logging.debug("Context made current")
        self.deck_a.paint()
        logging.debug("Deck A painted")
        self.deck_b.paint()
        logging.debug("Deck B painted")

        glBindFramebuffer(GL_FRAMEBUFFER, self.gl_widget.defaultFramebufferObject())
        glViewport(0, 0, self.width(), self.height())
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glUseProgram(self.shader_program)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.deck_a.get_texture())
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.deck_b.get_texture())
        glUniform1i(glGetUniformLocation(self.shader_program, "texture1"), 0)
        glUniform1i(glGetUniformLocation(self.shader_program, "texture2"), 1)
        glUniform1f(glGetUniformLocation(self.shader_program, "mixValue"), self.mix_value)

        glBindVertexArray(self.quad_vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)
        self.gl_widget.doneCurrent()
        logging.debug("Context done current")

        self.gl_widget.update()
        logging.debug("MixerWindow.paintGL end")

    def resizeGL(self, w, h):
        self.deck_a.resize(QSize(w, h))
        self.deck_b.resize(QSize(w, h))

    def set_mix_value(self, value):
        self.mix_value = value / 100.0

class ControlPanelWindow(QMainWindow):
    def __init__(self, mixer_window, settings_manager, midi_engine, visualizer_manager):
        super().__init__()
        logging.debug("ControlPanelWindow.__init__ called")
        self.mixer_window = mixer_window
        self.settings_manager = settings_manager
        self.midi_engine = midi_engine
        self.visualizer_manager = visualizer_manager

        self.setWindowTitle("Audio Visualizer Pro - Control Panel")
        self.setGeometry(950, 100, 400, 600)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        layout.addWidget(QLabel("<h2>Control Panel</h2>"))

        # Deck A
        deck_a_group = QWidget()
        deck_a_layout = QVBoxLayout(deck_a_group)
        deck_a_layout.addWidget(QLabel("<b>Deck A</b>"))
        self.preset_selector_a = QComboBox()
        self.preset_selector_a.addItems(self.visualizer_manager.get_visualizer_names())
        self.preset_selector_a.setCurrentIndex(0) # Set initial index
        self.preset_selector_a.currentIndexChanged.connect(lambda i: self.on_preset_selected('A', i))
        deck_a_layout.addWidget(self.preset_selector_a)

        # Deck B
        deck_b_group = QWidget()
        deck_b_layout = QVBoxLayout(deck_b_group)
        deck_b_layout.addWidget(QLabel("<b>Deck B</b>"))
        self.preset_selector_b = QComboBox()
        self.preset_selector_b.addItems(self.visualizer_manager.get_visualizer_names())
        self.preset_selector_b.setCurrentIndex(0) # Set initial index
        self.preset_selector_b.currentIndexChanged.connect(lambda i: self.on_preset_selected('B', i))
        deck_b_layout.addWidget(self.preset_selector_b)

        decks_layout = QHBoxLayout()
        decks_layout.addWidget(deck_a_group)
        decks_layout.addWidget(deck_b_group)
        layout.addLayout(decks_layout)

        # Mixer Fader
        layout.addWidget(QLabel("<b>Mixer</b>"))
        self.fader = QSlider(Qt.Orientation.Horizontal)
        self.fader.setRange(0, 100)
        self.fader.setValue(50)
        self.fader.valueChanged.connect(self.mixer_window.set_mix_value)
        layout.addWidget(self.fader)

        # Tabs for controls
        self.tabs = QTabWidget()
        self.tab_a = QWidget()
        self.tab_b = QWidget()
        self.controls_layout_a = QVBoxLayout(self.tab_a)
        self.controls_layout_b = QVBoxLayout(self.tab_b)
        self.tabs.addTab(self.tab_a, "Deck A Controls")
        self.tabs.addTab(self.tab_b, "Deck B Controls")
        layout.addWidget(self.tabs)

        # MIDI
        layout.addWidget(QLabel("MIDI Input Device:"))
        self.midi_device_selector = QComboBox()
        # ... (populate midi devices)
        layout.addWidget(self.midi_device_selector)

        layout.addStretch()

    def on_preset_selected(self, deck_id, index):
        logging.debug(f"on_preset_selected called for deck {deck_id} with index {index}")
        selector = self.preset_selector_a if deck_id == 'A' else self.preset_selector_b
        deck = self.mixer_window.deck_a if deck_id == 'A' else self.mixer_window.deck_b
        
        selected_preset = selector.currentText()
        logging.debug(f"Selected preset text: {selected_preset}")
        if selected_preset:
            deck.set_visualizer(selected_preset)
            self.create_controls(deck_id)

    def create_controls(self, deck_id):
        layout = self.controls_layout_a if deck_id == 'A' else self.controls_layout_b
        deck = self.mixer_window.deck_a if deck_id == 'A' else self.mixer_window.deck_b

        # Clear old controls
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()

        controls = deck.get_controls()
        for name, cfg in controls.items():
            layout.addWidget(QLabel(name))
            if cfg.get("type") == "slider":
                slider = QSlider(Qt.Orientation.Horizontal)
                slider.setRange(cfg.get("min", 0), cfg.get("max", 100))
                slider.setValue(cfg.get("value", 0))
                slider.valueChanged.connect(
                    lambda value, n=name, d=deck: d.update_control(n, value)
                )
                layout.addWidget(slider)
            elif cfg.get("type") == "dropdown":
                dropdown = QComboBox()
                dropdown.addItems(cfg.get("options", []))
                dropdown.setCurrentIndex(cfg.get("value", 0))
                dropdown.currentIndexChanged.connect(
                    lambda index, n=name, d=deck: d.update_control(n, index)
                )
                layout.addWidget(dropdown)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    format = QSurfaceFormat()
    format.setVersion(3, 3)
    format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    format.setDepthBufferSize(24)
    QSurfaceFormat.setDefaultFormat(format)

    settings_manager = SettingsManager()
    midi_engine = MidiEngine()
    visualizer_manager = VisualizerManager()

    mixer_window = MixerWindow(visualizer_manager)
    mixer_window.show()

    control_panel = ControlPanelWindow(mixer_window, settings_manager, midi_engine, visualizer_manager)
    control_panel.show()

    sys.exit(app.exec())