"""
MIDIListenerNode - Captures MIDI events in real-time
"""
import moderngl
from typing import Optional, Dict, Any
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry
from dataclasses import dataclass
import time


@dataclass
class MIDIMapping:
    """MIDI control mapping"""
    message_type: str  # 'note_on', 'note_off', 'control_change'
    channel: int = 0
    note: Optional[int] = None  # For note messages
    cc: Optional[int] = None  # For CC messages
    last_value: float = 0.0
    last_timestamp: float = 0.0
    is_active: bool = False  # For note_on/off tracking


@NodeRegistry.register("midi.listener")
class MIDIListenerNode(RenderNode):
    """
    MIDI Listener Node - Captures and outputs MIDI events

    Features:
    - MIDI Learn mode
    - Auto-detection of MIDI controls
    - Normalized output (0-1) or raw (0-127)
    - Visual feedback for MIDI activity
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # MIDI Learn mode
        self.midi_learn_mode: bool = False
        self.midi_mapping: Optional[MIDIMapping] = None

        # Add parameters
        self.add_param("device_index", 0.0, 0.0, 16.0)
        self.add_param("normalize", 1.0, 0.0, 1.0)  # 1 = normalize to 0-1, 0 = raw 0-127
        self.add_param("smoothing", 0.1, 0.0, 1.0)  # Value smoothing

        # Output value (will be sent to connected nodes)
        self.output_value: float = 0.0
        self.smoothed_value: float = 0.0

        # Activity indicator
        self.last_activity_time: float = 0.0
        self.activity_timeout: float = 0.5  # seconds

        # Placeholder visualization shader (just shows the current value)
        self.prog = self.ctx.program(
            vertex_shader="""
            #version 330
            in vec2 in_pos;
            in vec2 in_uv;
            out vec2 v_uv;
            void main() {
                v_uv = in_uv;
                gl_Position = vec4(in_pos, 0.0, 1.0);
            }
            """,
            fragment_shader="""
            #version 330
            in vec2 v_uv;
            out vec4 fragColor;
            uniform float u_value;
            uniform float u_is_active;
            uniform float u_time;

            void main() {
                vec2 uv = v_uv;

                // Display value as a horizontal bar
                float bar_height = 0.3;
                float bar_y = 0.5 - bar_height * 0.5;

                vec3 bg_color = vec3(0.1);
                vec3 bar_color = vec3(0.2, 0.8, 0.3);
                vec3 active_color = vec3(0.3, 1.0, 0.4);

                // Draw background
                vec3 color = bg_color;

                // Draw value bar
                if (uv.y > bar_y && uv.y < bar_y + bar_height) {
                    if (uv.x < u_value) {
                        color = mix(bar_color, active_color, u_is_active);
                    }
                }

                // Activity pulse
                if (u_is_active > 0.5) {
                    float pulse = sin(u_time * 10.0) * 0.5 + 0.5;
                    color += vec3(pulse * 0.2);
                }

                fragColor = vec4(color, 1.0);
            }
            """
        )

        # Create VAO
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

    def start_midi_learn(self):
        """Enter MIDI learn mode - next MIDI message will be captured"""
        self.midi_learn_mode = True
        print(f"MIDI Listener '{self.id}': MIDI Learn mode activated")

    def stop_midi_learn(self):
        """Exit MIDI learn mode"""
        self.midi_learn_mode = False
        print(f"MIDI Listener '{self.id}': MIDI Learn mode deactivated")

    def process_midi_message(self, msg: Any) -> bool:
        """
        Process incoming MIDI message
        Returns True if this listener should handle the message
        """
        # In learn mode, capture any message
        if self.midi_learn_mode:
            self._learn_from_message(msg)
            return True

        # If we have a mapping, check if message matches
        if self.midi_mapping:
            return self._handle_mapped_message(msg)

        return False

    def _learn_from_message(self, msg: Any):
        """Learn MIDI mapping from message"""
        if msg.type == 'note_on':
            self.midi_mapping = MIDIMapping(
                message_type='note_on',
                channel=msg.channel,
                note=msg.note
            )
            print(f"MIDI Listener '{self.id}': Learned Note {msg.note} on Channel {msg.channel + 1}")
            self.midi_learn_mode = False

        elif msg.type == 'control_change':
            self.midi_mapping = MIDIMapping(
                message_type='control_change',
                channel=msg.channel,
                cc=msg.control
            )
            print(f"MIDI Listener '{self.id}': Learned CC {msg.control} on Channel {msg.channel + 1}")
            self.midi_learn_mode = False

    def _handle_mapped_message(self, msg: Any) -> bool:
        """Handle message if it matches our mapping"""
        if not self.midi_mapping:
            return False

        mapping = self.midi_mapping

        # Check if message matches mapping
        if msg.type != mapping.message_type:
            return False

        if msg.channel != mapping.channel:
            return False

        # Type-specific matching
        if mapping.message_type == 'note_on' and msg.note == mapping.note:
            # Store velocity as value
            raw_value = float(msg.velocity)
            self._update_value(raw_value)
            mapping.is_active = msg.velocity > 0
            return True

        elif mapping.message_type == 'note_off' and msg.note == mapping.note:
            self._update_value(0.0)
            mapping.is_active = False
            return True

        elif mapping.message_type == 'control_change' and msg.control == mapping.cc:
            raw_value = float(msg.value)
            self._update_value(raw_value)
            return True

        return False

    def _update_value(self, raw_value: float):
        """Update output value from raw MIDI value"""
        normalize = self.get_param_value("normalize", 1.0) > 0.5

        if normalize:
            self.output_value = raw_value / 127.0
        else:
            self.output_value = raw_value

        # Update activity indicator
        self.last_activity_time = time.time()

        # Update mapping timestamp
        if self.midi_mapping:
            self.midi_mapping.last_value = self.output_value
            self.midi_mapping.last_timestamp = time.time()

    def get_output_value(self) -> float:
        """Get the current smoothed output value"""
        return self.smoothed_value

    def is_active(self) -> bool:
        """Check if MIDI was recently active"""
        return (time.time() - self.last_activity_time) < self.activity_timeout

    def render(self):
        """Render visual representation of MIDI listener"""
        self.fbo.use()

        # Apply smoothing to output value
        smoothing = self.get_param_value("smoothing", 0.1)
        self.smoothed_value = self.smoothed_value + (self.output_value - self.smoothed_value) * (1.0 - smoothing)

        # Set uniforms
        self.prog["u_value"].value = self.smoothed_value if self.get_param_value("normalize", 1.0) > 0.5 else self.smoothed_value / 127.0
        self.prog["u_is_active"].value = 1.0 if self.is_active() else 0.0
        self.prog["u_time"].value = self.time

        self.vao.render(moderngl.TRIANGLE_STRIP)

    def get_info_text(self) -> str:
        """Get text description of current mapping"""
        if self.midi_learn_mode:
            return "MIDI LEARN MODE"

        if not self.midi_mapping:
            return "No MIDI mapping"

        mapping = self.midi_mapping
        if mapping.message_type == 'note_on':
            return f"Note {mapping.note} Ch {mapping.channel + 1}"
        elif mapping.message_type == 'control_change':
            return f"CC {mapping.cc} Ch {mapping.channel + 1}"

        return "Unknown mapping"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        data = super().to_dict()
        if self.midi_mapping:
            data['midi_mapping'] = {
                'message_type': self.midi_mapping.message_type,
                'channel': self.midi_mapping.channel,
                'note': self.midi_mapping.note,
                'cc': self.midi_mapping.cc,
            }
        return data

    def from_dict(self, data: Dict[str, Any]):
        """Deserialize from dictionary"""
        super().from_dict(data)
        if 'midi_mapping' in data:
            mapping_data = data['midi_mapping']
            self.midi_mapping = MIDIMapping(
                message_type=mapping_data['message_type'],
                channel=mapping_data['channel'],
                note=mapping_data.get('note'),
                cc=mapping_data.get('cc'),
            )
