"""
GlitchScanlinesNode - Scanline/interlace glitch effect
"""
import moderngl
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("vfx.glitch.scanlines")
class GlitchScanlinesNode(RenderNode):
    """
    Scanline glitch effect - creates interlaced/scanline artifacts
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("line_count", 200.0, 50.0, 1000.0)
        self.add_param("intensity", 0.5, 0.0, 1.0)
        self.add_param("speed", 1.0, 0.0, 5.0)
        self.add_param("distortion", 0.3, 0.0, 1.0)
        self.add_param("roll_speed", 0.1, 0.0, 2.0)

        # Scanline shader
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
            uniform sampler2D u_input;
            uniform float u_time;
            uniform float u_line_count;
            uniform float u_intensity;
            uniform float u_speed;
            uniform float u_distortion;
            uniform float u_roll_speed;

            float hash(vec2 p) {
                return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
            }

            float noise(vec2 p) {
                vec2 i = floor(p);
                vec2 f = fract(p);
                f = f * f * (3.0 - 2.0 * f);
                return mix(
                    mix(hash(i + vec2(0,0)), hash(i + vec2(1,0)), f.x),
                    mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), f.x),
                    f.y
                );
            }

            void main() {
                vec2 uv = v_uv;
                float time = u_time * u_speed;

                // Vertical roll
                uv.y += u_time * u_roll_speed * 0.1;
                uv.y = fract(uv.y);

                // Scanline pattern
                float line = sin(uv.y * u_line_count * 6.28318);
                line = line * 0.5 + 0.5;

                // Random line jumps
                float line_idx = floor(uv.y * u_line_count);
                float line_noise = noise(vec2(line_idx, floor(time * 10.0)));
                float jump = step(0.95, line_noise) * u_distortion * 0.1;

                // Apply distortion
                uv.x += jump;

                // Sample texture
                vec4 color = texture(u_input, uv);

                // Apply scanline darkening
                color.rgb *= mix(1.0, line, u_intensity);

                // Scanline flicker
                float flicker = noise(vec2(line_idx * 0.1, time * 20.0)) * 0.1;
                color.rgb *= 1.0 - (flicker * u_intensity);

                fragColor = color;
            }
            """
        )

        # Create VAO
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

    def render(self):
        """Render scanline glitch"""
        input_tex = self.get_input_texture("input0")

        if not input_tex:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        self.fbo.use()
        input_tex.use(location=0)

        self.prog["u_input"].value = 0
        self.prog["u_time"].value = self.state.time if hasattr(self, 'state') else 0.0
        self.prog["u_line_count"].value = self.get_param_value("line_count", 200.0)
        self.prog["u_intensity"].value = self.get_param_value("intensity", 0.5)
        self.prog["u_speed"].value = self.get_param_value("speed", 1.0)
        self.prog["u_distortion"].value = self.get_param_value("distortion", 0.3)
        self.prog["u_roll_speed"].value = self.get_param_value("roll_speed", 0.1)

        self.vao.render(moderngl.TRIANGLE_STRIP)
