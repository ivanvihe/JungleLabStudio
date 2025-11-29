"""
BlendNode - Blends two inputs together
"""
import moderngl
import numpy as np
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("blend")
class BlendNode(RenderNode):
    """
    Blend node - blends two inputs together
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Blend shader
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
            uniform sampler2D u_input0;
            uniform sampler2D u_input1;
            uniform float u_opacity;
            uniform int u_mode;  // 0=mix, 1=add, 2=multiply, 3=screen

            void main() {
                vec4 a = texture(u_input0, v_uv);
                vec4 b = texture(u_input1, v_uv);

                vec4 result;
                if (u_mode == 0) {
                    // Mix
                    result = mix(a, b, u_opacity);
                } else if (u_mode == 1) {
                    // Add
                    result = a + b * u_opacity;
                } else if (u_mode == 2) {
                    // Multiply
                    result = a * mix(vec4(1.0), b, u_opacity);
                } else if (u_mode == 3) {
                    // Screen
                    result = 1.0 - (1.0 - a) * (1.0 - b * u_opacity);
                } else {
                    result = a;
                }

                fragColor = result;
            }
            """
        )

        # Create VAO for fullscreen quad
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

        # Parameters
        self.add_param("opacity", 0.5, 0.0, 1.0)
        self.add_param("mode", 0.0, 0.0, 3.0)  # 0=mix, 1=add, 2=multiply, 3=screen

    def render(self):
        """Blend two inputs"""
        input0 = self.get_input_texture("input0")
        input1 = self.get_input_texture("input1")

        if not input0:
            # No inputs, render black
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        # Blend
        self.fbo.use()

        if input0:
            input0.use(location=0)
        if input1:
            input1.use(location=1)

        self.prog['u_input0'].value = 0
        self.prog['u_input1'].value = 1
        self.prog['u_opacity'].value = self.get_param_value("opacity", 0.5)
        self.prog['u_mode'].value = int(self.get_param_value("mode", 0))

        self.vao.render(moderngl.TRIANGLE_STRIP)
