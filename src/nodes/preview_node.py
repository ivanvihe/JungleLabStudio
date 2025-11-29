"""
PreviewNode - Output node for preview purposes
"""
import moderngl
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("preview")
class PreviewNode(RenderNode):
    """
    Preview node - acts exactly like OutputNode.
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
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        self.fbo.use()
        input_tex.use(location=0)
        self.prog['u_input'].value = 0
        self.vao.render(moderngl.TRIANGLE_STRIP)
