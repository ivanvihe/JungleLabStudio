import sys
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtCore import QTimer

from utils.settings_manager import SettingsManager
from midi.midi_engine import MidiEngine
from visuals.visualizer_manager import VisualizerManager
from audio.audio_analyzer import AudioAnalyzer
from .mixer_window import MixerWindow
from .control_panel_window import ControlPanelWindow
from .midi_mapping_dialog import MidiMappingDialog

# Force reload of visualizer_manager to ensure fresh loading
import importlib
import visuals.visualizer_manager
importlib.reload(visuals.visualizer_manager)
from visuals.visualizer_manager import VisualizerManager

# Configure logging with better formatting
logging.basicConfig(
    level=logging.DEBUG,  # Ensure base level is DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('audiovisualizer.log', mode='w')
    ]
)

# Get specific loggers and set their levels to DEBUG
logging.getLogger('visuals.deck').setLevel(logging.DEBUG)
logging.getLogger('ui.mixer_window').setLevel(logging.DEBUG)
logging.getLogger('visuals.visualizer_manager').setLevel(logging.DEBUG)

class MainApplication:
    def __init__(self):
        logging.info("🚀 Initializing Audio Visualizer Pro...")
        
        try:
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("Audio Visualizer Pro")
            self.app.setApplicationVersion("1.0")
            
            # Set up OpenGL format for better compatibility
            self.setup_opengl_format()
            
            # Initialize core components
            self.initialize_components()
            
            # Validate components
            self.validate_initialization()
            
            # Create UI windows
            self.create_windows()
            
            # Setup connections and auto-connect devices
            self.setup_connections()
            self.auto_connect_devices()
            
            # Setup debug connections for MIDI
            self.setup_debug_connections()
            
            logging.info("✅ Audio Visualizer Pro initialized successfully!")
            
        except Exception as e:
            logging.critical(f"❌ Failed to initialize application: {e}")
            self.show_critical_error("Initialization Error", str(e))
            sys.exit(1)

    def setup_opengl_format(self):
        """Setup OpenGL surface format with better compatibility"""
        try:
            format = QSurfaceFormat()
            format.setVersion(3, 3)
            format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
            format.setDepthBufferSize(24)
            format.setStencilBufferSize(8)
            format.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
            format.setSamples(4)  # Anti-aliasing
            QSurfaceFormat.setDefaultFormat(format)
            logging.debug("✅ OpenGL format configured")
        except Exception as e:
            logging.error(f"❌ Error setting up OpenGL format: {e}")
            raise

    def initialize_components(self):
        """Initialize all core components"""
        try:
            # Initialize settings manager first
            logging.info("📋 Initializing Settings Manager...")
            self.settings_manager = SettingsManager()
            
            # Initialize visualizer manager
            logging.info("🎨 Initializing Visualizer Manager...")
            self.visualizer_manager = VisualizerManager()
            
            # Initialize MIDI engine
            logging.info("🎹 Initializing MIDI Engine...")
            self.midi_engine = MidiEngine(self.settings_manager, self.visualizer_manager)
            
            # Initialize audio analyzer
            logging.info("🎵 Initializing Audio Analyzer...")
            self.audio_analyzer = AudioAnalyzer()
            
            logging.info("✅ Core components initialized")
            
        except Exception as e:
            logging.error(f"❌ Error initializing components: {e}")
            raise

    def validate_initialization(self):
        """Validate that all components initialized correctly"""
        try:
            # Check visualizers
            visualizer_names = self.visualizer_manager.get_visualizer_names()
            if not visualizer_names:
                raise Exception("No visualizers found! Check your visuals directory.")
            
            logging.info(f"🎨 Loaded {len(visualizer_names)} visualizers: {visualizer_names}")
            
            # List all visualizer classes for debugging
            for name in visualizer_names:
                visualizer_class = self.visualizer_manager.get_visualizer_class(name)
                logging.debug(f"  Visualizer '{name}' -> {visualizer_class}")
            
            # Check MIDI mappings
            midi_mappings = self.midi_engine.get_midi_mappings()
            logging.info(f"🎹 Loaded {len(midi_mappings)} MIDI mappings")
            for mapping_id, mapping_data in midi_mappings.items():
                midi_key = mapping_data.get('midi', 'no_midi')
                action_type = mapping_data.get('type', 'unknown')
                logging.info(f"  📋 MIDI Mapping: {midi_key} -> {action_type}")
            
            # Check settings
            settings = self.settings_manager.get_all_settings()
            logging.info(f"📋 Loaded settings with {len(settings)} entries")
            
        except Exception as e:
            logging.error(f"❌ Validation failed: {e}")
            raise

    def create_windows(self):
        """Create and setup UI windows"""
        try:
            logging.info("🖥️ Creating UI windows...")
            
            # Create mixer window
            self.mixer_window = MixerWindow(self.visualizer_manager)
            logging.debug("✅ Mixer window created")
            
            # Create control panel
            self.control_panel = ControlPanelWindow(
                self.mixer_window, 
                self.settings_manager, 
                self.midi_engine, 
                self.visualizer_manager,
                self.audio_analyzer,
                self.open_midi_mapping_dialog
            )
            logging.debug("✅ Control panel created")
            
            # Set application references in MIDI engine for action execution
            self.midi_engine.set_application_references(
                mixer_window=self.mixer_window,
                control_panel=self.control_panel
            )
            logging.debug("✅ MIDI engine references set")
            
        except Exception as e:
            logging.error(f"❌ Error creating windows: {e}")
            raise

    def setup_connections(self):
        """Setup all signal connections"""
        try:
            logging.info("🔗 Setting up connections...")
            
            # Connect MIDI signals to control panel for UI updates
            self.midi_engine.device_connected.connect(self.on_midi_device_connected)
            self.midi_engine.device_disconnected.connect(self.on_midi_device_disconnected)
            self.midi_engine.bpm_changed.connect(self.on_bmp_changed)
            
            logging.info("✅ MIDI connections established")
            
        except Exception as e:
            logging.error(f"❌ Error setting up connections: {e}")
            raise

    def setup_debug_connections(self):
        """Setup debug connections for MIDI monitoring"""
        try:
            # Connect to MIDI learning signal for debugging
            self.midi_engine.midi_message_received_for_learning.connect(self.debug_midi_message)
            
            # Connect to raw MIDI messages for activity monitoring
            self.midi_engine.midi_message_received.connect(self.debug_raw_midi_message)
            
            logging.info("🐛 Debug connections established")
            
        except Exception as e:
            logging.warning(f"⚠️ Could not setup debug connections: {e}")

    def debug_midi_message(self, message_key):
        """Debug method to log all MIDI messages and check mappings"""
        try:
            logging.info(f"🎹 MIDI Learning Signal: {message_key}")
            
            # Check if this message has a mapping
            mappings_found = 0
            for action_id, mapping_data in self.midi_engine.midi_mappings.items():
                if mapping_data.get('midi') == message_key:
                    action_type = mapping_data.get('type', 'unknown')
                    params = mapping_data.get('params', {})
                    logging.info(f"🎯 Found mapping: {action_id} -> {action_type} {params}")
                    mappings_found += 1
            
            if mappings_found == 0:
                logging.info(f"❌ No mapping found for: {message_key}")
            else:
                logging.info(f"✅ Found {mappings_found} mapping(s) for: {message_key}")
                
        except Exception as e:
            logging.error(f"Error in debug_midi_message: {e}")

    def debug_raw_midi_message(self, msg):
        """Debug raw MIDI messages"""
        try:
            if hasattr(msg, 'type'):
                if msg.type in ['note_on', 'note_off', 'control_change']:
                    logging.debug(f"🎼 Raw MIDI: {msg.type} - {msg}")
        except Exception as e:
            logging.error(f"Error in debug_raw_midi_message: {e}")

    def on_midi_device_connected(self, device_name):
        """Handle MIDI device connection"""
        try:
            self.control_panel.update_midi_device_display(device_name)
            logging.info(f"🎹 MIDI device connected: {device_name}")
            
            # Load and apply any saved mappings
            mappings = self.midi_engine.get_midi_mappings()
            if mappings:
                logging.info(f"📝 Applied {len(mappings)} saved MIDI mappings")
                
        except Exception as e:
            logging.error(f"Error handling MIDI device connection: {e}")

    def on_midi_device_disconnected(self, device_name):
        """Handle MIDI device disconnection"""
        try:
            self.control_panel.update_midi_device_display(None)
            logging.info(f"🎹 MIDI device disconnected: {device_name}")
        except Exception as e:
            logging.error(f"Error handling MIDI device disconnection: {e}")

    def on_bmp_changed(self, bpm):
        """Handle BPM change"""
        try:
            self.control_panel.update_bpm_display(bpm)
            logging.debug(f"🥁 BPM updated: {bpm:.1f}")
        except Exception as e:
            logging.error(f"Error handling BPM change: {e}")

    def auto_connect_devices(self):
        """Auto-connect previously saved devices"""
        try:
            logging.info("🔌 Auto-connecting saved devices...")
            
            # Auto-connect MIDI device
            last_midi_device = self.settings_manager.get_setting("last_midi_device", "")
            if last_midi_device and last_midi_device != "":
                available_midi = self.midi_engine.list_input_ports()
                logging.debug(f"Available MIDI devices: {available_midi}")
                
                if last_midi_device in available_midi:
                    if self.midi_engine.open_input_port(last_midi_device):
                        logging.info(f"✅ Auto-connected to MIDI device: {last_midi_device}")
                    else:
                        logging.warning(f"⚠️ Failed to auto-connect to MIDI device: {last_midi_device}")
                else:
                    logging.info(f"❌ Previously used MIDI device '{last_midi_device}' not available")
            else:
                logging.info("ℹ️ No MIDI device saved for auto-connection")
            
            # Auto-connect audio device
            last_audio_device = self.settings_manager.get_setting("audio_settings.input_device", "")
            if last_audio_device and last_audio_device != "":
                available_audio = self.audio_analyzer.get_available_devices()
                logging.debug(f"Available audio devices: {len(available_audio)} devices")
                
                for device in available_audio:
                    device_text = f"{device['name']} ({device['channels']} ch)"
                    if device_text == last_audio_device:
                        self.audio_analyzer.set_input_device(device['index'])
                        self.audio_analyzer.start_analysis()
                        logging.info(f"✅ Auto-connected to audio device: {last_audio_device}")
                        break
                else:
                    logging.info(f"❌ Previously used audio device '{last_audio_device}' not available")
            else:
                logging.info("ℹ️ No audio device saved for auto-connection")
                
        except Exception as e:
            logging.error(f"Error in auto_connect_devices: {e}")

    def open_midi_mapping_dialog(self, parent_widget):
        """Open the MIDI mapping dialog"""
        try:
            logging.info("🎛️ Opening MIDI mapping dialog...")
            
            visualizer_names = self.visualizer_manager.get_visualizer_names()
            dialog = MidiMappingDialog(visualizer_names, self.midi_engine, parent_widget)
            
            # Connect the mappings saved signal to update the engine
            dialog.mappings_saved.connect(self.on_midi_mappings_saved)
            
            result = dialog.exec()
            
            if result == dialog.DialogCode.Accepted:
                logging.info("✅ MIDI mapping dialog closed with changes saved")
            else:
                logging.info("ℹ️ MIDI mapping dialog closed without saving")
                
        except Exception as e:
            logging.error(f"Error opening MIDI mapping dialog: {e}")
            QMessageBox.critical(
                parent_widget, 
                "Error", 
                f"No se pudo abrir el diálogo de mapeo MIDI: {str(e)}"
            )

    def on_midi_mappings_saved(self, mappings):
        """Handle saved MIDI mappings"""
        try:
            logging.info(f"💾 MIDI mappings saved from dialog: {len(mappings)} mappings")
            
            # Log details of saved mappings
            for action_id, mapping_data in mappings.items():
                midi_key = mapping_data.get('midi', 'no_midi')
                action_type = mapping_data.get('type', 'unknown')
                logging.info(f"  💾 Saved mapping: {midi_key} -> {action_type}")
            
        except Exception as e:
            logging.error(f"Error handling saved MIDI mappings: {e}")

    def test_midi_mapping(self):
        """Test method to manually trigger a MIDI mapping"""
        try:
            logging.info("🧪 Testing MIDI mapping functionality...")
            
            # Get available mappings
            mappings = self.midi_engine.get_midi_mappings()
            if not mappings:
                logging.info("❌ No MIDI mappings available to test")
                return
            
            # Test the first mapping
            first_mapping = next(iter(mappings.values()))
            test_message_key = first_mapping.get('midi')
            
            if test_message_key:
                logging.info(f"🎹 Testing mapping with key: {test_message_key}")
                self.midi_engine.execute_mapped_action(test_message_key, 127)
            else:
                logging.info("❌ No valid MIDI key found in mappings")
                
        except Exception as e:
            logging.error(f"Error testing MIDI mapping: {e}")

    def test_visualizer_directly(self):
        """Test setting visualizer directly"""
        try:
            logging.info("🧪 Testing direct visualizer change...")
            
            # Test changing deck A visualizer
            visualizer_names = self.visualizer_manager.get_visualizer_names()
            if visualizer_names and len(visualizer_names) > 1:
                test_visualizer = visualizer_names[1]  # Use second visualizer
                logging.info(f"🎨 Testing direct visualizer change to: {test_visualizer}")
                self.mixer_window.safe_set_deck_visualizer('A', test_visualizer)
                
                # Test changing crossfader
                QTimer.singleShot(2000, lambda: self.mixer_window.safe_set_mix_value(75))
                logging.info("🎚️ Testing crossfader change to 75%")
                
        except Exception as e:
            logging.error(f"Error testing visualizer directly: {e}")

    def show_critical_error(self, title, message):
        """Show critical error dialog"""
        try:
            app = QApplication.instance()
            if app:
                QMessageBox.critical(None, title, message)
        except:
            print(f"CRITICAL ERROR: {title} - {message}")

    def show_windows(self):
        """Show both windows with proper positioning"""
        try:
            logging.info("🖥️ Showing application windows...")
            
            # Show mixer window first
            self.mixer_window.show()
            
            # Show control panel
            self.control_panel.show()
            
            # Apply saved window positions
            QTimer.singleShot(100, self.apply_window_positions)
            
            logging.info("✅ Windows displayed")
            
        except Exception as e:
            logging.error(f"Error showing windows: {e}")
            raise

    def apply_window_positions(self):
        """Apply saved window positions"""
        try:
            # Get saved positions
            cp_position = self.settings_manager.get_window_position("control_panel")
            mixer_position = self.settings_manager.get_window_position("main_window")
            
            # Apply control panel position
            if cp_position:
                self.control_panel.setGeometry(
                    cp_position.get('x', 50),
                    cp_position.get('y', 50),
                    cp_position.get('width', 1200),
                    cp_position.get('height', 800)
                )
            
            # Apply mixer window position
            if mixer_position:
                self.mixer_window.setGeometry(
                    mixer_position.get('x', 100),
                    mixer_position.get('y', 100),
                    mixer_position.get('width', 800),
                    mixer_position.get('height', 600)
                )
                
            logging.debug("✅ Window positions applied")
            
        except Exception as e:
            logging.error(f"Error applying window positions: {e}")

    def save_window_positions(self):
        """Save current window positions"""
        try:
            # Save control panel position
            cp_geometry = self.control_panel.geometry()
            self.settings_manager.set_window_position(
                "control_panel",
                cp_geometry.x(),
                cp_geometry.y(), 
                cp_geometry.width(),
                cp_geometry.height()
            )
            
            # Save mixer window position
            mixer_geometry = self.mixer_window.geometry()
            self.settings_manager.set_window_position(
                "main_window",
                mixer_geometry.x(),
                mixer_geometry.y(),
                mixer_geometry.width(), 
                mixer_geometry.height()
            )
            
            logging.debug("✅ Window positions saved")
            
        except Exception as e:
            logging.error(f"Error saving window positions: {e}")

    def cleanup(self):
        """Cleanup application resources"""
        try:
            logging.info("🧹 Cleaning up application resources...")
            
            # Save window positions
            self.save_window_positions()
            
            # Close MIDI connection
            if self.midi_engine:
                self.midi_engine.close_input_port()
                logging.debug("✅ MIDI connection closed")
            
            # Stop audio analysis
            if self.audio_analyzer:
                self.audio_analyzer.stop_analysis()
                logging.debug("✅ Audio analysis stopped")
            
            # Cleanup mixer window OpenGL resources
            if hasattr(self, 'mixer_window') and self.mixer_window:
                self.mixer_window.cleanup()
                logging.debug("✅ OpenGL resources cleaned")
            
            logging.info("✅ Cleanup completed")
            
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

    def run(self):
        """Run the application"""
        try:
            logging.info("🚀 Starting Audio Visualizer Pro...")
            
            # Show windows
            self.show_windows()
            
            # Test visualizer change after 3 seconds
            # QTimer.singleShot(3000, self.test_visualizer_directly)
            
            # Test MIDI mapping after 5 seconds (if any exist)
            QTimer.singleShot(5000, self.test_midi_mapping)
            
            # Run the application
            result = self.app.exec()
            
            logging.info(f"📱 Application finished with exit code: {result}")
            return result
            
        except Exception as e:
            logging.error(f"Error running application: {e}")
            return 1
        finally:
            # Always cleanup
            self.cleanup()