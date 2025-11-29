"""
VignetteNode - Vignette darkening effect
"""
import moderngl
import numpy as np
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("effect.vignette")
class VignetteNode(RenderNode):
    """
    Vignette effect node - adds darkening around the edges
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("intensity", 0.5, 0.0, 1.0)
        self.add_param("falloff", 0.5, 0.1, 2.0)
        self.add_param("center_x", 0.5, 0.0, 1.0)
        self.add_param("center_y", 0.5, 0.0, 1.0)

        # Vignette shader
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
            uniform float u_intensity;
            uniform float u_falloff;
            uniform vec2 u_center;

            void main() {
                vec4 color = texture(u_input, v_uv);

                // Calculate distance from center
                vec2 pos = v_uv - u_center;
                float dist = length(pos);

                // Create vignette mask
                float vignette = 1.0 - smoothstep(0.0, u_falloff, dist);
                vignette = mix(1.0, vignette, u_intensity);

                // Apply vignette
                fragColor = vec4(color.rgb * vignette, color.a);
            }
            """
        )

        # Create VAO
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

    def render(self):
        """Render vignette effect"""
        input_tex = self.get_input_texture("input0")

        if not input_tex:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        self.fbo.use()
        input_tex.use(location=0)

        self.prog["u_input"].value = 0
        self.prog["u_intensity"].value = self.get_param_value("intensity", 0.5)
        self.prog["u_falloff"].value = self.get_param_value("falloff", 0.5)

        center_x = self.get_param_value("center_x", 0.5)
        center_y = self.get_param_value("center_y", 0.5)
        self.prog["u_center"].value = (center_x, center_y)

        self.vao.render(moderngl.TRIANGLE_STRIP)
