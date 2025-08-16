# midi/midi_visual_mapper.py - GESTIÓN DINÁMICA DE MAPPINGS VISUALES
import logging
import json
import os
from pathlib import Path

class MidiVisualMapper:
    """
    Clase para gestionar mappings MIDI de visuales de forma dinámica.
    Permite añadir/quitar visuales sin modificar el midi_engine.py
    """
    
    def __init__(self, visualizer_manager=None):
        self.visualizer_manager = visualizer_manager
        self.visual_mappings_config = {}
        self.default_channel = 0
        
        # Cargar configuración de mappings
        self.load_visual_mappings_config()
        
        logging.info(f"🎨 MidiVisualMapper initialized with {len(self.visual_mappings_config)} visual configs")

    def load_visual_mappings_config(self):
        """Cargar configuración de mappings desde archivo JSON"""
        try:
            config_path = Path(__file__).parent / "visual_mappings_config.json"
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.visual_mappings_config = json.load(f)
                logging.info(f"✅ Loaded visual mappings config from {config_path}")
            else:
                # Crear configuración por defecto
                self.create_default_visual_config()
                self.save_visual_mappings_config()
                
        except Exception as e:
            logging.error(f"❌ Error loading visual mappings config: {e}")
            self.create_default_visual_config()

    def save_visual_mappings_config(self):
        """Guardar configuración de mappings a archivo JSON"""
        try:
            config_path = Path(__file__).parent / "visual_mappings_config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.visual_mappings_config, f, indent=2, ensure_ascii=False)
            logging.info(f"✅ Saved visual mappings config to {config_path}")
        except Exception as e:
            logging.error(f"❌ Error saving visual mappings config: {e}")

    def create_default_visual_config(self):
        """Crear configuración por defecto de mappings visuales"""
        self.visual_mappings_config = {
            "deck_layouts": {
                "deck_a": {
                    "start_note": 36,  # C1
                    "end_note": 46,    # A#1 (46 = clear)
                    "clear_note": 46
                },
                "deck_b": {
                    "start_note": 60,  # C3
                    "end_note": 70,    # A#3 (70 = clear)
                    "clear_note": 70
                }
            },
            "visual_priority_order": [
                "Simple Test",
                "Intro Background",
                "Intro Text ROBOTICA",
                "Wire Terrain",
                "Abstract Lines",
                "Geometric Particles",
                "Evolutive Particles",
                "Abstract Shapes",
                "Mobius Band",
                "Building Madness",
                "Cosmic Flow",
                "Fluid Particles",
                "Vortex Particles"
            ],
            "mix_actions": {
                "start_note": 48,  # C2
                "end_note": 59,    # B2
                "actions": [
                    {"preset": "A to B", "duration": "10s"},
                    {"preset": "B to A", "duration": "10s"},
                    {"preset": "A to B", "duration": "5s"},
                    {"preset": "B to A", "duration": "5s"},
                    {"preset": "A to B", "duration": "500ms"},
                    {"preset": "B to A", "duration": "500ms"},
                    {"preset": "Instant A", "duration": "50ms"},
                    {"preset": "Instant B", "duration": "50ms"},
                    {"preset": "Cut to Center", "duration": "50ms"},
                    {"preset": "Reset Mix", "duration": "50ms"}
                ]
            }
        }

    def get_available_visuals(self):
        """Obtener lista de visuales disponibles desde el visualizer_manager"""
        if self.visualizer_manager:
            available = self.visualizer_manager.get_visualizer_names()
            logging.debug(f"🎨 Available visuals from manager: {available}")
            return available
        return []

    def generate_dynamic_deck_mappings(self, deck_id):
        """Generar mappings MIDI dinámicos para un deck basado en visuales disponibles"""
        mappings = {}
        
        try:
            deck_config = self.visual_mappings_config["deck_layouts"].get(deck_id.lower())
            if not deck_config:
                logging.error(f"❌ No deck config found for {deck_id}")
                return mappings

            available_visuals = self.get_available_visuals()
            priority_order = self.visual_mappings_config.get("visual_priority_order", [])
            
            # Ordenar visuales según prioridad definida
            ordered_visuals = []
            
            # Primero añadir los que están en la lista de prioridad
            for visual_name in priority_order:
                if visual_name in available_visuals:
                    ordered_visuals.append(visual_name)
            
            # Luego añadir los que no están en la lista de prioridad
            for visual_name in available_visuals:
                if visual_name not in ordered_visuals:
                    ordered_visuals.append(visual_name)

            start_note = deck_config["start_note"]
            clear_note = deck_config["clear_note"]
            max_slots = clear_note - start_note  # Slots disponibles antes del clear
            
            logging.info(f"🎵 Generating mappings for Deck {deck_id.upper()}:")
            logging.info(f"   Notes {start_note}-{clear_note-1} (visual slots)")
            logging.info(f"   Note {clear_note} (clear deck)")
            logging.info(f"   Available visuals: {len(available_visuals)}")
            logging.info(f"   Max slots: {max_slots}")

            # Generar mappings para visuales
            for i, visual_name in enumerate(ordered_visuals[:max_slots]):
                note = start_note + i
                action_id = f"deck_{deck_id.lower()}_preset_{i}"
                
                mappings[action_id] = {
                    "type": "load_preset",
                    "params": {
                        "deck_id": deck_id.upper(),
                        "preset_name": visual_name,
                        "custom_values": ""
                    },
                    "midi": f"note_on_ch{self.default_channel}_note{note}"
                }
                
                logging.info(f"   📝 Note {note} ({self.get_note_name(note)}): {visual_name}")

            # Generar mapping para clear deck
            clear_action_id = f"deck_{deck_id.lower()}_clear"
            mappings[clear_action_id] = {
                "type": "load_preset",
                "params": {
                    "deck_id": deck_id.upper(),
                    "preset_name": None,
                    "custom_values": ""
                },
                "midi": f"note_on_ch{self.default_channel}_note{clear_note}"
            }
            
            logging.info(f"   📝 Note {clear_note} ({self.get_note_name(clear_note)}): [Clear Deck]")

        except Exception as e:
            logging.error(f"❌ Error generating deck mappings for {deck_id}: {e}")

        return mappings

    def generate_mix_action_mappings(self):
        """Generar mappings para acciones de mix"""
        mappings = {}
        
        try:
            mix_config = self.visual_mappings_config.get("mix_actions", {})
            start_note = mix_config.get("start_note", 48)
            actions = mix_config.get("actions", [])

            logging.info(f"🎛️ Generating mix action mappings:")
            
            for i, action in enumerate(actions):
                note = start_note + i
                action_id = f"mix_action_{i}"
                
                mappings[action_id] = {
                    "type": "crossfade_action",
                    "params": {
                        "preset": action["preset"],
                        "duration": action["duration"],
                        "target": "Visual Mix"
                    },
                    "midi": f"note_on_ch{self.default_channel}_note{note}"
                }
                
                logging.info(f"   📝 Note {note} ({self.get_note_name(note)}): {action['preset']} ({action['duration']})")

        except Exception as e:
            logging.error(f"❌ Error generating mix mappings: {e}")

        return mappings

    def generate_all_visual_mappings(self):
        """Generar todos los mappings visuales dinámicamente"""
        all_mappings = {}
        
        try:
            # Generar mappings para Deck A
            deck_a_mappings = self.generate_dynamic_deck_mappings("A")
            all_mappings.update(deck_a_mappings)
            
            # Generar mappings para Deck B  
            deck_b_mappings = self.generate_dynamic_deck_mappings("B")
            all_mappings.update(deck_b_mappings)
            
            # Generar mappings para acciones de mix
            mix_mappings = self.generate_mix_action_mappings()
            all_mappings.update(mix_mappings)
            
            logging.info(f"🎹 Generated {len(all_mappings)} dynamic visual mappings")
            
        except Exception as e:
            logging.error(f"❌ Error generating all visual mappings: {e}")

        return all_mappings

    def add_visual_to_config(self, visual_name, priority_position=None):
        """Añadir un nuevo visual a la configuración"""
        try:
            priority_order = self.visual_mappings_config.get("visual_priority_order", [])
            
            if visual_name not in priority_order:
                if priority_position is not None and 0 <= priority_position <= len(priority_order):
                    priority_order.insert(priority_position, visual_name)
                else:
                    priority_order.append(visual_name)
                
                self.visual_mappings_config["visual_priority_order"] = priority_order
                self.save_visual_mappings_config()
                
                logging.info(f"✅ Added visual '{visual_name}' to config at position {priority_position or len(priority_order)-1}")
                return True
            else:
                logging.warning(f"⚠️ Visual '{visual_name}' already in config")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error adding visual to config: {e}")
            return False

    def remove_visual_from_config(self, visual_name):
        """Remover un visual de la configuración"""
        try:
            priority_order = self.visual_mappings_config.get("visual_priority_order", [])
            
            if visual_name in priority_order:
                priority_order.remove(visual_name)
                self.visual_mappings_config["visual_priority_order"] = priority_order
                self.save_visual_mappings_config()
                
                logging.info(f"✅ Removed visual '{visual_name}' from config")
                return True
            else:
                logging.warning(f"⚠️ Visual '{visual_name}' not found in config")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error removing visual from config: {e}")
            return False

    def update_visual_priority(self, visual_name, new_position):
        """Actualizar la prioridad de un visual"""
        try:
            priority_order = self.visual_mappings_config.get("visual_priority_order", [])
            
            if visual_name in priority_order:
                # Remover de posición actual
                priority_order.remove(visual_name)
                # Insertar en nueva posición
                priority_order.insert(new_position, visual_name)
                
                self.visual_mappings_config["visual_priority_order"] = priority_order
                self.save_visual_mappings_config()
                
                logging.info(f"✅ Updated visual '{visual_name}' priority to position {new_position}")
                return True
            else:
                logging.warning(f"⚠️ Visual '{visual_name}' not found in config")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error updating visual priority: {e}")
            return False

    def sync_with_available_visuals(self):
        """Sincronizar configuración con visuales realmente disponibles"""
        try:
            available_visuals = self.get_available_visuals()
            current_priority = self.visual_mappings_config.get("visual_priority_order", [])
            
            # Remover visuales que ya no existen
            updated_priority = [v for v in current_priority if v in available_visuals]
            
            # Añadir nuevos visuales que no estaban en la config
            for visual in available_visuals:
                if visual not in updated_priority:
                    updated_priority.append(visual)
                    logging.info(f"🆕 Auto-added new visual: {visual}")
            
            # Reportar visuales removidos
            removed_visuals = [v for v in current_priority if v not in available_visuals]
            for visual in removed_visuals:
                logging.info(f"🗑️ Removed unavailable visual: {visual}")
            
            if updated_priority != current_priority:
                self.visual_mappings_config["visual_priority_order"] = updated_priority
                self.save_visual_mappings_config()
                logging.info(f"✅ Synced visual config: {len(updated_priority)} visuals")
            
        except Exception as e:
            logging.error(f"❌ Error syncing with available visuals: {e}")

    def get_visual_mapping_info(self):
        """Obtener información detallada de los mappings actuales"""
        info = {
            "deck_a": {},
            "deck_b": {},
            "mix_actions": {},
            "total_mappings": 0
        }
        
        try:
            # Generar mappings actuales
            deck_a_mappings = self.generate_dynamic_deck_mappings("A")
            deck_b_mappings = self.generate_dynamic_deck_mappings("B")
            mix_mappings = self.generate_mix_action_mappings()
            
            # Procesar info de Deck A
            for action_id, mapping in deck_a_mappings.items():
                note_key = mapping["midi"].split("_note")[-1]
                note_num = int(note_key)
                info["deck_a"][note_num] = {
                    "note_name": self.get_note_name(note_num),
                    "visual_name": mapping["params"].get("preset_name", "Clear"),
                    "action_id": action_id
                }
            
            # Procesar info de Deck B
            for action_id, mapping in deck_b_mappings.items():
                note_key = mapping["midi"].split("_note")[-1]
                note_num = int(note_key)
                info["deck_b"][note_num] = {
                    "note_name": self.get_note_name(note_num),
                    "visual_name": mapping["params"].get("preset_name", "Clear"),
                    "action_id": action_id
                }
            
            # Procesar info de Mix Actions
            for action_id, mapping in mix_mappings.items():
                note_key = mapping["midi"].split("_note")[-1]
                note_num = int(note_key)
                params = mapping["params"]
                info["mix_actions"][note_num] = {
                    "note_name": self.get_note_name(note_num),
                    "preset": params.get("preset", "Unknown"),
                    "duration": params.get("duration", "instant"),
                    "action_id": action_id
                }
            
            info["total_mappings"] = len(deck_a_mappings) + len(deck_b_mappings) + len(mix_mappings)
            
        except Exception as e:
            logging.error(f"❌ Error getting visual mapping info: {e}")
        
        return info

    def get_note_name(self, note_number):
        """Convertir número de nota MIDI a nombre"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (note_number // 12) - 1
        note_name = note_names[note_number % 12]
        return f"{note_name}{octave}"

    def set_default_channel(self, channel):
        """Configurar canal MIDI por defecto"""
        if 0 <= channel <= 15:
            self.default_channel = channel
            logging.info(f"🎹 Visual mapper default channel set to: {channel}")

    def print_current_visual_mappings(self):
        """Imprimir mappings visuales actuales para debugging"""
        try:
            info = self.get_visual_mapping_info()
            
            logging.info("🎨 CURRENT VISUAL MAPPINGS:")
            logging.info("=" * 60)
            
            # Print Deck A
            logging.info("🔴 DECK A:")
            for note_num in sorted(info["deck_a"].keys()):
                mapping_info = info["deck_a"][note_num]
                logging.info(f"  {mapping_info['note_name']} (Note {note_num}): {mapping_info['visual_name']}")
            
            # Print Mix Actions
            logging.info("🟡 MIX ACTIONS:")
            for note_num in sorted(info["mix_actions"].keys()):
                mapping_info = info["mix_actions"][note_num]
                logging.info(f"  {mapping_info['note_name']} (Note {note_num}): {mapping_info['preset']} ({mapping_info['duration']})")
            
            # Print Deck B
            logging.info("🟢 DECK B:")
            for note_num in sorted(info["deck_b"].keys()):
                mapping_info = info["deck_b"][note_num]
                logging.info(f"  {mapping_info['note_name']} (Note {note_num}): {mapping_info['visual_name']}")
            
            logging.info(f"📊 Total mappings: {info['total_mappings']}")
            logging.info("=" * 60)
            
        except Exception as e:
            logging.error(f"❌ Error printing visual mappings: {e}")