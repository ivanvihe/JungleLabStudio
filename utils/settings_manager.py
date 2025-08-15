import json
import os
import logging

class SettingsManager:
    def __init__(self, settings_file='config/settings.json'):
        self.settings_file = settings_file
        # Archivo separado para mapeos MIDI
        self.mappings_file = 'config/midi_mappings.json'
        self.settings = self.load_settings()
        
        # Set default values if they don't exist
        self.ensure_defaults()

    def ensure_defaults(self):
        """Ensure default settings exist"""
        defaults = {
            "control_panel_monitor": 0,
            "main_window_monitor": 0,
            "last_midi_device": "virtual 20",
            "auto_save_settings": True,
            "window_positions": {
                "control_panel": {"x": 50, "y": 50, "width": 1200, "height": 800},
                "main_window": {"x": 100, "y": 100, "width": 800, "height": 600}
            },
            "deck_settings": {
                "deck_a": {
                    "last_visualizer": "",
                    "last_controls": {}
                },
                "deck_b": {
                    "last_visualizer": "",
                    "last_controls": {}
                }
            },
            "mixer_settings": {
                "last_mix_value": 50,
                "crossfader_curve": "linear"
            },
            "audio_settings": {
                "input_device": "",
                "buffer_size": 1024,
                "sample_rate": 44100
            },
            "visual_settings": {
                "fps_limit": 60,
                "vsync": True,
                "quality": "high"
            },
            "midi_mappings": {}  # Default empty MIDI mappings
        }
        
        # Add missing defaults
        for key, value in defaults.items():
            if key not in self.settings:
                self.settings[key] = value
                
        # Save updated settings
        self.save_settings()

    def load_settings(self):
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                logging.debug(f"Loaded settings from {self.settings_file}")
                return settings
            else:
                logging.debug(f"Settings file {self.settings_file} not found, using defaults")
                return {}
        except Exception as e:
            logging.error(f"Error loading settings: {e}")
            return {}

    def save_settings(self):
        """Save settings to file"""
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            logging.debug(f"Settings saved to {self.settings_file}")
        except Exception as e:
            logging.error(f"Error saving settings: {e}")

    def get_setting(self, key, default=None):
        """Get a setting value with optional default"""
        try:
            # Support nested keys like "deck_settings.deck_a.last_visualizer"
            if '.' in key:
                keys = key.split('.')
                value = self.settings
                for k in keys:
                    value = value.get(k, {})
                return value if value != {} else default
            else:
                return self.settings.get(key, default)
        except Exception as e:
            logging.error(f"Error getting setting {key}: {e}")
            return default

    def set_setting(self, key, value):
        """Set a setting value"""
        try:
            # Support nested keys
            if '.' in key:
                keys = key.split('.')
                current = self.settings
                
                # Navigate to the nested location, creating dicts as needed
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                
                # Set the final value
                current[keys[-1]] = value
            else:
                self.settings[key] = value
            
            # Auto-save if enabled
            if self.get_setting("auto_save_settings", True):
                self.save_settings()
                
            logging.debug(f"Setting {key} set to {value}")
        except Exception as e:
            logging.error(f"Error setting {key}: {e}")

    def get_window_position(self, window_name):
        """Get saved window position and size"""
        return self.get_setting(f"window_positions.{window_name}", {})

    def set_window_position(self, window_name, x, y, width, height):
        """Save window position and size"""
        position_data = {"x": x, "y": y, "width": width, "height": height}
        self.set_setting(f"window_positions.{window_name}", position_data)

    def get_deck_setting(self, deck_id, setting_name, default=None):
        """Get a deck-specific setting"""
        return self.get_setting(f"deck_settings.{deck_id}.{setting_name}", default)

    def set_deck_setting(self, deck_id, setting_name, value):
        """Set a deck-specific setting"""
        self.set_setting(f"deck_settings.{deck_id}.{setting_name}", value)

    def get_mixer_setting(self, setting_name, default=None):
        """Get a mixer-specific setting"""
        return self.get_setting(f"mixer_settings.{setting_name}", default)

    def set_mixer_setting(self, setting_name, value):
        """Set a mixer-specific setting"""
        self.set_setting(f"mixer_settings.{setting_name}", value)

    def export_settings(self, export_path):
        """Export settings to a different file"""
        try:
            with open(export_path, 'w') as f:
                json.dump(self.settings, f, indent=4)
            logging.info(f"Settings exported to {export_path}")
            return True
        except Exception as e:
            logging.error(f"Error exporting settings: {e}")
            return False

    def import_settings(self, import_path):
        """Import settings from a file"""
        try:
            with open(import_path, 'r') as f:
                imported_settings = json.load(f)
            
            # Merge with current settings (imported takes precedence)
            self.settings.update(imported_settings)
            self.save_settings()
            logging.info(f"Settings imported from {import_path}")
            return True
        except Exception as e:
            logging.error(f"Error importing settings: {e}")
            return False

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings = {}
        self.ensure_defaults()
        logging.info("Settings reset to defaults")

    def get_all_settings(self):
        """Get a copy of all settings"""
        return self.settings.copy()

    def get_monitor_settings(self):
        """Get monitor assignment settings"""
        return {
            "control_panel_monitor": self.get_setting("control_panel_monitor", 0),
            "main_window_monitor": self.get_setting("main_window_monitor", 0)
        }

    def set_monitor_settings(self, control_panel_monitor=None, main_window_monitor=None):
        """Set monitor assignment settings"""
        if control_panel_monitor is not None:
            self.set_setting("control_panel_monitor", control_panel_monitor)
        if main_window_monitor is not None:
            self.set_setting("main_window_monitor", main_window_monitor)

    # --- FUNCIONES MIDI MEJORADAS ---
    def load_midi_mappings(self):
        """Load MIDI mappings from settings - improved version"""
        try:
            logging.info("💾 Loading MIDI mappings...")
            # First try to load from the main settings file
            mappings = self.get_setting("midi_mappings", {})
            
            # Also try to load from separate mappings file for backward compatibility
            if not mappings and os.path.exists(self.mappings_file):
                logging.info(f"Trying to load from backup file: {self.mappings_file}")
                with open(self.mappings_file, 'r') as f:
                    file_mappings = json.load(f)
                    if isinstance(file_mappings, dict):
                        mappings = file_mappings
            
            if isinstance(mappings, dict):
                logging.info(f"✅ Loaded {len(mappings)} MIDI mappings")
                return mappings
            else:
                logging.warning("Invalid MIDI mappings format, returning empty dict")
                return {}
                
        except Exception as e:
            logging.error(f"Error loading MIDI mappings: {e}")
            return {}

    def save_midi_mappings(self, mappings):
        """Save MIDI mappings to settings - improved version"""
        try:
            if isinstance(mappings, dict):
                logging.info(f"💾 Saving {len(mappings)} MIDI mappings to settings.")
                # Save to main settings
                self.set_setting("midi_mappings", mappings)
                
                # Also save to separate file for backup
                try:
                    os.makedirs(os.path.dirname(self.mappings_file), exist_ok=True)
                    with open(self.mappings_file, 'w') as f:
                        json.dump(mappings, f, indent=4)
                    logging.info(f"✅ MIDI mappings also saved to backup file: {self.mappings_file}")
                except Exception as backup_error:
                    logging.warning(f"Could not save MIDI mappings backup: {backup_error}")
                
                logging.info(f"Saved {len(mappings)} MIDI mappings")
            else:
                logging.error("Invalid mappings format, must be a dictionary")
                
        except Exception as e:
            logging.error(f"Error saving MIDI mappings: {e}")

    def get_midi_device_settings(self):
        """Get MIDI device settings"""
        return {
            'last_device': self.get_setting("last_midi_device", ""),
            'auto_connect': self.get_setting("midi_auto_connect", True),
            'learn_timeout': self.get_setting("midi_learn_timeout", 10)
        }

    def set_midi_device_settings(self, device_settings):
        """Set MIDI device settings"""
        try:
            for key, value in device_settings.items():
                if key == 'last_device':
                    self.set_setting("last_midi_device", value)
                elif key == 'auto_connect':
                    self.set_setting("midi_auto_connect", value)
                elif key == 'learn_timeout':
                    self.set_setting("midi_learn_timeout", value)
            logging.info("MIDI device settings updated")
        except Exception as e:
            logging.error(f"Error setting MIDI device settings: {e}")

    def export_midi_mappings(self, filename):
        """Export MIDI mappings to a file"""
        try:
            mappings = self.load_midi_mappings()
            with open(filename, 'w') as f:
                json.dump(mappings, f, indent=2)
            logging.info(f"MIDI mappings exported to {filename}")
            return True
        except Exception as e:
            logging.error(f"Error exporting MIDI mappings: {e}")
            return False

    def import_midi_mappings(self, filename):
        """Import MIDI mappings from a file"""
        try:
            with open(filename, 'r') as f:
                mappings = json.load(f)
            if isinstance(mappings, dict):
                self.save_midi_mappings(mappings)
                logging.info(f"MIDI mappings imported from {filename}")
                return True
            else:
                logging.error("Invalid file format for MIDI mappings")
                return False
        except Exception as e:
            logging.error(f"Error importing MIDI mappings: {e}")
            return False