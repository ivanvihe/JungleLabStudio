"""
GlowNode - Glow/bloom post-processing effect
"""
import moderngl
import numpy as np
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("effect.glow")
class GlowNode(RenderNode):
    """
    Glow/bloom effect node - adds luminous glow to bright areas
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("threshold", 0.7, 0.0, 1.0)
        self.add_param("intensity", 1.5, 0.0, 5.0)
        self.add_param("radius", 8.0, 1.0, 16.0)

        # Threshold shader (extract bright areas)
        self.threshold_prog = self.ctx.program(
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
            uniform float u_threshold;

            void main() {
                vec4 color = texture(u_input, v_uv);
                float brightness = dot(color.rgb, vec3(0.2126, 0.7152, 0.0722));

                if (brightness > u_threshold) {
                    fragColor = color;
                } else {
                    fragColor = vec4(0.0, 0.0, 0.0, 0.0);
                }
            }
            """
        )

        # Blur shader (gaussian blur for glow)
        self.blur_prog = self.ctx.program(
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
            uniform vec2 u_direction;
            uniform float u_radius;

            void main() {
                vec2 resolution = textureSize(u_input, 0);
                vec2 texel_size = 1.0 / resolution;

                vec4 color = vec4(0.0);
                float total_weight = 0.0;

                // Gaussian blur kernel
                for (float i = -u_radius; i <= u_radius; i += 1.0) {
                    float weight = exp(-0.5 * (i * i) / (u_radius * u_radius));
                    vec2 offset = i * u_direction * texel_size;
                    color += texture(u_input, v_uv + offset) * weight;
                    total_weight += weight;
                }

                fragColor = color / total_weight;
            }
            """
        )

        # Composite shader (blend glow with original)
        self.composite_prog = self.ctx.program(
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
            uniform sampler2D u_original;
            uniform sampler2D u_glow;
            uniform float u_intensity;

            void main() {
                vec4 original = texture(u_original, v_uv);
                vec4 glow = texture(u_glow, v_uv);

                fragColor = original + glow * u_intensity;
                fragColor.a = original.a;
            }
            """
        )

        # Create intermediate textures and FBOs
        self.threshold_tex = self.ctx.texture(resolution, 4)
        self.threshold_fbo = self.ctx.framebuffer(color_attachments=[self.threshold_tex])

        self.blur_h_tex = self.ctx.texture(resolution, 4)
        self.blur_h_fbo = self.ctx.framebuffer(color_attachments=[self.blur_h_tex])

        self.blur_v_tex = self.ctx.texture(resolution, 4)
        self.blur_v_fbo = self.ctx.framebuffer(color_attachments=[self.blur_v_tex])

        # Create VAO
        self.vao = self.ctx.vertex_array(
            self.threshold_prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

    def render(self):
        """Render glow effect with multi-pass pipeline"""
        input_tex = self.get_input_texture("input0")

        if not input_tex:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        # Pass 1: Extract bright areas
        self.threshold_fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 0.0)
        input_tex.use(location=0)

        self.threshold_prog["u_input"].value = 0
        self.threshold_prog["u_threshold"].value = self.get_param_value("threshold", 0.7)
        self.vao.render(moderngl.TRIANGLE_STRIP)

        # Pass 2: Horizontal blur
        self.blur_h_fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 0.0)
        self.threshold_tex.use(location=0)

        vao_blur_h = self.ctx.vertex_array(
            self.blur_prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )
        self.blur_prog["u_input"].value = 0
        self.blur_prog["u_direction"].value = (1.0, 0.0)
        self.blur_prog["u_radius"].value = self.get_param_value("radius", 8.0)
        vao_blur_h.render(moderngl.TRIANGLE_STRIP)

        # Pass 3: Vertical blur
        self.blur_v_fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 0.0)
        self.blur_h_tex.use(location=0)

        vao_blur_v = self.ctx.vertex_array(
            self.blur_prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )
        self.blur_prog["u_direction"].value = (0.0, 1.0)
        vao_blur_v.render(moderngl.TRIANGLE_STRIP)

        # Pass 4: Composite glow with original
        self.fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 0.0)
        input_tex.use(location=0)
        self.blur_v_tex.use(location=1)

        vao_composite = self.ctx.vertex_array(
            self.composite_prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )
        self.composite_prog["u_original"].value = 0
        self.composite_prog["u_glow"].value = 1
        self.composite_prog["u_intensity"].value = self.get_param_value("intensity", 1.5)
        vao_composite.render(moderngl.TRIANGLE_STRIP)
