"""
FeedbackNode - Temporal feedback effect
"""
import moderngl
import numpy as np
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("effect.feedback")
class FeedbackNode(RenderNode):
    """
    Feedback effect node - creates temporal feedback loops
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("amount", 0.95, 0.0, 1.0)
        self.add_param("zoom", 1.02, 0.95, 1.1)
        self.add_param("rotation", 0.01, -0.1, 0.1)
        self.add_param("offset_x", 0.0, -0.1, 0.1)
        self.add_param("offset_y", 0.0, -0.1, 0.1)

        # Feedback buffer
        self.feedback_tex = self.ctx.texture(resolution, 4)
        self.feedback_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.feedback_fbo = self.ctx.framebuffer(color_attachments=[self.feedback_tex])

        # Feedback shader
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
            uniform sampler2D u_feedback;
            uniform float u_amount;
            uniform float u_zoom;
            uniform float u_rotation;
            uniform vec2 u_offset;

            void main() {
                vec2 uv = v_uv - 0.5;

                // Apply zoom
                uv *= u_zoom;

                // Apply rotation
                float angle = u_rotation;
                float c = cos(angle);
                float s = sin(angle);
                mat2 rot = mat2(c, -s, s, c);
                uv = rot * uv;

                // Apply offset
                uv += u_offset;
                uv += 0.5;

                // Mix input with feedback
                vec4 inputColor = texture(u_input, v_uv);
                vec4 feedbackColor = texture(u_feedback, uv);

                fragColor = mix(inputColor, feedbackColor, u_amount);
            }
            """
        )

        # Create VAO
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

    def render(self):
        """Render feedback effect"""
        input_tex = self.get_input_texture("input0")

        if not input_tex:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        # Render with feedback
        self.fbo.use()
        input_tex.use(location=0)
        self.feedback_tex.use(location=1)

        self.prog["u_input"].value = 0
        self.prog["u_feedback"].value = 1
        self.prog["u_amount"].value = self.get_param_value("amount", 0.95)
        self.prog["u_zoom"].value = self.get_param_value("zoom", 1.02)
        self.prog["u_rotation"].value = self.get_param_value("rotation", 0.01)
        self.prog["u_offset"].value = (
            self.get_param_value("offset_x", 0.0),
            self.get_param_value("offset_y", 0.0)
        )

        self.vao.render(moderngl.TRIANGLE_STRIP)

        # Copy output to feedback buffer for next frame
        self.feedback_fbo.use()
        self.texture.use(location=0)
        self.ctx.copy_framebuffer(self.feedback_fbo, self.fbo)
