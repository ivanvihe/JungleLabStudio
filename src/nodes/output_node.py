"""
OutputNode - Final output node for the render graph
"""
import moderngl
import numpy as np
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("output")
class OutputNode(RenderNode):
    """
    Output node - passes through the first input unchanged.
    This is the final node in the graph.
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Simple passthrough shader
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
            void main() {
                fragColor = texture(u_input, v_uv);
            }
            """
        )

        # Create VAO for fullscreen quad
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

    def render(self):
        """Simply copy input0 to output"""
        input_tex = self.get_input_texture("input0")

        if not input_tex:
            # No input, render black
            if not hasattr(self, '_warned_no_input'):
                print(f"OutputNode {self.id}: WARNING - No input texture!")
                self._warned_no_input = True
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        # Debug first render
        if not hasattr(self, '_first_render'):
            print(f"OutputNode {self.id}: First render, input texture size: {input_tex.size}")
            self._first_render = True

        # Blit input to output using shader
        self.fbo.use()
        input_tex.use(location=0)
        self.prog['u_input'].value = 0
        self.vao.render(moderngl.TRIANGLE_STRIP)
