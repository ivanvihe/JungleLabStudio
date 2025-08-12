import rtmidi
import time
import logging
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from collections import deque

class MidiEngine(QObject):
    midi_message_received = pyqtSignal(list)  # Signal to emit parsed MIDI messages
    bpm_changed = pyqtSignal(float)  # Signal when BPM changes
    device_connected = pyqtSignal(str)  # Signal when device connects
    device_disconnected = pyqtSignal()  # Signal when device disconnects
    
    def __init__(self):
        super().__init__()
        self.midi_in = rtmidi.MidiIn()
        self.midi_out = rtmidi.MidiOut()
        self.connected_port = None
        self.connected_port_index = None
        
        # BPM calculation
        self.clock_times = deque(maxlen=24)  # Store last 24 clock messages (1 quarter note)
        self.current_bpm = 0.0
        self.last_clock_time = 0
        
        # MIDI message stats
        self.total_messages = 0
        self.note_on_count = 0
        self.note_off_count = 0
        self.cc_count = 0
        self.clock_count = 0
        
        # Device monitoring timer
        self.device_monitor_timer = QTimer()
        self.device_monitor_timer.timeout.connect(self.check_device_status)
        self.device_monitor_timer.start(2000)  # Check every 2 seconds
        
        # Set callback
        self.midi_in.set_callback(self._midi_callback)
        
        logging.info("MIDI Engine initialized")

    def get_midi_input_ports(self):
        """Get list of available MIDI input ports"""
        try:
            ports = self.midi_in.get_ports()
            logging.debug(f"Available MIDI ports: {ports}")
            return ports
        except Exception as e:
            logging.error(f"Error getting MIDI ports: {e}")
            return []

    def get_midi_output_ports(self):
        """Get list of available MIDI output ports"""
        try:
            return self.midi_out.get_ports()
        except Exception as e:
            logging.error(f"Error getting MIDI output ports: {e}")
            return []

    def open_midi_input_port(self, port_name):
        """Open a MIDI input port by name"""
        try:
            ports = self.get_midi_input_ports()
            if port_name in ports:
                port_index = ports.index(port_name)
                
                # Close existing port if open
                if self.midi_in.is_port_open():
                    self.close_midi_input_port()
                
                self.midi_in.open_port(port_index)
                self.connected_port = port_name
                self.connected_port_index = port_index
                
                # Reset BPM calculation
                self.reset_bpm_calculation()
                
                logging.info(f"Opened MIDI input port: {port_name}")
                self.device_connected.emit(port_name)
                return True
            else:
                logging.warning(f"MIDI input port not found: {port_name}")
                return False
        except Exception as e:
            logging.error(f"Error opening MIDI port {port_name}: {e}")
            self.connected_port = None
            self.connected_port_index = None
            return False

    def close_midi_input_port(self):
        """Close the current MIDI input port"""
        try:
            if self.midi_in.is_port_open():
                self.midi_in.close_port()
                logging.info(f"Closed MIDI input port: {self.connected_port}")
                
            self.connected_port = None
            self.connected_port_index = None
            self.reset_bpm_calculation()
            self.device_disconnected.emit()
        except Exception as e:
            logging.error(f"Error closing MIDI port: {e}")

    def check_device_status(self):
        """Check if the connected device is still available"""
        if self.connected_port:
            available_ports = self.get_midi_input_ports()
            if self.connected_port not in available_ports:
                logging.warning(f"MIDI device {self.connected_port} was disconnected")
                self.connected_port = None
                self.connected_port_index = None
                self.reset_bpm_calculation()
                self.device_disconnected.emit()

    def reset_bpm_calculation(self):
        """Reset BPM calculation variables"""
        self.clock_times.clear()
        self.current_bpm = 0.0
        self.last_clock_time = 0
        self.bpm_changed.emit(0.0)

    def calculate_bpm(self):
        """Calculate BPM from MIDI clock messages"""
        if len(self.clock_times) < 2:
            return
            
        # Calculate average time between clocks
        time_diffs = []
        for i in range(1, len(self.clock_times)):
            diff = self.clock_times[i] - self.clock_times[i-1]
            if diff > 0:  # Avoid division by zero
                time_diffs.append(diff)
        
        if time_diffs:
            avg_clock_interval = sum(time_diffs) / len(time_diffs)
            
            # MIDI clock sends 24 pulses per quarter note
            # BPM = 60 / (avg_clock_interval * 24)
            if avg_clock_interval > 0:
                bpm = 60.0 / (avg_clock_interval * 24)
                
                # Only update if BPM has changed significantly
                if abs(bpm - self.current_bpm) > 0.5:
                    self.current_bpm = bpm
                    self.bpm_changed.emit(bpm)

    def _midi_callback(self, message, time_stamp):
        """Handle incoming MIDI messages"""
        try:
            self.total_messages += 1
            self.midi_message_received.emit(message)
            
            if not message:
                return
                
            status_byte = message[0]
            current_time = time.time()
            
            # Handle different message types
            if 0x90 <= status_byte <= 0x9F:  # Note On
                self.note_on_count += 1
                if len(message) >= 3:
                    channel = status_byte & 0x0F
                    note = message[1]
                    velocity = message[2]
                    logging.debug(f"MIDI Note On: Ch={channel}, Note={note}, Vel={velocity}")
                    
            elif 0x80 <= status_byte <= 0x8F:  # Note Off
                self.note_off_count += 1
                if len(message) >= 3:
                    channel = status_byte & 0x0F
                    note = message[1]
                    velocity = message[2]
                    logging.debug(f"MIDI Note Off: Ch={channel}, Note={note}, Vel={velocity}")
                    
            elif 0xB0 <= status_byte <= 0xBF:  # Control Change
                self.cc_count += 1
                if len(message) >= 3:
                    channel = status_byte & 0x0F
                    controller = message[1]
                    value = message[2]
                    logging.debug(f"MIDI CC: Ch={channel}, CC={controller}, Val={value}")
                    
            elif status_byte == 0xF8:  # MIDI Clock
                self.clock_count += 1
                self.clock_times.append(current_time)
                self.last_clock_time = current_time
                
                # Calculate BPM every few clock messages
                if len(self.clock_times) >= 12:  # Half a quarter note
                    self.calculate_bpm()
                    
            elif status_byte == 0xFA:  # MIDI Start
                logging.info("MIDI Start received")
                self.reset_bpm_calculation()
                
            elif status_byte == 0xFB:  # MIDI Continue
                logging.info("MIDI Continue received")
                
            elif status_byte == 0xFC:  # MIDI Stop
                logging.info("MIDI Stop received")
                self.reset_bpm_calculation()
                
            elif status_byte == 0xFF:  # System Reset
                logging.info("MIDI System Reset received")
                self.reset_bpm_calculation()
                
        except Exception as e:
            logging.error(f"Error in MIDI callback: {e}")

    def get_connected_port(self):
        """Get the name of the currently connected port"""
        return self.connected_port

    def get_current_bpm(self):
        """Get the current calculated BPM"""
        return self.current_bpm

    def get_midi_stats(self):
        """Get MIDI message statistics"""
        return {
            "total_messages": self.total_messages,
            "note_on": self.note_on_count,
            "note_off": self.note_off_count,
            "control_change": self.cc_count,
            "clock": self.clock_count,
            "current_bpm": self.current_bpm,
            "connected_port": self.connected_port,
            "last_clock_time": self.last_clock_time
        }

    def reset_stats(self):
        """Reset MIDI statistics"""
        self.total_messages = 0
        self.note_on_count = 0
        self.note_off_count = 0
        self.cc_count = 0
        self.clock_count = 0

    def send_midi_message(self, message):
        """Send a MIDI message (if output port is available)"""
        try:
            if hasattr(self, 'midi_out') and self.midi_out:
                # This would require opening an output port
                # Implementation depends on specific requirements
                pass
        except Exception as e:
            logging.error(f"Error sending MIDI message: {e}")

    def is_receiving_clock(self):
        """Check if we're currently receiving MIDI clock"""
        if self.last_clock_time == 0:
            return False
        return (time.time() - self.last_clock_time) < 1.0  # Less than 1 second ago

    def get_device_info(self):
        """Get information about the connected device"""
        if not self.connected_port:
            return None
            
        return {
            "name": self.connected_port,
            "port_index": self.connected_port_index,
            "is_receiving_clock": self.is_receiving_clock(),
            "current_bpm": self.current_bpm,
            "total_messages": self.total_messages
        }

    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.close_midi_input_port()
            if hasattr(self, 'device_monitor_timer'):
                self.device_monitor_timer.stop()
        except Exception as e:
            logging.error(f"Error in MIDI engine cleanup: {e}")