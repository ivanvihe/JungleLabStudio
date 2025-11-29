"""
PixelateNode - Pixelation/mosaic effect
"""
import moderngl
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("effect.pixelate")
class PixelateNode(RenderNode):
    """
    Pixelate effect node - creates retro pixel/mosaic effect
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("pixel_size", 8.0, 1.0, 64.0)
        self.add_param("smoothing", 0.0, 0.0, 1.0)

        # Pixelate shader
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
            uniform float u_pixel_size;
            uniform float u_smoothing;
            uniform vec2 u_resolution;

            void main() {
                vec2 uv = v_uv;

                // Calculate pixelated coordinates
                vec2 pixel_size = vec2(u_pixel_size) / u_resolution;
                vec2 pixelated_uv = floor(uv / pixel_size) * pixel_size;

                // Center sample point in pixel
                pixelated_uv += pixel_size * 0.5;

                // Sample color
                vec4 color = texture(u_input, pixelated_uv);

                // Optional smoothing with original
                if (u_smoothing > 0.0) {
                    vec4 original = texture(u_input, uv);
                    color = mix(color, original, u_smoothing);
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
        """Render pixelate effect"""
        input_tex = self.get_input_texture("input0")

        if not input_tex:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        self.fbo.use()
        input_tex.use(location=0)

        self.prog["u_input"].value = 0
        self.prog["u_pixel_size"].value = self.get_param_value("pixel_size", 8.0)
        self.prog["u_smoothing"].value = self.get_param_value("smoothing", 0.0)
        self.prog["u_resolution"].value = self.resolution

        self.vao.render(moderngl.TRIANGLE_STRIP)
