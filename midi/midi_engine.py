import mido
import mido.backends.rtmidi
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt
import time
import logging
import queue
import copy

class MidiEngine(QObject):
    # Existing signals
    midi_message_received = pyqtSignal(object)  # Original signal for raw MIDI messages
    control_changed = pyqtSignal(str, int)
    note_on_received = pyqtSignal(int, int)
    note_off_received = pyqtSignal(int)
    preset_loaded_on_deck = pyqtSignal(str, str)

    # New signals for the mapping system
    midi_message_received_for_learning = pyqtSignal(str)  # New signal for MIDI learning (message key as string)
    bpm_changed = pyqtSignal(float)
    device_connected = pyqtSignal(str)
    device_disconnected = pyqtSignal(str)
    # Signal used to execute mapped actions on the Qt main thread
    mapped_action_triggered = pyqtSignal(str, int)

    def __init__(self, settings_manager, visualizer_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.visualizer_manager = visualizer_manager
        
        # Load mappings from settings manager
        try:
            # Use deepcopy to avoid accidental shared references
            self.midi_mappings = copy.deepcopy(self.settings_manager.load_midi_mappings())
            if not isinstance(self.midi_mappings, dict):
                self.midi_mappings = {}
            logging.info(
                f"🎹 Loaded {len(self.midi_mappings)} MIDI mappings from settings"
            )

        except Exception as e:
            logging.warning(f"Could not load MIDI mappings: {e}")
            self.midi_mappings = {}

        # Precompute lookup table {midi_key: (action_id, mapping)}
        self._build_midi_lookup()
        
        self.input_port = None
        self.running = False
        self._last_bpm_time = 0
        self._beat_intervals = []

        # References to application components (set later)
        self.mixer_window = None
        self.control_panel = None

        # Crossfade animation variables
        self.crossfade_timer = None
        self.crossfade_start_value = 0.5
        self.crossfade_target_value = 0.5
        self.crossfade_duration = 1000
        self.crossfade_start_time = 0

        # Queue to decouple MIDI reception from processing
        self._message_queue = queue.Queue()

        logging.info("MidiEngine initialized")

        # Route mapped_action_triggered through Qt's event loop to ensure thread safety
        self.mapped_action_triggered.connect(
            self.execute_mapped_action_safe, Qt.ConnectionType.QueuedConnection
        )

        # Timer to process queued MIDI messages on the Qt thread
        self._queue_timer = QTimer()
        self._queue_timer.setInterval(1)
        self._queue_timer.timeout.connect(self._process_midi_queue)
        self._queue_timer.start()

        # Setup default mappings if none exist (delayed to ensure everything is loaded)
        QTimer.singleShot(1000, self.setup_default_mappings)

    def _build_midi_lookup(self):
        """Build lookup table for MIDI message keys"""
        self.midi_lookup = {}
        try:
            for action_id, mapping_data in self.midi_mappings.items():
                if not isinstance(mapping_data, dict):
                    continue
                midi_key = mapping_data.get("midi")
                if midi_key:
                    self.midi_lookup[midi_key] = (action_id, mapping_data)
            logging.debug(
                f"🎹 MIDI lookup table built with {len(self.midi_lookup)} entries"
            )
        except Exception as e:
            logging.error(f"❌ Error building MIDI lookup: {e}")
            self.midi_lookup = {}

    def set_application_references(self, mixer_window=None, control_panel=None):
        """Set references to application components for executing actions"""
        self.mixer_window = mixer_window
        self.control_panel = control_panel
        logging.info(f"✅ Application references set in MidiEngine:")
        logging.info(f"   mixer_window: {type(self.mixer_window).__name__ if self.mixer_window else 'None'}")
        logging.info(f"   control_panel: {type(self.control_panel).__name__ if self.control_panel else 'None'}")

    def list_input_ports(self):
        """List available MIDI input ports"""
        try:
            return mido.get_input_names()
        except Exception as e:
            logging.error(f"Error listing MIDI input ports: {e}")
            return []

    def open_input_port(self, port_name):
        """Open a MIDI input port - ENHANCED DEBUG"""
        try:
            logging.info(f"🔌 ATTEMPTING to open MIDI port: {port_name}")
            
            # Close existing port if open
            self.close_input_port()
            
            # List available ports for debugging
            available_ports = mido.get_input_names()
            logging.info(f"📋 Available MIDI ports: {available_ports}")
            
            if port_name not in available_ports:
                logging.error(f"❌ Port '{port_name}' not in available ports!")
                return False
            
            # Open the port with callback
            logging.info(f"🔌 Opening port with callback: {self._enqueue_midi_message}")
            self.input_port = mido.open_input(port_name, callback=self._enqueue_midi_message)
            self.running = True
            
            # Save the last used device
            if self.settings_manager:
                self.settings_manager.set_setting("last_midi_device", port_name)
            
            # Test the connection
            logging.info(f"✅ MIDI port opened successfully: {port_name}")
            logging.info(f"   Port object: {self.input_port}")
            logging.info(f"   Running: {self.running}")
            logging.info("🎵 READY TO RECEIVE MIDI MESSAGES!")
            
            self.device_connected.emit(port_name)
            print(f"Puerto MIDI de entrada abierto: {port_name}")
            return True
            
        except (IOError, ValueError) as e:
            logging.error(f"❌ FAILED to open MIDI port: {e}")
            print(f"Error al abrir el puerto MIDI: {e}")
            self.input_port = None
            self.running = False
            return False
        except Exception as e:
            logging.error(f"❌ UNEXPECTED error opening MIDI port: {e}")
            import traceback
            traceback.print_exc()
            self.input_port = None
            self.running = False
            return False

    def close_input_port(self):
        """Close the current MIDI input port"""
        if self.input_port:
            try:
                old_port_name = str(self.input_port)
                self.input_port.close()
                self.input_port = None
                self.running = False
                self.device_disconnected.emit(old_port_name)
                logging.info("🔌 Puerto MIDI de entrada cerrado.")
            except Exception as e:
                logging.error(f"Error closing MIDI port: {e}")

    def is_port_open(self):
        """Check if a MIDI input port is currently open"""
        return self.input_port is not None and self.running

    def is_input_port_open(self):
        """Alternative method name for checking port status"""
        return self.is_port_open()

    def is_connected(self):
        """Check if MIDI is connected (alternative method name)"""
        return self.is_port_open()

    def get_connected_device_name(self):
        """Get the name of the currently connected MIDI device"""
        if self.input_port:
            return str(self.input_port)
        return None

    def _enqueue_midi_message(self, msg):
        """Callback used by mido to enqueue incoming messages"""
        try:
            self._message_queue.put(msg)
        except Exception as e:
            logging.error(f"❌ Error enqueuing MIDI message: {e}")

    def _process_midi_queue(self):
        """Process all pending MIDI messages from the queue"""
        try:
            while not self._message_queue.empty():
                msg = self._message_queue.get_nowait()
                self.handle_midi_message(msg)
        except Exception as e:
            logging.error(f"❌ Error processing MIDI queue: {e}")

    def handle_midi_message(self, msg):
        """Process a MIDI message from the internal queue"""
        try:
            # CRITICAL: Log EVERY incoming message for debugging
            logging.info(f"🎼 RAW MIDI RECEIVED: {msg}")
            logging.info(f"   Type: {msg.type}")
            logging.info(f"   Channel: {getattr(msg, 'channel', 'N/A')}")
            logging.info(f"   Note: {getattr(msg, 'note', 'N/A')}")
            logging.info(f"   Velocity: {getattr(msg, 'velocity', 'N/A')}")
            logging.info(f"   Control: {getattr(msg, 'control', 'N/A')}")
            logging.info(f"   Value: {getattr(msg, 'value', 'N/A')}")

            # Create message key for the new mapping system FIRST
            message_key = self.create_message_key(msg)
            logging.info(f"🔑 Created message key: {message_key}")

            # Emit signals for monitoring; Qt will queue them to the main thread if needed
            self.midi_message_received.emit(msg)
            self.midi_message_received_for_learning.emit(message_key)

            # Process different message types
            if msg.type == 'note_on':
                logging.info(f"🎵 Processing note_on: note={msg.note}, velocity={msg.velocity}")

                if msg.velocity > 0:
                    # Emit signals for downstream processing
                    self.note_on_received.emit(msg.note, msg.velocity)
                    self.process_bpm_from_note()

                    # Execute mapped actions via Qt signal to ensure thread safety
                    logging.info(f"🚀 Executing mapped action for {message_key}")
                    self.mapped_action_triggered.emit(message_key, msg.velocity)

                else:
                    # Velocity 0 is actually note_off
                    logging.info("🎵 Note_on with velocity 0 treated as note_off")
                    self.note_off_received.emit(msg.note)

            elif msg.type == 'note_off':
                logging.info(f"🎵 Processing note_off: note={msg.note}")
                self.note_off_received.emit(msg.note)
                # Don't execute actions on note_off for now

            elif msg.type == 'control_change':
                logging.info(f"🎛️ Processing control_change: cc={msg.control}, value={msg.value}")
                self.control_changed.emit(f"cc_{msg.control}", msg.value)
                self.mapped_action_triggered.emit(message_key, msg.value)

            elif msg.type == 'program_change':
                logging.info(f"🎼 Processing program_change: program={msg.program}")
                self.mapped_action_triggered.emit(message_key, msg.program)

            else:
                logging.info(f"❓ Unhandled MIDI message type: {msg.type}")

        except Exception as e:
            logging.error(f"❌ CRITICAL ERROR handling MIDI message: {e}")
            import traceback
            traceback.print_exc()
        finally:
            logging.debug("🔃 MIDI processing completed")

    def execute_mapped_action_safe(self, message_key, value):
        """Thread-safe wrapper for executing mapped actions"""
        try:
            logging.info(f"🎯 SAFE EXECUTION: Searching for mapping for key: {message_key}")
            self.execute_mapped_action(message_key, value)
        except Exception as e:
            logging.error(f"❌ Error in execute_mapped_action_safe: {e}")
            import traceback
            traceback.print_exc()

    def create_message_key(self, msg):
        """Create a unique key for a MIDI message - IMPROVED to accept ALL channels"""
        try:
            # CRITICAL: Log the key creation process
            logging.debug(f"🔑 Creating message key for: {msg}")
            
            if msg.type == 'note_on':
                # Accept ANY channel - normalize to ch0 for mapping lookup
                key = f"note_on_ch0_note{msg.note}"
                logging.debug(f"🔑 Note_on key: {key} (original channel: {msg.channel})")
                return key
                
            elif msg.type == 'note_off':
                key = f"note_off_ch0_note{msg.note}"
                logging.debug(f"🔑 Note_off key: {key}")
                return key
                
            elif msg.type == 'control_change':
                key = f"cc_ch0_cc{msg.control}"
                logging.debug(f"🔑 CC key: {key}")
                return key
                
            elif msg.type == 'program_change':
                key = f"pc_ch0_prog{msg.program}"
                logging.debug(f"🔑 PC key: {key}")
                return key
                
            elif msg.type == 'pitchwheel':
                key = f"pitchwheel_ch0"
                logging.debug(f"🔑 Pitchwheel key: {key}")
                return key
                
            else:
                key = f"{msg.type}_ch0"
                logging.debug(f"🔑 Generic key: {key}")
                return key
                
        except Exception as e:
            logging.error(f"❌ Error creating message key: {e}")
            fallback_key = f"unknown_message_{time.time()}"
            logging.debug(f"🔑 Fallback key: {fallback_key}")
            return fallback_key

    def process_bpm_from_note(self):
        """Process BPM calculation from note timing"""
        try:
            current_time = time.time()
            
            if self._last_bpm_time > 0:
                interval = current_time - self._last_bpm_time
                self._beat_intervals.append(interval)
                
                # Keep only last 8 beats for averaging
                if len(self._beat_intervals) > 8:
                    self._beat_intervals.pop(0)
                
                # Calculate BPM if we have enough data
                if len(self._beat_intervals) >= 2:
                    avg_interval = sum(self._beat_intervals) / len(self._beat_intervals)
                    bpm = 60.0 / avg_interval
                    
                    # Only emit if BPM is reasonable (40-200 BPM)
                    if 40 <= bpm <= 200:
                        self.bpm_changed.emit(bpm)
            
            self._last_bpm_time = current_time
            
        except Exception as e:
            logging.error(f"Error processing BPM: {e}")

    def execute_mapped_action(self, message_key, value):
        """Execute action mapped to a MIDI message - ENHANCED DEBUG"""
        try:
            logging.info(f"🔍 SEARCHING for mapping: {message_key}")
            logging.info(f"📋 Available mappings: {len(self.midi_lookup)}")

            # Direct lookup for efficiency and correctness
            mapped_action = self.midi_lookup.get(message_key)

            if not mapped_action:
                # Enhanced debugging for no mapping found
                logging.warning(f"❌ NO MAPPING FOUND for: {message_key}")
                logging.info("📋 Available MIDI keys:")
                for midi_key in sorted(self.midi_lookup.keys()):
                    logging.info(f"   {midi_key}")
                return  # No action mapped to this message

            action_id, mapping_data = mapped_action
            action_type = mapping_data.get('type')
            params = mapping_data.get('params', {})
            
            logging.info(f"🎹 EXECUTING MIDI action: {action_id}")
            logging.info(f"   Type: {action_type}")
            logging.info(f"   Message: {message_key}")
            logging.info(f"   Value: {value}")
            logging.info(f"   Params: {params}")
            
            # Execute different types of actions
            if action_type == "load_preset":
                logging.info("🎮 Executing load_preset action...")
                self.execute_load_preset_action(params)
            elif action_type == "crossfade_action":
                logging.info("🎛️ Executing crossfade action...")
                self.execute_crossfade_action(params)
            elif action_type == "animate_crossfade":
                logging.info("🎬 Executing animate_crossfade action...")
                self.execute_animate_crossfade_action(params)
            elif action_type == "control_parameter":
                logging.info("🎚️ Executing control_parameter action...")
                self.execute_control_parameter_action(params, value)
            else:
                logging.warning(f"⚠️ Unknown action type: {action_type}")
                
        except Exception as e:
            logging.error(f"❌ CRITICAL ERROR executing mapped action for {message_key}: {e}")
            import traceback
            traceback.print_exc()

    def execute_load_preset_action(self, params):
        """Execute load preset action - THREAD SAFE VERSION"""
        try:
            deck_id = params.get('deck_id')
            preset_name = params.get('preset_name')
            custom_values = params.get('custom_values', '')
            
            logging.info(f"🎮 EXECUTING load preset: deck={deck_id}, preset={preset_name}, values={custom_values}")
            
            # Check if we have mixer window reference
            if not self.mixer_window:
                logging.error("❌ Mixer window reference not available!")
                logging.error("   Make sure set_application_references() was called")
                return
            
            if deck_id and preset_name:
                # CRITICAL: Always use the thread-safe method directly
                logging.info(f"🔄 Calling safe_set_deck_visualizer({deck_id}, {preset_name})")

                # This method already uses signals internally for thread safety
                self.mixer_window.safe_set_deck_visualizer(deck_id, preset_name)

                # Parse and apply custom values if provided
                if custom_values:
                    self.apply_custom_values(deck_id, custom_values)

                logging.info(f"✅ Triggered preset load '{preset_name}' on deck {deck_id}")

                # Emit signal for UI update
                self.preset_loaded_on_deck.emit(deck_id, preset_name)

            # Handle special case of clearing deck (preset_name = None)
            elif deck_id and preset_name is None:
                logging.info(f"🚫 Clearing deck {deck_id}")

                # Use thread-safe method
                self.mixer_window.safe_set_deck_visualizer(deck_id, None)

                logging.info(f"✅ Deck {deck_id} cleared")

                # Signal emission for cleared deck
                self.preset_loaded_on_deck.emit(deck_id, "-- No preset selected --")
                
        except Exception as e:
            logging.error(f"❌ Error executing load preset action: {e}")
            import traceback
            traceback.print_exc()

    def apply_custom_values(self, deck_id, custom_values):
        """Apply custom parameter values to a deck"""
        try:
            # Parse the custom values string (format: "param1:value1;param2:value2")
            if not custom_values:
                return
                
            logging.info(f"🎚️ Applying custom values to deck {deck_id}: {custom_values}")
            
            pairs = custom_values.split(';')
            for pair in pairs:
                if ':' in pair:
                    param_name, param_value = pair.split(':', 1)
                    param_name = param_name.strip()
                    param_value = param_value.strip()
                    
                    # Try to convert to appropriate type
                    try:
                        # Try integer first
                        if param_value.isdigit() or (param_value.startswith('-') and param_value[1:].isdigit()):
                            param_value = int(param_value)
                        # Try float
                        elif '.' in param_value:
                            param_value = float(param_value)
                    except ValueError:
                        # Keep as string if conversion fails
                        pass
                    
                    # Apply the parameter using thread-safe method
                    if self.mixer_window and hasattr(self.mixer_window, 'safe_update_deck_control'):
                        self.mixer_window.safe_update_deck_control(deck_id, param_name, param_value)
                        logging.info(f"✅ Applied custom value: {deck_id}.{param_name} = {param_value}")
                        
        except Exception as e:
            logging.error(f"❌ Error applying custom values: {e}")

    def execute_crossfade_action(self, params):
        """Execute crossfade action - IMPROVED to use animation"""
        try:
            preset = params.get('preset', 'A to B')
            duration = params.get('duration', '')
            
            logging.info(f"🎛️ Executing crossfade: {preset} duration: {duration}")
            
            # Parse duration string to milliseconds
            duration_ms = 1000  # Default 1 second
            if duration:
                if 'ms' in duration:
                    duration_ms = int(duration.replace('ms', ''))
                elif 's' in duration:
                    duration_ms = int(float(duration.replace('s', '')) * 1000)
            
            # Map preset to target value
            if preset == "Instant A":
                target_value = 0.0
                duration_ms = 50  # Almost instant
            elif preset == "Instant B":
                target_value = 1.0
                duration_ms = 50  # Almost instant
            elif preset == "Cut to Center":
                target_value = 0.5
                duration_ms = 50  # Almost instant
            elif preset == "A to B":
                target_value = 1.0  # Full B
            elif preset == "B to A":
                target_value = 0.0  # Full A
            else:
                target_value = 0.5  # Default center
            
            # Use the animated crossfade
            animation_params = {
                'target_value': target_value,
                'duration_ms': duration_ms,
                'curve': 'linear'
            }
            
            self.execute_animate_crossfade_action(animation_params)
            
        except Exception as e:
            logging.error(f"❌ Error executing crossfade action: {e}")

    def execute_animate_crossfade_action(self, params):
        """Execute animated crossfade action - FIXED IMPLEMENTATION"""
        try:
            target_value = params.get('target_value', 0.5)
            duration_ms = params.get('duration_ms', 1000)
            curve = params.get('curve', 'linear')
            
            if not self.mixer_window:
                logging.error("❌ Mixer window not available for crossfade animation")
                return
            
            # Get current mix value
            current_value = self.mixer_window.get_mix_value() if hasattr(self.mixer_window, 'get_mix_value') else 0.5
            
            logging.info(f"🎛️ Animating crossfade from {current_value:.2f} to {target_value:.2f} over {duration_ms}ms")
            
            # Store animation parameters
            self.crossfade_start_value = current_value
            self.crossfade_target_value = target_value
            self.crossfade_duration = duration_ms
            self.crossfade_start_time = time.time() * 1000  # Convert to milliseconds
            
            # Stop any existing animation
            if self.crossfade_timer:
                self.crossfade_timer.stop()
                self.crossfade_timer = None
            
            # Start animation timer (60 FPS = ~16ms intervals)
            self.crossfade_timer = QTimer()
            self.crossfade_timer.timeout.connect(self.update_crossfade_animation)
            self.crossfade_timer.start(16)  # 60 FPS
            
        except Exception as e:
            logging.error(f"❌ Error executing animate crossfade action: {e}")

    def update_crossfade_animation(self):
        """Update crossfade animation frame"""
        try:
            current_time = time.time() * 1000
            elapsed = current_time - self.crossfade_start_time
            progress = min(elapsed / self.crossfade_duration, 1.0)
            
            # Calculate current value (linear interpolation for now)
            current_value = self.crossfade_start_value + (self.crossfade_target_value - self.crossfade_start_value) * progress
            
            # Update mixer
            mixer_value = int(current_value * 100)
            if hasattr(self.mixer_window, 'safe_set_mix_value'):
                self.mixer_window.safe_set_mix_value(mixer_value)
            
            # Check if animation is complete
            if progress >= 1.0:
                if self.crossfade_timer:
                    self.crossfade_timer.stop()
                    self.crossfade_timer = None
                logging.info(f"✅ Crossfade animation completed at {self.crossfade_target_value:.2f}")
            
        except Exception as e:
            logging.error(f"❌ Error updating crossfade animation: {e}")
            if self.crossfade_timer:
                self.crossfade_timer.stop()
                self.crossfade_timer = None

    def execute_control_parameter_action(self, params, value):
        """Execute control parameter action"""
        try:
            deck_id = params.get('deck_id')
            parameter_name = params.get('parameter_name')
            
            if deck_id and parameter_name and self.mixer_window:
                # Scale MIDI value (0-127) to parameter range if needed
                scaled_value = value
                if 'min_value' in params and 'max_value' in params:
                    min_val = params['min_value']
                    max_val = params['max_value']
                    scaled_value = min_val + (value / 127.0) * (max_val - min_val)
                
                if hasattr(self.mixer_window, 'safe_update_deck_control'):
                    self.mixer_window.safe_update_deck_control(deck_id, parameter_name, scaled_value)
                    logging.info(f"✅ Updated {deck_id}.{parameter_name} to {scaled_value}")
            
        except Exception as e:
            logging.error(f"❌ Error executing control parameter action: {e}")

    def create_default_midi_mappings(self):
        """Create all default MIDI mappings for the drum rack setup - CORRECTED NAMES"""
        mappings = {}
        
        # DECK A PRESETS (36-45) - NOMBRES EXACTOS del visualizer_manager
        deck_a_presets = [
            "Simple Test", "Wire Terrain", "Abstract Lines", "Geometric Particles", 
            "Evolutive Particles", "Abstract Shapes", "Mobius Band", "Building Madness",
            "Cosmic Flow", "Fluid Particles"
        ]
        
        for i, preset_name in enumerate(deck_a_presets):
            note = 36 + i
            mappings[f"deck_a_preset_{i}"] = {
                "type": "load_preset",
                "params": {
                    "deck_id": "A",
                    "preset_name": preset_name,
                    "custom_values": ""
                },
                "midi": f"note_on_ch0_note{note}"
            }
        
        # DECK A CLEAR (46)
        mappings["deck_a_clear"] = {
            "type": "load_preset",
            "params": {
                "deck_id": "A",
                "preset_name": None,
                "custom_values": ""
            },
            "midi": "note_on_ch0_note46"
        }
        
        # MIX ACTIONS (48-53)
        mix_actions = [
            {"preset": "A to B", "duration": "10s"},
            {"preset": "B to A", "duration": "10s"},
            {"preset": "A to B", "duration": "5s"},
            {"preset": "B to A", "duration": "5s"},
            {"preset": "A to B", "duration": "500ms"},
            {"preset": "B to A", "duration": "500ms"}
        ]
        
        for i, action in enumerate(mix_actions):
            note = 48 + i
            mappings[f"mix_action_{i}"] = {
                "type": "crossfade_action",
                "params": {
                    "preset": action["preset"],
                    "duration": action["duration"],
                    "target": "Visual Mix"
                },
                "midi": f"note_on_ch0_note{note}"
            }
        
        # DECK B PRESETS (54-63) - NOMBRES EXACTOS del visualizer_manager
        deck_b_presets = [
            "Simple Test", "Wire Terrain", "Abstract Lines", "Geometric Particles", 
            "Evolutive Particles", "Abstract Shapes", "Mobius Band", "Building Madness",
            "Cosmic Flow", "Fluid Particles"
        ]
        
        for i, preset_name in enumerate(deck_b_presets):
            note = 54 + i
            mappings[f"deck_b_preset_{i}"] = {
                "type": "load_preset",
                "params": {
                    "deck_id": "B",
                    "preset_name": preset_name,
                    "custom_values": ""
                },
                "midi": f"note_on_ch0_note{note}"
            }
        
        # DECK B CLEAR (64)
        mappings["deck_b_clear"] = {
            "type": "load_preset",
            "params": {
                "deck_id": "B",
                "preset_name": None,
                "custom_values": ""
            },
            "midi": "note_on_ch0_note64"
        }
        
        logging.info(f"🎹 Created {len(mappings)} default MIDI mappings with corrected preset names")
        return mappings

    def setup_default_mappings(self):
        """Setup default MIDI mappings - call this after initialization"""
        try:
            # Only create default mappings if none exist
            if not self.midi_mappings or len(self.midi_mappings) == 0:
                logging.info("🎹 No existing MIDI mappings found, creating defaults...")
                default_mappings = self.create_default_midi_mappings()
                self.set_midi_mappings(default_mappings)
                logging.info("✅ Default MIDI mappings created and saved")
            else:
                logging.info(f"🎹 Using existing MIDI mappings: {len(self.midi_mappings)} mappings loaded")
                
            # Debug: Print all current mappings
            self.print_current_mappings()
                
        except Exception as e:
            logging.error(f"❌ Error setting up default mappings: {e}")

    def print_current_mappings(self):
        """Print current MIDI mappings for debugging"""
        try:
            logging.info("🎹 CURRENT MIDI MAPPINGS:")
            logging.info("=" * 60)
            
            # Group by type
            deck_a_mappings = []
            deck_b_mappings = []
            mix_mappings = []
            
            for action_id, mapping_data in self.midi_mappings.items():
                midi_key = mapping_data.get('midi', 'no_midi')
                action_type = mapping_data.get('type', 'unknown')
                params = mapping_data.get('params', {})
                
                if 'deck_a' in action_id or params.get('deck_id') == 'A':
                    deck_a_mappings.append((action_id, midi_key, params))
                elif 'deck_b' in action_id or params.get('deck_id') == 'B':
                    deck_b_mappings.append((action_id, midi_key, params))
                elif 'mix' in action_id or action_type == 'crossfade_action':
                    mix_mappings.append((action_id, midi_key, params))
            
            # Print Deck A
            logging.info("🔴 DECK A MAPPINGS:")
            for action_id, midi_key, params in sorted(deck_a_mappings, key=lambda x: x[1]):
                preset = params.get('preset_name', 'Clear') if params.get('preset_name') else 'Clear'
                note_num = midi_key.split('note')[-1] if 'note' in midi_key else '?'
                logging.info(f"  Note {note_num:2s}: {preset}")
            
            # Print Mix
            logging.info("🟡 MIX MAPPINGS:")
            for action_id, midi_key, params in sorted(mix_mappings, key=lambda x: x[1]):
                preset = params.get('preset', 'Unknown')
                duration = params.get('duration', 'instant')
                note_num = midi_key.split('note')[-1] if 'note' in midi_key else '?'
                logging.info(f"  Note {note_num:2s}: {preset} ({duration})")
            
            # Print Deck B
            logging.info("🟢 DECK B MAPPINGS:")
            for action_id, midi_key, params in sorted(deck_b_mappings, key=lambda x: x[1]):
                preset = params.get('preset_name', 'Clear') if params.get('preset_name') else 'Clear'
                note_num = midi_key.split('note')[-1] if 'note' in midi_key else '?'
                logging.info(f"  Note {note_num:2s}: {preset}")
                
            logging.info("=" * 60)
            
        except Exception as e:
            logging.error(f"❌ Error printing mappings: {e}")

    def test_midi_mapping(self, note_number):
        """Test a specific MIDI mapping by note number"""
        try:
            test_key = f"note_on_ch0_note{note_number}"
            logging.info(f"🧪 TESTING MIDI mapping for note {note_number} (key: {test_key})")
            
            # Find the mapping
            found_mapping = None
            for action_id, mapping_data in self.midi_mappings.items():
                if mapping_data.get('midi') == test_key:
                    found_mapping = (action_id, mapping_data)
                    break
            
            if found_mapping:
                action_id, mapping_data = found_mapping
                action_type = mapping_data.get('type')
                params = mapping_data.get('params', {})
                
                logging.info(f"✅ Found mapping: {action_id}")
                logging.info(f"  Type: {action_type}")
                logging.info(f"  Params: {params}")
                
                # Simulate execution
                logging.info(f"🚀 SIMULATING execution...")
                self.execute_mapped_action(test_key, 127)  # Full velocity
                
            else:
                logging.warning(f"❌ No mapping found for note {note_number}")
                logging.info("Available mappings:")
                for action_id, mapping_data in self.midi_mappings.items():
                    midi_key = mapping_data.get('midi', 'no_midi')
                    note_from_key = midi_key.split('note')[-1] if 'note' in midi_key else '?'
                    logging.info(f"  {action_id}: Note {note_from_key}")
                    
        except Exception as e:
            logging.error(f"❌ Error testing MIDI mapping: {e}")

    def set_midi_mappings(self, mappings):
        """Set MIDI mappings"""
        try:
            self.midi_mappings = copy.deepcopy(mappings)
            self._build_midi_lookup()
            if self.settings_manager:
                self.settings_manager.save_midi_mappings(self.midi_mappings)
            logging.info(
                f"🎹 MIDI mappings updated and saved: {len(self.midi_mappings)} mappings"
            )
                
        except Exception as e:
            logging.error(f"❌ Error setting MIDI mappings: {e}")

    def get_midi_mappings(self):
        """Get current MIDI mappings"""
        return self.midi_mappings.copy()

    def add_midi_mapping(self, action_id, mapping_data):
        """Add a single MIDI mapping"""
        try:
            self.midi_mappings[action_id] = mapping_data
            self._build_midi_lookup()
            if self.settings_manager:
                self.settings_manager.save_midi_mappings(self.midi_mappings)
            logging.info(f"Added MIDI mapping: {action_id}")
        except Exception as e:
            logging.error(f"Error adding MIDI mapping: {e}")

    def remove_midi_mapping(self, action_id):
        """Remove a MIDI mapping"""
        try:
            if action_id in self.midi_mappings:
                del self.midi_mappings[action_id]
                self._build_midi_lookup()
                if self.settings_manager:
                    self.settings_manager.save_midi_mappings(self.midi_mappings)
                logging.info(f"Removed MIDI mapping: {action_id}")
        except Exception as e:
            logging.error(f"Error removing MIDI mapping: {e}")

    def clear_all_mappings(self):
        """Clear all MIDI mappings"""
        try:
            self.midi_mappings.clear()
            self._build_midi_lookup()
            if self.settings_manager:
                self.settings_manager.save_midi_mappings(self.midi_mappings)
            logging.info("All MIDI mappings cleared")
        except Exception as e:
            logging.error(f"Error clearing MIDI mappings: {e}")

    def simulate_midi_message(self, message_key):
        """Simulate a MIDI message for testing purposes"""
        try:
            self.midi_message_received.emit(message_key)
            logging.info(f"Simulated MIDI message: {message_key}")
        except Exception as e:
            logging.error(f"Error simulating MIDI message: {e}")

    def refresh_available_ports(self):
        """Refresh the list of available MIDI ports"""
        try:
            return self.list_input_ports()
        except Exception as e:
            logging.error(f"Error refreshing MIDI ports: {e}")
            return []

    def get_device_info(self):
        """Get information about the current MIDI device"""
        if self.input_port:
            return {
                'name': str(self.input_port),
                'connected': True,
                'type': 'MIDI Input'
            }
        return None

    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.close_input_port()
        except:
            pass