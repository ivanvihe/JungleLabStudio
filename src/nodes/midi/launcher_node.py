"""
LauncherNode - Processes MIDI signals and activates generators
"""
import moderngl
from typing import Optional, Dict, Any, List
from enum import Enum
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry
from dataclasses import dataclass
import time


class ActivationType(Enum):
    """Types of activation for launchers"""
    ON_OFF = 0  # Simple boolean trigger
    RANGE = 1  # Map input range to output range
    VELOCITY = 2  # Velocity-sensitive
    TOGGLE = 3  # Toggle on/off state


class ModulationCurve(Enum):
    """Modulation curve types"""
    LINEAR = 0
    EXPONENTIAL = 1
    LOGARITHMIC = 2
    SMOOTH_STEP = 3


@dataclass
class LauncherState:
    """Internal state of the launcher"""
    is_active: bool = False
    current_value: float = 0.0
    target_value: float = 0.0
    toggle_state: bool = False
    last_trigger_time: float = 0.0
    ramp_progress: float = 0.0


@NodeRegistry.register("midi.launcher")
class LauncherNode(RenderNode):
    """
    Launcher Node - Processes MIDI signals and controls generators

    Features:
    - Multiple activation types (On/Off, Range, Velocity, Toggle)
    - Configurable threshold and timing
    - Modulation curves
    - Visual feedback
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add inputs
        self.add_input("midi_value")  # Input from MIDI Listener

        # Add parameters
        self.add_param("activation_type", 0.0, 0.0, 3.0)  # ActivationType enum
        self.add_param("threshold", 0.5, 0.0, 1.0)  # Activation threshold
        self.add_param("ramp_time", 0.1, 0.0, 5.0)  # Transition time (seconds)
        self.add_param("hold_time", 0.0, 0.0, 10.0)  # Hold time before release
        self.add_param("input_min", 0.0, 0.0, 1.0)  # Input range min
        self.add_param("input_max", 1.0, 0.0, 1.0)  # Input range max
        self.add_param("output_min", 0.0, 0.0, 1.0)  # Output range min
        self.add_param("output_max", 1.0, 0.0, 1.0)  # Output range max
        self.add_param("curve", 0.0, 0.0, 3.0)  # ModulationCurve enum
        self.add_param("invert", 0.0, 0.0, 1.0)  # Invert output

        # Internal state
        self.state = LauncherState()

        # Target generators (will be set by editor/connection system)
        self.target_generators: List[str] = []  # List of generator node IDs
        self.parameter_mappings: Dict[str, List[str]] = {}  # generator_id -> [param_names]

        # Visualization shader
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
            uniform float u_input_value;
            uniform float u_output_value;
            uniform float u_is_active;
            uniform float u_threshold;
            uniform float u_time;

            void main() {
                vec2 uv = v_uv;

                // Background
                vec3 color = vec3(0.15);

                // Input value bar (left side)
                if (uv.x < 0.45 && uv.y < u_input_value) {
                    color = vec3(0.3, 0.5, 0.8);
                }

                // Threshold line
                float threshold_y = u_threshold;
                if (abs(uv.y - threshold_y) < 0.01) {
                    color = vec3(1.0, 0.5, 0.0);
                }

                // Output value bar (right side)
                if (uv.x > 0.55 && uv.y < u_output_value) {
                    if (u_is_active > 0.5) {
                        color = vec3(0.2, 1.0, 0.3);
                    } else {
                        color = vec3(0.5, 0.5, 0.5);
                    }
                }

                // Active pulse
                if (u_is_active > 0.5) {
                    float pulse = sin(u_time * 8.0) * 0.5 + 0.5;
                    color += vec3(pulse * 0.1, pulse * 0.2, pulse * 0.1);
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

    def update(self, dt: float):
        """Update launcher state"""
        # Get input value from connected MIDI listener
        input_value = self._get_input_value()

        # Get activation type
        activation_type = ActivationType(int(self.get_param_value("activation_type", 0.0)))

        # Process based on activation type
        if activation_type == ActivationType.ON_OFF:
            self._process_on_off(input_value)
        elif activation_type == ActivationType.RANGE:
            self._process_range(input_value)
        elif activation_type == ActivationType.VELOCITY:
            self._process_velocity(input_value)
        elif activation_type == ActivationType.TOGGLE:
            self._process_toggle(input_value)

        # Apply ramping
        ramp_time = self.get_param_value("ramp_time", 0.1)
        if ramp_time > 0.0:
            ramp_speed = 1.0 / ramp_time
            if self.state.current_value < self.state.target_value:
                self.state.current_value = min(
                    self.state.target_value,
                    self.state.current_value + ramp_speed * dt
                )
            elif self.state.current_value > self.state.target_value:
                self.state.current_value = max(
                    self.state.target_value,
                    self.state.current_value - ramp_speed * dt
                )
        else:
            self.state.current_value = self.state.target_value

        # Apply modulation curve
        output = self._apply_curve(self.state.current_value)

        # Apply output range mapping
        output = self._map_output_range(output)

        # Apply inversion if enabled
        if self.get_param_value("invert", 0.0) > 0.5:
            output = 1.0 - output

        return output

    def _get_input_value(self) -> float:
        """Get input value from connected MIDI listener"""
        # Check if there's a connected MIDI listener node
        midi_input = self.get_input("midi_value")
        if midi_input and hasattr(midi_input, 'get_output_value'):
            return midi_input.get_output_value()
        return 0.0

    def _process_on_off(self, input_value: float):
        """Process as on/off trigger"""
        threshold = self.get_param_value("threshold", 0.5)

        if input_value >= threshold:
            self.state.is_active = True
            self.state.target_value = 1.0
            self.state.last_trigger_time = time.time()
        else:
            # Check hold time
            hold_time = self.get_param_value("hold_time", 0.0)
            if time.time() - self.state.last_trigger_time > hold_time:
                self.state.is_active = False
                self.state.target_value = 0.0

    def _process_range(self, input_value: float):
        """Process as range mapping"""
        # Map input range to 0-1
        input_min = self.get_param_value("input_min", 0.0)
        input_max = self.get_param_value("input_max", 1.0)

        if input_max > input_min:
            normalized = (input_value - input_min) / (input_max - input_min)
            normalized = max(0.0, min(1.0, normalized))  # Clamp to 0-1
        else:
            normalized = 0.0

        self.state.target_value = normalized
        self.state.is_active = normalized > 0.01

    def _process_velocity(self, input_value: float):
        """Process as velocity-sensitive"""
        # Similar to range but with threshold
        threshold = self.get_param_value("threshold", 0.1)

        if input_value >= threshold:
            self.state.is_active = True
            self.state.target_value = input_value
        else:
            self.state.is_active = False
            self.state.target_value = 0.0

    def _process_toggle(self, input_value: float):
        """Process as toggle"""
        threshold = self.get_param_value("threshold", 0.5)

        # Detect rising edge
        if input_value >= threshold and not self.state.is_active:
            self.state.toggle_state = not self.state.toggle_state
            self.state.is_active = True

        if input_value < threshold:
            self.state.is_active = False

        self.state.target_value = 1.0 if self.state.toggle_state else 0.0

    def _apply_curve(self, value: float) -> float:
        """Apply modulation curve"""
        curve = ModulationCurve(int(self.get_param_value("curve", 0.0)))

        if curve == ModulationCurve.LINEAR:
            return value
        elif curve == ModulationCurve.EXPONENTIAL:
            return value * value
        elif curve == ModulationCurve.LOGARITHMIC:
            return pow(value, 0.5)
        elif curve == ModulationCurve.SMOOTH_STEP:
            return value * value * (3.0 - 2.0 * value)

        return value

    def _map_output_range(self, value: float) -> float:
        """Map value to output range"""
        output_min = self.get_param_value("output_min", 0.0)
        output_max = self.get_param_value("output_max", 1.0)

        return output_min + value * (output_max - output_min)

    def get_output_value(self) -> float:
        """Get the current output value"""
        return self.state.current_value

    def is_active(self) -> bool:
        """Check if launcher is active"""
        return self.state.is_active

    def add_target_generator(self, generator_id: str, parameters: List[str]):
        """Add a target generator with parameter mappings"""
        if generator_id not in self.target_generators:
            self.target_generators.append(generator_id)
        self.parameter_mappings[generator_id] = parameters

    def remove_target_generator(self, generator_id: str):
        """Remove a target generator"""
        if generator_id in self.target_generators:
            self.target_generators.remove(generator_id)
        if generator_id in self.parameter_mappings:
            del self.parameter_mappings[generator_id]

    def render(self):
        """Render visual representation"""
        # Update state first
        output_value = self.update(1.0 / 60.0)  # Assuming 60fps

        self.fbo.use()

        # Get input value for visualization
        input_value = self._get_input_value()

        # Set uniforms
        self.prog["u_input_value"].value = input_value
        self.prog["u_output_value"].value = output_value
        self.prog["u_is_active"].value = 1.0 if self.state.is_active else 0.0
        self.prog["u_threshold"].value = self.get_param_value("threshold", 0.5)
        self.prog["u_time"].value = self.time

        self.vao.render(moderngl.TRIANGLE_STRIP)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        data = super().to_dict()
        data['target_generators'] = self.target_generators
        data['parameter_mappings'] = self.parameter_mappings
        return data

    def from_dict(self, data: Dict[str, Any]):
        """Deserialize from dictionary"""
        super().from_dict(data)
        self.target_generators = data.get('target_generators', [])
        self.parameter_mappings = data.get('parameter_mappings', {})
