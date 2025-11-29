"""
ColorAdjustNode - Color adjustment effect
"""
import moderngl
import numpy as np
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("effect.color")
class ColorAdjustNode(RenderNode):
    """
    Color adjustment node - adjusts brightness, contrast, saturation, hue
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("brightness", 1.0, 0.0, 2.0)
        self.add_param("contrast", 1.0, 0.0, 2.0)
        self.add_param("saturation", 1.0, 0.0, 2.0)
        self.add_param("hue", 0.0, 0.0, 1.0)

        # Color adjust shader
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
            uniform float u_brightness;
            uniform float u_contrast;
            uniform float u_saturation;
            uniform float u_hue;

            vec3 rgb2hsv(vec3 c) {
                vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
                vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
                vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));

                float d = q.x - min(q.w, q.y);
                float e = 1.0e-10;
                return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
            }

            vec3 hsv2rgb(vec3 c) {
                vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
                vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
                return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
            }

            void main() {
                vec4 color = texture(u_input, v_uv);

                // Brightness
                color.rgb *= u_brightness;

                // Contrast
                color.rgb = (color.rgb - 0.5) * u_contrast + 0.5;

                // Saturation and Hue (via HSV)
                vec3 hsv = rgb2hsv(color.rgb);
                hsv.x = fract(hsv.x + u_hue);  // Hue shift
                hsv.y *= u_saturation;          // Saturation
                color.rgb = hsv2rgb(hsv);

                fragColor = vec4(color.rgb, color.a);
            }
            """
        )

        # Create VAO
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

    def render(self):
        """Render color adjustment"""
        input_tex = self.get_input_texture("input0")

        if not input_tex:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        self.fbo.use()
        input_tex.use(location=0)

        self.prog["u_input"].value = 0
        self.prog["u_brightness"].value = self.get_param_value("brightness", 1.0)
        self.prog["u_contrast"].value = self.get_param_value("contrast", 1.0)
        self.prog["u_saturation"].value = self.get_param_value("saturation", 1.0)
        self.prog["u_hue"].value = self.get_param_value("hue", 0.0)

        self.vao.render(moderngl.TRIANGLE_STRIP)
