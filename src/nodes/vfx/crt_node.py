"""
CRTNode - CRT monitor effect
"""
import moderngl
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("vfx.crt")
class CRTNode(RenderNode):
    """CRT monitor effect with curvature and scanlines"""

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)
        self.add_param("curvature", 0.3, 0.0, 1.0)
        self.add_param("scanline_intensity", 0.4, 0.0, 1.0)
        self.add_param("vignette", 0.5, 0.0, 1.0)
        self.add_param("brightness", 1.2, 0.5, 2.0)

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
            uniform float u_curvature;
            uniform float u_scanline_intensity;
            uniform float u_vignette;
            uniform float u_brightness;
            uniform vec2 u_resolution;

            vec2 curve(vec2 uv) {
                uv = uv * 2.0 - 1.0;
                vec2 offset = abs(uv.yx) / vec2(u_curvature * 6.0);
                uv = uv + uv * offset * offset;
                uv = uv * 0.5 + 0.5;
                return uv;
            }

            void main() {
                vec2 uv = v_uv;

                // Apply CRT curvature
                uv = curve(uv);

                // Check if outside curved screen
                if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
                    fragColor = vec4(0.0, 0.0, 0.0, 1.0);
                    return;
                }

                // Sample texture
                vec4 color = texture(u_input, uv);

                // Scanlines
                float scanline = sin(uv.y * u_resolution.y * 2.0) * 0.5 + 0.5;
                color.rgb *= mix(1.0, scanline, u_scanline_intensity);

                // Vignette
                vec2 vig = uv * 2.0 - 1.0;
                float vignette = 1.0 - dot(vig, vig) * u_vignette * 0.3;
                color.rgb *= vignette;

                // Brightness boost
                color.rgb *= u_brightness;

                // Slight RGB separation at edges
                float edge = length(vig);
                if (edge > 0.7) {
                    float r = texture(u_input, uv + vec2(0.002, 0.0)).r;
                    float b = texture(u_input, uv - vec2(0.002, 0.0)).b;
                    color.r = r;
                    color.b = b;
                }

                fragColor = vec4(color.rgb, 1.0);
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
        self.prog["u_curvature"].value = self.get_param_value("curvature", 0.3)
        self.prog["u_scanline_intensity"].value = self.get_param_value("scanline_intensity", 0.4)
        self.prog["u_vignette"].value = self.get_param_value("vignette", 0.5)
        self.prog["u_brightness"].value = self.get_param_value("brightness", 1.2)
        self.prog["u_resolution"].value = self.resolution
        self.vao.render(moderngl.TRIANGLE_STRIP)
