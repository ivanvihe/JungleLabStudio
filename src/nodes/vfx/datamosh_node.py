"""
DatamoshNode - Datamoshing compression artifact effect
"""
import moderngl
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("vfx.datamosh")
class DatamoshNode(RenderNode):
    """Datamoshing effect - simulates video compression artifacts"""

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)
        self.add_param("intensity", 0.5, 0.0, 1.0)
        self.add_param("speed", 1.0, 0.0, 5.0)
        self.add_param("motion_blur", 0.3, 0.0, 1.0)
        self.add_param("block_size", 16.0, 4.0, 64.0)

        # Create feedback buffer for temporal effects
        self.feedback_tex = self.ctx.texture(resolution, 4)
        self.feedback_fbo = self.ctx.framebuffer(color_attachments=[self.feedback_tex])

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
            uniform float u_time;
            uniform float u_intensity;
            uniform float u_motion_blur;
            uniform float u_block_size;
            uniform vec2 u_resolution;

            float hash(vec2 p) {
                return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
            }

            void main() {
                vec2 uv = v_uv;

                // Block-based sampling (like video codecs)
                vec2 block_uv = floor(uv * u_resolution / u_block_size) * u_block_size / u_resolution;
                float block_hash = hash(block_uv + floor(u_time * 10.0));

                // Compression artifact simulation
                vec2 sample_uv = uv;
                if (block_hash < u_intensity * 0.5) {
                    // Use previous frame (I-frame reference)
                    sample_uv = block_uv + u_block_size / u_resolution * 0.5;
                }

                vec4 current = texture(u_input, sample_uv);
                vec4 previous = texture(u_feedback, uv);

                // Motion vector displacement (P-frame simulation)
                vec2 motion = vec2(
                    hash(block_uv + 0.1) - 0.5,
                    hash(block_uv + 0.2) - 0.5
                ) * u_intensity * 0.05;

                vec4 displaced = texture(u_feedback, uv + motion);

                // Mix with feedback for temporal artifacts
                float feedback_amount = mix(u_motion_blur, u_motion_blur * 0.9, block_hash);
                vec4 color = mix(current, displaced, feedback_amount);

                // Block boundary artifacts
                vec2 block_edge = fract(uv * u_resolution / u_block_size);
                float edge = step(0.95, max(block_edge.x, block_edge.y));
                color.rgb *= 1.0 - edge * 0.3 * u_intensity;

                fragColor = color;
            }
            """
        )
        self.vao = self.ctx.vertex_array(self.prog, [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")])

    def render(self):
        input_tex = self.get_input_texture("input0")
        if not input_tex:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        self.fbo.use()
        input_tex.use(location=0)
        self.feedback_tex.use(location=1)

        self.prog["u_input"].value = 0
        self.prog["u_feedback"].value = 1
        self.prog["u_time"].value = self.state.time if hasattr(self, 'state') else 0.0
        self.prog["u_intensity"].value = self.get_param_value("intensity", 0.5)
        self.prog["u_motion_blur"].value = self.get_param_value("motion_blur", 0.3)
        self.prog["u_block_size"].value = self.get_param_value("block_size", 16.0)
        self.prog["u_resolution"].value = self.resolution

        self.vao.render(moderngl.TRIANGLE_STRIP)

        # Copy output to feedback for next frame
        self.ctx.copy_framebuffer(self.feedback_fbo, self.fbo)
