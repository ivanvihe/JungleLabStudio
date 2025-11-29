"""
GlitchRGBNode - RGB split/chromatic aberration glitch
"""
import moderngl
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("vfx.glitch.rgb")
class GlitchRGBNode(RenderNode):
    """
    RGB split glitch effect - separates color channels
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("amount", 0.5, 0.0, 1.0)
        self.add_param("speed", 1.0, 0.0, 5.0)
        self.add_param("angle", 0.0, -3.14159, 3.14159)  # radians
        self.add_param("distortion", 0.3, 0.0, 1.0)

        # RGB split shader
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
            uniform float u_amount;
            uniform float u_speed;
            uniform float u_angle;
            uniform float u_distortion;

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

                // Calculate offset direction
                vec2 dir = vec2(cos(u_angle), sin(u_angle));

                // Add distortion noise
                float distort = noise(vec2(uv.y * 10.0 + time, time * 0.5)) * u_distortion;

                // Calculate channel offsets
                float offset_amount = u_amount * 0.02 * (1.0 + distort);
                vec2 offset_r = dir * offset_amount;
                vec2 offset_b = -dir * offset_amount;

                // Sample color channels with offsets
                float r = texture(u_input, uv + offset_r).r;
                float g = texture(u_input, uv).g;
                float b = texture(u_input, uv + offset_b).b;

                fragColor = vec4(r, g, b, 1.0);
            }
            """
        )

        # Create VAO
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

    def render(self):
        """Render RGB split glitch"""
        input_tex = self.get_input_texture("input0")

        if not input_tex:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        self.fbo.use()
        input_tex.use(location=0)

        self.prog["u_input"].value = 0
        self.prog["u_time"].value = self.state.time if hasattr(self, 'state') else 0.0
        self.prog["u_amount"].value = self.get_param_value("amount", 0.5)
        self.prog["u_speed"].value = self.get_param_value("speed", 1.0)
        self.prog["u_angle"].value = self.get_param_value("angle", 0.0)
        self.prog["u_distortion"].value = self.get_param_value("distortion", 0.3)

        self.vao.render(moderngl.TRIANGLE_STRIP)
