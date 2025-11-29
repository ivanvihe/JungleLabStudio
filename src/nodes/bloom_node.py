"""
BloomNode - Advanced high-performance bloom effect
"""
import moderngl
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("effect.advanced_bloom")
class AdvancedBloomNode(RenderNode):
    """
    Advanced Bloom - uses downsampling for better performance and larger glow radius.
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        self.add_param("threshold", 0.6, 0.0, 1.0)
        self.add_param("intensity", 1.2, 0.0, 5.0)
        self.add_param("radius", 1.0, 0.0, 5.0) # Radius multiplier
        self.add_param("smoothness", 1.0, 0.0, 1.0) # Threshold smoothing

        # Downsampled resolution (1/4)
        self.low_res = (max(1, resolution[0] // 4), max(1, resolution[1] // 4))

        # Textures for ping-pong blur
        self.tex_a = self.ctx.texture(self.low_res, 4)
        self.tex_b = self.ctx.texture(self.low_res, 4)
        
        # FBOs
        self.fbo_a = self.ctx.framebuffer(color_attachments=[self.tex_a])
        self.fbo_b = self.ctx.framebuffer(color_attachments=[self.tex_b])

        # 1. Prefilter Shader (Threshold + Downsample)
        self.prog_prefilter = self.ctx.program(
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
            uniform sampler2D u_texture;
            uniform float u_threshold;
            uniform float u_smooth;

            void main() {
                vec3 color = texture(u_texture, v_uv).rgb;
                float brightness = max(color.r, max(color.g, color.b));
                
                float knee = u_threshold * u_smooth;
                float soft = brightness - u_threshold + knee;
                soft = clamp(soft, 0.0, 2.0 * knee);
                soft = soft * soft / (4.0 * knee + 0.00001);
                
                float contribution = max(soft, brightness - u_threshold);
                contribution /= max(brightness, 0.00001);
                
                fragColor = vec4(color * contribution, 1.0);
            }
            """
        )

        # 2. Blur Shader (Gaussian-ish)
        self.prog_blur = self.ctx.program(
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
            uniform sampler2D u_texture;
            uniform vec2 u_dir;
            uniform float u_radius;

            void main() {
                // Simple 5-tap gaussian approximation or linear sampling optimization?
                // Let's use a 9-tap optimized loop for quality
                vec2 texel = 1.0 / textureSize(u_texture, 0);
                vec3 result = texture(u_texture, v_uv).rgb * 0.227027;
                
                vec2 off1 = vec2(1.3846153846) * u_dir * texel * u_radius;
                vec2 off2 = vec2(3.2307692308) * u_dir * texel * u_radius;
                
                result += texture(u_texture, v_uv + off1).rgb * 0.3162162162;
                result += texture(u_texture, v_uv - off1).rgb * 0.3162162162;
                result += texture(u_texture, v_uv + off2).rgb * 0.0702702703;
                result += texture(u_texture, v_uv - off2).rgb * 0.0702702703;
                
                fragColor = vec4(result, 1.0);
            }
            """
        )

        # 3. Composite Shader (Upsample + Add)
        self.prog_composite = self.ctx.program(
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
            uniform sampler2D u_scene;
            uniform sampler2D u_bloom;
            uniform float u_intensity;

            void main() {
                vec4 scene = texture(u_scene, v_uv);
                vec3 bloom = texture(u_bloom, v_uv).rgb;
                
                // Additive blending
                fragColor = vec4(scene.rgb + bloom * u_intensity, scene.a);
            }
            """
        )

        self.vao = self.ctx.vertex_array(
            self.prog_prefilter,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

    def render(self):
        input_tex = self.get_input_texture("input0")
        if not input_tex:
            self.fbo.use()
            self.ctx.clear()
            return

        # 1. Prefilter (Downsample + Threshold) -> Write to A
        self.fbo_a.use()
        input_tex.use(location=0)
        self.prog_prefilter["u_texture"].value = 0
        self.prog_prefilter["u_threshold"].value = self.get_param_value("threshold", 0.6)
        self.prog_prefilter["u_smooth"].value = self.get_param_value("smoothness", 0.5)
        self.vao.render(moderngl.TRIANGLE_STRIP)

        # 2. Blur Horizontal -> Write to B
        self.fbo_b.use()
        self.tex_a.use(location=0)
        self.prog_blur["u_texture"].value = 0
        self.prog_blur["u_dir"].value = (1.0, 0.0)
        self.prog_blur["u_radius"].value = self.get_param_value("radius", 1.0)
        self.vao.render(moderngl.TRIANGLE_STRIP)

        # 3. Blur Vertical -> Write to A (Ping Pong)
        self.fbo_a.use()
        self.tex_b.use(location=0)
        self.prog_blur["u_texture"].value = 0
        self.prog_blur["u_dir"].value = (0.0, 1.0)
        self.vao.render(moderngl.TRIANGLE_STRIP)

        # 4. Composite -> Write to Output FBO
        self.fbo.use()
        input_tex.use(location=0)
        self.tex_a.use(location=1) # The blurred result is in A
        self.prog_composite["u_scene"].value = 0
        self.prog_composite["u_bloom"].value = 1
        self.prog_composite["u_intensity"].value = self.get_param_value("intensity", 1.0)
        self.vao.render(moderngl.TRIANGLE_STRIP)

    def resize(self, resolution: tuple[int, int]):
        super().resize(resolution)
        self.low_res = (max(1, resolution[0] // 4), max(1, resolution[1] // 4))
        # Recreate internal textures
        self.tex_a = self.ctx.texture(self.low_res, 4)
        self.tex_b = self.ctx.texture(self.low_res, 4)
        self.fbo_a = self.ctx.framebuffer(color_attachments=[self.tex_a])
        self.fbo_b = self.ctx.framebuffer(color_attachments=[self.tex_b])
