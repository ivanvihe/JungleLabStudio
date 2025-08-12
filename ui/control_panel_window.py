import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QComboBox,
    QGroupBox, QGridLayout, QFrame, QProgressBar, QMenuBar, QMenu, QFormLayout, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction

from .preferences_dialog import PreferencesDialog
from .preview_gl_widget import PreviewGLWidget

class ControlPanelWindow(QMainWindow):
    def __init__(self, mixer_window, settings_manager, midi_engine, visualizer_manager, audio_analyzer):
        super().__init__(mixer_window)  # Set mixer window as parent for monitor management
        logging.debug("ControlPanelWindow.__init__ called")
        self.mixer_window = mixer_window
        self.settings_manager = settings_manager
        self.midi_engine = midi_engine
        self.visualizer_manager = visualizer_manager
        self.audio_analyzer = audio_analyzer

        self.setWindowTitle("Audio Visualizer Pro - Control Panel")
        self.setGeometry(50, 50, 1200, 800)
        
        # Create menu bar
        self.create_menu_bar()

        # Create main UI
        self.create_ui()
        
        # Connect MIDI signals
        self.midi_engine.bpm_changed.connect(self.update_bpm_display)
        self.midi_engine.device_connected.connect(self.update_midi_device_display)
        self.midi_engine.device_disconnected.connect(self.update_midi_device_display)
        
        # Connect audio signals
        self.audio_analyzer.level_changed.connect(self.update_audio_level)
        self.audio_analyzer.fft_data_ready.connect(self.update_frequency_bands)
        
        # Timer for updating preview and info
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_info_and_previews)
        self.update_timer.start(50)  # 20 FPS for previews

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # Settings menu
        settings_menu = menubar.addMenu('Settings')
        
        preferences_action = QAction('Preferences...', self)
        preferences_action.triggered.connect(self.show_preferences)
        settings_menu.addAction(preferences_action)

    def show_preferences(self):
        dialog = PreferencesDialog(self.settings_manager, self.midi_engine, self.audio_analyzer, self)
        dialog.exec()

    def move_control_panel_to_monitor(self, monitor_index):
        """Move control panel to specified monitor"""
        screens = QApplication.screens()
        if monitor_index < len(screens):
            screen = screens[monitor_index]
            self.move(screen.geometry().x(), screen.geometry().y())

    def move_main_window_to_monitor(self, monitor_index):
        """Move main window to specified monitor"""
        screens = QApplication.screens()
        if monitor_index < len(screens):
            screen = screens[monitor_index]
            self.mixer_window.move(screen.geometry().x(), screen.geometry().y())

    def create_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(10)
        
        # Deck A Section (Left)
        deck_a_section = self.create_deck_section('A')
        main_layout.addWidget(deck_a_section, 2)
        
        # Center Mixer Section
        mixer_section = self.create_mixer_section()
        main_layout.addWidget(mixer_section, 1)
        
        # Deck B Section (Right)
        deck_b_section = self.create_deck_section('B')
        main_layout.addWidget(deck_b_section, 2)
        
        # Apply monitor settings
        self.apply_monitor_settings()

    def apply_monitor_settings(self):
        """Apply saved monitor settings"""
        cp_monitor = self.settings_manager.get_setting("control_panel_monitor", 0)
        main_monitor = self.settings_manager.get_setting("main_window_monitor", 0)
        
        # Use QTimer to delay the move operations until after window is shown
        QTimer.singleShot(100, lambda: self.move_control_panel_to_monitor(cp_monitor))
        QTimer.singleShot(100, lambda: self.move_main_window_to_monitor(main_monitor))

    def create_deck_section(self, deck_id):
        """Create a complete deck section with preview, controls, etc."""
        deck_frame = QFrame()
        deck_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        deck_layout = QVBoxLayout(deck_frame)
        
        # Deck title
        title = QLabel(f"<h2>DECK {deck_id}</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #00ff00; background-color: #1a1a1a; padding: 10px; border-radius: 5px;")
        deck_layout.addWidget(title)
        
        # Preview window
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Get the appropriate deck for preview
        deck = self.mixer_window.deck_a if deck_id == 'A' else self.mixer_window.deck_b
        preview_widget = PreviewGLWidget(deck)
        preview_widget.setFixedSize(250, 200)
        preview_layout.addWidget(preview_widget)
        deck_layout.addWidget(preview_group)
        
        # Store reference to preview widget
        if deck_id == 'A':
            self.preview_a = preview_widget
        else:
            self.preview_b = preview_widget
        
        # Visualizer selector
        selector_group = QGroupBox("Visualizer")
        selector_layout = QVBoxLayout(selector_group)
        
        selector = QComboBox()
        visualizer_names = self.visualizer_manager.get_visualizer_names()
        selector.addItems(visualizer_names)
        
        # Set initial selection and ensure mixer window is updated
        if visualizer_names:
            if deck_id == 'A':
                selector.setCurrentIndex(0)
                # Ensure mixer deck is set to this visualizer
                QTimer.singleShot(200, lambda: self.mixer_window.set_deck_visualizer('A', visualizer_names[0]))
            elif len(visualizer_names) > 1:
                selector.setCurrentIndex(1)
                QTimer.singleShot(200, lambda: self.mixer_window.set_deck_visualizer('B', visualizer_names[1]))
            else:
                selector.setCurrentIndex(0)
                QTimer.singleShot(200, lambda: self.mixer_window.set_deck_visualizer('B', visualizer_names[0]))
        
        selector.currentTextChanged.connect(lambda text, d=deck_id: self.on_preset_selected(d, text))
        selector_layout.addWidget(selector)
        deck_layout.addWidget(selector_group)
        
        # Store reference to selector
        if deck_id == 'A':
            self.preset_selector_a = selector
        else:
            self.preset_selector_b = selector
        
        # Controls section
        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        deck_layout.addWidget(controls_group)
        
        # Store reference to controls layout
        if deck_id == 'A':
            self.controls_layout_a = controls_layout
        else:
            self.controls_layout_b = controls_layout
        
        # Initialize controls for this deck (delayed to ensure everything is set up)
        QTimer.singleShot(1000, lambda: self.create_controls(deck_id))
        
        return deck_frame

    def create_mixer_section(self):
        """Create the center mixer section"""
        mixer_frame = QFrame()
        mixer_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        mixer_layout = QVBoxLayout(mixer_frame)
        
        # Mixer title
        title = QLabel("<h2>MIXER</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #ff6600; background-color: #1a1a1a; padding: 10px; border-radius: 5px;")
        mixer_layout.addWidget(title)
        
        # Crossfader section
        fader_group = QGroupBox("Crossfader")
        fader_layout = QVBoxLayout(fader_group)
        
        # Fader labels
        labels_layout = QHBoxLayout()
        labels_layout.addWidget(QLabel("A"))
        labels_layout.addStretch()
        labels_layout.addWidget(QLabel("B"))
        fader_layout.addLayout(labels_layout)
        
        # The fader itself
        self.fader = QSlider(Qt.Orientation.Horizontal)
        self.fader.setRange(0, 100)
        self.fader.setValue(50)
        self.fader.valueChanged.connect(self.mixer_window.set_mix_value)
        self.fader.valueChanged.connect(self.update_fader_label)
        fader_layout.addWidget(self.fader)
        
        # Fader value label
        self.fader_label = QLabel("Mix: 50%")
        self.fader_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fader_layout.addWidget(self.fader_label)
        
        mixer_layout.addWidget(fader_group)
        
        # Create information section
        info_group = QGroupBox("System Info")
        info_layout = QVBoxLayout(info_group)
        
        # MIDI device info
        self.midi_device_label = QLabel("MIDI: Not Connected")
        self.midi_device_label.setStyleSheet("color: #ff6600; font-weight: bold;")
        info_layout.addWidget(self.midi_device_label)
        
        # BPM info
        self.bpm_label = QLabel("BPM: ---")
        self.bpm_label.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 14px;")
        info_layout.addWidget(self.bpm_label)
        
        # Audio input device
        self.audio_device_label = QLabel("Audio: Not Connected")
        self.audio_device_label.setStyleSheet("color: #00aaff; font-weight: bold;")
        info_layout.addWidget(self.audio_device_label)
        
        # Audio level indicators
        levels_layout = QVBoxLayout()
        
        # Overall level
        levels_layout.addWidget(QLabel("Audio Level:"))
        self.audio_level_bar = QProgressBar()
        self.audio_level_bar.setRange(0, 100)
        self.audio_level_bar.setValue(0)
        self.audio_level_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #333;
                border-radius: 3px;
                background-color: #1a1a1a;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff00, stop:0.7 #ffff00, stop:1 #ff0000);
                border-radius: 2px;
            }
        """)
        levels_layout.addWidget(self.audio_level_bar)
        
        # Frequency bands
        freq_bands_layout = QHBoxLayout()
        self.freq_band_bars = []
        band_names = ["Bass", "Low-Mid", "Mid", "High-Mid", "Treble"]
        
        for i, name in enumerate(band_names):
            band_layout = QVBoxLayout()
            band_bar = QProgressBar()
            band_bar.setRange(0, 100)
            band_bar.setValue(0)
            band_bar.setOrientation(Qt.Orientation.Vertical)
            band_bar.setFixedSize(20, 60)
            band_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid #333;
                    border-radius: 2px;
                    background-color: #1a1a1a;
                }}
                QProgressBar::chunk {{
                    background-color: hsl({i * 60}, 100%, 50%);
                    border-radius: 1px;
                }}
            """)
            
            band_label = QLabel(name)
            band_label.setStyleSheet("font-size: 8px; color: #ccc;")
            band_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            band_layout.addWidget(band_bar)
            band_layout.addWidget(band_label)
            freq_bands_layout.addLayout(band_layout)
            self.freq_band_bars.append(band_bar)
        
        levels_layout.addWidget(QLabel("Frequency Bands:"))
        levels_layout.addLayout(freq_bands_layout)
        info_layout.addLayout(levels_layout)
        
        mixer_layout.addWidget(info_group)
        
        # Stretch to fill remaining space
        mixer_layout.addStretch()
        
        return mixer_frame

    def update_fader_label(self, value):
        self.fader_label.setText(f"Mix: {value}% (A←→B)")

    def on_preset_selected(self, deck_id, preset_name):
        logging.debug(f"on_preset_selected called for deck {deck_id} with preset {preset_name}")
        if preset_name:
            # Update the mixer window
            self.mixer_window.set_deck_visualizer(deck_id, preset_name)
            # Wait a moment for the visualizer to be set, then update controls
            QTimer.singleShot(200, lambda: self.create_controls(deck_id))

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
            
            # Create control group
            control_frame = QFrame()
            control_frame.setFrameStyle(QFrame.Shape.Box)
            control_layout = QVBoxLayout(control_frame)
            
            # Control label
            label = QLabel(name)
            label.setStyleSheet("font-weight: bold; color: #ffffff;")
            control_layout.addWidget(label)
            
            if cfg.get("type") == "slider":
                slider = QSlider(Qt.Orientation.Horizontal)
                slider.setRange(cfg.get("min", 0), cfg.get("max", 100))
                slider.setValue(cfg.get("value", 0))
                slider.valueChanged.connect(
                    lambda value, n=name, d=deck_id: self.mixer_window.update_deck_control(d, n, value)
                )
                control_layout.addWidget(slider)
                
                # Value display
                value_label = QLabel(str(cfg.get("value", 0)))
                value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                value_label.setStyleSheet("color: #00ff00;")
                control_layout.addWidget(value_label)
                
                # Update value label when slider changes
                slider.valueChanged.connect(lambda v, lbl=value_label: lbl.setText(str(v)))
                
            elif cfg.get("type") == "dropdown":
                dropdown = QComboBox()
                dropdown.addItems(cfg.get("options", []))
                dropdown.setCurrentIndex(cfg.get("value", 0))
                dropdown.currentIndexChanged.connect(
                    lambda index, n=name, d=deck_id: self.mixer_window.update_deck_control(d, n, index)
                )
                control_layout.addWidget(dropdown)
            
            layout.addWidget(control_frame)
        
        layout.addStretch()

    def populate_midi_devices(self):
        """Populate MIDI device selector"""
        self.midi_device_selector.clear()
        self.midi_device_selector.addItem("No Device")
        
        devices = self.midi_engine.get_midi_input_ports()
        for device in devices:
            self.midi_device_selector.addItem(device)

    def populate_audio_devices(self):
        """Populate audio device selector"""
        self.audio_device_selector.clear()
        self.audio_device_selector.addItem("No Device")
        
        devices = self.audio_analyzer.get_available_devices()
        for device in devices:
            self.audio_device_selector.addItem(f"{device['name']} ({device['channels']} ch)")

    def on_midi_device_changed(self, device_name):
        """Handle MIDI device selection change"""
        if device_name == "No Device":
            self.midi_engine.close_midi_input_port()
        else:
            self.midi_engine.open_midi_input_port(device_name)

    def on_audio_device_changed(self, device_text):
        """Handle audio device selection change"""
        if device_text == "No Device":
            self.audio_analyzer.stop_analysis()
        else:
            # Extract device index from the text
            devices = self.audio_analyzer.get_available_devices()
            for i, device in enumerate(devices):
                if device_text.startswith(device['name']):
                    self.audio_analyzer.set_input_device(device['index'])
                    self.audio_analyzer.start_analysis()
                    break

    def update_bpm_display(self, bpm):
        """Update BPM display"""
        if bpm > 0:
            self.bpm_label.setText(f"BPM: {bpm:.1f}")
        else:
            self.bpm_label.setText("BPM: ---")

    def update_midi_device_display(self, device_name=None):
        """Update MIDI device display"""
        if device_name:
            self.midi_device_label.setText(f"MIDI: {device_name}")
        else:
            self.midi_device_label.setText("MIDI: Not Connected")

    def update_audio_level(self, level):
        """Update audio level display"""
        self.audio_level_bar.setValue(int(level))

    def update_frequency_bands(self, fft_data):
        """Update frequency band displays"""
        try:
            bands = self.audio_analyzer.get_frequency_bands(len(self.freq_band_bars))
            for i, bar in enumerate(self.freq_band_bars):
                if i < len(bands):
                    bar.setValue(int(bands[i]))
        except Exception as e:
            logging.error(f"Error updating frequency bands: {e}")

    def update_info_and_previews(self):
        """Update preview windows and system information"""
        # Update preview windows
        if hasattr(self, 'preview_a'):
            self.preview_a.update_preview()
        if hasattr(self, 'preview_b'):
            self.preview_b.update_preview()
        
        # Update audio device info
        if self.audio_analyzer.is_active():
            device_info = self.audio_analyzer.get_device_info()
            if device_info:
                self.audio_device_label.setText(f"Audio: {device_info['name']}")
            else:
                self.audio_device_label.setText("Audio: Active")
        else:
            self.audio_device_label.setText("Audio: Not Connected")