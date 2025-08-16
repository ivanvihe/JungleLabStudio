# ui/control_panel_window.py - ACTUALIZADO CON NUEVA UI MIDI
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QGroupBox, QGridLayout, QFrame, QProgressBar, QMenuBar, QMenu, QFormLayout, QApplication,
    QMessageBox, QTextEdit, QScrollArea, QSplitter, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QTimer, QMutex, QMutexLocker, QSize
from PyQt6.QtGui import QAction, QFont, QColor

from .preferences_dialog import PreferencesDialog
from .midi_config_widget import MidiConfigWidget
from .layout_sections import create_header_section, create_footer_section
from .live_control_tab import create_live_control_tab
from .monitor_tab import create_monitor_tab
from .midi_config_tab import create_midi_config_tab

class ControlPanelWindow(QMainWindow):
    def __init__(self, mixer_window, settings_manager, midi_engine, visualizer_manager, audio_analyzer):
        super().__init__(mixer_window)
        logging.debug("ControlPanelWindow.__init__ called - CON NUEVA UI MIDI")
        
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
        
        self.setWindowTitle("Audio Visualizer Pro - MIDI Control Center (Enhanced)")
        self.setGeometry(50, 50, 1600, 900)
        
        # Create menu bar
        self.create_menu_bar()

        # Create main UI - REDISEÑADO CON NUEVA UI MIDI
        self.create_enhanced_ui()
        
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
                self.midi_engine.midi_message_received.connect(
                    self.on_midi_activity, Qt.ConnectionType.QueuedConnection
                )
            if hasattr(self.midi_engine, 'note_on_received'):
                self.midi_engine.note_on_received.connect(
                    self.on_note_activity, Qt.ConnectionType.QueuedConnection
                )
            if hasattr(self.midi_engine, 'control_changed'):
                self.midi_engine.control_changed.connect(
                    self.on_cc_activity, Qt.ConnectionType.QueuedConnection
                )
            if hasattr(self.midi_engine, 'device_connected'):
                self.midi_engine.device_connected.connect(
                    self.on_midi_device_connected, Qt.ConnectionType.QueuedConnection
                )
            if hasattr(self.midi_engine, 'device_disconnected'):
                self.midi_engine.device_disconnected.connect(
                    self.on_midi_device_disconnected, Qt.ConnectionType.QueuedConnection
                )
            if hasattr(self.midi_engine, 'preset_loaded_on_deck'):
                self.midi_engine.preset_loaded_on_deck.connect(
                    self.on_preset_loaded_on_deck, Qt.ConnectionType.QueuedConnection
                )
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

        # MIDI menu - MEJORADO
        midi_menu = menubar.addMenu('MIDI')
        
        midi_config_action = QAction('🎹 Configuración MIDI Completa...', self)
        midi_config_action.triggered.connect(self.show_midi_config)
        midi_menu.addAction(midi_config_action)
        
        midi_menu.addSeparator()
        
        test_mappings_action = QAction('Test MIDI Mappings', self)
        test_mappings_action.triggered.connect(self.test_midi_mappings)
        midi_menu.addAction(test_mappings_action)
        
        print_mappings_action = QAction('Print Current Mappings', self)
        print_mappings_action.triggered.connect(self.print_midi_mappings)
        midi_menu.addAction(print_mappings_action)
        
        midi_menu.addSeparator()
        
        debug_midi_action = QAction('🔧 Debug MIDI Connection', self)
        debug_midi_action.triggered.connect(self.run_midi_debug)
        midi_menu.addAction(debug_midi_action)

        # View menu
        view_menu = menubar.addMenu('View')
        
        refresh_action = QAction('Refresh Devices', self)
        refresh_action.triggered.connect(self.refresh_devices)
        view_menu.addAction(refresh_action)

    def create_enhanced_ui(self):
        """Create the enhanced UI with MIDI configuration integrated"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main layout
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header Section
        header_section = create_header_section(self)
        main_layout.addWidget(header_section)

        # Main Content: Tabs para mejor organización
        main_tabs = QTabWidget()

        # Tab 1: Control en Vivo
        live_tab = create_live_control_tab(self)
        main_tabs.addTab(live_tab, "🎛️ Control en Vivo")

        # Tab 2: Configuración MIDI
        midi_tab = create_midi_config_tab(self)
        main_tabs.addTab(midi_tab, "🎹 Configuración MIDI")

        # Tab 3: Monitoreo y Debug
        monitor_tab = create_monitor_tab(self)
        main_tabs.addTab(monitor_tab, "📊 Monitoreo")

        main_layout.addWidget(main_tabs)

        # Footer: Information panel
        footer_section = create_footer_section(self)
        main_layout.addWidget(footer_section)

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




    def _add_row_to_table(self, table, timestamp, msg_type, data_str, max_rows=20):
        """Utility to append a row to a QTableWidget with limit"""
        row = table.rowCount()
        table.insertRow(row)
        table.setItem(row, 0, QTableWidgetItem(timestamp))
        table.setItem(row, 1, QTableWidgetItem(msg_type))
        table.setItem(row, 2, QTableWidgetItem(data_str))
        table.scrollToBottom()
        if table.rowCount() > max_rows:
            table.removeRow(0)



    # === FUNCIONES DE EVENTOS MIDI ===

    def show_midi_config(self):
        """Mostrar configuración MIDI completa"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Configuración MIDI Completa")
            dialog.setModal(True)
            dialog.resize(1200, 800)
            
            layout = QVBoxLayout(dialog)
            
            config_widget = MidiConfigWidget(
                self.midi_engine, 
                self.visualizer_manager, 
                dialog
            )
            layout.addWidget(config_widget)
            
            # Botón cerrar
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            buttons.rejected.connect(dialog.accept)
            layout.addWidget(buttons)
            
            dialog.exec()
            
        except Exception as e:
            logging.error(f"Error opening MIDI config: {e}")
            QMessageBox.critical(self, "Error", f"Error abriendo configuración: {str(e)}")

    def test_mix_action(self, midi_key):
        """Probar acción de mix"""
        try:
            if self.midi_engine:
                # Simular mensaje MIDI
                self.midi_engine.simulate_midi_message(midi_key)
                logging.info(f"🧪 Testing mix action: {midi_key}")
        except Exception as e:
            logging.error(f"Error testing mix action: {e}")

    def clear_midi_activity(self):
        """Limpiar tabla de actividad MIDI"""
        try:
            if hasattr(self, 'midi_activity_table'):
                self.midi_activity_table.setRowCount(0)
                self.midi_activity_data = []
                self.midi_message_count = 0
        except Exception as e:
            logging.error(f"Error clearing MIDI activity: {e}")

    def toggle_midi_activity_monitoring(self):
        """Pausar/reanudar monitoreo MIDI"""
        try:
            self.midi_monitoring_paused = not self.midi_monitoring_paused
            # Implementar lógica de pausa
        except Exception as e:
            logging.error(f"Error toggling MIDI monitoring: {e}")

    def clear_events_log(self):
        """Limpiar log de eventos"""
        try:
            if hasattr(self, 'events_log'):
                self.events_log.clear()
        except Exception as e:
            logging.error(f"Error clearing events log: {e}")

    def export_events_log(self):
        """Exportar log de eventos"""
        try:
            # Implementar exportación
            QMessageBox.information(self, "Export", "Funcionalidad por implementar")
        except Exception as e:
            logging.error(f"Error exporting events log: {e}")

    def update_system_info(self):
        """Actualizar información del sistema"""
        try:
            if hasattr(self, 'system_info_text'):
                try:
                    import psutil
                    import platform
                    
                    info = f"""Sistema: {platform.system()} {platform.release()}
CPU: {psutil.cpu_percent()}%
RAM: {psutil.virtual_memory().percent}%
MIDI Engine: {'Activo' if self.midi_engine else 'Inactivo'}
Mappings: {len(self.midi_engine.get_midi_mappings()) if self.midi_engine else 0}
"""
                except ImportError:
                    import platform
                    info = f"""Sistema: Python {platform.python_version()}
MIDI Engine: {'Activo' if self.midi_engine else 'Inactivo'}
Mappings: {len(self.midi_engine.get_midi_mappings()) if self.midi_engine else 0}
"""
                self.system_info_text.setPlainText(info)
        except Exception as e:
            logging.error(f"Error updating system info: {e}")

    def on_midi_mappings_changed(self):
        """Manejar cambio de mappings MIDI"""
        try:
            # Recargar información
            self.update_mappings_info()
            logging.info("MIDI mappings changed")
        except Exception as e:
            logging.error(f"Error handling MIDI mappings change: {e}")
            
    def run_midi_debug(self):
        """Ejecutar debug completo de MIDI"""
        try:
            logging.info("🔧 USUARIO SOLICITÓ DEBUG MIDI")
            
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
            logging.info("🔧 INICIANDO DEBUG DE CONEXIÓN MIDI")
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
            
            # 4. Verificar mappings
            logging.info("3. VERIFICANDO MAPPINGS:")
            logging.info(f"   Total mappings: {len(self.midi_engine.midi_mappings)}")
            
            # Mostrar mappings críticos
            critical_notes = [36, 37, 48, 54, 55, 69]  # Incluye A3 (69)
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
            
            # 5. Test de referencias
            logging.info("4. VERIFICANDO REFERENCIAS:")
            logging.info(f"   mixer_window: {'✅' if self.midi_engine.mixer_window else '❌'}")
            logging.info(f"   control_panel: {'✅' if self.midi_engine.control_panel else '❌'}")
            
            logging.info("=" * 80)
            logging.info("🔧 DEBUG FINALIZADO")
            
        except Exception as e:
            logging.error(f"Error en debug_midi_connection: {e}")
            import traceback
            traceback.print_exc()

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
                    
            elif deck_id == 'B':
                self.deck_b_status['active_preset'] = preset_name
                self.deck_b_status['last_activity'] = current_time
                
                self.deck_b_preset_label.setText(f"Preset: {preset_name}")
                self.deck_b_activity_label.setText(f"Última actividad: {current_time}")
            
            logging.info(f"✅ UI updated for deck {deck_id} to preset {preset_name}")
        except Exception as e:
            logging.error(f"Error updating preset selector for deck {deck_id}: {e}")

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
        """Handle raw MIDI activity and update activity tables"""
        try:
            self.turn_on_midi_led()

            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            msg_type = getattr(msg, 'type', 'unknown')
            data_str = str(msg)
            midi_key = None
            note = control = value = velocity = None

            if msg_type == 'note_on':
                note = getattr(msg, 'note', 0)
                velocity = getattr(msg, 'velocity', 0)
                data_str = f"Note {note} Vel {velocity}"
                midi_key = f"note_on_ch{msg.channel}_note{note}"
            elif msg_type == 'note_off':
                note = getattr(msg, 'note', 0)
                data_str = f"Note {note} off"
                midi_key = f"note_off_ch{msg.channel}_note{note}"
            elif msg_type == 'control_change':
                control = getattr(msg, 'control', 0)
                value = getattr(msg, 'value', 0)
                data_str = f"CC {control} Val {value}"
                midi_key = f"cc_ch{msg.channel}_control{control}"

            deck_id = None
            if midi_key and self.midi_engine:
                mappings = self.midi_engine.get_midi_mappings()
                for mapping_data in mappings.values():
                    if mapping_data.get('midi') == midi_key:
                        deck_id = mapping_data.get('params', {}).get('deck_id')
                        break

            if hasattr(self, 'midi_activity_table') and not getattr(self, 'midi_monitoring_paused', False):
                row = self.midi_activity_table.rowCount()
                self.midi_activity_table.insertRow(row)
                self.midi_activity_table.setItem(row, 0, QTableWidgetItem(timestamp))
                self.midi_activity_table.setItem(row, 1, QTableWidgetItem(msg_type))
                self.midi_activity_table.setItem(row, 2, QTableWidgetItem(data_str))
                self.midi_activity_table.setItem(row, 3, QTableWidgetItem(deck_id or '--'))
                self.midi_activity_table.scrollToBottom()

            if deck_id == 'A':
                if hasattr(self, 'deck_a_activity_table'):
                    self._add_row_to_table(self.deck_a_activity_table, timestamp, msg_type, data_str)
                if hasattr(self, 'deck_a_activity_label'):
                    self.deck_a_activity_label.setText(f"Última actividad: {timestamp}")
                if msg_type == 'control_change' and hasattr(self, 'deck_a_controls_label'):
                    self.deck_a_controls_label.setText(f"CC {control}={value}")
            elif deck_id == 'B':
                if hasattr(self, 'deck_b_activity_table'):
                    self._add_row_to_table(self.deck_b_activity_table, timestamp, msg_type, data_str)
                if hasattr(self, 'deck_b_activity_label'):
                    self.deck_b_activity_label.setText(f"Última actividad: {timestamp}")
                if msg_type == 'control_change' and hasattr(self, 'deck_b_controls_label'):
                    self.deck_b_controls_label.setText(f"CC {control}={value}")

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

    def update_mappings_info(self):
        """Actualizar información de mappings"""
        try:
            if self.midi_engine:
                count = len(self.midi_engine.get_midi_mappings())
                self.footer_mappings_info.setText(f"MIDI Mappings: {count}")
            else:
                self.footer_mappings_info.setText("MIDI Mappings: 0")
        except Exception as e:
            logging.error(f"Error updating mappings info: {e}")

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