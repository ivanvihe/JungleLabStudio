"""
TransformNode - 2D transformation (rotate, scale, translate)
"""
import moderngl
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("effect.transform")
class TransformNode(RenderNode):
    """
    Transform effect node - applies 2D transformations
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("rotate", 0.0, -360.0, 360.0)
        self.add_param("scale_x", 1.0, 0.1, 5.0)
        self.add_param("scale_y", 1.0, 0.1, 5.0)
        self.add_param("translate_x", 0.0, -2.0, 2.0)
        self.add_param("translate_y", 0.0, -2.0, 2.0)
        self.add_param("anchor_x", 0.5, 0.0, 1.0)  # Transform origin X
        self.add_param("anchor_y", 0.5, 0.0, 1.0)  # Transform origin Y

        # Transform shader
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
            uniform float u_rotate;
            uniform float u_scale_x;
            uniform float u_scale_y;
            uniform float u_translate_x;
            uniform float u_translate_y;
            uniform float u_anchor_x;
            uniform float u_anchor_y;

            #define PI 3.14159265359

            mat2 rotate2d(float angle) {
                float s = sin(angle);
                float c = cos(angle);
                return mat2(c, -s, s, c);
            }

            void main() {
                vec2 uv = v_uv;

                // Translate to anchor point
                vec2 anchor = vec2(u_anchor_x, u_anchor_y);
                uv -= anchor;

                // Apply transformations in order: scale, rotate, translate
                // Scale
                uv.x /= u_scale_x;
                uv.y /= u_scale_y;

                // Rotate
                float angle = u_rotate * PI / 180.0;
                uv = rotate2d(-angle) * uv;

                // Translate
                uv.x -= u_translate_x;
                uv.y -= u_translate_y;

                // Translate back from anchor
                uv += anchor;

                // Sample texture
                vec4 color = vec4(0.0);
                if (uv.x >= 0.0 && uv.x <= 1.0 && uv.y >= 0.0 && uv.y <= 1.0) {
                    color = texture(u_input, uv);
                }

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
        """Render transform effect"""
        input_tex = self.get_input_texture("input0")

        if not input_tex:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        self.fbo.use()
        input_tex.use(location=0)

        self.prog["u_input"].value = 0
        self.prog["u_rotate"].value = self.get_param_value("rotate", 0.0)
        self.prog["u_scale_x"].value = self.get_param_value("scale_x", 1.0)
        self.prog["u_scale_y"].value = self.get_param_value("scale_y", 1.0)
        self.prog["u_translate_x"].value = self.get_param_value("translate_x", 0.0)
        self.prog["u_translate_y"].value = self.get_param_value("translate_y", 0.0)
        self.prog["u_anchor_x"].value = self.get_param_value("anchor_x", 0.5)
        self.prog["u_anchor_y"].value = self.get_param_value("anchor_y", 0.5)

        self.vao.render(moderngl.TRIANGLE_STRIP)
