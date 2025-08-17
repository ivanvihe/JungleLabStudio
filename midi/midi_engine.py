# midi/midi_engine.py - VERSIÓN SIMPLIFICADA SIN LÓGICA DE VISUALES
import mido
import mido.backends.rtmidi
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt
import time
import logging
import queue
import copy
import json
import os

from .midi_visual_mapper import MidiVisualMapper

class MidiEngine(QObject):
    # Existing signals
    midi_message_received = pyqtSignal(object)
    control_changed = pyqtSignal(str, int)
    note_on_received = pyqtSignal(int, int)
    note_off_received = pyqtSignal(int)
    preset_loaded_on_deck = pyqtSignal(str, str)

    # New signals for the mapping system
    midi_message_received_for_learning = pyqtSignal(str)
    bpm_changed = pyqtSignal(float)
    device_connected = pyqtSignal(str)
    device_disconnected = pyqtSignal(str)
    mapped_action_triggered = pyqtSignal(str, int)

    def __init__(self, settings_manager, visualizer_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.visualizer_manager = visualizer_manager
        
        # NUEVO: Inicializar mapper de visuales
        self.visual_mapper = MidiVisualMapper(visualizer_manager)
        
        # CONFIGURACIÓN MEJORADA DE CANALES MIDI
        self.accepted_channels = list(range(16))  # Acepta todos los canales (0-15)
        self.default_channel = 0  # Canal por defecto para mappings
        
        # Cargar mappings con prioridad
        self.midi_mappings = {}
        self.load_mappings_with_priority()
        
        # Construir tabla de lookup
        self._build_midi_lookup()
        
        # DEBUG mejorado
        logging.info(f"🎹 MIDI ENGINE INITIALIZED:")
        logging.info(f"   Total mappings loaded: {len(self.midi_mappings)}")
        logging.info(f"   Accepted MIDI channels: {self.accepted_channels}")
        logging.info(f"   Default channel: {self.default_channel}")
        
        self.input_port = None
        self.running = False
        self._last_bpm_time = 0
        self._beat_intervals = []

        # Referencias a componentes de aplicación
        self.mixer_window = None
        self.control_panel = None

        # Variables de animación de crossfade
        self.crossfade_timer = None
        self.crossfade_start_value = 0.5
        self.crossfade_target_value = 0.5
        self.crossfade_duration = 1000
        self.crossfade_start_time = 0

        # Cola para desacoplar recepción MIDI del procesamiento
        self._message_queue = queue.Queue()

        logging.info("MidiEngine initialized")

        # Conectar señal para ejecución thread-safe
        self.mapped_action_triggered.connect(
            self.execute_mapped_action_safe, Qt.ConnectionType.QueuedConnection
        )

        # Timer para procesar mensajes MIDI en cola
        self._queue_timer = QTimer()
        self._queue_timer.setInterval(1)
        self._queue_timer.timeout.connect(self._process_midi_queue)
        self._queue_timer.start()

        # Configurar mappings por defecto después de inicialización
        QTimer.singleShot(1000, self.setup_default_mappings)

    def set_accepted_channels(self, channels):
        """Configurar qué canales MIDI acepta el engine"""
        if isinstance(channels, (list, tuple)):
            self.accepted_channels = list(channels)
        elif isinstance(channels, int):
            self.accepted_channels = [channels]
        else:
            self.accepted_channels = list(range(16))  # Todos los canales
        
        logging.info(f"🎹 MIDI channels updated: {self.accepted_channels}")
        
        # Reconstruir lookup table con nuevos canales
        self._build_midi_lookup()
        
        # Actualizar canal en visual mapper
        self.visual_mapper.set_default_channel(self.default_channel)

    def set_default_channel(self, channel):
        """Configurar canal MIDI por defecto para nuevos mappings"""
        if 0 <= channel <= 15:
            self.default_channel = channel
            logging.info(f"🎹 Default MIDI channel set to: {channel}")
            # Actualizar en visual mapper
            self.visual_mapper.set_default_channel(channel)

    def create_message_key(self, msg):
        """FIXED: Crear clave única para mensaje MIDI - FILTRADO MEJORADO"""
        try:
            channel = getattr(msg, 'channel', 0)
            
            # FILTRAR MENSAJES QUE NO NECESITAN MAPPING
            if msg.type in ['clock', 'start', 'stop', 'continue', 'song_position']:
                return None
            
            # IMPORTANTE: Verificar si el canal está aceptado
            if channel not in self.accepted_channels:
                logging.debug(f"🚫 Channel {channel} not in accepted channels {self.accepted_channels}")
                return None
            
            logging.debug(f"🔑 Creating key for {msg.type} on channel {channel}")
            
            if msg.type == 'note_on':
                note_on_key = f"note_on_ch{channel}_note{msg.note}"
                logging.debug(f"🔑 Note_on key: {note_on_key}")
                return note_on_key
                
            elif msg.type == 'note_off':
                return None  # Ignorar note_off para reducir spam
                
            elif msg.type == 'control_change':
                cc_key = f"cc_ch{channel}_cc{msg.control}"
                logging.debug(f"🔑 CC key: {cc_key}")
                return cc_key
                
            elif msg.type == 'program_change':
                pc_key = f"pc_ch{channel}_prog{msg.program}"
                logging.debug(f"🔑 PC key: {pc_key}")
                return pc_key
                
            elif msg.type == 'pitchwheel':
                pw_key = f"pitchwheel_ch{channel}"
                logging.debug(f"🔑 Pitchwheel key: {pw_key}")
                return pw_key
            else:
                logging.debug(f"🔑 Unknown MIDI type: {msg.type}")
                return None
                
        except Exception as e:
            logging.error(f"❌ Error creating message key: {e}")
            return None

    def create_default_midi_mappings(self):
        """NUEVO: Crear mappings usando el visual mapper dinámico"""
        try:
            logging.info("🎨 Creating dynamic MIDI mappings using MidiVisualMapper...")
            
            # Sincronizar con visuales disponibles
            self.visual_mapper.sync_with_available_visuals()
            
            # Generar mappings dinámicos
            dynamic_mappings = self.visual_mapper.generate_all_visual_mappings()
            
            logging.info(f"✅ Generated {len(dynamic_mappings)} dynamic MIDI mappings")
            
            # Mostrar información de mappings
            self.visual_mapper.print_current_visual_mappings()
            
            return dynamic_mappings
            
        except Exception as e:
            logging.error(f"❌ Error creating dynamic mappings: {e}")
            # Fallback a mappings vacíos
            return {}

    def handle_midi_message(self, msg):
        """FIXED: Procesar mensaje MIDI con filtrado mejorado"""
        try:
            # PROCESAR MIDI CLOCK/SYNC por separado (NO logging spam)
            if msg.type in ['clock', 'start', 'stop', 'continue', 'song_position']:
                self.process_midi_sync(msg)
                return
            
            # Log básico solo para note_on/note_off importantes
            if hasattr(msg, 'type') and msg.type == 'note_on':
                channel = getattr(msg, 'channel', 0)
                note = getattr(msg, 'note', 0)
                velocity = getattr(msg, 'velocity', 0)
                
                if velocity > 0:  # Solo note_on reales
                    logging.info(f"🎵 MIDI: {msg.type} Ch{channel+1} Note{note} Vel{velocity}")
            
            # Crear clave de mensaje
            message_key = self.create_message_key(msg)
            
            if message_key is None:
                return
            
            # Emitir señales para monitoreo
            self.midi_message_received.emit(msg)
            self.midi_message_received_for_learning.emit(message_key)
            
            # Verificar si existe mapping
            mapping_exists = message_key in self.midi_lookup
            
            if mapping_exists:
                action_id, mapping_data = self.midi_lookup[message_key]
                action_type = mapping_data.get('type', 'unknown')
                params = mapping_data.get('params', {})
                logging.info(f"✅ FOUND MAPPING: {message_key} -> {action_id} ({action_type})")
            else:
                # Solo log debug para mappings no encontrados
                logging.debug(f"❌ NO MAPPING for: {message_key}")
            
            # Procesar diferentes tipos de mensaje
            if msg.type == 'note_on':
                velocity = getattr(msg, 'velocity', 0)
                note = getattr(msg, 'note', 0)
                
                self.note_on_received.emit(note, velocity)
                
                if velocity > 0:
                    # Note on real
                    self.process_bpm_from_note()
                    if mapping_exists:
                        logging.info(f"🚀 EXECUTING note_on action for {message_key}")
                        self.mapped_action_triggered.emit(message_key, velocity)
                else:
                    # Note on con velocity 0 = note off
                    self.note_off_received.emit(note)
                    
            elif msg.type == 'control_change':
                control = getattr(msg, 'control', 0)
                value = getattr(msg, 'value', 0)
                self.control_changed.emit(f"cc_{control}", value)
                if mapping_exists:
                    self.mapped_action_triggered.emit(message_key, value)
                    
            elif msg.type == 'program_change':
                program = getattr(msg, 'program', 0)
                if mapping_exists:
                    self.mapped_action_triggered.emit(message_key, program)

        except Exception as e:
            logging.error(f"❌ Error handling MIDI message: {e}")
            import traceback
            traceback.print_exc()

    def _build_midi_lookup(self):
        """Build lookup table from simple visual->note mappings."""
        self.midi_lookup = {}
        try:
            deck_channels = self.visual_mapper.config.get("deck_channels", {})
            if not deck_channels:
                deck_channels = {"A": 0, "B": 1, "C": 2, "D": 3}

            for visual_name, note in self.midi_mappings.items():
                if not isinstance(note, int):
                    continue
                for deck_id, channel in deck_channels.items():
                    midi_key = f"note_on_ch{channel}_note{note}"
                    action_id = f"{visual_name.replace(' ', '_').lower()}_{deck_id.lower()}"
                    mapping_data = {
                        'type': 'load_preset',
                        'params': {
                            'deck_id': deck_id,
                            'preset_name': visual_name,
                            'custom_values': '',
                        },
                        'midi': midi_key,
                    }
                    self.midi_lookup[midi_key] = (action_id, mapping_data)
            logging.info(f"✅ MIDI lookup table built with {len(self.midi_lookup)} entries")
        except Exception as e:
            logging.error(f"❌ Error building MIDI lookup: {e}")
            self.midi_lookup = {}

    # === FUNCIONES PARA UI DE CONFIGURACIÓN ===
    
    def get_available_channels(self):
        """Obtener canales MIDI disponibles"""
        return list(range(16))  # MIDI channels 1-16 (0-15 internally)
    
    def get_channel_display_name(self, channel):
        """Obtener nombre de display para canal MIDI"""
        return f"Channel {channel + 1}"  # Display as 1-16
    
    def add_custom_mapping(self, action_type, params, midi_key):
        """Añadir mapping personalizado desde UI"""
        try:
            # Generar ID único
            import uuid
            action_id = f"custom_{action_type}_{str(uuid.uuid4())[:8]}"
            
            mapping_data = {
                "type": action_type,
                "params": params,
                "midi": midi_key
            }
            
            self.midi_mappings[action_id] = mapping_data
            self._build_midi_lookup()
            
            # Guardar cambios
            if self.settings_manager:
                self.settings_manager.save_midi_mappings(self.midi_mappings)
            
            logging.info(f"✅ Custom mapping added: {action_id} -> {midi_key}")
            return action_id
            
        except Exception as e:
            logging.error(f"❌ Error adding custom mapping: {e}")
            return None
    
    def remove_mapping(self, action_id):
        """Remover mapping específico"""
        try:
            if action_id in self.midi_mappings:
                midi_key = self.midi_mappings[action_id].get('midi', 'unknown')
                del self.midi_mappings[action_id]
                self._build_midi_lookup()
                
                # Guardar cambios
                if self.settings_manager:
                    self.settings_manager.save_midi_mappings(self.midi_mappings)
                
                logging.info(f"✅ Mapping removed: {action_id} ({midi_key})")
                return True
        except Exception as e:
            logging.error(f"❌ Error removing mapping: {e}")
        return False
    
    def update_mapping(self, action_id, new_midi_key=None, new_params=None):
        """Actualizar mapping existente"""
        try:
            if action_id not in self.midi_mappings:
                return False
                
            mapping = self.midi_mappings[action_id]
            
            if new_midi_key:
                mapping['midi'] = new_midi_key
            if new_params:
                mapping['params'].update(new_params)
            
            self._build_midi_lookup()
            
            # Guardar cambios
            if self.settings_manager:
                self.settings_manager.save_midi_mappings(self.midi_mappings)
            
            logging.info(f"✅ Mapping updated: {action_id}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error updating mapping: {e}")
            return False

    def get_mappings_for_channel(self, channel):
        """Obtener todos los mappings para un canal específico"""
        channel_mappings = {}
        for action_id, mapping_data in self.midi_mappings.items():
            midi_key = mapping_data.get('midi', '')
            if f'_ch{channel}_' in midi_key:
                channel_mappings[action_id] = mapping_data
        return channel_mappings

    def get_note_mapping_info(self, note, channel=None):
        """Obtener información de mapping para una nota específica"""
        if channel is None:
            channel = self.default_channel
            
        note_on_key = f"note_on_ch{channel}_note{note}"
        note_off_key = f"note_off_ch{channel}_note{note}"
        
        info = {
            'note': note,
            'channel': channel,
            'note_name': self.get_note_name(note),
            'note_on_mapping': None,
            'note_off_mapping': None,
            'has_mapping': False
        }
        
        if note_on_key in self.midi_lookup:
            action_id, mapping_data = self.midi_lookup[note_on_key]
            info['note_on_mapping'] = {
                'action_id': action_id,
                'mapping_data': mapping_data
            }
            info['has_mapping'] = True
            
        if note_off_key in self.midi_lookup:
            action_id, mapping_data = self.midi_lookup[note_off_key]
            info['note_off_mapping'] = {
                'action_id': action_id,
                'mapping_data': mapping_data
            }
            info['has_mapping'] = True
            
        return info

    def get_note_name(self, note_number):
        """Convertir número de nota MIDI a nombre (ej: 69 -> A3)"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (note_number // 12) - 1
        note_name = note_names[note_number % 12]
        return f"{note_name}{octave}"

    def export_mappings_to_file(self, filename):
        """Exportar mappings a archivo JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.midi_mappings, f, indent=2, ensure_ascii=False)
            logging.info(f"✅ Mappings exported to {filename}")
            return True
        except Exception as e:
            logging.error(f"❌ Error exporting mappings: {e}")
            return False

    def import_mappings_from_file(self, filename):
        """Importar mappings desde archivo JSON"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported_mappings = json.load(f)
            
            if isinstance(imported_mappings, dict):
                self.midi_mappings = imported_mappings
                self._build_midi_lookup()
                
                # Guardar cambios
                if self.settings_manager:
                    self.settings_manager.save_midi_mappings(self.midi_mappings)
                
                logging.info(f"✅ Mappings imported from {filename}")
                return True
        except Exception as e:
            logging.error(f"❌ Error importing mappings: {e}")
        return False

    # === FUNCIONES HEREDADAS (mantenidas para compatibilidad) ===
    
    def load_mappings_with_priority(self):
        """Cargar mappings con prioridad"""
        try:
            config_mappings_path = 'config/midi_mappings.json'
            if os.path.exists(config_mappings_path):
                try:
                    with open(config_mappings_path, 'r') as f:
                        config_mappings = json.load(f)
                    
                    if isinstance(config_mappings, dict) and len(config_mappings) > 0:
                        self.midi_mappings = copy.deepcopy(config_mappings)
                        logging.info(f"✅ Loaded {len(self.midi_mappings)} mappings from {config_mappings_path}")
                        return
                except Exception as e:
                    logging.error(f"❌ Error loading from {config_mappings_path}: {e}")
            
            # Fallback a settings_manager
            if self.settings_manager:
                try:
                    settings_mappings = self.settings_manager.load_midi_mappings()
                    if isinstance(settings_mappings, dict) and len(settings_mappings) > 0:
                        self.midi_mappings = copy.deepcopy(settings_mappings)
                        logging.info(f"✅ Loaded {len(self.midi_mappings)} mappings from settings")
                        return
                except Exception as e:
                    logging.error(f"❌ Error loading from settings: {e}")
            
            # Mappings vacíos
            self.midi_mappings = {}
            logging.warning("⚠️ No mappings found - will create defaults")
            
        except Exception as e:
            logging.error(f"❌ Critical error loading mappings: {e}")
            self.midi_mappings = {}
    
    def set_application_references(self, mixer_window=None, control_panel=None):
        """Set references to application components for executing actions"""
        self.mixer_window = mixer_window
        self.control_panel = control_panel
        logging.info(f"✅ Application references set in MidiEngine")

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
            self.close_input_port()
            
            available_ports = mido.get_input_names()
            if port_name not in available_ports:
                logging.error(f"❌ Port '{port_name}' not available")
                return False
            
            self.input_port = mido.open_input(port_name, callback=self._enqueue_midi_message)
            self.running = True
            
            if self.settings_manager:
                self.settings_manager.set_setting("last_midi_device", port_name)
            
            logging.info(f"✅ MIDI port opened: {port_name}")
            self.device_connected.emit(port_name)
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to open MIDI port: {e}")
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
                logging.info("✅ MIDI port closed")
            except Exception as e:
                logging.error(f"Error closing MIDI port: {e}")

    def is_port_open(self):
        """Check if a MIDI input port is currently open"""
        return self.input_port is not None and self.running

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

    def execute_mapped_action_safe(self, message_key, value):
        """Thread-safe wrapper for executing mapped actions"""
        try:
            if message_key not in self.midi_lookup:
                logging.error(f"❌ Attempting to execute non-existent mapping: {message_key}")
                return
            
            self.execute_mapped_action(message_key, value)
        except Exception as e:
            logging.error(f"❌ Error in execute_mapped_action_safe: {e}")

    def execute_mapped_action(self, message_key, value):
        """Execute action mapped to a MIDI message"""
        try:
            mapped_action = self.midi_lookup.get(message_key)
            if not mapped_action:
                return

            action_id, mapping_data = mapped_action
            action_type = mapping_data.get('type')
            params = mapping_data.get('params', {})
            
            logging.info(f"🎹 EXECUTING: {action_id} ({action_type}) with value {value}")
            
            if action_type == "load_preset":
                self.execute_load_preset_action(params)
            elif action_type == "crossfade_action":
                self.execute_crossfade_action(params)
            elif action_type == "animate_crossfade":
                self.execute_animate_crossfade_action(params)
            elif action_type == "control_parameter":
                self.execute_control_parameter_action(params, value)
            elif action_type == "preset_action":
                self.execute_preset_action(params)
            else:
                logging.warning(f"⚠️ Unknown action type: {action_type}")
                
        except Exception as e:
            logging.error(f"❌ Error executing mapped action: {e}")

    def execute_load_preset_action(self, params):
        """Execute load preset action"""
        try:
            deck_id = params.get('deck_id')
            preset_name = params.get('preset_name')
            custom_values = params.get('custom_values', '')
            
            if not self.mixer_window:
                logging.error("❌ Mixer window reference not available!")
                return
            
            if deck_id and preset_name is not None:
                self.mixer_window.safe_set_deck_visualizer(deck_id, preset_name)

                if custom_values:
                    self.apply_custom_values(deck_id, custom_values)

                if preset_name is None:
                    logging.info(f"✅ Deck {deck_id} cleared")
                    self.preset_loaded_on_deck.emit(deck_id, "-- No preset selected --")
                else:
                    logging.info(f"✅ Preset '{preset_name}' loaded on deck {deck_id}")
                    self.preset_loaded_on_deck.emit(deck_id, preset_name)
                    
        except Exception as e:
            logging.error(f"❌ Error in execute_load_preset_action: {e}")

    def execute_crossfade_action(self, params):
        """Execute crossfade action"""
        try:
            preset = params.get('preset', 'A to B')
            duration = params.get('duration', '')
            
            # Parse duration string to milliseconds
            duration_ms = 1000
            if duration:
                if 'ms' in duration:
                    duration_ms = int(duration.replace('ms', ''))
                elif 's' in duration:
                    duration_ms = int(float(duration.replace('s', '')) * 1000)
            
            # Map preset to target value
            target_value = 0.5
            if preset == "Instant A":
                target_value = 0.0
                duration_ms = 50
            elif preset == "Instant B":
                target_value = 1.0
                duration_ms = 50
            elif preset == "Cut to Center":
                target_value = 0.5
                duration_ms = 50
            elif preset == "Reset Mix":
                target_value = 0.5
                duration_ms = 50
            elif preset == "A to B":
                target_value = 1.0
            elif preset == "B to A":
                target_value = 0.0
            
            # Use animated crossfade
            animation_params = {
                'target_value': target_value,
                'duration_ms': duration_ms,
                'curve': 'linear'
            }
            
            self.execute_animate_crossfade_action(animation_params)
            
        except Exception as e:
            logging.error(f"❌ Error executing crossfade action: {e}")

    def execute_animate_crossfade_action(self, params):
        """Execute animated crossfade action"""
        try:
            target_value = params.get('target_value', 0.5)
            duration_ms = params.get('duration_ms', 1000)
            
            if not self.mixer_window:
                logging.error("❌ Mixer window not available for crossfade animation")
                return
            
            current_value = self.mixer_window.get_mix_value() if hasattr(self.mixer_window, 'get_mix_value') else 0.5
            
            self.crossfade_start_value = current_value
            self.crossfade_target_value = target_value
            self.crossfade_duration = duration_ms
            self.crossfade_start_time = time.time() * 1000
            
            if self.crossfade_timer:
                self.crossfade_timer.stop()
                self.crossfade_timer = None
            
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
            
            current_value = self.crossfade_start_value + (self.crossfade_target_value - self.crossfade_start_value) * progress
            
            mixer_value = int(current_value * 100)
            if hasattr(self.mixer_window, 'safe_set_mix_value'):
                self.mixer_window.safe_set_mix_value(mixer_value)
            
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

    def execute_preset_action(self, params):
        """Trigger a custom action on a deck's current preset"""
        try:
            deck_id = params.get('deck_id')
            preset_name = params.get('preset_name')
            action = params.get('custom_values', '')

            if not self.mixer_window:
                logging.error("❌ Mixer window reference not available!")
                return

            target_deck = None
            if deck_id == 'A':
                target_deck = self.mixer_window.deck_a
            elif deck_id == 'B':
                target_deck = self.mixer_window.deck_b

            if target_deck and target_deck.get_current_visualizer_name() == preset_name:
                self.mixer_window.safe_trigger_deck_action(deck_id, action)
                logging.info(f"✅ Triggered action '{action}' on deck {deck_id}")
            else:
                logging.debug(f"Deck {deck_id} not running preset {preset_name}")

        except Exception as e:
            logging.error(f"❌ Error executing preset action: {e}")

    def apply_custom_values(self, deck_id, custom_values):
        """Apply custom parameter values to a deck"""
        try:
            if not custom_values:
                return
                
            pairs = custom_values.split(';')
            for pair in pairs:
                if ':' in pair:
                    param_name, param_value = pair.split(':', 1)
                    param_name = param_name.strip()
                    param_value = param_value.strip()
                    
                    try:
                        if param_value.isdigit() or (param_value.startswith('-') and param_value[1:].isdigit()):
                            param_value = int(param_value)
                        elif '.' in param_value:
                            param_value = float(param_value)
                    except ValueError:
                        pass
                    
                    if self.mixer_window and hasattr(self.mixer_window, 'safe_update_deck_control'):
                        self.mixer_window.safe_update_deck_control(deck_id, param_name, param_value)
                        logging.info(f"✅ Applied custom value: {deck_id}.{param_name} = {param_value}")
                        
        except Exception as e:
            logging.error(f"❌ Error applying custom values: {e}")

    def process_bpm_from_note(self):
        """Process BPM calculation from note timing"""
        try:
            current_time = time.time()

            if self._last_bpm_time > 0:
                interval = current_time - self._last_bpm_time
                self._beat_intervals.append(interval)

                if len(self._beat_intervals) > 8:
                    self._beat_intervals.pop(0)

                if len(self._beat_intervals) >= 2:
                    avg_interval = sum(self._beat_intervals) / len(self._beat_intervals)
                    bpm = 60.0 / avg_interval

                    if 40 <= bpm <= 200:
                        self.bpm_changed.emit(bpm)

            self._last_bpm_time = current_time

        except Exception as e:
            logging.error(f"Error processing BPM: {e}")

    # Alias para compatibilidad retroactiva con el nombre anterior
    def process_bmp_from_note(self):
        """Backward compatible alias for misnamed function"""
        return self.process_bpm_from_note()

    def setup_default_mappings(self):
        """Setup default MIDI mappings"""
        try:
            if not self.midi_mappings or len(self.midi_mappings) == 0:
                logging.info("🎹 Creating default MIDI mappings...")
                default_mappings = self.create_default_midi_mappings()
                self.set_midi_mappings(default_mappings)
                logging.info("✅ Default MIDI mappings created and saved")
            else:
                logging.info(f"🎹 Using existing MIDI mappings: {len(self.midi_mappings)} mappings loaded")
                
        except Exception as e:
            logging.error(f"❌ Error setting up default mappings: {e}")

    def test_midi_mapping(self, note_number, channel=None):
        """Test a specific MIDI mapping by note number and optional channel"""
        try:
            if channel is None:
                channel = self.default_channel
            test_key = f"note_on_ch{channel}_note{note_number}"
            logging.info(
                f"🧪 TESTING MIDI mapping for note {note_number} on ch{channel} (key: {test_key})"
            )

            found_visual = None
            for visual, note in self.midi_mappings.items():
                if note == note_number:
                    found_visual = visual
                    break

            if found_visual:
                logging.info(f"✅ Found mapping: {found_visual}")
                logging.info("🚀 SIMULATING execution...")
                self.execute_mapped_action(test_key, 127)
            else:
                note_name = self.get_note_name(note_number)
                logging.warning(
                    f"❌ No mapping found for {note_name} (note {note_number}) on ch{channel}"
                )
        except Exception as e:
            logging.error(f"❌ Error testing MIDI mapping: {e}")

    def set_midi_mappings(self, mappings):
        """Set MIDI mappings"""
        try:
            self.midi_mappings = copy.deepcopy(mappings)
            self._build_midi_lookup()
            if self.settings_manager:
                self.settings_manager.save_midi_mappings(self.midi_mappings)
            logging.info(f"🎹 MIDI mappings updated and saved: {len(self.midi_mappings)} mappings")
                
        except Exception as e:
            logging.error(f"❌ Error setting MIDI mappings: {e}")

    def get_midi_mappings(self):
        """Get current MIDI mappings"""
        return self.midi_mappings.copy()

    def add_midi_mapping(self, visual_name, note):
        """Add a single MIDI mapping"""
        try:
            self.midi_mappings[visual_name] = note
            self._build_midi_lookup()
            if self.settings_manager:
                self.settings_manager.save_midi_mappings(self.midi_mappings)
            logging.info(f"Added MIDI mapping: {visual_name} -> {note}")
        except Exception as e:
            logging.error(f"Error adding MIDI mapping: {e}")

    def remove_midi_mapping(self, visual_name):
        """Remove a MIDI mapping"""
        try:
            if visual_name in self.midi_mappings:
                del self.midi_mappings[visual_name]
                self._build_midi_lookup()
                if self.settings_manager:
                    self.settings_manager.save_midi_mappings(self.midi_mappings)
                logging.info(f"Removed MIDI mapping: {visual_name}")
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

    def process_midi_sync(self, msg):
        """Procesar mensajes de MIDI clock/sync SIN spam de logs"""
        try:
            if msg.type == 'clock':
                self.process_midi_clock()
            elif msg.type == 'start':
                logging.info("▶️ MIDI Start received")
                self.midi_transport_start()
            elif msg.type == 'stop':
                logging.info("⏹️ MIDI Stop received")
                self.midi_transport_stop()
            elif msg.type == 'continue':
                logging.info("⏯️ MIDI Continue received")
                self.midi_transport_continue()
            elif msg.type == 'song_position':
                position = getattr(msg, 'pos', 0)
                logging.debug(f"🎶 MIDI Song Position: {position}")
                self.midi_song_position(position)

        except Exception as e:
            logging.error(f"Error processing MIDI sync: {e}")

    def process_midi_clock(self):
        """Procesar MIDI clock tick - SIN logging"""
        try:
            # Incrementar contador de clock interno
            if not hasattr(self, '_midi_clock_count'):
                self._midi_clock_count = 0
            
            self._midi_clock_count += 1
            
            # 24 clocks = 1 beat
            if self._midi_clock_count >= 24:
                self._midi_clock_count = 0
                # Aquí podemos emitir señal de beat para visuales
                # self.midi_beat_received.emit()
                
        except Exception as e:
            logging.error(f"Error processing MIDI clock: {e}")

    def midi_transport_start(self):
        """MIDI transport start"""
        try:
            self._midi_clock_count = 0
            # Reset timing para visuales
        except Exception as e:
            logging.error(f"Error in MIDI transport start: {e}")

    def midi_transport_stop(self):
        """MIDI transport stop"""
        try:
            self._midi_clock_count = 0
            # Parar timing para visuales
            pass
        except Exception as e:
            logging.error(f"Error in MIDI transport stop: {e}")

    def midi_transport_continue(self):
        """MIDI transport continue"""
        try:
            # Continuar desde posición actual
            pass
        except Exception as e:
            logging.error(f"Error in MIDI transport continue: {e}")

    def midi_song_position(self, position):
        """MIDI song position"""
        try:
            # Establecer posición en la canción
            pass
        except Exception as e:
            logging.error(f"Error in MIDI song position: {e}")

    def remove_duplicate_mappings(self):
        """Eliminar mappings duplicados manteniendo los más recientes"""
        try:
            # Limpiar mappings duplicados basados en pattern
            mappings = self.get_midi_mappings()
            clean_mappings = {}
            seen_midi_keys = {}
            
            # Priorizar IDs estándar sobre IDs automáticos
            priority_patterns = ['deck_a_preset_', 'deck_b_preset_', 'mix_action_', 'deck_a_clear', 'deck_b_clear']
            
            for action_id, mapping_data in mappings.items():
                midi_key = mapping_data.get('midi', '')
                
                if midi_key in seen_midi_keys:
                    # Ya existe este MIDI key
                    existing_id = seen_midi_keys[midi_key]
                    
                    # Determinar cuál mantener basado en prioridad
                    keep_current = False
                    for pattern in priority_patterns:
                        if pattern in action_id:
                            keep_current = True
                            break
                    
                    if keep_current:
                        # Reemplazar con el ID de mayor prioridad
                        if existing_id in clean_mappings:
                            del clean_mappings[existing_id]
                        clean_mappings[action_id] = mapping_data
                        seen_midi_keys[midi_key] = action_id
                        logging.info(f"🔄 Replaced duplicate {existing_id} with {action_id}")
                    else:
                        # Mantener el existente
                        logging.debug(f"⏭️ Keeping existing {existing_id} over {action_id}")
                else:
                    # Nuevo MIDI key
                    clean_mappings[action_id] = mapping_data
                    seen_midi_keys[midi_key] = action_id
            
            # Aplicar mappings limpios
            if len(clean_mappings) != len(mappings):
                logging.info(f"🧹 Cleaned mappings: {len(mappings)} -> {len(clean_mappings)}")
                self.set_midi_mappings(clean_mappings)
            
        except Exception as e:
            logging.error(f"Error removing duplicate mappings: {e}")

    # === NUEVOS MÉTODOS PARA GESTIÓN DINÁMICA DE VISUALES ===

    def refresh_visual_mappings(self):
        """Refrescar mappings de visuales dinámicamente"""
        try:
            logging.info("🔄 Refreshing visual mappings...")
            
            # Sincronizar con visuales disponibles
            self.visual_mapper.sync_with_available_visuals()
            
            # Regenerar mappings dinámicos
            new_visual_mappings = self.visual_mapper.generate_all_visual_mappings()
            
            # Mantener mappings personalizados que no sean de visuales
            custom_mappings = {}
            for action_id, mapping_data in self.midi_mappings.items():
                # Mantener mappings que no sean auto-generados
                if not any(pattern in action_id for pattern in ['deck_a_preset_', 'deck_b_preset_', 'mix_action_', 'deck_a_clear', 'deck_b_clear']):
                    custom_mappings[action_id] = mapping_data
            
            # Combinar mappings
            combined_mappings = {}
            combined_mappings.update(new_visual_mappings)
            combined_mappings.update(custom_mappings)
            
            # Aplicar nuevos mappings
            self.set_midi_mappings(combined_mappings)
            
            logging.info(f"✅ Visual mappings refreshed: {len(new_visual_mappings)} visual + {len(custom_mappings)} custom")
            
            # Mostrar información actualizada
            self.visual_mapper.print_current_visual_mappings()
            
        except Exception as e:
            logging.error(f"❌ Error refreshing visual mappings: {e}")

    def add_visual_to_mappings(self, visual_name, priority_position=None):
        """Añadir un nuevo visual a los mappings MIDI"""
        try:
            # Añadir a la configuración del visual mapper
            success = self.visual_mapper.add_visual_to_config(visual_name, priority_position)
            
            if success:
                # Refrescar mappings
                self.refresh_visual_mappings()
                logging.info(f"✅ Visual '{visual_name}' added to MIDI mappings")
                return True
            else:
                logging.warning(f"⚠️ Failed to add visual '{visual_name}' to mappings")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error adding visual to mappings: {e}")
            return False

    def remove_visual_from_mappings(self, visual_name):
        """Remover un visual de los mappings MIDI"""
        try:
            # Remover de la configuración del visual mapper
            success = self.visual_mapper.remove_visual_from_config(visual_name)
            
            if success:
                # Refrescar mappings
                self.refresh_visual_mappings()
                logging.info(f"✅ Visual '{visual_name}' removed from MIDI mappings")
                return True
            else:
                logging.warning(f"⚠️ Failed to remove visual '{visual_name}' from mappings")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error removing visual from mappings: {e}")
            return False

    def update_visual_priority(self, visual_name, new_position):
        """Actualizar la prioridad de un visual en los mappings"""
        try:
            # Actualizar en la configuración del visual mapper
            success = self.visual_mapper.update_visual_priority(visual_name, new_position)
            
            if success:
                # Refrescar mappings
                self.refresh_visual_mappings()
                logging.info(f"✅ Visual '{visual_name}' priority updated to position {new_position}")
                return True
            else:
                logging.warning(f"⚠️ Failed to update visual '{visual_name}' priority")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error updating visual priority: {e}")
            return False

    def get_visual_mapping_info(self):
        """Obtener información detallada de los mappings visuales"""
        try:
            return self.visual_mapper.get_visual_mapping_info()
        except Exception as e:
            logging.error(f"❌ Error getting visual mapping info: {e}")
            return {}

    def get_available_visuals(self):
        """Obtener lista de visuales disponibles"""
        try:
            return self.visual_mapper.get_available_visuals()
        except Exception as e:
            logging.error(f"❌ Error getting available visuals: {e}")
            return []

    def get_visual_priority_order(self):
        """Obtener el orden de prioridad actual de los visuales"""
        try:
            return self.visual_mapper.visual_mappings_config.get("visual_priority_order", [])
        except Exception as e:
            logging.error(f"❌ Error getting visual priority order: {e}")
            return []

    def remove_duplicate_mappings_smart(self):
        """Ensure each MIDI note maps to only one visual."""
        try:
            seen = {}
            duplicates_removed = 0
            clean = {}
            for visual, note in self.midi_mappings.items():
                if note in seen:
                    duplicates_removed += 1
                    continue
                seen[note] = visual
                clean[visual] = note
            if duplicates_removed:
                self.midi_mappings = clean
                if self.settings_manager:
                    self.settings_manager.save_midi_mappings(self.midi_mappings)
                logging.info(f"🧹 Removed {duplicates_removed} duplicate MIDI mappings")
            return duplicates_removed
        except Exception as e:
            logging.error(f"❌ Error removing duplicate mappings: {e}")
            return 0


    def choose_best_mapping(self, mapping_list):
        """Elegir el mejor mapping de una lista de duplicados"""

        # Patrones de prioridad (mayor prioridad = mejor)
        priority_patterns = [
            'mix_action_',      # Acciones de mix tienen máxima prioridad
            'deck_a_preset_',   # Presets estándar de deck
            'deck_b_preset_',
            'deck_c_preset_',
            'deck_d_preset_',
            'deck_a_clear',     # Acciones de clear
            'deck_b_clear',
            'deck_c_clear',
            'deck_d_clear',
            'note_',           # Patrones auto-generados (menor prioridad)
        ]

        best_mapping = mapping_list[0]  # Default al primero
        best_score = -1

        for action_id, mapping_data in mapping_list:
            # Calcular puntuación de prioridad
            priority = 0
            for i, pattern in enumerate(priority_patterns):
                if pattern in action_id:
                    priority = len(priority_patterns) - i
                    break

            # Calcular puntuación de completitud
            completeness = self.get_mapping_completeness(mapping_data)
            total_score = priority * 100 + completeness

            if total_score > best_score:
                best_score = total_score
                best_mapping = (action_id, mapping_data)

        return best_mapping


    def get_mapping_completeness(self, mapping_data):
        """Puntuar mapping basado en qué tan completo/útil es"""
        score = 0

        # Tiene tipo válido
        if mapping_data.get('type'):
            score += 10

        # Tiene parámetros
        params = mapping_data.get('params', {})
        if params:
            score += 5

            # Tiene nombre de preset
            if params.get('preset_name'):
                score += 10

            # Tiene deck ID
            if params.get('deck_id'):
                score += 5

        # Tiene MIDI key válido
        midi_key = mapping_data.get('midi', '')
        if midi_key and 'note' in midi_key:
            score += 5

        return score


    def clean_midi_mappings_manual(self):
        """Limpiar mappings MIDI manualmente desde UI"""
        try:
            logging.info("🧹 Manual MIDI cleanup requested by user")

            original_count = len(self.midi_mappings)
            duplicates_removed = self.remove_duplicate_mappings_smart()

            if duplicates_removed > 0:
                # Reconstruir lookup
                self._build_midi_lookup()

                message = (
                          f"✅ Cleanup completado!\n\n"
                          f"Mappings originales: {original_count}\n"
                          f"Duplicados removidos: {duplicates_removed}\n"
                          f"Mappings finales: {len(self.midi_mappings)}"
                      )

                logging.info(f"✅ Manual cleanup complete: removed {duplicates_removed} duplicates")
                return True, message
            else:
                message = "✨ No se encontraron duplicados - los mappings ya están limpios!"
                logging.info("✨ Manual cleanup: no duplicates found")
                return True, message

        except Exception as e:
            error_msg = f"❌ Error durante limpieza manual: {str(e)}"
            logging.error(error_msg)
            return False, error_msg

    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.close_input_port()
        except:
            pass