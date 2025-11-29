"""
KaleidoscopeNode - Kaleidoscope mirror effect
"""
import moderngl
import numpy as np
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("effect.kaleidoscope")
class KaleidoscopeNode(RenderNode):
    """
    Kaleidoscope effect node - creates mirror symmetry patterns
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("segments", 6.0, 2.0, 16.0)
        self.add_param("rotation", 0.0, 0.0, 6.28318)
        self.add_param("zoom", 1.0, 0.1, 3.0)

        # Kaleidoscope shader
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
            uniform float u_segments;
            uniform float u_rotation;
            uniform float u_zoom;

            #define PI 3.14159265359

            void main() {
                vec2 uv = (v_uv - 0.5) * u_zoom;

                // Convert to polar coordinates
                float angle = atan(uv.y, uv.x) + u_rotation;
                float radius = length(uv);

                // Apply kaleidoscope effect
                float segmentAngle = 2.0 * PI / u_segments;
                angle = mod(angle, segmentAngle);

                // Mirror every other segment
                if (mod(floor(atan(uv.y, uv.x) / segmentAngle), 2.0) > 0.5) {
                    angle = segmentAngle - angle;
                }

                // Convert back to cartesian
                vec2 kaleidoUV = vec2(cos(angle), sin(angle)) * radius;
                kaleidoUV = kaleidoUV * 0.5 + 0.5;

                fragColor = texture(u_input, kaleidoUV);
            }
            """
        )

        # Create VAO
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

    def render(self):
        """Render kaleidoscope effect"""
        input_tex = self.get_input_texture("input0")

        if not input_tex:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        self.fbo.use()
        input_tex.use(location=0)

        self.prog["u_input"].value = 0
        self.prog["u_segments"].value = self.get_param_value("segments", 6.0)
        self.prog["u_rotation"].value = self.get_param_value("rotation", 0.0)
        self.prog["u_zoom"].value = self.get_param_value("zoom", 1.0)

        self.vao.render(moderngl.TRIANGLE_STRIP)
