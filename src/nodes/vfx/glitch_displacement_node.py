"""
GlitchDisplacementNode - UV displacement glitch
"""
import moderngl
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("vfx.glitch.displacement")
class GlitchDisplacementNode(RenderNode):
    """UV displacement glitch effect"""

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)
        self.add_param("amount", 0.5, 0.0, 1.0)
        self.add_param("speed", 1.0, 0.0, 5.0)
        self.add_param("frequency", 10.0, 1.0, 50.0)
        self.add_param("chaos", 0.5, 0.0, 1.0)

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
            uniform float u_frequency;
            uniform float u_chaos;

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

                // Generate displacement vectors
                float n1 = noise(uv * u_frequency + u_time);
                float n2 = noise(uv * u_frequency + u_time + 100.0);

                // Add chaos with sharp transitions
                float chaos_mult = step(0.9, noise(vec2(floor(u_time * 10.0), uv.y * 50.0)));
                chaos_mult *= u_chaos;

                vec2 displacement = vec2(n1, n2) * 2.0 - 1.0;
                displacement *= u_amount * 0.1 * (1.0 + chaos_mult * 3.0);

                uv += displacement;

                fragColor = texture(u_input, uv);
            }
            """
        )
        self.vao = self.ctx.vertex_array(self.prog, [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")])

    def render(self):
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
        self.prog["u_frequency"].value = self.get_param_value("frequency", 10.0)
        self.prog["u_chaos"].value = self.get_param_value("chaos", 0.5)
        self.vao.render(moderngl.TRIANGLE_STRIP)
