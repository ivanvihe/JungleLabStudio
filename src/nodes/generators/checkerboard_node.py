"""
CheckerboardNode - Procedural checkerboard pattern generator
"""
import moderngl
from core.graph.node import GeneratorNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("generator.checkerboard")
class CheckerboardNode(GeneratorNode):
    """
    Checkerboard pattern generator
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("size", 8.0, 1.0, 64.0)
        self.add_param("rotation", 0.0, 0.0, 360.0)
        self.add_param("color_a", [0.0, 0.0, 0.0])
        self.add_param("color_b", [1.0, 1.0, 1.0])
        self.add_param("smoothing", 0.0, 0.0, 0.5)

        # Checkerboard shader
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
            uniform float u_size;
            uniform float u_rotation;
            uniform float u_smoothing;
            uniform vec3 u_color_a;
            uniform vec3 u_color_b;

            #define PI 3.14159265359

            // 2D rotation matrix
            mat2 rotate2d(float angle) {
                float s = sin(angle);
                float c = cos(angle);
                return mat2(c, -s, s, c);
            }

            void main() {
                vec2 uv = v_uv;

                // Center and rotate
                uv -= 0.5;
                uv = rotate2d(u_rotation * PI / 180.0) * uv;
                uv += 0.5;

                // Scale to checkerboard size
                vec2 st = uv * u_size;

                // Create checkerboard pattern
                vec2 checker = floor(st);
                float pattern = mod(checker.x + checker.y, 2.0);

                // Optional smoothing
                if (u_smoothing > 0.0) {
                    vec2 fract_st = fract(st);
                    float edge_dist = min(
                        min(fract_st.x, 1.0 - fract_st.x),
                        min(fract_st.y, 1.0 - fract_st.y)
                    );

                    pattern = smoothstep(u_smoothing, u_smoothing + 0.01, edge_dist) * pattern +
                              smoothstep(u_smoothing, u_smoothing + 0.01, edge_dist) * (1.0 - pattern);
                }

                // Mix between two colors
                vec3 color = mix(u_color_a, u_color_b, pattern);

                fragColor = vec4(color, 1.0);
            }
            """
        )

        # Create VAO
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

    def render(self):
        """Render checkerboard pattern"""
        self.fbo.use()

        self.prog["u_size"].value = self.get_param_value("size", 8.0)
        self.prog["u_rotation"].value = self.get_param_value("rotation", 0.0)
        self.prog["u_smoothing"].value = self.get_param_value("smoothing", 0.0)

        color_a = self.get_param_value("color_a", [0.0, 0.0, 0.0])
        color_b = self.get_param_value("color_b", [1.0, 1.0, 1.0])
        self.prog["u_color_a"].value = tuple(color_a)
        self.prog["u_color_b"].value = tuple(color_b)

        self.vao.render(moderngl.TRIANGLE_STRIP)
