import mido
import mido.backends.rtmidi
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import time
import logging

class MidiEngine(QObject):
    # Existing signals
    midi_message_received = pyqtSignal(object)  # Original signal for raw MIDI messages
    control_changed = pyqtSignal(str, int)
    note_on_received = pyqtSignal(int, int)
    note_off_received = pyqtSignal(int)
    
    # New signals for the mapping system
    midi_message_received_for_learning = pyqtSignal(str)  # New signal for MIDI learning (message key as string)
    bpm_changed = pyqtSignal(float)
    device_connected = pyqtSignal(str)
    device_disconnected = pyqtSignal(str)

    def __init__(self, settings_manager, visualizer_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.visualizer_manager = visualizer_manager
        
        # Load mappings from settings manager
        try:
            self.midi_mappings = self.settings_manager.load_midi_mappings()
            if not isinstance(self.midi_mappings, dict):
                self.midi_mappings = {}
            logging.info(f"🎹 Loaded {len(self.midi_mappings)} MIDI mappings from settings")
            
            # Debug: Print loaded mappings
            for action_id, mapping_data in self.midi_mappings.items():
                midi_key = mapping_data.get('midi', 'no_midi')
                action_type = mapping_data.get('type', 'unknown')
                logging.debug(f"  📋 Loaded mapping: {midi_key} -> {action_type}")
                
        except Exception as e:
            logging.warning(f"Could not load MIDI mappings: {e}")
            self.midi_mappings = {}
        
        self.input_port = None
        self.input_thread = None
        self.running = False
        self._last_bpm_time = 0
        self._beat_intervals = []
        
        # References to application components (set later)
        self.mixer_window = None
        self.control_panel = None
        
        logging.info("MidiEngine initialized")

    def set_application_references(self, mixer_window=None, control_panel=None):
        """Set references to application components for executing actions"""
        self.mixer_window = mixer_window
        self.control_panel = control_panel
        logging.debug("Application references set in MidiEngine")

    def list_input_ports(self):
        """List available MIDI input ports"""
        try:
            return mido.get_input_names()
        except Exception as e:
            logging.error(f"Error listing MIDI input ports: {e}")
            return []

    def open_input_port(self, port_name):
        """Open a MIDI input port"""
        try:
            # Close existing port if open
            self.close_input_port()
            
            self.input_port = mido.open_input(port_name, callback=self.handle_midi_message)
            self.running = True
            
            # Save the last used device
            if self.settings_manager:
                self.settings_manager.set_setting("last_midi_device", port_name)
            
            self.device_connected.emit(port_name)
            logging.info(f"🔌 Puerto MIDI de entrada abierto: {port_name}")
            print(f"Puerto MIDI de entrada abierto: {port_name}")
            return True
            
        except (IOError, ValueError) as e:
            logging.error(f"❌ Error al abrir el puerto MIDI: {e}")
            print(f"Error al abrir el puerto MIDI: {e}")
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
                print("Puerto MIDI de entrada cerrado.")
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

    def handle_midi_message(self, msg):
        """Handle incoming MIDI messages"""
        try:
            # Emit original signal for backward compatibility
            self.midi_message_received.emit(msg)
            
            # Create message key for the new mapping system
            message_key = self.create_message_key(msg)
            
            # Emit new signal for MIDI learning
            self.midi_message_received_for_learning.emit(message_key)
            
            # Debug: Log all MIDI messages with current mappings
            logging.debug(f"🎼 MIDI Message: {msg.type} -> Key: {message_key}")
            
            # Process the message for existing functionality
            if msg.type == 'control_change':
                control_id = f"cc_{msg.control}"
                if control_id in self.midi_mappings:
                    mapping_info = self.midi_mappings[control_id]
                    deck = mapping_info['deck']
                    parameter = mapping_info['parameter']
                    if self.visualizer_manager:
                        self.visualizer_manager.update_visualizer_parameter(deck, parameter, msg.value)
                    self.control_changed.emit(f"{deck}.{parameter}", msg.value)
                
                # Check new-style mappings
                self.execute_mapped_action(message_key, msg.value)
                
            elif msg.type == 'note_on':
                # Only process note_on with velocity > 0
                if msg.velocity > 0:
                    self.note_on_received.emit(msg.note, msg.velocity)
                    self.process_bpm_from_note()
                    # Execute mapped actions
                    self.execute_mapped_action(message_key, msg.velocity)
                else:
                    # Velocity 0 is actually note_off
                    note_off_key = self.create_note_off_key(msg)
                    self.note_off_received.emit(msg.note)
                    self.execute_mapped_action(note_off_key, 0)
                
            elif msg.type == 'note_off':
                self.note_off_received.emit(msg.note)
                self.execute_mapped_action(message_key, 0)
                
            elif msg.type == 'program_change':
                self.execute_mapped_action(message_key, msg.program)
                
        except Exception as e:
            logging.error(f"❌ Error handling MIDI message: {e}")

    def create_message_key(self, msg):
        """Create a unique key for a MIDI message"""
        try:
            if msg.type == 'note_on':
                return f"note_on_ch{msg.channel}_note{msg.note}"
            elif msg.type == 'note_off':
                return f"note_off_ch{msg.channel}_note{msg.note}"
            elif msg.type == 'control_change':
                return f"cc_ch{msg.channel}_cc{msg.control}"
            elif msg.type == 'program_change':
                return f"pc_ch{msg.channel}_prog{msg.program}"
            elif msg.type == 'pitchwheel':
                return f"pitchwheel_ch{msg.channel}"
            else:
                return f"{msg.type}_ch{msg.channel}"
        except Exception as e:
            logging.error(f"Error creating message key: {e}")
            return f"unknown_message_{time.time()}"

    def create_note_off_key(self, msg):
        """Create note_off key from note_on with velocity 0"""
        return f"note_off_ch{msg.channel}_note{msg.note}"

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
        """Execute action mapped to a MIDI message"""
        try:
            # Find action mapped to this MIDI message
            mapped_action = None
            for action_id, mapping_data in self.midi_mappings.items():
                if isinstance(mapping_data, dict) and mapping_data.get('midi') == message_key:
                    mapped_action = (action_id, mapping_data)
                    break
            
            if not mapped_action:
                # Debug: Log that no mapping was found
                logging.debug(f"🔍 No mapping found for: {message_key}")
                return  # No action mapped to this message
            
            action_id, mapping_data = mapped_action
            action_type = mapping_data.get('type')
            params = mapping_data.get('params', {})
            
            logging.info(f"🎹 EXECUTING MIDI action: {action_id} (type: {action_type}) for message: {message_key} with value: {value}")
            
            # Execute different types of actions
            if action_type == "load_preset":
                self.execute_load_preset_action(params)
            elif action_type == "crossfade_action":
                self.execute_crossfade_action(params)
            elif action_type == "animate_crossfade":
                self.execute_animate_crossfade_action(params)
            elif action_type == "control_parameter":
                self.execute_control_parameter_action(params, value)
            else:
                logging.warning(f"⚠️ Unknown action type: {action_type}")
                
        except Exception as e:
            logging.error(f"❌ Error executing mapped action for {message_key}: {e}")

    def execute_load_preset_action(self, params):
        """Execute load preset action"""
        try:
            deck_id = params.get('deck_id')
            preset_name = params.get('preset_name')
            custom_values = params.get('custom_values', '')
            
            logging.info(f"🎮 EXECUTING load preset: deck={deck_id}, preset={preset_name}, values={custom_values}")
            
            if deck_id and preset_name:
                if self.mixer_window and hasattr(self.mixer_window, 'safe_set_deck_visualizer'):
                    # Use the thread-safe method
                    logging.info(f"🔄 Calling safe_set_deck_visualizer({deck_id}, {preset_name})")
                    self.mixer_window.safe_set_deck_visualizer(deck_id, preset_name)
                    
                    # Parse and apply custom values if provided
                    if custom_values:
                        # Small delay to ensure visualizer is set first
                        QTimer.singleShot(300, lambda: self.apply_custom_values(deck_id, custom_values))
                    
                    logging.info(f"✅ Triggered preset load '{preset_name}' on deck {deck_id}")
                elif self.mixer_window:
                    # Fallback to direct method
                    logging.info(f"🔄 Calling direct set_deck_visualizer({deck_id}, {preset_name})")
                    self.mixer_window.set_deck_visualizer(deck_id, preset_name)
                    
                    if custom_values:
                        QTimer.singleShot(300, lambda: self.apply_custom_values(deck_id, custom_values))
                        
                    logging.info(f"✅ Direct preset load '{preset_name}' on deck {deck_id}")
                else:
                    logging.error("❌ Mixer window not available for load preset action")
                    logging.error(f"❌ mixer_window reference: {self.mixer_window}")
                
        except Exception as e:
            logging.error(f"❌ Error executing load preset action: {e}")

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
                    if self.mixer_window:
                        if hasattr(self.mixer_window, 'safe_update_deck_control'):
                            self.mixer_window.safe_update_deck_control(deck_id, param_name, param_value)
                        else:
                            self.mixer_window.update_deck_control(deck_id, param_name, param_value)
                        logging.info(f"✅ Applied custom value: {deck_id}.{param_name} = {param_value}")
                        
        except Exception as e:
            logging.error(f"❌ Error applying custom values: {e}")

    def execute_crossfade_action(self, params):
        """Execute crossfade action"""
        try:
            preset = params.get('preset', 'A to B')
            duration = params.get('duration', '')
            
            logging.info(f"🎛️ Executing crossfade action: {preset}, duration: {duration}")
            
            if self.mixer_window:
                # Map preset to mix value
                if preset == "Instant A":
                    mix_value = 0
                elif preset == "Instant B":
                    mix_value = 100
                elif preset == "Cut to Center":
                    mix_value = 50
                elif preset == "A to B":
                    mix_value = 100  # Full B
                elif preset == "B to A":
                    mix_value = 0    # Full A
                else:
                    mix_value = 50   # Default center
                
                # Use the thread-safe method
                if hasattr(self.mixer_window, 'safe_set_mix_value'):
                    self.mixer_window.safe_set_mix_value(mix_value)
                else:
                    self.mixer_window.set_mix_value(mix_value)
                logging.info(f"✅ Set crossfade to: {mix_value}% ({preset})")
            else:
                logging.warning("❌ Mixer window not available for crossfade action")
            
        except Exception as e:
            logging.error(f"❌ Error executing crossfade action: {e}")

    def execute_animate_crossfade_action(self, params):
        """Execute animated crossfade action"""
        try:
            target_value = params.get('target_value', 0.5)
            duration_ms = params.get('duration_ms', 1000)
            
            if self.mixer_window:
                # For now, just set the value immediately
                # TODO: Implement actual animation
                mixer_value = int(target_value * 100)
                if hasattr(self.mixer_window, 'safe_set_mix_value'):
                    self.mixer_window.safe_set_mix_value(mixer_value)
                else:
                    self.mixer_window.set_mix_value(mixer_value)
                logging.info(f"✅ Animated crossfade to {target_value} over {duration_ms}ms (immediate)")
            
        except Exception as e:
            logging.error(f"❌ Error executing animate crossfade action: {e}")

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
                else:
                    self.mixer_window.update_deck_control(deck_id, parameter_name, scaled_value)
                logging.info(f"✅ Updated {deck_id}.{parameter_name} to {scaled_value}")
            
        except Exception as e:
            logging.error(f"❌ Error executing control parameter action: {e}")

    def set_midi_mappings(self, mappings):
        """Set MIDI mappings"""
        try:
            self.midi_mappings = mappings.copy()
            if self.settings_manager:
                self.settings_manager.save_midi_mappings(self.midi_mappings)
            logging.info(f"🎹 MIDI mappings updated and saved: {len(mappings)} mappings")
            
            # Debug: print the mappings
            for action_id, mapping_data in self.midi_mappings.items():
                midi_key = mapping_data.get('midi', 'no_midi')
                action_type = mapping_data.get('type', 'unknown')
                params = mapping_data.get('params', {})
                logging.info(f"  📋 Mapping {action_id}: {midi_key} -> {action_type} {params}")
                
        except Exception as e:
            logging.error(f"❌ Error setting MIDI mappings: {e}")

    def get_midi_mappings(self):
        """Get current MIDI mappings"""
        return self.midi_mappings.copy()

    def add_midi_mapping(self, action_id, mapping_data):
        """Add a single MIDI mapping"""
        try:
            self.midi_mappings[action_id] = mapping_data
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
                if self.settings_manager:
                    self.settings_manager.save_midi_mappings(self.midi_mappings)
                logging.info(f"Removed MIDI mapping: {action_id}")
        except Exception as e:
            logging.error(f"Error removing MIDI mapping: {e}")

    def clear_all_mappings(self):
        """Clear all MIDI mappings"""
        try:
            self.midi_mappings.clear()
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