# ui/control_panel_window.py - REDISEÑADO PARA OPERACIÓN 100% DESDE ABLETON
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QGroupBox, QGridLayout, QFrame, QProgressBar, QMenuBar, QMenu, QFormLayout, QApplication,
    QMessageBox, QTextEdit, QScrollArea, QSplitter, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt6.QtCore import Qt, QTimer, QMutex, QMutexLocker, QSize
from PyQt6.QtGui import QAction, QFont, QColor

from .preferences_dialog import PreferencesDialog

class ControlPanelWindow(QMainWindow):
    def __init__(self, mixer_window, settings_manager, midi_engine, visualizer_manager, audio_analyzer):
        super().__init__(mixer_window)  # Set mixer window as parent for monitor management
        logging.debug("ControlPanelWindow.__init__ called - REDISEÑADO PARA ABLETON")
        
        # Store references
        self.mixer_window = mixer_window
        self.settings_manager = settings_manager
        self.midi_engine = midi_engine
        self.visualizer_manager = visualizer_manager
        self.audio_analyzer = audio_analyzer

        # Thread safety
        self._mutex = QMutex()
        
        # Estado de actividad MIDI en tiempo real
        self.deck_a_status = {
            'active_preset': None,
            'last_activity': None,
            'controls': {'intensity': 0, 'speed': 0, 'color': 0}
        }
        
        self.deck_b_status = {
            'active_preset': None,
            'last_activity': None,
            'controls': {'intensity': 0, 'speed': 0, 'color': 0}
        }
        
        self.mix_status = {
            'crossfader_value': 50,
            'last_mix_action': None,
            'last_activity': None
        }
        
        self.setWindowTitle("Audio Visualizer Pro - MIDI Control Center (Ableton Mode)")
        self.setGeometry(50, 50, 1600, 900)
        
        # Create menu bar
        self.create_menu_bar()

        # Create main UI - REDISEÑADO
        self.create_midi_focused_ui()
        
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
            if hasattr(self.midi_engine, 'preset_loaded_on_deck'):
                self.midi_engine.preset_loaded_on_deck.connect(self.on_preset_loaded_on_deck)
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

        # MIDI menu
        midi_menu = menubar.addMenu('MIDI')
        
        test_mappings_action = QAction('Test MIDI Mappings', self)
        test_mappings_action.triggered.connect(self.test_midi_mappings)
        midi_menu.addAction(test_mappings_action)
        
        print_mappings_action = QAction('Print Current Mappings', self)
        print_mappings_action.triggered.connect(self.print_midi_mappings)
        midi_menu.addAction(print_mappings_action)

        # View menu
        view_menu = menubar.addMenu('View')
        
        refresh_action = QAction('Refresh Devices', self)
        refresh_action.triggered.connect(self.refresh_devices)
        view_menu.addAction(refresh_action)

    def create_midi_focused_ui(self):
        """Create the new MIDI-focused UI"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main layout
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header Section
        header_section = self.create_header_section()
        main_layout.addWidget(header_section)
        
        # Main Content: 3 Column Layout (Deck A, Mix, Deck B)
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Column 1: Deck A
        deck_a_widget = self.create_deck_section('A')
        content_splitter.addWidget(deck_a_widget)
        
        # Column 2: Mix Section
        mix_widget = self.create_mix_section()
        content_splitter.addWidget(mix_widget)
        
        # Column 3: Deck B
        deck_b_widget = self.create_deck_section('B')
        content_splitter.addWidget(deck_b_widget)
        
        # Set equal proportions
        content_splitter.setSizes([500, 600, 500])
        main_layout.addWidget(content_splitter)
        
        # Footer: Drum Rack Guide
        footer_section = self.create_footer_section()
        main_layout.addWidget(footer_section)

    def create_header_section(self):
        """Create header with status information including MIDI indicator and debug button"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #00ff00;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        
        # Title
        title_label = QLabel("<b>🎛️ CONTROL PANEL MIDI - Operación 100% desde Ableton Live</b>")
        title_label.setStyleSheet("font-size: 18px; color: #00ff00; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # MIDI Activity Indicator (NUEVO)
        midi_activity = self.create_midi_activity_indicator()
        header_layout.addWidget(midi_activity)
        
        # MIDI Status
        self.midi_status_label = QLabel("MIDI: Checking...")
        self.midi_status_label.setStyleSheet("font-weight: bold; padding: 5px; color: #ffaa00;")
        header_layout.addWidget(self.midi_status_label)
        
        # Debug Button (NUEVO)
        debug_btn = QPushButton("🔍 Debug")
        debug_btn.setMaximumWidth(80)
        debug_btn.setStyleSheet("background-color: #0066cc; color: white; padding: 5px;")
        debug_btn.clicked.connect(self.run_midi_debug)
        header_layout.addWidget(debug_btn)
        
        # Audio Level (compact)
        level_widget = QWidget()
        level_layout = QVBoxLayout(level_widget)
        level_layout.setContentsMargins(0, 0, 0, 0)
        level_layout.setSpacing(2)
        
        level_label = QLabel("Audio Level:")
        level_label.setStyleSheet("font-size: 10px; color: #ffffff;")
        level_layout.addWidget(level_label)
        
        self.audio_level_bar = QProgressBar()
        self.audio_level_bar.setRange(0, 100)
        self.audio_level_bar.setValue(0)
        self.audio_level_bar.setMaximumHeight(15)
        self.audio_level_bar.setMaximumWidth(120)
        self.audio_level_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #333;
                border-radius: 3px;
                background-color: #1a1a1a;
                text-align: center;
                font-size: 9px;
                color: white;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff00, stop:0.7 #ffff00, stop:1 #ff0000);
                border-radius: 2px;
            }
        """)
        level_layout.addWidget(self.audio_level_bar)
        
        header_layout.addWidget(level_widget)
        
        return header_frame

    def create_midi_activity_indicator(self):
        """Crear indicador visual de actividad MIDI como en Ableton"""
        indicator_widget = QWidget()
        indicator_layout = QHBoxLayout(indicator_widget)
        indicator_layout.setContentsMargins(5, 2, 5, 2)
        indicator_layout.setSpacing(5)
        
        # Label MIDI
        midi_label = QLabel("MIDI:")
        midi_label.setStyleSheet("color: #ffffff; font-size: 10px;")
        indicator_layout.addWidget(midi_label)
        
        # Indicador LED (círculo)
        self.midi_led = QLabel("●")
        self.midi_led.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 16px;
                font-weight: bold;
                background-color: transparent;
                border-radius: 8px;
                min-width: 16px;
                max-width: 16px;
                text-align: center;
            }
        """)
        indicator_layout.addWidget(self.midi_led)
        
        # Timer para apagar el LED
        self.midi_led_timer = QTimer()
        self.midi_led_timer.setSingleShot(True)
        self.midi_led_timer.timeout.connect(self.turn_off_midi_led)
        
        return indicator_widget

    def turn_on_midi_led(self):
        """Encender LED de actividad MIDI"""
        try:
            self.midi_led.setStyleSheet("""
                QLabel {
                    color: #00ff00;
                    font-size: 16px;
                    font-weight: bold;
                    background-color: transparent;
                    border-radius: 8px;
                    min-width: 16px;
                    max-width: 16px;
                    text-align: center;
                }
            """)
            # Apagar después de 100ms
            self.midi_led_timer.start(100)
        except Exception as e:
            logging.error(f"Error turning on MIDI LED: {e}")

    def turn_off_midi_led(self):
        """Apagar LED de actividad MIDI"""
        try:
            self.midi_led.setStyleSheet("""
                QLabel {
                    color: #333333;
                    font-size: 16px;
                    font-weight: bold;
                    background-color: transparent;
                    border-radius: 8px;
                    min-width: 16px;
                    max-width: 16px;
                    text-align: center;
                }
            """)
        except Exception as e:
            logging.error(f"Error turning off MIDI LED: {e}")

    def run_midi_debug(self):
        """Ejecutar debug completo de MIDI"""
        try:
            logging.info("🔍 USUARIO SOLICITÓ DEBUG MIDI")
            
            if not self.midi_engine:
                QMessageBox.warning(self, "Debug Error", "MIDI Engine no disponible")
                return
            
            # Ejecutar debug
            self.debug_midi_connection()
            
            # Mostrar resultado
            QMessageBox.information(self, "Debug MIDI", 
                                  "Debug MIDI ejecutado.\nRevisa la consola para detalles completos.")
            
        except Exception as e:
            logging.error(f"Error en run_midi_debug: {e}")
            QMessageBox.critical(self, "Error", f"Error ejecutando debug: {str(e)}")

    def debug_midi_connection(self):
        """Debug completo de la conexión MIDI"""
        try:
            logging.info("🔍 INICIANDO DEBUG DE CONEXIÓN MIDI")
            logging.info("=" * 80)
            
            # 1. Verificar engine
            if not self.midi_engine:
                logging.error("❌ MIDI Engine no existe!")
                return
            
            # 2. Verificar estado del puerto
            logging.info("1. ESTADO DEL PUERTO MIDI:")
            logging.info(f"   input_port: {self.midi_engine.input_port}")
            logging.info(f"   running: {self.midi_engine.running}")
            logging.info(f"   is_port_open(): {self.midi_engine.is_port_open()}")
            
            # 3. Puertos disponibles
            logging.info("2. PUERTOS MIDI DISPONIBLES:")
            available_ports = self.midi_engine.list_input_ports()
            for i, port in enumerate(available_ports):
                logging.info(f"   {i}: {port}")
            
            # 4. Verificar callback
            logging.info("3. VERIFICANDO CALLBACK:")
            if self.midi_engine.input_port:
                try:
                    # Intentar acceder al callback del puerto
                    logging.info(f"   Puerto existe: {self.midi_engine.input_port}")
                    logging.info(f"   Tipo de puerto: {type(self.midi_engine.input_port)}")
                except Exception as cb_error:
                    logging.error(f"   Error verificando callback: {cb_error}")
            else:
                logging.error("   ❌ Puerto MIDI no existe")
            
            # 5. Verificar mappings
            logging.info("4. VERIFICANDO MAPPINGS:")
            logging.info(f"   Total mappings: {len(self.midi_engine.midi_mappings)}")
            
            # Mostrar mappings críticos
            critical_notes = [36, 37, 48, 54, 55]  # Algunas notas importantes
            for note in critical_notes:
                test_key = f"note_on_ch0_note{note}"
                found = False
                for action_id, mapping_data in self.midi_engine.midi_mappings.items():
                    if mapping_data.get('midi') == test_key:
                        action_type = mapping_data.get('type', 'unknown')
                        params = mapping_data.get('params', {})
                        preset = params.get('preset_name', 'N/A')
                        logging.info(f"   ✅ Note {note}: {action_id} -> {action_type} ({preset})")
                        found = True
                        break
                if not found:
                    logging.warning(f"   ❌ Note {note}: No mapping found")
            
            # 6. Test de referencias
            logging.info("5. VERIFICANDO REFERENCIAS:")
            logging.info(f"   mixer_window: {'✅' if self.midi_engine.mixer_window else '❌'}")
            logging.info(f"   control_panel: {'✅' if self.midi_engine.control_panel else '❌'}")
            
            # 7. Test simulado
            logging.info("6. TEST SIMULADO:")
            try:
                import mido
                test_msg = mido.Message('note_on', channel=0, note=37, velocity=127)
                logging.info(f"   Simulando: {test_msg}")
                
                # Llamar directamente al handler
                self.midi_engine.handle_midi_message(test_msg)
                logging.info("   ✅ Handler llamado sin errores")
                
            except Exception as sim_error:
                logging.error(f"   ❌ Error en simulación: {sim_error}")
            
            logging.info("=" * 80)
            logging.info("🔍 DEBUG FINALIZADO")
            
        except Exception as e:
            logging.error(f"Error en debug_midi_connection: {e}")
            import traceback
            traceback.print_exc()

    def create_deck_section(self, deck_id):
        """Create a deck section (A or B)"""
        deck_frame = QFrame()
        deck_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        
        # Color coding
        if deck_id == 'A':
            border_color = "#ff4444"
            deck_name = "DECK A"
        else:
            border_color = "#44ff44"
            deck_name = "DECK B"
            
        deck_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #1a1a1a;
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 5px;
            }}
        """)
        
        deck_layout = QVBoxLayout(deck_frame)
        deck_layout.setSpacing(10)
        
        # Deck Header
        header_label = QLabel(f"<b>{deck_name}</b>")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setStyleSheet(f"color: {border_color}; font-size: 16px; font-weight: bold; padding: 5px;")
        deck_layout.addWidget(header_label)
        
        # Status Information
        status_group = self.create_deck_status_section(deck_id)
        deck_layout.addWidget(status_group)
        
        # MIDI Mappings
        mappings_group = self.create_deck_mappings_section(deck_id)
        deck_layout.addWidget(mappings_group)
        
        return deck_frame

    def create_deck_status_section(self, deck_id):
        """Create deck status information section"""
        status_group = QGroupBox("📊 Estado Actual")
        status_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #ffffff;
                border: 1px solid #666;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        status_layout = QVBoxLayout(status_group)
        
        # Create status labels
        if deck_id == 'A':
            self.deck_a_preset_label = QLabel("Preset: Ninguno")
            self.deck_a_activity_label = QLabel("Última actividad: --")
            self.deck_a_controls_label = QLabel("Controles: --")
            
            self.deck_a_preset_label.setStyleSheet("color: #00ff00; font-weight: bold;")
            self.deck_a_activity_label.setStyleSheet("color: #888; font-size: 10px;")
            self.deck_a_controls_label.setStyleSheet("color: #00aaff; font-size: 10px;")
            
            status_layout.addWidget(self.deck_a_preset_label)
            status_layout.addWidget(self.deck_a_activity_label)
            status_layout.addWidget(self.deck_a_controls_label)
        else:
            self.deck_b_preset_label = QLabel("Preset: Ninguno")
            self.deck_b_activity_label = QLabel("Última actividad: --")
            self.deck_b_controls_label = QLabel("Controles: --")
            
            self.deck_b_preset_label.setStyleSheet("color: #00ff00; font-weight: bold;")
            self.deck_b_activity_label.setStyleSheet("color: #888; font-size: 10px;")
            self.deck_b_controls_label.setStyleSheet("color: #00aaff; font-size: 10px;")
            
            status_layout.addWidget(self.deck_b_preset_label)
            status_layout.addWidget(self.deck_b_activity_label)
            status_layout.addWidget(self.deck_b_controls_label)
        
        return status_group

    def create_deck_mappings_section(self, deck_id):
        """Create MIDI mappings section for deck"""
        mappings_group = QGroupBox("🎹 MIDI Mappings - Presets")
        mappings_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #ffffff;
                border: 1px solid #666;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        mappings_layout = QVBoxLayout(mappings_group)
        
        # Create table for mappings
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Pad", "Preset", "Status"])
        
        # Style the table
        table.setStyleSheet("""
            QTableWidget {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #444;
                border-radius: 3px;
                gridline-color: #444;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #333;
            }
            QTableWidget::item:selected {
                background-color: #555;
            }
            QHeaderView::section {
                background-color: #333;
                color: white;
                padding: 5px;
                border: 1px solid #444;
                font-weight: bold;
            }
        """)
        
        # Configure table
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(0, 60)
        table.setColumnWidth(2, 80)
        
        # Populate with mappings
        self.populate_deck_mappings_table(table, deck_id)
        
        # Store table reference
        if deck_id == 'A':
            self.deck_a_mappings_table = table
        else:
            self.deck_b_mappings_table = table
        
        mappings_layout.addWidget(table)
        
        return mappings_group

    def populate_deck_mappings_table(self, table, deck_id):
        """Populate deck mappings table"""
        try:
            # Get mappings from MIDI engine
            if not self.midi_engine:
                return
                
            mappings = self.midi_engine.get_midi_mappings()
            
            # Filter mappings for this deck
            deck_mappings = []
            for action_id, mapping_data in mappings.items():
                params = mapping_data.get('params', {})
                if params.get('deck_id') == deck_id:
                    deck_mappings.append((action_id, mapping_data))
            
            # Sort by MIDI note
            deck_mappings.sort(key=lambda x: int(x[1].get('midi', 'note0').split('note')[-1]))
            
            table.setRowCount(len(deck_mappings))
            
            for row, (action_id, mapping_data) in enumerate(deck_mappings):
                midi_key = mapping_data.get('midi', '')
                params = mapping_data.get('params', {})
                preset_name = params.get('preset_name', 'Clear') if params.get('preset_name') else 'Clear'
                
                # Extract note number and convert to pad name
                note_num = int(midi_key.split('note')[-1]) if 'note' in midi_key else 0
                pad_name = self.note_to_pad_name(note_num)
                
                # Pad column
                pad_item = QTableWidgetItem(pad_name)
                pad_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 0, pad_item)
                
                # Preset column
                preset_item = QTableWidgetItem(preset_name)
                table.setItem(row, 1, preset_item)
                
                # Status column
                status = "●" if self.is_preset_active(deck_id, preset_name) else "○"
                status_item = QTableWidgetItem(status)
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if status == "●":
                    status_item.setForeground(QColor("#00ff00"))
                else:
                    status_item.setForeground(QColor("#666"))
                table.setItem(row, 2, status_item)
                
        except Exception as e:
            logging.error(f"Error populating deck mappings table: {e}")

    def note_to_pad_name(self, note_number):
        """Convert MIDI note number to pad name"""
        # Standard MIDI note mapping
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (note_number // 12) - 1
        note_name = note_names[note_number % 12]
        return f"{note_name}{octave}"

    def is_preset_active(self, deck_id, preset_name):
        """Check if preset is currently active on deck"""
        if deck_id == 'A':
            return self.deck_a_status['active_preset'] == preset_name
        else:
            return self.deck_b_status['active_preset'] == preset_name

    def create_mix_section(self):
        """Create mix section"""
        mix_frame = QFrame()
        mix_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        mix_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #ffaa00;
                border-radius: 8px;
                padding: 5px;
            }
        """)
        
        mix_layout = QVBoxLayout(mix_frame)
        mix_layout.setSpacing(10)
        
        # Mix Header
        header_label = QLabel("<b>🎚️ VISUAL MIX</b>")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setStyleSheet("color: #ffaa00; font-size: 16px; font-weight: bold; padding: 5px;")
        mix_layout.addWidget(header_label)
        
        # Mix Status
        status_group = self.create_mix_status_section()
        mix_layout.addWidget(status_group)
        
        # Mix Mappings
        mappings_group = self.create_mix_mappings_section()
        mix_layout.addWidget(mappings_group)
        
        # Future Features
        future_group = self.create_future_features_section()
        mix_layout.addWidget(future_group)
        
        return mix_frame

    def create_mix_status_section(self):
        """Create mix status section"""
        status_group = QGroupBox("📊 Estado del Mix")
        status_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #ffffff;
                border: 1px solid #666;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        status_layout = QVBoxLayout(status_group)
        
        # Crossfader value
        self.mix_value_label = QLabel("Crossfader: 50%")
        self.mix_value_label.setStyleSheet("color: #ffaa00; font-weight: bold;")
        status_layout.addWidget(self.mix_value_label)
        
        # Visual crossfader representation
        fader_widget = QWidget()
        fader_layout = QVBoxLayout(fader_widget)
        fader_layout.setContentsMargins(0, 0, 0, 0)
        
        # Labels
        labels_layout = QHBoxLayout()
        labels_layout.addWidget(QLabel("← A"))
        labels_layout.addStretch()
        labels_layout.addWidget(QLabel("B →"))
        fader_layout.addLayout(labels_layout)
        
        # Progress bar as visual fader
        self.mix_progress_bar = QProgressBar()
        self.mix_progress_bar.setRange(0, 100)
        self.mix_progress_bar.setValue(50)
        self.mix_progress_bar.setMaximumHeight(20)
        self.mix_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #333;
                border-radius: 10px;
                background-color: #1a1a1a;
                text-align: center;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff4444, stop:0.5 #ffaa00, stop:1 #44ff44);
                border-radius: 8px;
            }
        """)
        fader_layout.addWidget(self.mix_progress_bar)
        
        status_layout.addWidget(fader_widget)
        
        # Last activity
        self.mix_activity_label = QLabel("Última actividad: --")
        self.mix_activity_label.setStyleSheet("color: #888; font-size: 10px;")
        status_layout.addWidget(self.mix_activity_label)
        
        return status_group

    def create_mix_mappings_section(self):
        """Create mix mappings section"""
        mappings_group = QGroupBox("🎹 MIDI Mappings - Mix Actions")
        mappings_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #ffffff;
                border: 1px solid #666;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        mappings_layout = QVBoxLayout(mappings_group)
        
        # Create table for mix mappings
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Pad", "Action", "Duration", "Status"])
        
        # Style the table
        table.setStyleSheet("""
            QTableWidget {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #444;
                border-radius: 3px;
                gridline-color: #444;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #333;
            }
            QTableWidget::item:selected {
                background-color: #555;
            }
            QHeaderView::section {
                background-color: #333;
                color: white;
                padding: 5px;
                border: 1px solid #444;
                font-weight: bold;
            }
        """)
        
        # Configure table
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(0, 60)
        table.setColumnWidth(2, 80)
        table.setColumnWidth(3, 60)
        
        # Populate with mix mappings
        self.populate_mix_mappings_table(table)
        
        self.mix_mappings_table = table
        mappings_layout.addWidget(table)
        
        return mappings_group

    def populate_mix_mappings_table(self, table):
        """Populate mix mappings table"""
        try:
            if not self.midi_engine:
                return
                
            mappings = self.midi_engine.get_midi_mappings()
            
            # Filter mix mappings
            mix_mappings = []
            for action_id, mapping_data in mappings.items():
                if mapping_data.get('type') == 'crossfade_action':
                    mix_mappings.append((action_id, mapping_data))
            
            # Sort by MIDI note
            mix_mappings.sort(key=lambda x: int(x[1].get('midi', 'note0').split('note')[-1]))
            
            table.setRowCount(len(mix_mappings))
            
            for row, (action_id, mapping_data) in enumerate(mix_mappings):
                midi_key = mapping_data.get('midi', '')
                params = mapping_data.get('params', {})
                
                # Extract note number and convert to pad name
                note_num = int(midi_key.split('note')[-1]) if 'note' in midi_key else 0
                pad_name = self.note_to_pad_name(note_num)
                
                # Pad column
                pad_item = QTableWidgetItem(pad_name)
                pad_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 0, pad_item)
                
                # Action column
                preset = params.get('preset', 'Unknown')
                action_item = QTableWidgetItem(preset)
                table.setItem(row, 1, action_item)
                
                # Duration column
                duration = params.get('duration', '--')
                duration_item = QTableWidgetItem(duration)
                duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 2, duration_item)
                
                # Status column
                status_item = QTableWidgetItem("○")
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                status_item.setForeground(QColor("#666"))
                table.setItem(row, 3, status_item)
                
        except Exception as e:
            logging.error(f"Error populating mix mappings table: {e}")

    def create_future_features_section(self):
        """Create future features section"""
        future_group = QGroupBox("🚀 Próximamente")
        future_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #00aaff;
                border: 1px solid #00aaff;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        future_layout = QVBoxLayout(future_group)
        
        features = [
            "• Efectos visuales en tiempo real",
            "• Control de colores por MIDI",
            "• Ajustes de contraste y brillo",
            "• Efectos de transición avanzados",
            "• Sincronización con BPM",
            "• Macros de control visual"
        ]
        
        for feature in features:
            label = QLabel(feature)
            label.setStyleSheet("color: #00aaff; font-size: 10px; padding: 2px;")
            future_layout.addWidget(label)
        
        return future_group

    def create_footer_section(self):
        """Create footer with drum rack guide"""
        footer_frame = QFrame()
        footer_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        footer_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #666;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        footer_frame.setMaximumHeight(100)
        
        footer_layout = QVBoxLayout(footer_frame)
        
        # Title
        title_label = QLabel("<b>🥁 Guía para Drum Rack de Ableton Live</b>")
        title_label.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold;")
        footer_layout.addWidget(title_label)
        
        # Guide grid
        guide_layout = QHBoxLayout()
        
        # Deck A
        deck_a_guide = QLabel("<b>Deck A (C1-A#1):</b> Notas 36-46<br>Presets visuales para Deck A")
        deck_a_guide.setStyleSheet("color: #ff4444; font-size: 10px;")
        guide_layout.addWidget(deck_a_guide)
        
        # Mix
        mix_guide = QLabel("<b>Mix (C2-F2):</b> Notas 48-53<br>Acciones de mezcla y crossfader")
        mix_guide.setStyleSheet("color: #ffaa00; font-size: 10px;")
        guide_layout.addWidget(mix_guide)
        
        # Deck B
        deck_b_guide = QLabel("<b>Deck B (F#2-E3):</b> Notas 54-64<br>Presets visuales para Deck B")
        deck_b_guide.setStyleSheet("color: #44ff44; font-size: 10px;")
        guide_layout.addWidget(deck_b_guide)
        
        footer_layout.addLayout(guide_layout)
        
        # Configuration instructions
        config_label = QLabel("<b>Configuración:</b> Crea un track en Ableton → Añade Drum Rack → "
                             "Para cada pad, añade External Instrument → Configura MIDI Out al dispositivo virtual")
        config_label.setStyleSheet("color: #888; font-size: 9px;")
        config_label.setWordWrap(True)
        footer_layout.addWidget(config_label)
        
        return footer_frame

    def show_preferences(self):
        try:
            dialog = PreferencesDialog(self.settings_manager, self.midi_engine, self.audio_analyzer, self)
            dialog.exec()
        except Exception as e:
            logging.error(f"Error opening preferences: {e}")
            QMessageBox.critical(self, "Error", f"Could not open preferences: {str(e)}")

    def test_midi_mappings(self):
        """Test MIDI mappings"""
        try:
            if self.midi_engine:
                # Test a few key mappings
                test_notes = [37, 50, 55]  # Wire Terrain A, Mix A→B 5s, Wire Terrain B
                for note in test_notes:
                    self.midi_engine.test_midi_mapping(note)
                    
                QMessageBox.information(self, "MIDI Test", 
                                      f"Tested MIDI mappings for notes: {test_notes}\nCheck console for results.")
            else:
                QMessageBox.warning(self, "Error", "MIDI Engine not available")
        except Exception as e:
            logging.error(f"Error testing MIDI mappings: {e}")
            QMessageBox.critical(self, "Error", f"Error testing MIDI mappings: {str(e)}")

    def print_midi_mappings(self):
        """Print current MIDI mappings"""
        try:
            if self.midi_engine:
                self.midi_engine.print_current_mappings()
                QMessageBox.information(self, "MIDI Mappings", "Current MIDI mappings printed to console.")
            else:
                QMessageBox.warning(self, "Error", "MIDI Engine not available")
        except Exception as e:
            logging.error(f"Error printing MIDI mappings: {e}")

    def refresh_devices(self):
        """Refresh device information and update displays"""
        try:
            self.update_midi_device_display()
            self.update_audio_device_display()
            logging.info("Device information refreshed")
        except Exception as e:
            logging.error(f"Error refreshing devices: {e}")

    def on_preset_loaded_on_deck(self, deck_id, preset_name):
        """Handle preset loading from MIDI to update the UI"""
        try:
            import time
            current_time = time.strftime("%H:%M:%S")
            
            if deck_id == 'A':
                self.deck_a_status['active_preset'] = preset_name
                self.deck_a_status['last_activity'] = current_time
                
                self.deck_a_preset_label.setText(f"Preset: {preset_name}")
                self.deck_a_activity_label.setText(f"Última actividad: {current_time}")
                
                # Update table
                if hasattr(self, 'deck_a_mappings_table'):
                    self.refresh_deck_mappings_table(self.deck_a_mappings_table, 'A')
                    
            elif deck_id == 'B':
                self.deck_b_status['active_preset'] = preset_name
                self.deck_b_status['last_activity'] = current_time
                
                self.deck_b_preset_label.setText(f"Preset: {preset_name}")
                self.deck_b_activity_label.setText(f"Última actividad: {current_time}")
                
                # Update table
                if hasattr(self, 'deck_b_mappings_table'):
                    self.refresh_deck_mappings_table(self.deck_b_mappings_table, 'B')
            
            logging.info(f"✅ UI updated for deck {deck_id} to preset {preset_name}")
        except Exception as e:
            logging.error(f"Error updating preset selector for deck {deck_id}: {e}")

    def refresh_deck_mappings_table(self, table, deck_id):
        """Refresh deck mappings table status"""
        try:
            for row in range(table.rowCount()):
                preset_item = table.item(row, 1)
                status_item = table.item(row, 2)
                
                if preset_item and status_item:
                    preset_name = preset_item.text()
                    is_active = self.is_preset_active(deck_id, preset_name)
                    
                    status = "●" if is_active else "○"
                    status_item.setText(status)
                    
                    if is_active:
                        status_item.setForeground(QColor("#00ff00"))
                    else:
                        status_item.setForeground(QColor("#666"))
        except Exception as e:
            logging.error(f"Error refreshing deck mappings table: {e}")

    def update_midi_device_display(self, device_name=None):
        """Update MIDI device display with enhanced visual feedback"""
        try:
            if device_name:
                self.midi_status_label.setText(f"MIDI: {device_name}")
                self.midi_status_label.setStyleSheet("color: #00ff00; font-weight: bold; padding: 5px;")
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
                
                self.midi_status_label.setText(f"MIDI: {device_info}")
                if midi_connected:
                    self.midi_status_label.setStyleSheet("color: #00ff00; font-weight: bold; padding: 5px;")
                else:
                    self.midi_status_label.setStyleSheet("color: #ff6600; font-weight: bold; padding: 5px;")
                    
        except Exception as e:
            logging.error(f"Error updating MIDI device display: {e}")
            self.midi_status_label.setText("MIDI: Error")
            self.midi_status_label.setStyleSheet("color: red; font-weight: bold; padding: 5px;")

    def update_audio_device_display(self):
        """Update audio device display"""
        try:
            # This is for future implementation if needed
            pass
        except Exception as e:
            logging.error(f"Error updating audio device display: {e}")

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
            # Update mix value from mixer window
            if self.mixer_window and hasattr(self.mixer_window, 'get_mix_value_percent'):
                mix_value = self.mixer_window.get_mix_value_percent()
                self.mix_value_label.setText(f"Crossfader: {mix_value}%")
                self.mix_progress_bar.setValue(mix_value)
            
            # Update device displays periodically
            import time
            current_time = time.time()
            if not hasattr(self, 'last_device_update'):
                self.last_device_update = 0
                
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
        """Handle raw MIDI activity for monitoring with enhanced feedback and LED"""
        try:
            # ✅ ENCENDER LED DE ACTIVIDAD
            self.turn_on_midi_led()
            
            # FIX: Usar datetime para obtener microsegundos correctamente
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Incluir milisegundos
            
            if hasattr(msg, 'type'):
                # Log CRÍTICO - CADA mensaje debe aparecer aquí
                logging.info(f"🎼 MIDI ACTIVITY DETECTED: {msg}")
                logging.info(f"   ⏰ Timestamp: {timestamp}")
                logging.info(f"   🔍 Type: {msg.type}")
                logging.info(f"   📡 Channel: {getattr(msg, 'channel', 'N/A')}")
                
                if msg.type == 'note_on':
                    velocity = getattr(msg, 'velocity', 0)
                    note = getattr(msg, 'note', 0)
                    
                    logging.info(f"   🎵 NOTE_ON DETAILS:")
                    logging.info(f"      Note: {note}")
                    logging.info(f"      Velocity: {velocity}")
                    
                    # Solo procesar si velocity > 0
                    if velocity > 0:
                        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                        octave = note // 12 - 1
                        note_name = note_names[note % 12]
                        
                        logging.info(f"🎵 ACTIVE NOTE: {note_name}{octave} (#{note}) Ch:{msg.channel+1} Vel:{velocity}")
                        
                        # CRÍTICO: Verificar mapping
                        if self.midi_engine:
                            mappings = self.midi_engine.get_midi_mappings()
                            expected_key = f"note_on_ch0_note{note}"
                            
                            logging.info(f"🔍 BUSCANDO MAPPING PARA: {expected_key}")
                            
                            found_mapping = False
                            for action_id, mapping_data in mappings.items():
                                midi_key = mapping_data.get('midi', 'no_midi')
                                if midi_key == expected_key:
                                    action_type = mapping_data.get('type', 'unknown')
                                    params = mapping_data.get('params', {})
                                    logging.info(f"✅ MAPPING ENCONTRADO!")
                                    logging.info(f"   Action ID: {action_id}")
                                    logging.info(f"   Type: {action_type}")
                                    logging.info(f"   Params: {params}")
                                    found_mapping = True
                                    break
                            
                            if not found_mapping:
                                logging.warning(f"❌ NO HAY MAPPING PARA: {expected_key}")
                                logging.info(f"📋 Mappings disponibles:")
                                for i, (aid, mdata) in enumerate(list(mappings.items())[:5]):
                                    logging.info(f"   {aid}: {mdata.get('midi', 'no_midi')}")
                                if len(mappings) > 5:
                                    logging.info(f"   ... y {len(mappings) - 5} más")
                    else:
                        logging.info(f"   🎵 NOTE_ON with velocity 0 (note off)")
                        
                elif msg.type == 'note_off':
                    note = getattr(msg, 'note', 0)
                    logging.info(f"   🎵 NOTE_OFF: Note={note}")
                    
                elif msg.type == 'control_change':
                    control = getattr(msg, 'control', 0)
                    value = getattr(msg, 'value', 0)
                    logging.info(f"   🎛️ CC: Control={control}, Value={value}")
                    
            logging.info(f"🔃 MIDI ACTIVITY PROCESSING COMPLETE")
                    
        except Exception as e:
            logging.error(f"❌ ERROR EN on_midi_activity: {e}")
            import traceback
            traceback.print_exc()

    def on_note_activity(self, note, velocity):
        """Handle note activity"""
        try:
            import time
            timestamp = time.strftime("%H:%M:%S")
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            octave = note // 12 - 1
            note_name = note_names[note % 12]
            logging.debug(f"🎵 [{timestamp}] Note: {note_name}{octave} Vel:{velocity}")
        except Exception as e:
            logging.error(f"Error handling note activity: {e}")

    def on_cc_activity(self, control_id, value):
        """Handle CC activity"""
        try:
            import time
            timestamp = time.strftime("%H:%M:%S")
            logging.debug(f"🎛️ [{timestamp}] CC: {control_id} = {value}")
        except Exception as e:
            logging.error(f"Error handling CC activity: {e}")

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