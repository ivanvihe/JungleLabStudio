"""
EdgeDetectNode - Edge detection using Sobel operator
"""
import moderngl
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("effect.edge_detect")
class EdgeDetectNode(RenderNode):
    """
    Edge detection effect node - uses Sobel operator for edge detection
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("threshold", 0.1, 0.0, 1.0)
        self.add_param("thickness", 1.0, 0.5, 5.0)
        self.add_param("invert", 0.0, 0.0, 1.0)  # 0 = black edges, 1 = white edges
        self.add_param("color", [1.0, 1.0, 1.0])  # Edge color

        # Edge detection shader
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
            uniform float u_threshold;
            uniform float u_thickness;
            uniform float u_invert;
            uniform vec3 u_color;
            uniform vec2 u_resolution;

            float luminance(vec3 color) {
                return dot(color, vec3(0.299, 0.587, 0.114));
            }

            void main() {
                vec2 uv = v_uv;
                vec2 texel = u_thickness / u_resolution;

                // Sobel kernels
                mat3 Gx = mat3(
                    -1, 0, 1,
                    -2, 0, 2,
                    -1, 0, 1
                );

                mat3 Gy = mat3(
                    -1, -2, -1,
                     0,  0,  0,
                     1,  2,  1
                );

                // Sample 3x3 neighborhood
                float gx = 0.0;
                float gy = 0.0;

                for (int i = -1; i <= 1; i++) {
                    for (int j = -1; j <= 1; j++) {
                        vec2 offset = vec2(float(i), float(j)) * texel;
                        float lum = luminance(texture(u_input, uv + offset).rgb);

                        gx += lum * Gx[i+1][j+1];
                        gy += lum * Gy[i+1][j+1];
                    }
                }

                // Calculate edge magnitude
                float edge = sqrt(gx * gx + gy * gy);

                // Apply threshold
                edge = step(u_threshold, edge);

                // Invert if needed
                if (u_invert > 0.5) {
                    edge = 1.0 - edge;
                }

                // Apply edge color
                fragColor = vec4(u_color * edge, 1.0);
            }
            """
        )

        # Create VAO
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

    def render(self):
        """Render edge detection effect"""
        input_tex = self.get_input_texture("input0")

        if not input_tex:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        self.fbo.use()
        input_tex.use(location=0)

        self.prog["u_input"].value = 0
        self.prog["u_threshold"].value = self.get_param_value("threshold", 0.1)
        self.prog["u_thickness"].value = self.get_param_value("thickness", 1.0)
        self.prog["u_invert"].value = self.get_param_value("invert", 0.0)

        color_param = self.get_param_value("color", [1.0, 1.0, 1.0])
        self.prog["u_color"].value = tuple(color_param)

        self.prog["u_resolution"].value = self.resolution

        self.vao.render(moderngl.TRIANGLE_STRIP)
