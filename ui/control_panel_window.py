import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QComboBox,
    QGroupBox, QGridLayout, QFrame, QProgressBar, QMenuBar, QMenu, QFormLayout, QApplication,
    QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction

from .preferences_dialog import PreferencesDialog
from .preview_gl_widget import PreviewGLWidget

class ControlPanelWindow(QMainWindow):
    def __init__(self, mixer_window, settings_manager, midi_engine, visualizer_manager, audio_analyzer, open_midi_mapping_dialog_callback):
        super().__init__(mixer_window)  # Set mixer window as parent for monitor management
        logging.debug("ControlPanelWindow.__init__ called")
        self.mixer_window = mixer_window
        self.settings_manager = settings_manager
        self.midi_engine = midi_engine
        self.visualizer_manager = visualizer_manager
        self.audio_analyzer = audio_analyzer
        self.open_midi_mapping_dialog_callback = open_midi_mapping_dialog_callback

        self.setWindowTitle("Audio Visualizer Pro - Control Panel")
        self.setGeometry(50, 50, 1200, 800)
        
        # Create menu bar
        self.create_menu_bar()

        # Create main UI
        self.create_ui()
        
        # Connect MIDI signals for activity monitoring
        try:
            if hasattr(self.midi_engine, 'midi_message_received'):
                self.midi_engine.midi_message_received.connect(self.on_midi_activity)
            if hasattr(self.midi_engine, 'note_on_received'):
                self.midi_engine.note_on_received.connect(self.on_note_activity)
            if hasattr(self.midi_engine, 'control_changed'):
                self.midi_engine.control_changed.connect(self.on_cc_activity)
        except Exception as e:
            logging.warning(f"Could not connect MIDI activity signals: {e}")
        
        # Connect audio signals
        try:
            self.audio_analyzer.level_changed.connect(self.update_audio_level)
            self.audio_analyzer.fft_data_ready.connect(self.update_frequency_bands)
        except Exception as e:
            logging.warning(f"Could not connect audio signals: {e}")
        
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

        midi_mapping_action = QAction('MIDI Mapping...', self)
        midi_mapping_action.triggered.connect(self.show_midi_mapping_dialog)
        settings_menu.addAction(midi_mapping_action)

        # View menu
        view_menu = menubar.addMenu('View')
        
        refresh_action = QAction('Refresh Devices', self)
        refresh_action.triggered.connect(self.refresh_devices)
        view_menu.addAction(refresh_action)

    def show_preferences(self):
        try:
            dialog = PreferencesDialog(self.settings_manager, self.midi_engine, self.audio_analyzer, self)
            dialog.exec()
        except Exception as e:
            logging.error(f"Error opening preferences: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo abrir las preferencias: {str(e)}")

    def show_midi_mapping_dialog(self):
        try:
            if self.open_midi_mapping_dialog_callback:
                self.open_midi_mapping_dialog_callback(self)
        except Exception as e:
            logging.error(f"Error opening MIDI mapping dialog: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo abrir el diálogo de mapeo MIDI: {str(e)}")

    def refresh_devices(self):
        """Refresh device information and update displays"""
        try:
            self.update_midi_device_display()
            self.update_audio_device_display()
            logging.info("Device information refreshed")
        except Exception as e:
            logging.error(f"Error refreshing devices: {e}")

    def move_control_panel_to_monitor(self, monitor_index):
        """Move control panel to specified monitor"""
        try:
            screens = QApplication.screens()
            if monitor_index < len(screens):
                screen = screens[monitor_index]
                self.move(screen.geometry().x(), screen.geometry().y())
                logging.debug(f"Moved control panel to monitor {monitor_index}")
        except Exception as e:
            logging.error(f"Error moving control panel to monitor {monitor_index}: {e}")

    def move_main_window_to_monitor(self, monitor_index):
        """Move main window to specified monitor"""
        try:
            screens = QApplication.screens()
            if monitor_index < len(screens):
                screen = screens[monitor_index]
                self.mixer_window.move(screen.geometry().x(), screen.geometry().y())
                logging.debug(f"Moved main window to monitor {monitor_index}")
        except Exception as e:
            logging.error(f"Error moving main window to monitor {monitor_index}: {e}")

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
        try:
            cp_monitor = self.settings_manager.get_setting("control_panel_monitor", 0)
            main_monitor = self.settings_manager.get_setting("main_window_monitor", 0)
            
            # Use QTimer to delay the move operations until after window is shown
            QTimer.singleShot(100, lambda: self.move_control_panel_to_monitor(cp_monitor))
            QTimer.singleShot(100, lambda: self.move_main_window_to_monitor(main_monitor))
        except Exception as e:
            logging.error(f"Error applying monitor settings: {e}")

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

        try:
            # Get the appropriate deck for preview
            deck = self.mixer_window.deck_a if deck_id == 'A' else self.mixer_window.deck_b
            preview_widget = PreviewGLWidget(deck)
            preview_widget.setFixedSize(250, 200)
            preview_layout.addWidget(preview_widget)

            # Store reference to preview widget
            if deck_id == 'A':
                self.preview_a = preview_widget
            else:
                self.preview_b = preview_widget

        except Exception as e:
            logging.error(f"Error creating preview widget for deck {deck_id}: {e}")
            error_label = QLabel(f"Preview Error: {str(e)}")
            error_label.setStyleSheet("color: red; background-color: #2a2a2a; padding: 10px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setFixedSize(250, 200)
            preview_layout.addWidget(error_label)
        
        deck_layout.addWidget(preview_group)
        
        # Visualizer selector
        selector_group = QGroupBox("Visualizer")
        selector_layout = QVBoxLayout(selector_group)
        
        selector = QComboBox()
        try:
            visualizer_names = self.visualizer_manager.get_visualizer_names()
            selector.addItems(visualizer_names)
            
            # Set initial selection and ensure mixer window is updated
            if visualizer_names:
                if deck_id == 'A':
                    selector.setCurrentIndex(0)
                    # Ensure mixer deck is set to this visualizer - USE THREAD-SAFE METHOD
                    QTimer.singleShot(200, lambda: self.set_deck_visualizer_safe('A', visualizer_names[0]))
                elif len(visualizer_names) > 1:
                    selector.setCurrentIndex(1)
                    QTimer.singleShot(200, lambda: self.set_deck_visualizer_safe('B', visualizer_names[1]))
                else:
                    selector.setCurrentIndex(0)
                    QTimer.singleShot(200, lambda: self.set_deck_visualizer_safe('B', visualizer_names[0]))
            
            selector.currentTextChanged.connect(lambda text, d=deck_id: self.on_preset_selected(d, text))
            
        except Exception as e:
            logging.error(f"Error setting up visualizer selector for deck {deck_id}: {e}")
            selector.addItem("Error loading visualizers")
        
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

    def set_deck_visualizer_safe(self, deck_id, visualizer_name):
        """Safely set deck visualizer with error handling - USES THREAD-SAFE METHOD"""
        try:
            logging.info(f"🎮 Control Panel setting deck {deck_id} to {visualizer_name}")
            # Use the thread-safe method
            self.mixer_window.safe_set_deck_visualizer(deck_id, visualizer_name)
        except Exception as e:
            logging.error(f"❌ Error setting visualizer {visualizer_name} for deck {deck_id}: {e}")

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
        # USE THREAD-SAFE METHOD
        self.fader.valueChanged.connect(self.mixer_window.safe_set_mix_value)
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
        self.midi_device_label = QLabel("MIDI: Checking...")
        self.midi_device_label.setStyleSheet("color: #ff6600; font-weight: bold;")
        info_layout.addWidget(self.midi_device_label)
        
        # BPM info
        self.bpm_label = QLabel("BPM: ---")
        self.bpm_label.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 14px;")
        info_layout.addWidget(self.bpm_label)
        
        # Audio input device
        self.audio_device_label = QLabel("Audio: Checking...")
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
        
        # MIDI Activity Monitor
        midi_activity_group = QGroupBox("MIDI Activity")
        midi_activity_layout = QVBoxLayout(midi_activity_group)
        
        # MIDI activity log
        self.midi_activity_log = QTextEdit()
        self.midi_activity_log.setMaximumHeight(120)
        self.midi_activity_log.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                border: 1px solid #333;
                border-radius: 3px;
            }
        """)
        self.midi_activity_log.setReadOnly(True)
        midi_activity_layout.addWidget(self.midi_activity_log)
        
        # Clear button for MIDI log
        clear_midi_btn = QPushButton("Clear Log")
        clear_midi_btn.setFixedHeight(25)
        clear_midi_btn.clicked.connect(self.clear_midi_log)
        clear_midi_btn.setStyleSheet("background-color: #444; color: white; border: 1px solid #666;")
        midi_activity_layout.addWidget(clear_midi_btn)
        
        mixer_layout.addWidget(midi_activity_group)
        
        # Stretch to fill remaining space
        mixer_layout.addStretch()
        
        return mixer_frame

    def update_fader_label(self, value):
        self.fader_label.setText(f"Mix: {value}% (A←→B)")

    def on_preset_selected(self, deck_id, preset_name):
        logging.info(f"🎮 on_preset_selected called for deck {deck_id} with preset {preset_name}")
        if preset_name and preset_name != "Error loading visualizers":
            try:
                # Update the mixer window - USE THREAD-SAFE METHOD
                self.mixer_window.safe_set_deck_visualizer(deck_id, preset_name)
                # Wait a moment for the visualizer to be set, then update controls
                QTimer.singleShot(200, lambda: self.create_controls(deck_id))
            except Exception as e:
                logging.error(f"❌ Error in on_preset_selected: {e}")

    def create_controls(self, deck_id):
        logging.debug(f"🎛️ Creating controls for deck {deck_id}") # Changed to debug
        
        try:
            layout = self.controls_layout_a if deck_id == 'A' else self.controls_layout_b

            # Clear old controls
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget: 
                    widget.deleteLater()

            # Get controls from the mixer window
            controls = self.mixer_window.get_deck_controls(deck_id)
            logging.debug(f"📋 Got controls for deck {deck_id}: {controls}") # Changed to debug
            
            if not controls:
                no_controls_label = QLabel("No controls available")
                layout.addWidget(no_controls_label)
                layout.addStretch()
                logging.debug(f"No controls found for deck {deck_id}") # Added debug
                return
                
            for name, cfg in controls.items():
                logging.debug(f"🔧 Adding control: {name} = {cfg}")
                
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
                        lambda value, n=name, d=deck_id: self.update_deck_control_safe(d, n, value)
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
                    options = cfg.get("options", [])
                    dropdown.addItems(options)
                    current_value = cfg.get("value", 0)
                    if current_value < len(options):
                        dropdown.setCurrentIndex(current_value)
                    dropdown.currentIndexChanged.connect(
                        lambda index, n=name, d=deck_id: self.update_deck_control_safe(d, n, index)
                    )
                    control_layout.addWidget(dropdown)
                
                layout.addWidget(control_frame)
            
            layout.addStretch()
            
        except Exception as e:
            logging.error(f"❌ Error creating controls for deck {deck_id}: {e}")
            # Show error in the controls area
            error_label = QLabel(f"Error loading controls: {str(e)}")
            error_label.setStyleSheet("color: red; background-color: #2a2a2a; padding: 5px;")
            layout.addWidget(error_label)
            layout.addStretch()

    def update_deck_control_safe(self, deck_id, name, value):
        """Safely update deck control with error handling - USES THREAD-SAFE METHOD"""
        try:
            logging.info(f"🎛️ Control Panel updating deck {deck_id} control {name} to {value}")
            # Use the thread-safe method
            self.mixer_window.safe_update_deck_control(deck_id, name, value)
        except Exception as e:
            logging.error(f"❌ Error updating deck control {name} for deck {deck_id}: {e}")

    def update_bpm_display(self, bpm):
        """Update BPM display"""
        try:
            if bpm > 0:
                self.bpm_label.setText(f"BPM: {bpm:.1f}")
            else:
                self.bpm_label.setText("BPM: ---")
        except Exception as e:
            logging.error(f"Error updating BPM display: {e}")

    def update_midi_device_display(self, device_name=None):
        """Update MIDI device display"""
        try:
            if device_name:
                self.midi_device_label.setText(f"MIDI: {device_name}")
                self.midi_device_label.setStyleSheet("color: #00ff00; font-weight: bold;")
            else:
                # Check current MIDI status
                midi_connected = False
                device_info = "Not Connected"
                
                if self.midi_engine:
                    try:
                        if hasattr(self.midi_engine, 'list_input_ports'):
                            ports = self.midi_engine.list_input_ports()
                            if ports:
                                device_info = f"Available ({len(ports)} devices)"
                                midi_connected = True
                        
                        # Check if a specific device is connected
                        if hasattr(self.midi_engine, 'is_port_open'):
                            if self.midi_engine.is_port_open():
                                device_info = "Connected"
                                midi_connected = True
                        elif hasattr(self.midi_engine, 'is_input_port_open'):
                            if self.midi_engine.is_input_port_open():
                                device_info = "Connected"
                                midi_connected = True
                                
                    except Exception as e:
                        device_info = f"Error: {str(e)}"
                        logging.error(f"Error checking MIDI status: {e}")
                
                self.midi_device_label.setText(f"MIDI: {device_info}")
                if midi_connected:
                    self.midi_device_label.setStyleSheet("color: #00ff00; font-weight: bold;")
                else:
                    self.midi_device_label.setStyleSheet("color: #ff6600; font-weight: bold;")
                    
        except Exception as e:
            logging.error(f"Error updating MIDI device display: {e}")
            self.midi_device_label.setText("MIDI: Error")
            self.midi_device_label.setStyleSheet("color: red; font-weight: bold;")

    def update_audio_device_display(self):
        """Update audio device display"""
        try:
            if self.audio_analyzer.is_active():
                device_info = self.audio_analyzer.get_device_info()
                if device_info:
                    self.audio_device_label.setText(f"Audio: {device_info['name']}")
                    self.audio_device_label.setStyleSheet("color: #00ff00; font-weight: bold;")
                else:
                    self.audio_device_label.setText("Audio: Active")
                    self.audio_device_label.setStyleSheet("color: #00aaff; font-weight: bold;")
            else:
                self.audio_device_label.setText("Audio: Not Connected")
                self.audio_device_label.setStyleSheet("color: #ff6600; font-weight: bold;")
        except Exception as e:
            logging.error(f"Error updating audio device display: {e}")
            self.audio_device_label.setText("Audio: Error")
            self.audio_device_label.setStyleSheet("color: red; font-weight: bold;")

    def update_audio_level(self, level):
        """Update audio level display"""
        try:
            self.audio_level_bar.setValue(int(level))
        except Exception as e:
            logging.error(f"Error updating audio level: {e}")

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
        try:
            if hasattr(self, 'preview_a'):
                self.preview_a.update_preview()
            if hasattr(self, 'preview_b'):
                self.preview_b.update_preview()
            
            # Update device displays periodically (every 2 seconds)
            if not hasattr(self, '_last_device_update'):
                self._last_device_update = 0
            
            import time
            current_time = time.time()
            if current_time - self._last_device_update > 2.0:
                self.update_midi_device_display()
                self.update_audio_device_display()
                self._last_device_update = current_time
                
        except Exception as e:
            logging.error(f"Error in update_info_and_previews: {e}")

    def on_midi_activity(self, msg):
        """Handle raw MIDI activity for monitoring"""
        try:
            import time
            timestamp = time.strftime("%H:%M:%S")
            
            # Only log notes and CC messages, skip sync/timing messages
            if hasattr(msg, 'type'):
                if msg.type == 'note_on' and hasattr(msg, 'velocity') and msg.velocity > 0:
                    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                    octave = msg.note // 12 - 1
                    note_name = note_names[msg.note % 12]
                    activity_msg = f"[{timestamp}] Note ON: {note_name}{octave} (#{msg.note}) Ch:{msg.channel+1} Vel:{msg.velocity}"
                    self.add_midi_activity(activity_msg)
                    
                elif msg.type == 'note_off' or (msg.type == 'note_on' and hasattr(msg, 'velocity') and msg.velocity == 0):
                    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                    octave = msg.note // 12 - 1
                    note_name = note_names[msg.note % 12]
                    activity_msg = f"[{timestamp}] Note OFF: {note_name}{octave} (#{msg.note}) Ch:{msg.channel+1}"
                    self.add_midi_activity(activity_msg)
                    
                elif msg.type == 'control_change':
                    activity_msg = f"[{timestamp}] CC: #{msg.control} Ch:{msg.channel+1} Val:{msg.value}"
                    self.add_midi_activity(activity_msg)
                    
                elif msg.type == 'program_change':
                    activity_msg = f"[{timestamp}] PC: #{msg.program} Ch:{msg.channel+1}"
                    self.add_midi_activity(activity_msg)
                    
                elif msg.type == 'pitchwheel':
                    activity_msg = f"[{timestamp}] Pitch: {msg.pitch} Ch:{msg.channel+1}"
                    self.add_midi_activity(activity_msg)
                    
        except Exception as e:
            logging.error(f"Error handling MIDI activity: {e}")

    def on_note_activity(self, note, velocity):
        """Handle note activity (alternative signal)"""
        try:
            import time
            timestamp = time.strftime("%H:%M:%S")
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            octave = note // 12 - 1
            note_name = note_names[note % 12]
            activity_msg = f"[{timestamp}] Note: {note_name}{octave} (#{note}) Vel:{velocity}"
            self.add_midi_activity(activity_msg)
        except Exception as e:
            logging.error(f"Error handling note activity: {e}")

    def on_cc_activity(self, control_id, value):
        """Handle CC activity (alternative signal)"""
        try:
            import time
            timestamp = time.strftime("%H:%M:%S")
            activity_msg = f"[{timestamp}] Control: {control_id} = {value}"
            self.add_midi_activity(activity_msg)
        except Exception as e:
            logging.error(f"Error handling CC activity: {e}")

    def add_midi_activity(self, message):
        """Add a message to the MIDI activity log"""
        try:
            if hasattr(self, 'midi_activity_log'):
                # Add message to log
                self.midi_activity_log.append(message)
                
                # Keep only last 50 lines to prevent memory issues
                document = self.midi_activity_log.document()
                if document.blockCount() > 50:
                    cursor = self.midi_activity_log.textCursor()
                    cursor.movePosition(cursor.MoveOperation.Start)
                    cursor.select(cursor.SelectionType.LineUnderCursor)
                    cursor.removeSelectedText()
                    cursor.deleteChar()  # Remove the newline
                
                # Auto-scroll to bottom
                scrollbar = self.midi_activity_log.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
                
        except Exception as e:
            logging.error(f"Error adding MIDI activity: {e}")

    def clear_midi_log(self):
        """Clear the MIDI activity log"""
        try:
            if hasattr(self, 'midi_activity_log'):
                self.midi_activity_log.clear()
                self.add_midi_activity("MIDI Activity Monitor - Log Cleared")
        except Exception as e:
            logging.error(f"Error clearing MIDI log: {e}")