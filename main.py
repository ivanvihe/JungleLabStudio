
import sys
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QComboBox, QTabWidget
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QSurfaceFormat
from OpenGL.GL import *
import numpy as np
import ctypes

from utils.settings_manager import SettingsManager
from midi.midi_engine import MidiEngine
from visuals.visualizer_manager import VisualizerManager
from visuals.deck import Deck

# Force reload of visualizer_manager to ensure fresh loading
import importlib
import visuals.visualizer_manager
importlib.reload(visuals.visualizer_manager)
from visuals.visualizer_manager import VisualizerManager

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
        
        # Initialize with first available visualizer - but delay until OpenGL is ready
        self.initial_setup_done = False
        
        # Set up timer for continuous animation
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(16)  # ~60 FPS

    def initializeGL(self):
        logging.debug("MixerWindow.initializeGL called")
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        self.load_shaders()
        self.setup_quad()
        
        # Initialize decks with current size - NOW with valid OpenGL context
        current_size = QSize(max(self.gl_widget.width(), 800), max(self.gl_widget.height(), 600))
        self.deck_a.resize(current_size)
        self.deck_b.resize(current_size)
        
        # Force initialization of visualizers if they exist
        if self.deck_a.visualizer:
            self.deck_a._needs_init_and_resize = True
        if self.deck_b.visualizer:
            self.deck_b._needs_init_and_resize = True
        
        # Setup initial visualizers now that OpenGL is ready
        if not self.initial_setup_done:
            self.setup_initial_visualizers()
            self.initial_setup_done = True
        
        logging.debug(f"MixerWindow OpenGL initialized with size {current_size.width()}x{current_size.height()}")

    def setup_initial_visualizers(self):
        """Setup initial visualizers now that OpenGL context is available"""
        visualizer_names = self.visualizer_manager.get_visualizer_names()
        if visualizer_names:
            logging.debug(f"Setting up initial visualizers from: {visualizer_names}")
            # Set default visualizers for both decks
            self.deck_a.set_visualizer(visualizer_names[0])
            if len(visualizer_names) > 1:
                self.deck_b.set_visualizer(visualizer_names[1])
            else:
                self.deck_b.set_visualizer(visualizer_names[0])
                
            # Force resize to create FBOs
            current_size = QSize(max(self.gl_widget.width(), 800), max(self.gl_widget.height(), 600))
            self.deck_a.resize(current_size)
            self.deck_b.resize(current_size)
            
    def animate(self):
        """Called by timer to trigger repaints"""
        if self.gl_widget:
            self.gl_widget.update()

    def load_shaders(self):
        try:
            # Shader for mixing the two deck textures
            with open("shaders/mix.vert", 'r') as f:
                vs_src = f.read()
            with open("shaders/mix.frag", 'r') as f:
                fs_src = f.read()

            vs = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vs, vs_src)
            glCompileShader(vs)
            
            # Check vertex shader compilation
            if not glGetShaderiv(vs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(vs).decode()
                logging.error(f"Vertex shader compilation failed: {error}")
                raise Exception(f"Vertex shader error: {error}")

            fs = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fs, fs_src)
            glCompileShader(fs)
            
            # Check fragment shader compilation
            if not glGetShaderiv(fs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(fs).decode()
                logging.error(f"Fragment shader compilation failed: {error}")
                raise Exception(f"Fragment shader error: {error}")

            self.shader_program = glCreateProgram()
            glAttachShader(self.shader_program, vs)
            glAttachShader(self.shader_program, fs)
            glLinkProgram(self.shader_program)
            
            # Check program linking
            if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(self.shader_program).decode()
                logging.error(f"Shader program linking failed: {error}")
                raise Exception(f"Shader program error: {error}")

            glDeleteShader(vs)
            glDeleteShader(fs)
            logging.debug("Shaders loaded successfully")
            
        except Exception as e:
            logging.error(f"Failed to load shaders: {e}")
            # Create a fallback shader or handle the error appropriately
            raise

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
        glBindVertexArray(0)

    def paintGL(self):
        logging.debug("MixerWindow.paintGL start")
        
        # Make sure we have the current context
        self.gl_widget.makeCurrent()
        
        # Render both decks to their framebuffers
        self.deck_a.paint()
        self.deck_b.paint()

        # Now composite them in the main framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, self.gl_widget.defaultFramebufferObject())
        glViewport(0, 0, self.gl_widget.width(), self.gl_widget.height())
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Use the mixing shader
        glUseProgram(self.shader_program)
        
        # Bind textures
        glActiveTexture(GL_TEXTURE0)
        texture_a = self.deck_a.get_texture()
        if texture_a:
            glBindTexture(GL_TEXTURE_2D, texture_a)
        
        glActiveTexture(GL_TEXTURE1)
        texture_b = self.deck_b.get_texture()
        if texture_b:
            glBindTexture(GL_TEXTURE_2D, texture_b)
        
        # Set uniforms
        glUniform1i(glGetUniformLocation(self.shader_program, "texture1"), 0)
        glUniform1i(glGetUniformLocation(self.shader_program, "texture2"), 1)
        glUniform1f(glGetUniformLocation(self.shader_program, "mixValue"), self.mix_value)

        # Draw the quad
        glBindVertexArray(self.quad_vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)
        
        # Clean up
        glUseProgram(0)
        
        logging.debug("MixerWindow.paintGL end")

    def resizeGL(self, w, h):
        current_size = QSize(w, h)
        self.deck_a.resize(current_size)
        self.deck_b.resize(current_size)
        logging.debug(f"MixerWindow resized to {w}x{h}")

    def set_mix_value(self, value):
        self.mix_value = value / 100.0
        logging.debug(f"Mix value set to: {self.mix_value}")
        self.gl_widget.update()  # Trigger a repaint
        
    def set_deck_visualizer(self, deck_id, visualizer_name):
        """Called by control panel to change visualizers"""
        logging.debug(f"Setting deck {deck_id} to visualizer: {visualizer_name}")
        
        # Make sure we have OpenGL context
        self.gl_widget.makeCurrent()
        
        if deck_id == 'A':
            self.deck_a.set_visualizer(visualizer_name)
            # Force resize to ensure FBO is created
            self.deck_a.resize(self.deck_a.size)
        elif deck_id == 'B':
            self.deck_b.set_visualizer(visualizer_name)
            # Force resize to ensure FBO is created
            self.deck_b.resize(self.deck_b.size)
            
        self.gl_widget.update()  # Trigger a repaint
        
    def get_deck_controls(self, deck_id):
        """Get controls for the specified deck"""
        if deck_id == 'A':
            return self.deck_a.get_controls()
        elif deck_id == 'B':
            return self.deck_b.get_controls()
        return {}
        
    def update_deck_control(self, deck_id, name, value):
        """Update a control for the specified deck"""
        if deck_id == 'A':
            self.deck_a.update_control(name, value)
        elif deck_id == 'B':
            self.deck_b.update_control(name, value)
        self.gl_widget.update()  # Trigger a repaint

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
        visualizer_names = self.visualizer_manager.get_visualizer_names()
        self.preset_selector_a.addItems(visualizer_names)
        if visualizer_names:
            self.preset_selector_a.setCurrentIndex(0)
        self.preset_selector_a.currentIndexChanged.connect(lambda i: self.on_preset_selected('A', i))
        deck_a_layout.addWidget(self.preset_selector_a)

        # Deck B
        deck_b_group = QWidget()
        deck_b_layout = QVBoxLayout(deck_b_group)
        deck_b_layout.addWidget(QLabel("<b>Deck B</b>"))
        self.preset_selector_b = QComboBox()
        self.preset_selector_b.addItems(visualizer_names)
        if len(visualizer_names) > 1:
            self.preset_selector_b.setCurrentIndex(1)
        elif visualizer_names:
            self.preset_selector_b.setCurrentIndex(0)
        self.preset_selector_b.currentIndexChanged.connect(lambda i: self.on_preset_selected('B', i))
        deck_b_layout.addWidget(self.preset_selector_b)

        decks_layout = QHBoxLayout()
        decks_layout.addWidget(deck_a_group)
        decks_layout.addWidget(deck_b_group)
        layout.addLayout(decks_layout)

        # Mixer Fader
        layout.addWidget(QLabel("<b>Mixer</b>"))
        fader_layout = QHBoxLayout()
        fader_layout.addWidget(QLabel("A"))
        self.fader = QSlider(Qt.Orientation.Horizontal)
        self.fader.setRange(0, 100)
        self.fader.setValue(50)
        self.fader.valueChanged.connect(self.mixer_window.set_mix_value)
        self.fader.valueChanged.connect(self.update_fader_label)
        fader_layout.addWidget(self.fader)
        fader_layout.addWidget(QLabel("B"))
        layout.addLayout(fader_layout)
        
        # Fader value label
        self.fader_label = QLabel("Mix: 50%")
        layout.addWidget(self.fader_label)

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
        # TODO: populate midi devices
        layout.addWidget(self.midi_device_selector)

        layout.addStretch()
        
        # Initialize controls for both decks after a short delay to ensure mixer is ready
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(500, lambda: self.create_controls('A'))
        QTimer.singleShot(500, lambda: self.create_controls('B'))

    def update_fader_label(self, value):
        self.fader_label.setText(f"Mix: {value}% (A←→B)")

    def on_preset_selected(self, deck_id, index):
        logging.debug(f"on_preset_selected called for deck {deck_id} with index {index}")
        selector = self.preset_selector_a if deck_id == 'A' else self.preset_selector_b
        
        selected_preset = selector.currentText()
        logging.debug(f"Selected preset text: {selected_preset}")
        if selected_preset:
            # Update the mixer window
            self.mixer_window.set_deck_visualizer(deck_id, selected_preset)
            # Wait a moment for the visualizer to be set, then update controls
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self.create_controls(deck_id))

    def create_controls(self, deck_id):
        logging.debug(f"Creating controls for deck {deck_id}")
        layout = self.controls_layout_a if deck_id == 'A' else self.controls_layout_b

        # Clear old controls
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget: 
                widget.deleteLater()

        # Get controls from the mixer window
        controls = self.mixer_window.get_deck_controls(deck_id)
        logging.debug(f"Got controls for deck {deck_id}: {controls}")
        
        if not controls:
            no_controls_label = QLabel("No controls available")
            layout.addWidget(no_controls_label)
            layout.addStretch()
            return
            
        for name, cfg in controls.items():
            logging.debug(f"Adding control: {name} = {cfg}")
            layout.addWidget(QLabel(name))
            if cfg.get("type") == "slider":
                slider = QSlider(Qt.Orientation.Horizontal)
                slider.setRange(cfg.get("min", 0), cfg.get("max", 100))
                slider.setValue(cfg.get("value", 0))
                slider.valueChanged.connect(
                    lambda value, n=name, d=deck_id: self.mixer_window.update_deck_control(d, n, value)
                )
                layout.addWidget(slider)
            elif cfg.get("type") == "dropdown":
                dropdown = QComboBox()
                dropdown.addItems(cfg.get("options", []))
                dropdown.setCurrentIndex(cfg.get("value", 0))
                dropdown.currentIndexChanged.connect(
                    lambda index, n=name, d=deck_id: self.mixer_window.update_deck_control(d, n, index)
                )
                layout.addWidget(dropdown)
        
        layout.addStretch()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set up OpenGL format
    format = QSurfaceFormat()
    format.setVersion(3, 3)
    format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    format.setDepthBufferSize(24)
    format.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
    QSurfaceFormat.setDefaultFormat(format)

    # Initialize components
    settings_manager = SettingsManager()
    midi_engine = MidiEngine()
    visualizer_manager = VisualizerManager()

    # Check if visualizers were loaded
    visualizer_names = visualizer_manager.get_visualizer_names()
    if not visualizer_names:
        logging.error("No visualizers found! Check your visuals directory.")
        sys.exit(1)
    else:
        logging.info(f"Loaded visualizers: {visualizer_names}")
        
    # List all visualizer classes for debugging
    for name in visualizer_names:
        visualizer_class = visualizer_manager.get_visualizer_class(name)
        logging.info(f"Visualizer '{name}' -> {visualizer_class}")
        
        # Try to create an instance to check for immediate issues
        try:
            test_instance = visualizer_class()
            logging.info(f"✓ Successfully created test instance of {name}")
            if hasattr(test_instance, 'cleanup'):
                test_instance.cleanup()
        except Exception as e:
            logging.error(f"✗ Failed to create test instance of {name}: {e}")

    # Create windows
    mixer_window = MixerWindow(visualizer_manager)
    mixer_window.show()

    control_panel = ControlPanelWindow(mixer_window, settings_manager, midi_engine, visualizer_manager)
    control_panel.show()

    sys.exit(app.exec())

class PreviewGLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.texture_id = 0
        self.quad_vao = 0
        self.quad_vbo = 0

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.load_shaders()
        self.setup_quad()

    def load_shaders(self):
        # Simple shader to render a texture
        vs_src = """
        #version 330 core
        layout (location = 0) in vec2 aPos;
        layout (location = 1) in vec2 aTexCoord;
        out vec2 TexCoord;
        void main()
        {
            gl_Position = vec4(aPos.x, aPos.y, 0.0, 1.0);
            TexCoord = aTexCoord;
        }
        """
        fs_src = """
        #version 330 core
        out vec4 FragColor;
        in vec2 TexCoord;
        uniform sampler2D screenTexture;
        void main()
        {
            FragColor = texture(screenTexture, TexCoord);
        }
        """

        vs = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vs, vs_src)
        glCompileShader(vs)
        # Check for compile errors (omitted for brevity, but should be present)

        fs = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fs, fs_src)
        glCompileShader(fs)
        # Check for compile errors

        self.shader_program = glCreateProgram()
        glAttachShader(self.shader_program, vs)
        glAttachShader(self.shader_program, fs)
        glLinkProgram(self.shader_program)
        # Check for linking errors

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
        glBindVertexArray(0)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.shader_program)
        
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glUniform1i(glGetUniformLocation(self.shader_program, "screenTexture"), 0)

        glBindVertexArray(self.quad_vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)
        glUseProgram(0)

    def set_texture(self, texture_id):
        self.texture_id = texture_id
        self.update() # Trigger repaint
