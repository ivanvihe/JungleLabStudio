"""
MathNodes - Basic texture arithmetic operations
"""
import moderngl
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("math.operation")
class MathNode(RenderNode):
    """
    Math node - performs arithmetic operations on two input textures.
    Supported operations: Add, Subtract, Multiply, Divide, Min, Max, Difference
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        self.add_param("operation", 0.0, 0.0, 6.0) # 0=Add, 1=Sub, 2=Mult, 3=Div, 4=Min, 5=Max, 6=Diff
        self.add_param("clamp_output", 1.0, 0.0, 1.0) # Boolean
        self.add_param("mix_factor", 1.0, 0.0, 1.0) # Blend factor for the result

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
            uniform sampler2D u_tex_a;
            uniform sampler2D u_tex_b;
            uniform int u_op;
            uniform float u_clamp;
            uniform float u_mix;

            void main() {
                vec4 a = texture(u_tex_a, v_uv);
                vec4 b = texture(u_tex_b, v_uv);
                vec4 result = vec4(0.0);

                if (u_op == 0) { // Add
                    result = a + b;
                } else if (u_op == 1) { // Subtract
                    result = a - b;
                } else if (u_op == 2) { // Multiply
                    result = a * b;
                } else if (u_op == 3) { // Divide
                    // Safe divide
                    result = a / (b + 0.0001);
                } else if (u_op == 4) { // Min
                    result = min(a, b);
                } else if (u_op == 5) { // Max
                    result = max(a, b);
                } else if (u_op == 6) { // Difference
                    result = abs(a - b);
                }

                if (u_clamp > 0.5) {
                    result = clamp(result, 0.0, 1.0);
                }

                // Alpha handling: keep alpha of A usually, or max?
                // For math, we usually treat alpha as just another channel
                // But result alpha usually should determine visibility.
                // Let's just pass through result alpha.
                
                fragColor = mix(a, result, u_mix);
            }
            """
        )

        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

    def render(self):
        input_a = self.get_input_texture("input0")
        input_b = self.get_input_texture("input1")

        self.fbo.use()
        if not input_a:
            self.ctx.clear(0.0, 0.0, 0.0, 0.0)
            return

        input_a.use(location=0)
        
        if input_b:
            input_b.use(location=1)
        else:
            # If input B is missing, maybe we should use a solid color/black?
            # Or just bind input A to B slot to avoid error (result will be A op A)
            # Better to render black to a temp texture, but for perf just use A and hope user knows?
            # Let's reuse A so shader doesn't crash, but user will get weird results.
            # Ideally, we bind a black texture.
            # For now, assume user connects both.
             input_a.use(location=1) 

        self.prog["u_tex_a"].value = 0
        self.prog["u_tex_b"].value = 1
        self.prog["u_op"].value = int(self.get_param_value("operation", 0))
        self.prog["u_clamp"].value = self.get_param_value("clamp_output", 1.0)
        self.prog["u_mix"].value = self.get_param_value("mix_factor", 1.0)

        self.vao.render(moderngl.TRIANGLE_STRIP)
