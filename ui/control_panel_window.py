# ui/control_panel_window.py - CLEAN AND MODERN VERSION
import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QGroupBox, QGridLayout, QFrame, QProgressBar, QMenuBar, QMenu, QFormLayout, QApplication,
    QMessageBox, QTextEdit, QScrollArea, QSplitter, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, QTimer, QMutex, QMutexLocker, QSize
from PySide6.QtGui import QAction, QFont, QColor

from .preferences_dialog import PreferencesDialog
from .midi_config_widget import MidiConfigWidget
from .layout_sections import create_header_section, create_footer_section
from .live_control_tab import create_live_control_tab
from .monitor_tab import create_monitor_tab
from .visual_settings_tab import create_visual_settings_tab
from .mixer_window import MixerWindow

class ControlPanelWindow(QMainWindow):
    def __init__(self, mixer_window, settings_manager, midi_engine, visualizer_manager, audio_analyzer):
        super().__init__(mixer_window)
        logging.debug("ControlPanelWindow.__init__ called - MODERN UI VERSION")
        
        # Store references
        self.mixer_window = mixer_window
        self.settings_manager = settings_manager
        self.midi_engine = midi_engine
        self.visualizer_manager = visualizer_manager
        self.audio_analyzer = audio_analyzer

        # Track fullscreen output windows
        self.fullscreen_windows = []

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
        
        self.setWindowTitle("Audio Visualizer Pro - Control Center (Modern)")
        self.setGeometry(50, 50, 1600, 900)
        
        # Create menu bar
        self.create_menu_bar()

        # Create modern UI
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

        # MIDI menu
        midi_menu = menubar.addMenu('MIDI')
        
        midi_config_action = QAction(' MIDI Configuration...', self)
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
        
        debug_midi_action = QAction(' Debug MIDI Connection', self)
        debug_midi_action.triggered.connect(self.run_midi_debug)
        midi_menu.addAction(debug_midi_action)

        # View menu
        view_menu = menubar.addMenu('View')
        
        refresh_action = QAction('Refresh Devices', self)
        refresh_action.triggered.connect(self.refresh_devices)
        view_menu.addAction(refresh_action)
        
        refresh_visuals_action = QAction(' Refresh Visual Grids', self)
        refresh_visuals_action.triggered.connect(self.refresh_visual_grids)
        view_menu.addAction(refresh_visuals_action)

    def create_enhanced_ui(self):
        """Create the enhanced UI with modern styling integration."""
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
        """)
        self.setCentralWidget(main_widget)
        
        # Main layout
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Modern header Section
        header_section = create_header_section(self)
        main_layout.addWidget(header_section)

        # Main Content: Modern tabs
        main_tabs = self.create_modern_tab_widget()
        
        # Tab 1: Modern Live Control Grid (4 layers)
        live_tab = create_live_control_tab(self)
        main_tabs.addTab(live_tab, " LIVE GRID")

        # Tab 2: Visual Settings 
        visuals_tab = create_visual_settings_tab(self)
        main_tabs.addTab(visuals_tab, " VISUAL SETTINGS")

        # Tab 3: Monitoring and Debug
        monitor_tab = create_monitor_tab(self)
        main_tabs.addTab(monitor_tab, " MONITORING")

        main_layout.addWidget(main_tabs)

        # Modern footer
        footer_section = create_footer_section(self)
        main_layout.addWidget(footer_section)

    def create_modern_tab_widget(self):
        """Create modern tab widget with professional styling."""
        main_tabs = QTabWidget()
        main_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #333333;
                border-radius: 6px;
                background-color: #151515;
                margin-top: 2px;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a2a2a,
                    stop:1 #1a1a1a);
                color: #b0b0b0;
                padding: 12px 20px;
                margin-right: 1px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 600;
                font-size: 11px;
                border: 1px solid #333333;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff6b35,
                    stop:1 #e55a2b);
                color: white;
                border-bottom: 2px solid #ff6b35;
            }
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a3a3a,
                    stop:1 #2a2a2a);
                color: #ffffff;
            }
        """)
        return main_tabs

    # === MODERN MIDI LED METHODS ===
    def turn_on_midi_led(self):
        """Modern MIDI LED activation with glow effect."""
        try:
            if hasattr(self, 'midi_led'):
                self.midi_led.setStyleSheet("""
                    QLabel {
                        color: #00d4aa;
                        background: radial-gradient(circle, 
                            rgba(0, 212, 170, 40) 0%, 
                            transparent 70%);
                        border-radius: 6px;
                        min-width: 12px;
                        max-width: 12px;
                        text-align: center;
                    }
                """)
                if hasattr(self, 'midi_led_timer'):
                    self.midi_led_timer.start(200)
        except Exception as e:
            logging.error(f"Error turning on modern MIDI LED: {e}")

    def turn_off_midi_led(self):
        """Modern MIDI LED deactivation."""
        try:
            if hasattr(self, 'midi_led'):
                self.midi_led.setStyleSheet("""
                    QLabel {
                        color: #666666;
                        background: transparent;
                        border-radius: 6px;
                        min-width: 12px;
                        max-width: 12px;
                        text-align: center;
                    }
                """)
        except Exception as e:
            logging.error(f"Error turning off modern MIDI LED: {e}")

    def update_midi_device_display(self, device_name=None):
        """Update MIDI device display with modern styling."""
        try:
            if hasattr(self, 'midi_status_label'):
                if device_name:
                    self.midi_status_label.setText(f"MIDI: {device_name}")
                    self.midi_status_label.setStyleSheet("""
                        QLabel {
                            color: #00d4aa;
                            background: rgba(0, 212, 170, 20);
                            padding: 4px 8px;
                            border-radius: 3px;
                            border: 1px solid rgba(0, 212, 170, 100);
                            font-weight: 600;
                        }
                    """)
                else:
                    # Check current MIDI status
                    midi_connected = False
                    device_info = "Disconnected"
                    
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
                        self.midi_status_label.setStyleSheet("""
                            QLabel {
                                color: #00d4aa;
                                background: rgba(0, 212, 170, 20);
                                padding: 4px 8px;
                                border-radius: 3px;
                                border: 1px solid rgba(0, 212, 170, 100);
                                font-weight: 600;
                            }
                        """)
                    else:
                        self.midi_status_label.setStyleSheet("""
                            QLabel {
                                color: #ff4444;
                                background: rgba(255, 68, 68, 20);
                                padding: 4px 8px;
                                border-radius: 3px;
                                border: 1px solid rgba(255, 68, 68, 100);
                                font-weight: 600;
                            }
                        """)
                        
        except Exception as e:
            logging.error(f"Error updating modern MIDI device display: {e}")
            if hasattr(self, 'midi_status_label'):
                self.midi_status_label.setText("MIDI: Error")
                self.midi_status_label.setStyleSheet("""
                    QLabel {
                        color: #ff4444;
                        background: rgba(255, 68, 68, 20);
                        padding: 4px 8px;
                        border-radius: 3px;
                        border: 1px solid rgba(255, 68, 68, 100);
                        font-weight: 600;
                    }
                """)

    def update_mappings_info(self):
        """Update mappings info with modern styling."""
        try:
            if hasattr(self, 'footer_mappings_info'):
                if self.midi_engine:
                    count = len(self.midi_engine.get_midi_mappings())
                    self.footer_mappings_info.setText(f"{count} mappings")
                    
                    # Modern color coding based on mapping count
                    if count > 0:
                        self.footer_mappings_info.setStyleSheet("""
                            QLabel {
                                color: #ffffff;
                                background: rgba(0, 212, 170, 20);
                                padding: 2px 6px;
                                border-radius: 3px;
                                border: 1px solid rgba(0, 212, 170, 100);
                                font-weight: 600;
                            }
                        """)
                    else:
                        self.footer_mappings_info.setStyleSheet("""
                            QLabel {
                                color: #ffffff;
                                background: rgba(255, 170, 0, 20);
                                padding: 2px 6px;
                                border-radius: 3px;
                                border: 1px solid rgba(255, 170, 0, 100);
                                font-weight: 600;
                            }
                        """)
                else:
                    self.footer_mappings_info.setText("0 mappings")
                    self.footer_mappings_info.setStyleSheet("""
                        QLabel {
                            color: #ffffff;
                            background: rgba(102, 102, 102, 20);
                            padding: 2px 6px;
                            border-radius: 3px;
                            border: 1px solid rgba(102, 102, 102, 100);
                            font-weight: 600;
                        }
                    """)
        except Exception as e:
            logging.error(f"Error updating modern mappings info: {e}")

    def refresh_visual_grids(self):
        """Refresh visual grids with modern animation feedback."""
        try:
            logging.info("Refreshing modern visual grids...")
            
            # Find and refresh tabs with modern transition
            main_tabs = self.centralWidget().findChild(QTabWidget)
            if main_tabs:
                current_index = main_tabs.currentIndex()
                
                # Refresh Live Control tab (4-layer grid)
                for i in range(main_tabs.count()):
                    tab_text = main_tabs.tabText(i)
                    if "LIVE GRID" in tab_text or "Live Control" in tab_text:
                        old_widget = main_tabs.widget(i)
                        new_widget = create_live_control_tab(self)
                        main_tabs.removeTab(i)
                        main_tabs.insertTab(i, new_widget, " LIVE GRID")
                        old_widget.deleteLater()
                        break
                
                # Refresh Visual Settings tab
                for i in range(main_tabs.count()):
                    tab_text = main_tabs.tabText(i)
                    if "VISUAL SETTINGS" in tab_text or "Visual Settings" in tab_text:
                        old_widget = main_tabs.widget(i)
                        new_widget = create_visual_settings_tab(self)
                        main_tabs.removeTab(i)
                        main_tabs.insertTab(i, new_widget, " VISUAL SETTINGS")
                        old_widget.deleteLater()
                        break
                
                # Restore current tab
                main_tabs.setCurrentIndex(current_index)
            
            # Modern success notification
            self.show_modern_notification(" Visual grids refreshed successfully!", "success")
            logging.info("Modern visual grids refreshed")
            
        except Exception as e:
            logging.error(f"Error refreshing modern visual grids: {e}")
            self.show_modern_notification(f" Error refreshing grids: {str(e)}", "error")

    def show_modern_notification(self, message, type="info"):
        """Show modern notification with professional styling."""
        try:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Audio Visualizer Pro")
            msg_box.setText(message)
            
            # Modern styling based on type
            if type == "success":
                msg_box.setStyleSheet("""
                    QMessageBox {
                        background-color: #151515;
                        color: #ffffff;
                        font-family: 'Segoe UI';
                    }
                    QMessageBox QPushButton {
                        background-color: #00d4aa;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 8px 16px;
                        font-weight: bold;
                        min-width: 80px;
                    }
                    QMessageBox QPushButton:hover {
                        background-color: #00b894;
                    }
                """)
            elif type == "error":
                msg_box.setStyleSheet("""
                    QMessageBox {
                        background-color: #151515;
                        color: #ffffff;
                        font-family: 'Segoe UI';
                    }
                    QMessageBox QPushButton {
                        background-color: #ff4444;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 8px 16px;
                        font-weight: bold;
                        min-width: 80px;
                    }
                    QMessageBox QPushButton:hover {
                        background-color: #e63939;
                    }
                """)
            else:  # info
                msg_box.setStyleSheet("""
                    QMessageBox {
                        background-color: #151515;
                        color: #ffffff;
                        font-family: 'Segoe UI';
                    }
                    QMessageBox QPushButton {
                        background-color: #4a9eff;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 8px 16px;
                        font-weight: bold;
                        min-width: 80px;
                    }
                    QMessageBox QPushButton:hover {
                        background-color: #3d8bdb;
                    }
                """)
            
            msg_box.exec()
            
        except Exception as e:
            logging.error(f"Error showing modern notification: {e}")

    def update_live_grid_highlight(self, deck_id, preset_name):
        """Update live grid highlight with modern animation."""
        try:
            cells = getattr(self, 'live_grid_cells', {}).get(deck_id, {})
            color = getattr(self, 'live_grid_deck_colors', {}).get(deck_id, '#ff6b35')

            # Reset all cells to base style
            for cell in cells.values():
                if hasattr(cell, 'base_style'):
                    cell.setStyleSheet(cell.base_style)

            # Highlight active cell with modern glow effect
            if preset_name and preset_name in cells:
                cell = cells[preset_name]
                cell.setObjectName("visual-cell")
                
                # Modern highlight style with subtle glow
                highlight_style = f"""
                QFrame#visual-cell {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #252525,
                        stop:1 #1a1a1a);
                    border: 2px solid {color};
                    border-radius: 4px;
                    margin: 1px;
                    box-shadow: 0 0 10px rgba({self._hex_to_rgb(color)}, 0.5);
                }}
                QFrame#visual-cell:hover {{
                    border: 2px solid {color};
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2a2a2a,
                        stop:1 #1f1f1f);
                }}
                QLabel {{
                    border: none;
                    background: transparent;
                    color: white;
                }}
                """
                cell.setStyleSheet(highlight_style)
                
        except Exception as e:
            logging.error(f"Error updating modern grid highlight: {e}")

    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB values for CSS."""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"{r}, {g}, {b}"
        except:
            return "255, 107, 53"  # Default orange

    # === UTILITY METHODS ===
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

    # === MIDI DIALOG METHODS ===
    def show_midi_config(self):
        """Show modern MIDI configuration dialog."""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle(" MIDI Configuration")
            dialog.setModal(True)
            dialog.resize(1400, 900)
            
            # Modern dialog styling
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #0a0a0a;
                    color: #ffffff;
                    font-family: 'Segoe UI';
                }
            """)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(12, 12, 12, 12)
            layout.setSpacing(12)
            
            # Modern MIDI config widget
            config_widget = MidiConfigWidget(
                self.midi_engine, 
                self.visualizer_manager, 
                dialog
            )
            layout.addWidget(config_widget)
            
            # Modern close button
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            buttons.setStyleSheet("""
                QDialogButtonBox QPushButton {
                    background-color: #ff6b35;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                    min-width: 80px;
                }
                QDialogButtonBox QPushButton:hover {
                    background-color: #e55a2b;
                }
            """)
            buttons.rejected.connect(dialog.accept)
            layout.addWidget(buttons)
            
            dialog.exec()
            
            # Refresh grids after MIDI config changes
            self.refresh_visual_grids()
            
        except Exception as e:
            logging.error(f"Error opening modern MIDI config: {e}")
            self.show_modern_notification(f"Error opening MIDI configuration: {str(e)}", "error")

    # === MIDI TESTING AND DEBUG ===
    def test_midi_mappings(self):
        """Test MIDI mappings"""
        try:
            if self.midi_engine:
                test_notes = [37, 50, 55]
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

    def run_midi_debug(self):
        """Run complete MIDI debug"""
        try:
            logging.info("USER REQUESTED MIDI DEBUG")
            
            if not self.midi_engine:
                QMessageBox.warning(self, "Debug Error", "MIDI Engine not available")
                return
            
            self.debug_midi_connection()
            
            QMessageBox.information(self, "Debug MIDI", 
                                  "MIDI debug executed.\nCheck console for complete details.")
            
        except Exception as e:
            logging.error(f"Error in run_midi_debug: {e}")
            QMessageBox.critical(self, "Error", f"Error executing debug: {str(e)}")

    def debug_midi_connection(self):
        """Complete MIDI connection debug"""
        try:
            logging.info("STARTING MIDI CONNECTION DEBUG")
            logging.info("=" * 80)
            
            if not self.midi_engine:
                logging.error("MIDI Engine does not exist!")
                return
            
            # Check port status
            logging.info("1. MIDI PORT STATUS:")
            logging.info(f"   input_port: {self.midi_engine.input_port}")
            logging.info(f"   running: {self.midi_engine.running}")
            logging.info(f"   is_port_open(): {self.midi_engine.is_port_open()}")
            
            # Available ports
            logging.info("2. AVAILABLE MIDI PORTS:")
            available_ports = self.midi_engine.list_input_ports()
            for i, port in enumerate(available_ports):
                logging.info(f"   {i}: {port}")
            
            # Check mappings
            logging.info("3. CHECKING MAPPINGS:")
            logging.info(f"   Total mappings: {len(self.midi_engine.midi_mappings)}")
            
            # Check references
            logging.info("4. CHECKING REFERENCES:")
            logging.info(f"   mixer_window: {'' if self.midi_engine.mixer_window else ''}")
            logging.info(f"   control_panel: {'' if self.midi_engine.control_panel else ''}")
            
            logging.info("=" * 80)
            logging.info("DEBUG COMPLETED")
            
        except Exception as e:
            logging.error(f"Error in debug_midi_connection: {e}")
            import traceback
            traceback.print_exc()

    # === EVENT HANDLERS ===
    def on_preset_loaded_on_deck(self, deck_id, preset_name):
        """Handle preset loading from MIDI to update the UI"""
        try:
            import time
            current_time = time.strftime("%H:%M:%S")
            
            if deck_id == 'A':
                self.deck_a_status['active_preset'] = preset_name
                self.deck_a_status['last_activity'] = current_time
                
                if hasattr(self, 'deck_a_preset_label'):
                    self.deck_a_preset_label.setText(f"Preset: {preset_name}")
                if hasattr(self, 'deck_a_activity_label'):
                    self.deck_a_activity_label.setText(f"Última actividad: {current_time}")
                    
            elif deck_id == 'B':
                self.deck_b_status['active_preset'] = preset_name
                self.deck_b_status['last_activity'] = current_time
                
                if hasattr(self, 'deck_b_preset_label'):
                    self.deck_b_preset_label.setText(f"Preset: {preset_name}")
                if hasattr(self, 'deck_b_activity_label'):
                    self.deck_b_activity_label.setText(f"Última actividad: {current_time}")

            # Update grid highlight
            self.update_live_grid_highlight(deck_id, preset_name)

            logging.info(f"UI updated for deck {deck_id} to preset {preset_name}")
        except Exception as e:
            logging.error(f"Error updating preset selector for deck {deck_id}: {e}")

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
                lookup_entry = getattr(self.midi_engine, 'midi_lookup', {}).get(midi_key)
                if lookup_entry:
                    _, mapping_data = lookup_entry
                    deck_id = mapping_data.get('params', {}).get('deck_id')

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
            logging.error(f"ERROR IN on_midi_activity: {e}")
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
            logging.debug(f"[{timestamp}] Note: {note_name}{octave} Vel:{velocity}")
        except Exception as e:
            logging.error(f"Error handling note activity: {e}")

    def on_cc_activity(self, control_id, value):
        """Handle CC activity"""
        try:
            import time
            timestamp = time.strftime("%H:%M:%S")
            logging.debug(f"[{timestamp}] CC: {control_id} = {value}")
        except Exception as e:
            logging.error(f"Error handling CC activity: {e}")

    def on_midi_device_connected(self, device_name):
        """Handle MIDI device connection"""
        try:
            self.update_midi_device_display(device_name)
            logging.info(f"MIDI device connected: {device_name}")
        except Exception as e:
            logging.error(f"Error handling MIDI device connection: {e}")

    def on_midi_device_disconnected(self, device_name):
        """Handle MIDI device disconnection"""
        try:
            self.update_midi_device_display(None)
            logging.info(f"MIDI device disconnected: {device_name}")
        except Exception as e:
            logging.error(f"Error handling MIDI device disconnection: {e}")

    # === MONITORING METHODS ===
    def clear_midi_activity(self):
        """Clear MIDI activity table"""
        try:
            if hasattr(self, 'midi_activity_table'):
                self.midi_activity_table.setRowCount(0)
                self.midi_activity_data = []
                self.midi_message_count = 0
        except Exception as e:
            logging.error(f"Error clearing MIDI activity: {e}")

    def toggle_midi_activity_monitoring(self):
        """Pause/resume MIDI monitoring"""
        try:
            self.midi_monitoring_paused = not getattr(self, 'midi_monitoring_paused', False)
        except Exception as e:
            logging.error(f"Error toggling MIDI monitoring: {e}")

    def clear_events_log(self):
        """Clear events log"""
        try:
            if hasattr(self, 'events_log'):
                self.events_log.clear()
        except Exception as e:
            logging.error(f"Error clearing events log: {e}")

    def export_events_log(self):
        """Export events log"""
        try:
            QMessageBox.information(self, "Export", "Functionality to be implemented")
        except Exception as e:
            logging.error(f"Error exporting events log: {e}")

    def update_system_info(self):
        """Update system information"""
        try:
            if hasattr(self, 'system_info_text'):
                try:
                    import psutil
                    import platform

                    info = (
                        f"Sistema: {platform.system()} {platform.release()}\n"
                        f"CPU: {psutil.cpu_percent()}%\n"
                        f"RAM: {psutil.virtual_memory().percent}%\n"
                        f"MIDI Engine: {'Activo' if self.midi_engine else 'Inactivo'}\n"
                        f"Mappings: {len(self.midi_engine.get_midi_mappings()) if self.midi_engine else 0}"
                    )
                except ImportError:
                    import platform
                    info = (
                        f"Sistema: Python {platform.python_version()}\n"
                        f"MIDI Engine: {'Activo' if self.midi_engine else 'Inactivo'}\n"
                        f"Mappings: {len(self.midi_engine.get_midi_mappings()) if self.midi_engine else 0}"
                    )

                if self.mixer_window:
                    status_a = self.mixer_window.get_deck_status('A')
                    status_b = self.mixer_window.get_deck_status('B')
                    info += (
                        f"\nDeck A GPU: {status_a.get('gpu_renderer', 'N/A')} | FPS: {status_a.get('fps', 0):.1f}"
                        f"\nDeck B GPU: {status_b.get('gpu_renderer', 'N/A')} | FPS: {status_b.get('fps', 0):.1f}"
                    )

                self.system_info_text.setPlainText(info)
        except Exception as e:
            logging.error(f"Error updating system info: {e}")

    # === DEVICE AND AUDIO METHODS ===
    def refresh_devices(self):
        """Refresh device information and update displays"""
        try:
            self.update_midi_device_display()
            self.update_audio_device_display()
            logging.info("Device information refreshed")
        except Exception as e:
            logging.error(f"Error refreshing devices: {e}")

    def update_audio_device_display(self):
        """Update audio device display"""
        try:
            # Future implementation if needed
            pass
        except Exception as e:
            logging.error(f"Error updating audio device display: {e}")

    def update_audio_level(self, level):
        """Update audio level display"""
        try:
            if hasattr(self, 'audio_level_bar'):
                self.audio_level_bar.setValue(int(max(0, min(100, level))))
        except Exception as e:
            logging.error(f"Error updating audio level: {e}")

    def update_frequency_bands(self, fft_data):
        """Update frequency band displays"""
        try:
            # Future implementation if needed
            pass
        except Exception as e:
            logging.error(f"Error updating frequency bands: {e}")

    def update_info(self):
        """Update system information"""
        try:
            # Update mix value from mixer window
            if self.mixer_window and hasattr(self.mixer_window, 'get_mix_value_percent'):
                mix_value = self.mixer_window.get_mix_value_percent()
                if hasattr(self, 'mix_value_label'):
                    self.mix_value_label.setText(f"Crossfader: {mix_value}%")
                if hasattr(self, 'mix_progress_bar'):
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

    # === FULLSCREEN HANDLING ===
    def activate_fullscreen_mode(self):
        """Launch mixer output fullscreen on configured monitors"""
        monitors = self.settings_manager.get_fullscreen_monitors()
        if not monitors:
            QMessageBox.warning(self, "Fullscreen", "No monitors configured for fullscreen mode.")
            return

        screens = QApplication.screens()
        self.exit_fullscreen_mode()

        for i, monitor_index in enumerate(monitors):
            try:
                screen = screens[monitor_index] if monitor_index < len(screens) else screens[0]
                if i == 0:
                    window = self.mixer_window
                else:
                    share_context_handle = None
                    try:
                        main_gl_context = self.mixer_window.gl_widget.context()
                    except Exception as e:
                        logging.warning(f"Could not access mixer OpenGL context: {e}")
                        main_gl_context = None

                    if main_gl_context:
                        try:
                            share_context_handle = main_gl_context.rawHandle()
                        except AttributeError:
                            try:
                                native = main_gl_context.nativeInterface()
                                if native and hasattr(native, "context"):
                                    share_context_handle = native.context()
                            except Exception as e:
                                logging.debug(f"Could not obtain native GL handle: {e}")

                    window = MixerWindow(self.visualizer_manager, self.settings_manager, 
                                       self.audio_analyzer, share_context=share_context_handle)
                    
                    # Connect signals
                    self.mixer_window.signal_set_mix_value.connect(window.set_mix_value)
                    self.mixer_window.signal_set_deck_visualizer.connect(window.set_deck_visualizer)
                    self.mixer_window.signal_update_deck_control.connect(window.update_deck_control)
                    self.mixer_window.signal_set_deck_opacity.connect(window.set_deck_opacity)
                    self.mixer_window.signal_trigger_deck_action.connect(window.trigger_deck_action)

                # Apply current mixer state
                def init_state(win=window):
                    win.set_mix_value(int(self.mixer_window.mix_value * 100))
                    if self.mixer_window.deck_a and self.mixer_window.deck_a.current_visualizer_name:
                        win.set_deck_visualizer('A', self.mixer_window.deck_a.current_visualizer_name)
                    if self.mixer_window.deck_b and self.mixer_window.deck_b.current_visualizer_name:
                        win.set_deck_visualizer('B', self.mixer_window.deck_b.current_visualizer_name)

                window.gl_ready.connect(init_state)
                if window.gl_initialized:
                    init_state()

                window.exit_fullscreen.connect(self.exit_fullscreen_mode)

                # Set screen and show fullscreen
                handle = window.windowHandle()
                if handle is None:
                    window.show()
                    handle = window.windowHandle()
                if handle:
                    try:
                        handle.setScreen(screen)
                        window.setGeometry(screen.geometry())
                    except Exception as e:
                        logging.warning(f"Could not set screen geometry: {e}")
                        window.move(screen.geometry().topLeft())
                else:
                    window.move(screen.geometry().topLeft())

                window.showFullScreen()
                self.fullscreen_windows.append(window)
                
            except Exception as e:
                logging.error(f"Error activating fullscreen on monitor {monitor_index}: {e}")

    def exit_fullscreen_mode(self):
        """Exit fullscreen mode and close extra windows"""
        for w in list(self.fullscreen_windows):
            try:
                if w.isFullScreen():
                    w.showNormal()
                if w is not self.mixer_window:
                    w.close()
            except Exception as e:
                logging.error(f"Error closing fullscreen window: {e}")
        self.fullscreen_windows.clear()

    # === PREFERENCES AND GPU ===
    def show_preferences(self):
        try:
            dialog = PreferencesDialog(self.settings_manager, self.midi_engine, self.audio_analyzer, self)
            dialog.exec()
        except Exception as e:
            logging.error(f"Error opening preferences: {e}")
            QMessageBox.critical(self, "Error", f"Could not open preferences: {str(e)}")

    def apply_gpu_selection(self, index, backend_type=None):
        """Forward GPU selection changes to the mixer window"""
        try:
            if self.mixer_window:
                self.mixer_window.apply_gpu_selection(index, backend_type)
        except Exception as e:
            logging.error(f"Error applying GPU selection: {e}")

    # === HELPER METHODS ===
    def on_midi_mappings_changed(self):
        """Handle MIDI mappings change"""
        try:
            self.update_mappings_info()
            logging.info("MIDI mappings changed")
        except Exception as e:
            logging.error(f"Error handling MIDI mappings change: {e}")

    def test_mix_action(self, midi_key):
        """Test mix action"""
        try:
            if self.midi_engine:
                self.midi_engine.simulate_midi_message(midi_key)
                logging.info(f"Testing mix action: {midi_key}")
        except Exception as e:
            logging.error(f"Error testing mix action: {e}")

    # === CLEANUP ===
    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'update_timer'):
                self.update_timer.stop()
            
            logging.debug("Control panel cleaned up")
            
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