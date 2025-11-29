"""
MirrorNode - Mirror symmetry effect
"""
import moderngl
import numpy as np
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("effect.mirror")
class MirrorNode(RenderNode):
    """
    Mirror effect node - creates mirror symmetry
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("mode", 0.0, 0.0, 3.0)  # 0=horizontal, 1=vertical, 2=both, 3=diagonal
        self.add_param("position", 0.5, 0.0, 1.0)

        # Mirror shader
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
            uniform int u_mode;
            uniform float u_position;

            void main() {
                vec2 uv = v_uv;

                if (u_mode == 0) {
                    // Horizontal mirror
                    if (uv.x > u_position) {
                        uv.x = u_position - (uv.x - u_position);
                    }
                } else if (u_mode == 1) {
                    // Vertical mirror
                    if (uv.y > u_position) {
                        uv.y = u_position - (uv.y - u_position);
                    }
                } else if (u_mode == 2) {
                    // Both axes
                    if (uv.x > u_position) {
                        uv.x = u_position - (uv.x - u_position);
                    }
                    if (uv.y > u_position) {
                        uv.y = u_position - (uv.y - u_position);
                    }
                } else if (u_mode == 3) {
                    // Diagonal mirror
                    if (uv.x + uv.y > 1.0) {
                        float temp = uv.x;
                        uv.x = 1.0 - uv.y;
                        uv.y = 1.0 - temp;
                    }
                }

                fragColor = texture(u_input, uv);
            }
            """
        )

        # Create VAO
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

    def render(self):
        """Render mirror effect"""
        input_tex = self.get_input_texture("input0")

        if not input_tex:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        self.fbo.use()
        input_tex.use(location=0)

        self.prog["u_input"].value = 0
        self.prog["u_mode"].value = int(self.get_param_value("mode", 0.0))
        self.prog["u_position"].value = self.get_param_value("position", 0.5)

        self.vao.render(moderngl.TRIANGLE_STRIP)
