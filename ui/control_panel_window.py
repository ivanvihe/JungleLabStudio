# ui/control_panel_window.py
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QComboBox,
    QGroupBox, QGridLayout, QFrame, QProgressBar, QMenuBar, QMenu, QFormLayout, QApplication,
    QMessageBox, QTextEdit, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QMutex, QMutexLocker
from PyQt6.QtGui import QAction

from .preferences_dialog import PreferencesDialog
from .midi_mapping_dialog import MidiMappingDialog

class ControlPanelWindow(QMainWindow):
    def __init__(self, mixer_window, settings_manager, midi_engine, visualizer_manager, audio_analyzer):
        super().__init__(mixer_window)  # Set mixer window as parent for monitor management
        logging.debug("ControlPanelWindow.__init__ called")
        
        # Store references
        self.mixer_window = mixer_window
        self.settings_manager = settings_manager
        self.midi_engine = midi_engine
        self.visualizer_manager = visualizer_manager
        self.audio_analyzer = audio_analyzer

        # Thread safety
        self._mutex = QMutex()
        
        # UI state tracking
        self.preset_selectors = {}
        self.controls_layouts = {}
        self.last_device_update = 0
        
        self.setWindowTitle("Audio Visualizer Pro - Control Panel")
        self.setGeometry(50, 50, 1200, 800)
        
        # Create menu bar
        self.create_menu_bar()

        # Create main UI
        self.create_ui()
        
        # Connect MIDI signals for activity monitoring
        self.setup_midi_connections()
        
        # Connect audio signals
        self.setup_audio_connections()
        
        # Timer for updating system information
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_info)
        self.update_timer.start(100)  # 10 FPS for UI updates

    def setup_midi_connections(self):
        """Setup MIDI signal connections"""
        try:
            if hasattr(self.midi_engine, 'midi_message_received'):
                self.midi_engine.midi_message_received.connect(self.on_midi_activity)
            if hasattr(self.midi_engine, 'note_on_received'):
                self.midi_engine.note_on_received.connect(self.on_note_activity)
            if hasattr(self.midi_engine, 'control_changed'):
                self.midi_engine.control_changed.connect(self.on_cc_activity)
            if hasattr(self.midi_engine, 'device_connected'):
                self.midi_engine.device_connected.connect(self.on_midi_device_connected)
            if hasattr(self.midi_engine, 'device_disconnected'):
                self.midi_engine.device_disconnected.connect(self.on_midi_device_disconnected)
        except Exception as e:
            logging.warning(f"Could not connect MIDI activity signals: {e}")

    def setup_audio_connections(self):
        """Setup audio signal connections"""
        try:
            if hasattr(self.audio_analyzer, 'level_changed'):
                self.audio_analyzer.level_changed.connect(self.update_audio_level)
            if hasattr(self.audio_analyzer, 'fft_data_ready'):
                self.audio_analyzer.fft_data_ready.connect(self.update_frequency_bands)
        except Exception as e:
            logging.warning(f"Could not connect audio signals: {e}")

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # Settings menu
        settings_menu = menubar.addMenu('Settings')
        
        preferences_action = QAction('Preferences...', self)
        preferences_action.triggered.connect(self.show_preferences)
        settings_menu.addAction(preferences_action)

        # View menu
        view_menu = menubar.addMenu('View')
        
        refresh_action = QAction('Refresh Devices', self)
        refresh_action.triggered.connect(self.refresh_devices)
        view_menu.addAction(refresh_action)

        reload_visualizers_action = QAction('Reload Visualizers', self)
        reload_visualizers_action.triggered.connect(self.reload_visualizers)
        view_menu.addAction(reload_visualizers_action)

    def show_preferences(self):
        try:
            dialog = PreferencesDialog(self.settings_manager, self.midi_engine, self.audio_analyzer, self)
            dialog.exec()
        except Exception as e:
            logging.error(f"Error opening preferences: {e}")
            QMessageBox.critical(self, "Error", f"Could not open preferences: {str(e)}")


    def refresh_devices(self):
        """Refresh device information and update displays"""
        try:
            self.update_midi_device_display()
            self.update_audio_device_display()
            logging.info("Device information refreshed")
        except Exception as e:
            logging.error(f"Error refreshing devices: {e}")

    def reload_visualizers(self):
        """Reload visualizers and update selectors"""
        try:
            self.visualizer_manager.reload_visualizers()
            self.update_visualizer_selectors()
            logging.info("Visualizers reloaded")
        except Exception as e:
            logging.error(f"Error reloading visualizers: {e}")

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
        
        # Apply monitor settings after a delay
        QTimer.singleShot(200, self.apply_monitor_settings)

    def apply_monitor_settings(self):
        """Apply saved monitor settings"""
        try:
            cp_monitor = self.settings_manager.get_setting("control_panel_monitor", 0)
            main_monitor = self.settings_manager.get_setting("main_window_monitor", 0)
            
            screens = QApplication.screens()
            if cp_monitor < len(screens):
                screen = screens[cp_monitor]
                self.move(screen.geometry().x(), screen.geometry().y())
                logging.debug(f"Moved control panel to monitor {cp_monitor}")
                
        except Exception as e:
            logging.error(f"Error applying monitor settings: {e}")

    def create_deck_section(self, deck_id):
        """Create a complete deck section with controls and mappings"""
        deck_frame = QFrame()
        deck_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        deck_frame.setMaximumWidth(400)
        deck_layout = QVBoxLayout(deck_frame)
        
        # Deck title
        title = QLabel(f"<h2>DECK {deck_id}</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #00ff00; background-color: #1a1a1a; padding: 10px; border-radius: 5px;")
        deck_layout.addWidget(title)
        
        # Visualizer selector
        selector_group = QGroupBox("Visualizer")
        selector_layout = QVBoxLayout(selector_group)
        
        selector = QComboBox()
        try:
            visualizer_names = self.visualizer_manager.get_visualizer_names()
            if visualizer_names:
                selector.addItems(visualizer_names)
                
                # Set different initial selections for each deck
                if deck_id == 'A':
                    # Try to select "Simple Test" for deck A
                    if "Simple Test" in visualizer_names:
                        selector.setCurrentText("Simple Test")
                    else:
                        selector.setCurrentIndex(0)
                else:  # Deck B
                    # Try to select "Wire Terrain" for deck B, or second item
                    if "Wire Terrain" in visualizer_names:
                        selector.setCurrentText("Wire Terrain")
                    elif len(visualizer_names) > 1:
                        selector.setCurrentIndex(1)
                    else:
                        selector.setCurrentIndex(0)
                
                # Connect signal
                selector.currentTextChanged.connect(lambda text, d=deck_id: self.on_preset_selected(d, text))
                
                # Store reference
                self.preset_selectors[deck_id] = selector
                
                # Apply initial selection with delay
                QTimer.singleShot(500, lambda: self.apply_initial_visualizer(deck_id, selector.currentText()))
                
            else:
                selector.addItem("No visualizers available")
                logging.warning("No visualizers found!")
            
        except Exception as e:
            logging.error(f"Error setting up visualizer selector for deck {deck_id}: {e}")
            selector.addItem("Error loading visualizers")
        
        selector_layout.addWidget(selector)
        deck_layout.addWidget(selector_group)
        
        # Controls section with scroll area
        controls_group = QGroupBox("Controls")
        controls_scroll = QScrollArea()
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        controls_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        controls_scroll.setMaximumHeight(150)
        
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        controls_scroll.setWidget(controls_widget)
        
        controls_group_layout = QVBoxLayout(controls_group)
        controls_group_layout.addWidget(controls_scroll)
        deck_layout.addWidget(controls_group)

        # Embedded MIDI mapping widget
        midi_group = QGroupBox("MIDI Mapping")
        midi_layout = QVBoxLayout(midi_group)
        midi_widget = MidiMappingDialog(
            self.visualizer_manager.get_visualizer_names(),
            self.midi_engine,
            deck_id=deck_id,
            parent=self,
            as_widget=True,
        )
        midi_layout.addWidget(midi_widget)
        deck_layout.addWidget(midi_group)

        # Store reference to controls layout
        self.controls_layouts[deck_id] = controls_layout

        return deck_frame

    def apply_initial_visualizer(self, deck_id, visualizer_name):
        """Apply initial visualizer selection"""
        if visualizer_name and visualizer_name not in ["No visualizers available", "Error loading visualizers"]:
            try:
                logging.info(f"🎮 Applying initial visualizer for deck {deck_id}: {visualizer_name}")
                self.mixer_window.safe_set_deck_visualizer(deck_id, visualizer_name)
                # Update controls after a short delay
                QTimer.singleShot(800, lambda: self.create_controls(deck_id))
            except Exception as e:
                logging.error(f"Error applying initial visualizer: {e}")

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
        
        info_layout.addLayout(levels_layout)
        mixer_layout.addWidget(info_group)
        
        # MIDI Activity Monitor
        midi_activity_group = QGroupBox("MIDI Activity")
        midi_activity_layout = QVBoxLayout(midi_activity_group)
        
        # MIDI activity log
        self.midi_activity_log = QTextEdit()
        self.midi_activity_log.setMaximumHeight(100)
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
        """Update fader label"""
        self.fader_label.setText(f"Mix: {value}% (A←→B)")

    def on_preset_selected(self, deck_id, preset_name):
        """Handle preset selection"""
        logging.info(f"🎮 Preset selected for deck {deck_id}: {preset_name}")
        if preset_name and preset_name not in ["No visualizers available", "Error loading visualizers"]:
            try:
                # Update the mixer window
                self.mixer_window.safe_set_deck_visualizer(deck_id, preset_name)
                # Update controls after a short delay
                QTimer.singleShot(300, lambda: self.create_controls(deck_id))
            except Exception as e:
                logging.error(f"Error in on_preset_selected: {e}")

    def create_controls(self, deck_id):
        """Create control widgets for a deck"""
        with QMutexLocker(self._mutex):
            logging.debug(f"🎛️ Creating controls for deck {deck_id}")
            
            try:
                layout = self.controls_layouts.get(deck_id)
                if not layout:
                    logging.warning(f"No controls layout found for deck {deck_id}")
                    return

                # Clear old controls
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget: 
                        widget.deleteLater()

                # Get controls from the mixer window
                controls = self.mixer_window.get_deck_controls(deck_id)
                logging.debug(f"📋 Got controls for deck {deck_id}: {list(controls.keys()) if controls else 'None'}")
                
                if not controls:
                    no_controls_label = QLabel("No controls available")
                    no_controls_label.setStyleSheet("color: #888; font-style: italic; padding: 10px;")
                    layout.addWidget(no_controls_label)
                    layout.addStretch()
                    return
                    
                # Create controls
                for name, cfg in controls.items():
                    control_widget = self.create_control_widget(deck_id, name, cfg)
                    if control_widget:
                        layout.addWidget(control_widget)
                
                layout.addStretch()
                
            except Exception as e:
                logging.error(f"Error creating controls for deck {deck_id}: {e}")
                # Show error in the controls area
                error_label = QLabel(f"Error loading controls: {str(e)}")
                error_label.setStyleSheet("color: red; background-color: #2a2a2a; padding: 5px;")
                layout.addWidget(error_label)
                layout.addStretch()

    def create_control_widget(self, deck_id, name, cfg):
        """Create a single control widget"""
        try:
            # Create control frame
            control_frame = QFrame()
            control_frame.setFrameStyle(QFrame.Shape.Box)
            control_frame.setStyleSheet("QFrame { border: 1px solid #444; border-radius: 5px; margin: 2px; }")
            control_layout = QVBoxLayout(control_frame)
            control_layout.setSpacing(5)
            control_layout.setContentsMargins(8, 8, 8, 8)
            
            # Control label
            label = QLabel(name)
            label.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 11px;")
            control_layout.addWidget(label)
            
            if cfg.get("type") == "slider":
                # Create slider with value display
                slider_layout = QHBoxLayout()
                
                slider = QSlider(Qt.Orientation.Horizontal)
                slider.setRange(cfg.get("min", 0), cfg.get("max", 100))
                slider.setValue(cfg.get("value", 0))
                slider.setStyleSheet("""
                    QSlider::groove:horizontal {
                        border: 1px solid #444;
                        height: 8px;
                        background: #222;
                        border-radius: 4px;
                    }
                    QSlider::handle:horizontal {
                        background: #00ff00;
                        border: 1px solid #333;
                        width: 18px;
                        margin: -5px 0;
                        border-radius: 9px;
                    }
                    QSlider::handle:horizontal:hover {
                        background: #44ff44;
                    }
                """)
                
                # Value display
                value_label = QLabel(str(cfg.get("value", 0)))
                value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                value_label.setStyleSheet("color: #00ff00; font-weight: bold; min-width: 30px;")
                value_label.setFixedWidth(40)
                
                slider_layout.addWidget(slider)
                slider_layout.addWidget(value_label)
                control_layout.addLayout(slider_layout)
                
                # Connect signals
                slider.valueChanged.connect(
                    lambda value, n=name, d=deck_id: self.update_deck_control_safe(d, n, value)
                )
                slider.valueChanged.connect(lambda v, lbl=value_label: lbl.setText(str(v)))
                
            elif cfg.get("type") == "dropdown":
                dropdown = QComboBox()
                dropdown.setStyleSheet("""
                    QComboBox {
                        background-color: #333;
                        color: white;
                        border: 1px solid #555;
                        border-radius: 3px;
                        padding: 2px;
                    }
                    QComboBox::drop-down {
                        border: none;
                    }
                    QComboBox::down-arrow {
                        image: none;
                        border: none;
                    }
                """)
                
                options = cfg.get("options", [])
                dropdown.addItems(options)
                current_value = cfg.get("value", 0)
                if current_value < len(options):
                    dropdown.setCurrentIndex(current_value)
                    
                dropdown.currentIndexChanged.connect(
                    lambda index, n=name, d=deck_id: self.update_deck_control_safe(d, n, index)
                )
                control_layout.addWidget(dropdown)
            
            return control_frame
            
        except Exception as e:
            logging.error(f"Error creating control widget {name}: {e}")
            return None

    def update_deck_control_safe(self, deck_id, name, value):
        """Safely update deck control"""
        try:
            logging.debug(f"🎛️ Updating deck {deck_id} control {name} to {value}")
            self.mixer_window.safe_update_deck_control(deck_id, name, value)
        except Exception as e:
            logging.error(f"Error updating deck control {name} for deck {deck_id}: {e}")

    def update_visualizer_selectors(self):
        """Update visualizer selectors with current list"""
        try:
            visualizer_names = self.visualizer_manager.get_visualizer_names()
            
            for deck_id, selector in self.preset_selectors.items():
                current_selection = selector.currentText()
                selector.clear()
                
                if visualizer_names:
                    selector.addItems(visualizer_names)
                    # Try to restore previous selection
                    if current_selection in visualizer_names:
                        selector.setCurrentText(current_selection)
                else:
                    selector.addItem("No visualizers available")
                    
        except Exception as e:
            logging.error(f"Error updating visualizer selectors: {e}")

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
                        if hasattr(self.midi_engine, 'is_port_open') and self.midi_engine.is_port_open():
                            device_info = "Connected"
                            midi_connected = True
                        elif hasattr(self.midi_engine, 'list_input_ports'):
                            ports = self.midi_engine.list_input_ports()
                            if ports:
                                device_info = f"Available ({len(ports)} devices)"
                    except Exception as e:
                        device_info = f"Error: {str(e)}"
                
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
            if self.audio_analyzer and self.audio_analyzer.is_active():
                device_info = getattr(self.audio_analyzer, 'get_device_info', lambda: None)()
                if device_info:
                    self.audio_device_label.setText(f"Audio: {device_info.get('name', 'Active')}")
                else:
                    self.audio_device_label.setText("Audio: Active")
                self.audio_device_label.setStyleSheet("color: #00ff00; font-weight: bold;")
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
            self.audio_level_bar.setValue(int(max(0, min(100, level))))
        except Exception as e:
            logging.error(f"Error updating audio level: {e}")

    def update_frequency_bands(self, fft_data):
        """Update frequency band displays"""
        try:
            # This would require frequency band bars to be implemented
            pass
        except Exception as e:
            logging.error(f"Error updating frequency bands: {e}")

    def update_info(self):
        """Update system information"""
        try:
            # Update device displays periodically
            import time
            current_time = time.time()
            if current_time - self.last_device_update > 3.0:  # Every 3 seconds
                self.update_midi_device_display()
                self.update_audio_device_display()
                self.last_device_update = current_time

        except Exception as e:
            logging.error(f"Error in update_info: {e}")

    def on_midi_device_connected(self, device_name):
        """Handle MIDI device connection"""
        try:
            self.update_midi_device_display(device_name)
            logging.info(f"🎹 MIDI device connected: {device_name}")
        except Exception as e:
            logging.error(f"Error handling MIDI device connection: {e}")

    def on_midi_device_disconnected(self, device_name):
        """Handle MIDI device disconnection"""
        try:
            self.update_midi_device_display(None)
            logging.info(f"🎹 MIDI device disconnected: {device_name}")
        except Exception as e:
            logging.error(f"Error handling MIDI device disconnection: {e}")

    def on_midi_activity(self, msg):
        """Handle raw MIDI activity for monitoring"""
        try:
            import time
            timestamp = time.strftime("%H:%M:%S")
            
            if hasattr(msg, 'type'):
                if msg.type == 'note_on' and hasattr(msg, 'velocity') and msg.velocity > 0:
                    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                    octave = msg.note // 12 - 1
                    note_name = note_names[msg.note % 12]
                    activity_msg = f"[{timestamp}] Note ON: {note_name}{octave} Ch:{msg.channel+1} Vel:{msg.velocity}"
                    self.add_midi_activity(activity_msg)
                    
                elif msg.type == 'control_change':
                    activity_msg = f"[{timestamp}] CC: #{msg.control} Ch:{msg.channel+1} Val:{msg.value}"
                    self.add_midi_activity(activity_msg)
                    
        except Exception as e:
            logging.error(f"Error handling MIDI activity: {e}")

    def on_note_activity(self, note, velocity):
        """Handle note activity"""
        try:
            import time
            timestamp = time.strftime("%H:%M:%S")
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            octave = note // 12 - 1
            note_name = note_names[note % 12]
            activity_msg = f"[{timestamp}] Note: {note_name}{octave} Vel:{velocity}"
            self.add_midi_activity(activity_msg)
        except Exception as e:
            logging.error(f"Error handling note activity: {e}")

    def on_cc_activity(self, control_id, value):
        """Handle CC activity"""
        try:
            import time
            timestamp = time.strftime("%H:%M:%S")
            activity_msg = f"[{timestamp}] CC: {control_id} = {value}"
            self.add_midi_activity(activity_msg)
        except Exception as e:
            logging.error(f"Error handling CC activity: {e}")

    def add_midi_activity(self, message):
        """Add a message to the MIDI activity log"""
        try:
            if hasattr(self, 'midi_activity_log'):
                # Add message to log
                self.midi_activity_log.append(message)
                
                # Keep only last 30 lines to prevent memory issues
                document = self.midi_activity_log.document()
                if document.blockCount() > 30:
                    cursor = self.midi_activity_log.textCursor()
                    cursor.movePosition(cursor.MoveOperation.Start)
                    cursor.select(cursor.SelectionType.LineUnderCursor)
                    cursor.removeSelectedText()
                    cursor.deleteChar()
                
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

    def cleanup(self):
        """Clean up resources"""
        try:
            # Stop timer
            if hasattr(self, 'update_timer'):
                self.update_timer.stop()
            
            logging.debug("✅ Control panel cleaned up")
            
        except Exception as e:
            logging.error(f"Error cleaning up control panel: {e}")

    def closeEvent(self, event):
        """Handle close event"""
        try:
            self.cleanup()
            super().closeEvent(event)
        except Exception as e:
            logging.error(f"Error in closeEvent: {e}")
            super().closeEvent(event)