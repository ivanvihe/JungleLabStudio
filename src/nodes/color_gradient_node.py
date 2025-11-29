"""
ColorGradientNode - Color grading with gradient mapping
"""
import moderngl
import numpy as np
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("effect.color_gradient")
class ColorGradientNode(RenderNode):
    """
    Color gradient mapping node - maps luminance to a color gradient
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("mix_amount", 1.0, 0.0, 1.0)
        self.add_param("color_low", [0.1, 0.0, 0.3, 1.0])  # Dark color
        self.add_param("color_mid", [0.5, 0.2, 0.8, 1.0])  # Mid color
        self.add_param("color_high", [1.0, 0.8, 0.3, 1.0])  # Bright color

        # Gradient shader
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
            uniform float u_mix_amount;
            uniform vec4 u_color_low;
            uniform vec4 u_color_mid;
            uniform vec4 u_color_high;

            // Calculate luminance
            float luminance(vec3 color) {
                return dot(color, vec3(0.2126, 0.7152, 0.0722));
            }

            // Map value through 3-point gradient
            vec3 gradient(float t) {
                if (t < 0.5) {
                    return mix(u_color_low.rgb, u_color_mid.rgb, t * 2.0);
                } else {
                    return mix(u_color_mid.rgb, u_color_high.rgb, (t - 0.5) * 2.0);
                }
            }

            void main() {
                vec4 original = texture(u_input, v_uv);

                // Calculate luminance
                float lum = luminance(original.rgb);

                // Map to gradient
                vec3 graded = gradient(lum);

                // Mix with original
                vec3 result = mix(original.rgb, graded, u_mix_amount);

                fragColor = vec4(result, original.a);
            }
            """
        )

        # Create VAO
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

    def render(self):
        """Render color gradient mapping"""
        input_tex = self.get_input_texture("input0")

        if not input_tex:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        self.fbo.use()
        input_tex.use(location=0)

        self.prog["u_input"].value = 0
        self.prog["u_mix_amount"].value = self.get_param_value("mix_amount", 1.0)

        # Color parameters
        color_low = self.get_param_value("color_low", [0.1, 0.0, 0.3, 1.0])
        color_mid = self.get_param_value("color_mid", [0.5, 0.2, 0.8, 1.0])
        color_high = self.get_param_value("color_high", [1.0, 0.8, 0.3, 1.0])

        if isinstance(color_low, list) and len(color_low) >= 4:
            self.prog["u_color_low"].value = tuple(color_low)
        else:
            self.prog["u_color_low"].value = (0.1, 0.0, 0.3, 1.0)

        if isinstance(color_mid, list) and len(color_mid) >= 4:
            self.prog["u_color_mid"].value = tuple(color_mid)
        else:
            self.prog["u_color_mid"].value = (0.5, 0.2, 0.8, 1.0)

        if isinstance(color_high, list) and len(color_high) >= 4:
            self.prog["u_color_high"].value = tuple(color_high)
        else:
            self.prog["u_color_high"].value = (1.0, 0.8, 0.3, 1.0)

        self.vao.render(moderngl.TRIANGLE_STRIP)
