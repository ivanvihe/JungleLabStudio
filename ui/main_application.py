# ui/main_application.py - FIXED VERSION
import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt6.QtGui import QSurfaceFormat, QPixmap
from PyQt6.QtCore import QTimer, Qt

from utils.settings_manager import SettingsManager
from midi.midi_engine import MidiEngine
from visuals.visualizer_manager import VisualizerManager
from audio.audio_analyzer import AudioAnalyzer
from .mixer_window import MixerWindow
from .control_panel_window import ControlPanelWindow

# Force reload of visualizer_manager to ensure fresh loading
import importlib
import visuals.visualizer_manager

from visuals.visualizer_manager import VisualizerManager

# Configure logging with better formatting
logging.basicConfig(
    level=logging.DEBUG,
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
            # Set up OpenGL format for better compatibility
            format = QSurfaceFormat()
            format.setVersion(3, 3)
            format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
            format.setDepthBufferSize(24)
            format.setStencilBufferSize(8)
            format.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
            format.setSamples(4)  # Anti-aliasing
            QSurfaceFormat.setDefaultFormat(format)
            logging.debug("✅ OpenGL format configured")

            self.app = QApplication(sys.argv)
            self.app.setApplicationName("Audio Visualizer Pro")
            self.app.setApplicationVersion("1.0")

            # Simple loading splash while initializing components
            pixmap = QPixmap(400, 300)
            pixmap.fill(Qt.GlobalColor.black)
            self.splash = QSplashScreen(pixmap)
            self.splash.showMessage(
                "Loading visuals and mappings...",
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom,
                Qt.GlobalColor.white,
            )
            self.splash.show()
            self.app.processEvents()

            # Initialize core components
            self.initialize_components()
            
            # Validate components
            self.validate_initialization()
            
            # Create UI windows with proper sequencing
            self.create_windows()

            # Close splash once windows are ready
            self.splash.finish(self.mixer_window)
            
            # CRITICAL: Setup connections and references BEFORE auto-connect
            self.setup_connections()
            
            # Setup debug connections for MIDI
            self.setup_debug_connections()
            
            logging.info("✅ Audio Visualizer Pro initialized successfully!")
            
        except Exception as e:
            logging.critical(f"❌ Failed to initialize application: {e}")
            import traceback
            traceback.print_exc()
            self.show_critical_error("Initialization Error", str(e))
            sys.exit(1)

    

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
            
            # Check MIDI mappings
            midi_mappings = self.midi_engine.get_midi_mappings()
            logging.info(f"🎹 Loaded {len(midi_mappings)} MIDI mappings")
            
            # Check settings
            settings = self.settings_manager.get_all_settings()
            logging.info(f"📋 Loaded settings with {len(settings)} entries")
            
            # Log GPU configuration
            gpu_index = self.settings_manager.get_setting("visual_settings.gpu_index", 0)
            backend = self.settings_manager.get_setting("visual_settings.backend", "OpenGL")
            gpu_name = self.settings_manager.get_setting("visual_settings.gpu_name", "Unknown")
            logging.info(f"🎮 GPU Configuration: {gpu_name} (Index: {gpu_index}, Backend: {backend})")
            
        except Exception as e:
            logging.error(f"❌ Validation failed: {e}")
            raise

    def create_windows(self):
        """Create and setup UI windows"""
        try:
            logging.info("🖥️ Creating UI windows...")
            
            # Create mixer window first
            self.mixer_window = MixerWindow(self.visualizer_manager, self.settings_manager)
            logging.info("✅ Mixer window created")
            
            # Create control panel (rediseñado para operación MIDI)
            self.control_panel = ControlPanelWindow(
                self.mixer_window,
                self.settings_manager,
                self.midi_engine,
                self.visualizer_manager,
                self.audio_analyzer,
            )
            logging.info("✅ Control panel created")
            
        except Exception as e:
            logging.error(f"❌ Error creating windows: {e}")
            raise

    def setup_connections(self):
        """Setup all signal connections and references - CRITICAL ORDER"""
        try:
            logging.info("🔗 Setting up connections and references...")
            
            # STEP 1: Set application references in MIDI engine FIRST
            logging.info("🔗 Setting MIDI engine references...")
            self.midi_engine.set_application_references(
                mixer_window=self.mixer_window,
                control_panel=self.control_panel
            )
            
            # STEP 2: Connect MIDI signals to control panel for UI updates
            logging.info("🔗 Connecting MIDI signals...")
            if hasattr(self.midi_engine, 'device_connected'):
                self.midi_engine.device_connected.connect(self.on_midi_device_connected)
            if hasattr(self.midi_engine, 'device_disconnected'):
                self.midi_engine.device_disconnected.connect(self.on_midi_device_disconnected)
            if hasattr(self.midi_engine, 'bpm_changed'):
                self.midi_engine.bpm_changed.connect(self.on_bpm_changed)
            
            # STEP 3: Verify references are set
            if not self.midi_engine.mixer_window:
                logging.error("❌ CRITICAL: mixer_window reference not set in MIDI engine!")
                raise Exception("MIDI engine mixer_window reference failed")
            
            if not self.midi_engine.control_panel:
                logging.error("❌ CRITICAL: control_panel reference not set in MIDI engine!")
                raise Exception("MIDI engine control_panel reference failed")
            
            logging.info("✅ All connections and references established")
            
        except Exception as e:
            logging.error(f"❌ Error setting up connections: {e}")
            raise

    def setup_debug_connections(self):
        """Setup debug connections for MIDI monitoring"""
        try:
            # Connect to MIDI learning signal for debugging
            if hasattr(self.midi_engine, 'midi_message_received_for_learning'):
                self.midi_engine.midi_message_received_for_learning.connect(self.debug_midi_message)
            
            # Connect to raw MIDI messages for activity monitoring
            if hasattr(self.midi_engine, 'midi_message_received'):
                self.midi_engine.midi_message_received.connect(self.debug_raw_midi_message)
            
            logging.info("🛠 Debug connections established")
            
        except Exception as e:
            logging.warning(f"⚠️ Could not setup debug connections: {e}")

    def debug_midi_message(self, message_key):
        """Debug method to log all MIDI messages and check mappings"""
        try:
            logging.debug(f"🎹 MIDI Learning Signal: {message_key}")

            # Look up mapping information using the MIDI lookup table
            mapping_entry = getattr(self.midi_engine, 'midi_lookup', {}).get(message_key)
            if mapping_entry:
                action_id, mapping_data = mapping_entry
                action_type = mapping_data.get('type', 'unknown')
                params = mapping_data.get('params', {})
                logging.debug(f"🎯 Found mapping: {action_id} -> {action_type} {params}")
            else:
                logging.debug(f"🔍 No mapping found for: {message_key}")
                
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
            if hasattr(self, 'control_panel'):
                self.control_panel.update_midi_device_display(device_name)
            logging.info(f"🎹 MIDI device connected: {device_name}")
                
        except Exception as e:
            logging.error(f"Error handling MIDI device connection: {e}")

    def on_midi_device_disconnected(self, device_name):
        """Handle MIDI device disconnection"""
        try:
            if hasattr(self, 'control_panel'):
                self.control_panel.update_midi_device_display(None)
            logging.info(f"🎹 MIDI device disconnected: {device_name}")
        except Exception as e:
            logging.error(f"Error handling MIDI device disconnection: {e}")

    def on_bpm_changed(self, bpm):
        """Handle BPM change"""
        try:
            if hasattr(self, 'control_panel'):
                # Update BPM display if control panel has this method
                if hasattr(self.control_panel, 'update_bpm_display'):
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
            if last_midi_device:
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
            if last_audio_device:
                try:
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
                except Exception as e:
                    logging.warning(f"⚠️ Error auto-connecting audio device: {e}")
            else:
                logging.info("ℹ️ No audio device saved for auto-connection")
                
        except Exception as e:
            logging.error(f"Error in auto_connect_devices: {e}")

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
            QTimer.singleShot(200, self.apply_window_positions)
            
            # IMPORTANT: Auto-connect devices AFTER windows are shown and connections established
            QTimer.singleShot(1000, self.auto_connect_devices)

            # Only load a test visualizer when explicitly requested
            if os.getenv("AVP_LOAD_TEST_VISUALS") == "1":
                QTimer.singleShot(2000, self.load_test_visualizers)
            
            logging.info("✅ Windows displayed")
            
        except Exception as e:
            logging.error(f"Error showing windows: {e}")
            raise

    def load_test_visualizers(self):
        """Load a test visualizer to verify the rendering pipeline (debug only)"""
        try:
            logging.info("🎨 Loading test visualizers...")
            
            # Get available visualizers
            visualizers = self.visualizer_manager.get_visualizer_names()
            if not visualizers:
                logging.error("❌ No visualizers available for testing!")
                return
            
            # Try to load a simple visualizer on Deck A for testing
            test_visualizer = None
            preferred_order = ['Simple Test', 'Intro Background', 'Abstract Lines', 'Geometric Particles']
            
            for preferred in preferred_order:
                if preferred in visualizers:
                    test_visualizer = preferred
                    break
            
            if not test_visualizer:
                # Use the first available visualizer
                test_visualizer = visualizers[0]
            
            logging.info(f"🧪 Loading test visualizer '{test_visualizer}' on Deck A")
            
            # Load the test visualizer on Deck A
            self.mixer_window.safe_set_deck_visualizer('A', test_visualizer)
            
            # Wait a bit and check if it worked
            QTimer.singleShot(1000, lambda: self.verify_test_visualizer(test_visualizer))
            
        except Exception as e:
            logging.error(f"Error loading test visualizers: {e}")

    def verify_test_visualizer(self, expected_visualizer):
        """Verify that the test visualizer loaded correctly"""
        try:
            current_visualizers = self.mixer_window.get_current_visualizers()
            deck_a_visualizer = current_visualizers.get('A')
            
            if deck_a_visualizer == expected_visualizer:
                logging.info(f"✅ Test visualizer '{expected_visualizer}' loaded successfully on Deck A")
                
                # Get deck status for additional verification
                deck_status = self.mixer_window.get_deck_status('A')
                logging.info(f"🎮 Deck A Status: {deck_status}")
                
                if deck_status.get('is_ready'):
                    logging.info("✅ Deck A is ready and should be rendering")
                else:
                    logging.warning("⚠️ Deck A loaded visualizer but is not ready")
                    
            else:
                logging.error(f"❌ Test visualizer failed to load. Expected: '{expected_visualizer}', Got: '{deck_a_visualizer}'")
                
                # Try troubleshooting
                self.troubleshoot_visualizer_loading()
                
        except Exception as e:
            logging.error(f"Error verifying test visualizer: {e}")

    def troubleshoot_visualizer_loading(self):
        """Troubleshoot visualizer loading issues"""
        try:
            logging.info("🔧 Troubleshooting visualizer loading...")
            
            # Check OpenGL status
            if self.mixer_window.gl_initialized:
                logging.info("✅ Mixer window OpenGL is initialized")
            else:
                logging.error("❌ Mixer window OpenGL is NOT initialized")
            
            # Check deck status
            if self.mixer_window.deck_a:
                deck_info = self.mixer_window.deck_a.get_deck_info()
                logging.info(f"🎮 Deck A Info: {deck_info}")
                
                if deck_info.get('gl_initialized'):
                    logging.info("✅ Deck A OpenGL is initialized")
                else:
                    logging.error("❌ Deck A OpenGL is NOT initialized")
                    
                # Try to force initialization
                logging.info("🔄 Attempting to force Deck A refresh...")
                self.mixer_window.deck_a.force_refresh()
            else:
                logging.error("❌ Deck A is None!")
            
            # Check visualizer manager
            available = self.visualizer_manager.get_visualizer_names()
            logging.info(f"🎨 Available visualizers: {len(available)} - {available[:5]}...")
            
        except Exception as e:
            logging.error(f"Error in troubleshooting: {e}")

    def apply_window_positions(self):
        """Apply saved window positions"""
        try:
            # Get saved positions
            cp_position = self.settings_manager.get_window_position("control_panel")
            mixer_position = self.settings_manager.get_window_position("main_window")
            
            # Apply control panel position
            if cp_position and hasattr(self, 'control_panel'):
                self.control_panel.setGeometry(
                    cp_position.get('x', 50),
                    cp_position.get('y', 50),
                    cp_position.get('width', 1600),
                    cp_position.get('height', 900)
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
            if hasattr(self, 'control_panel'):
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

    def apply_gpu_selection(self, device_index, backend_type=None):
        """Apply GPU selection changes to the mixer window"""
        try:
            logging.info(f"🎮 Applying GPU selection: index={device_index}, backend={backend_type}")
            
            if self.mixer_window:
                self.mixer_window.apply_gpu_selection(device_index, backend_type)
                
            # Save the settings
            if backend_type:
                self.settings_manager.set_setting("visual_settings.backend", backend_type)
            self.settings_manager.set_setting("visual_settings.gpu_index", device_index)
            
            logging.info("✅ GPU selection applied")
            
        except Exception as e:
            logging.error(f"Error applying GPU selection: {e}")

    def cleanup(self):
        """Cleanup application resources"""
        try:
            logging.info("🧹 Cleaning up application resources...")
            
            # Save window positions
            self.save_window_positions()
            
            # Close MIDI connection
            if hasattr(self, 'midi_engine') and self.midi_engine:
                self.midi_engine.close_input_port()
                logging.debug("✅ MIDI connection closed")
            
            # Stop audio analysis
            if hasattr(self, 'audio_analyzer') and self.audio_analyzer:
                self.audio_analyzer.stop_analysis()
                logging.debug("✅ Audio analysis stopped")
            
            # Cleanup mixer window OpenGL resources
            if hasattr(self, 'mixer_window') and self.mixer_window:
                self.mixer_window.cleanup()
                logging.debug("✅ OpenGL resources cleaned")
            
            # Cleanup control panel
            if hasattr(self, 'control_panel') and self.control_panel:
                self.control_panel.cleanup()
                logging.debug("✅ Control panel cleaned")
            
            logging.info("✅ Cleanup completed")
            
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

    def run(self):
        """Run the application"""
        try:
            logging.info("🚀 Starting Audio Visualizer Pro...")
            
            # Show windows
            self.show_windows()
            
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