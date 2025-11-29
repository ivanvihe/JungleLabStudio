"""
PosterizeNode - Color quantization/posterization effect
"""
import moderngl
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("effect.posterize")
class PosterizeNode(RenderNode):
    """
    Posterize effect node - reduces color depth for artistic effect
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("levels", 8.0, 2.0, 256.0)
        self.add_param("gamma", 1.0, 0.5, 2.0)

        # Posterize shader
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
            uniform float u_levels;
            uniform float u_gamma;

            vec3 posterize(vec3 color, float levels) {
                // Apply gamma correction first
                color = pow(color, vec3(u_gamma));

                // Quantize to levels
                color = floor(color * levels) / levels;

                // Reverse gamma
                color = pow(color, vec3(1.0 / u_gamma));

                return color;
            }

            void main() {
                vec2 uv = v_uv;
                vec4 color = texture(u_input, uv);

                // Posterize RGB channels
                color.rgb = posterize(color.rgb, u_levels);

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
        """Render posterize effect"""
        input_tex = self.get_input_texture("input0")

        if not input_tex:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        self.fbo.use()
        input_tex.use(location=0)

        self.prog["u_input"].value = 0
        self.prog["u_levels"].value = self.get_param_value("levels", 8.0)
        self.prog["u_gamma"].value = self.get_param_value("gamma", 1.0)

        self.vao.render(moderngl.TRIANGLE_STRIP)
