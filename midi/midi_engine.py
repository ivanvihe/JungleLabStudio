import rtmidi
from PyQt6.QtCore import QObject, pyqtSignal

class MidiEngine(QObject):
    midi_message_received = pyqtSignal(list) # Signal to emit parsed MIDI messages

    def __init__(self):
        super().__init__()
        self.midi_in = rtmidi.MidiIn()
        self.midi_out = rtmidi.MidiOut()
        self.connected_port = None
        self.midi_in.set_callback(self._midi_callback)

    def get_midi_input_ports(self):
        return self.midi_in.get_ports()

    def open_midi_input_port(self, port_name):
        ports = self.midi_in.get_ports()
        if port_name in ports:
            port_index = ports.index(port_name)
            if self.midi_in.is_port_open():
                self.midi_in.close_port()
            self.midi_in.open_port(port_index)
            self.connected_port = port_name
            print(f"Opened MIDI input port: {port_name}")
            return True
        print(f"MIDI input port not found: {port_name}")
        self.connected_port = None
        return False

    def close_midi_input_port(self):
        if self.midi_in.is_port_open():
            self.midi_in.close_port()
            self.connected_port = None
            print("Closed MIDI input port.")

    def _midi_callback(self, message, time_stamp):
        # message is a list of MIDI bytes, e.g., [status, data1, data2]
        # time_stamp is the time in seconds since the port was opened
        self.midi_message_received.emit(message) # Emit the raw message

        # Basic MIDI message parsing (for debugging/demonstration)
        status_byte = message[0]
        if 0x90 <= status_byte <= 0x9F: # Note On
            note = message[1]
            velocity = message[2]
            print(f"MIDI Note On: Note={note}, Velocity={velocity}")
        elif 0x80 <= status_byte <= 0x8F: # Note Off
            note = message[1]
            velocity = message[2]
            print(f"MIDI Note Off: Note={note}, Velocity={velocity}")
        elif 0xB0 <= status_byte <= 0xBF: # Control Change
            controller = message[1]
            value = message[2]
            print(f"MIDI CC: Controller={controller}, Value={value}")
        elif status_byte == 0xF8: # MIDI Clock
            print("MIDI Clock Tick")
        elif status_byte == 0xFA: # MIDI Start
            print("MIDI Start")
        elif status_byte == 0xFB: # MIDI Continue
            print("MIDI Continue")
        elif status_byte == 0xFC: # MIDI Stop
            print("MIDI Stop")

    def get_connected_port(self):
        return self.connected_port

    def __del__(self):
        self.close_midi_input_port()