"""
GlitchNoiseNode - Digital noise/corruption glitch
"""
import moderngl
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("vfx.glitch.noise")
class GlitchNoiseNode(RenderNode):
    """Digital noise glitch effect"""

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)
        self.add_param("intensity", 0.5, 0.0, 1.0)
        self.add_param("speed", 1.0, 0.0, 5.0)
        self.add_param("grain_size", 2.0, 1.0, 20.0)

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
            uniform float u_intensity;
            uniform float u_grain_size;
            uniform vec2 u_resolution;

            float hash(vec2 p) {
                return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
            }

            void main() {
                vec2 uv = v_uv;
                vec2 pixel = floor(uv * u_resolution / u_grain_size);
                float noise = hash(pixel + u_time * 100.0);

                vec4 color = texture(u_input, uv);

                // Add digital noise
                if (noise < u_intensity * 0.3) {
                    color.rgb = vec3(hash(pixel + vec3(1, 2, 3)));
                } else {
                    color.rgb = mix(color.rgb, vec3(noise), u_intensity * 0.2);
                }

                fragColor = color;
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
        self.prog["u_intensity"].value = self.get_param_value("intensity", 0.5)
        self.prog["u_grain_size"].value = self.get_param_value("grain_size", 2.0)
        self.prog["u_resolution"].value = self.resolution
        self.vao.render(moderngl.TRIANGLE_STRIP)
