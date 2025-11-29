"""
BlurNode - Gaussian blur effect
"""
import moderngl
import numpy as np
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("effect.blur")
class BlurNode(RenderNode):
    """
    Blur effect node - applies gaussian blur
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("amount", 5.0, 0.0, 20.0)
        self.add_param("quality", 8.0, 1.0, 16.0)

        # Blur shader
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
            uniform float u_amount;
            uniform float u_quality;
            uniform vec2 u_resolution;

            void main() {
                vec2 uv = v_uv;
                vec4 color = vec4(0.0);
                float total = 0.0;

                // Gaussian blur
                int quality = int(u_quality);
                float amount = u_amount / 1000.0;

                for (int x = -quality; x <= quality; x++) {
                    for (int y = -quality; y <= quality; y++) {
                        vec2 offset = vec2(float(x), float(y)) * amount;
                        float weight = exp(-0.5 * (float(x*x + y*y)) / (u_quality * u_quality));
                        color += texture(u_input, uv + offset) * weight;
                        total += weight;
                    }
                }

                fragColor = color / total;
            }
            """
        )

        # Create VAO
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

    def render(self):
        """Render blur effect"""
        input_tex = self.get_input_texture("input0")

        if not input_tex:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        self.fbo.use()
        input_tex.use(location=0)

        self.prog["u_input"].value = 0
        self.prog["u_amount"].value = self.get_param_value("amount", 5.0)
        self.prog["u_quality"].value = self.get_param_value("quality", 8.0)
        self.prog["u_resolution"].value = self.resolution

        self.vao.render(moderngl.TRIANGLE_STRIP)
