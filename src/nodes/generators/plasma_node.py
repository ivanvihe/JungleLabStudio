"""
PlasmaNode - Plasma/Tunnel Effect Generator
Generate psychedelic plasma and tunnel effects
"""

import moderngl
from core.graph.node import GeneratorNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("generator.plasma")
class PlasmaNode(GeneratorNode):
    """
    Plasma/Tunnel effect generator

    Creates psychedelic plasma and tunnel effects popular in demoscene and Shadertoy.

    Parameters:
    - effect_type: Effect type (0=Plasma, 1=Tunnel, 2=Radial, 3=Combined)
    - frequency: Pattern frequency/density
    - speed: Animation speed
    - distortion: Pattern distortion amount
    - color_speed: Color animation speed
    - color_offset: Color phase offset
    - brightness: Overall brightness
    - contrast: Pattern contrast
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        self.add_param('effect_type', 0.0, 0.0, 3.0)
        self.add_param('frequency', 4.0, 0.5, 20.0)
        self.add_param('speed', 1.0, 0.0, 5.0)
        self.add_param('distortion', 1.0, 0.0, 5.0)
        self.add_param('color_speed', 1.0, 0.0, 5.0)
        self.add_param('color_offset', 0.0, 0.0, 6.28)
        self.add_param('brightness', 1.0, 0.0, 2.0)
        self.add_param('contrast', 1.0, 0.0, 3.0)

        vertex_shader = """
        #version 330
        in vec2 in_pos;
        in vec2 in_uv;
        out vec2 v_uv;
        void main() {
            v_uv = in_uv;
            gl_Position = vec4(in_pos, 0.0, 1.0);
        }
        """

        fragment_shader = """
        #version 330
        in vec2 v_uv;
        out vec4 fragColor;

        uniform float u_time;
        uniform vec2 u_resolution;
        uniform int u_effect_type;
        uniform float u_frequency;
        uniform float u_speed;
        uniform float u_distortion;
        uniform float u_color_speed;
        uniform float u_color_offset;
        uniform float u_brightness;
        uniform float u_contrast;

        // Color palette
        vec3 palette(float t) {
            vec3 a = vec3(0.5, 0.5, 0.5);
            vec3 b = vec3(0.5, 0.5, 0.5);
            vec3 c = vec3(1.0, 1.0, 1.0);
            vec3 d = vec3(0.0, 0.33, 0.67);
            return a + b * cos(6.28318 * (c * t + d + u_color_offset));
        }

        // Classic plasma effect
        float plasma(vec2 uv, float time) {
            float value = 0.0;

            // Layer 1: Sine waves
            value += sin((uv.x + time) * u_frequency);
            value += sin((uv.y + time * 0.7) * u_frequency);

            // Layer 2: Circular patterns
            value += sin((uv.x + uv.y + time * 0.5) * u_frequency * 0.5);

            // Layer 3: Distance-based
            vec2 center = vec2(sin(time * 0.3), cos(time * 0.4));
            value += sin(length(uv - center) * u_frequency + time);

            return value * 0.25;
        }

        // Tunnel effect
        float tunnel(vec2 uv, float time) {
            // Convert to polar coordinates
            float r = length(uv);
            float a = atan(uv.y, uv.x);

            // Avoid division by zero
            if (r < 0.001) r = 0.001;

            // Create tunnel depth
            float depth = 1.0 / r;

            // Tunnel pattern
            float pattern = sin(depth * u_frequency + time * u_speed);
            pattern += sin(a * u_frequency * 0.5 + time * u_speed * 0.7);
            pattern += sin((depth + a) * u_frequency * 0.3);

            return pattern * 0.33;
        }

        // Radial waves
        float radial(vec2 uv, float time) {
            float r = length(uv);
            float a = atan(uv.y, uv.x);

            float value = 0.0;

            // Radial waves
            value += sin(r * u_frequency - time * u_speed);

            // Angular waves
            value += sin(a * u_frequency * 0.5 + time * u_speed * 0.5);

            // Combined
            value += sin((r + a) * u_frequency * 0.7 + time * u_speed * 0.3);

            // Distortion
            vec2 distort = vec2(
                sin(a * 3.0 + time * 0.5),
                cos(a * 4.0 - time * 0.3)
            );
            value += sin((r + length(distort) * u_distortion * 0.1) * u_frequency);

            return value * 0.25;
        }

        void main() {
            // Normalized coordinates (-1 to 1)
            vec2 uv = (v_uv - 0.5) * 2.0;
            uv.x *= u_resolution.x / u_resolution.y;

            float time = u_time * u_speed;
            float value = 0.0;

            // Select effect type
            if (u_effect_type == 0) {
                // Plasma
                value = plasma(uv, time);
            } else if (u_effect_type == 1) {
                // Tunnel
                value = tunnel(uv, time);
            } else if (u_effect_type == 2) {
                // Radial
                value = radial(uv, time);
            } else {
                // Combined - mix all effects
                float p = plasma(uv, time);
                float t = tunnel(uv, time * 0.7);
                float r = radial(uv, time * 0.5);
                value = (p + t + r) * 0.33;
            }

            // Apply distortion
            value += sin(length(uv) * u_frequency * 0.5 + time) * u_distortion * 0.1;

            // Normalize to 0-1
            value = value * 0.5 + 0.5;

            // Apply contrast
            value = pow(value, u_contrast);

            // Colorize with animated palette
            vec3 col = palette(value + u_time * u_color_speed * 0.1);

            // Apply brightness
            col *= u_brightness;

            fragColor = vec4(col, 1.0);
        }
        """

        try:
            self.program = self.ctx.program(
                vertex_shader=vertex_shader,
                fragment_shader=fragment_shader
            )
            self.vao = self.ctx.vertex_array(
                self.program,
                [(self.quad_vbo, '2f 2f', 'in_pos', 'in_uv')]
            )
        except Exception as e:
            print(f"PlasmaNode: Shader compilation failed: {e}")
            self.program = None
            self.vao = None

    def render(self):
        if not self.program or not self.vao:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        self.fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 0.0)

        self.program['u_time'].value = self.time
        self.program['u_resolution'].value = self.resolution
        self.program['u_effect_type'].value = int(self.get_param_value('effect_type'))
        self.program['u_frequency'].value = self.get_param_value('frequency')
        self.program['u_speed'].value = self.get_param_value('speed')
        self.program['u_distortion'].value = self.get_param_value('distortion')
        self.program['u_color_speed'].value = self.get_param_value('color_speed')
        self.program['u_color_offset'].value = self.get_param_value('color_offset')
        self.program['u_brightness'].value = self.get_param_value('brightness')
        self.program['u_contrast'].value = self.get_param_value('contrast')

        self.vao.render(moderngl.TRIANGLE_STRIP)
