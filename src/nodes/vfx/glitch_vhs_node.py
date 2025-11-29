"""
GlitchVHSNode - VHS tape glitch effect
"""
import moderngl
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("vfx.glitch.vhs")
class GlitchVHSNode(RenderNode):
    """
    VHS glitch effect - simulates analog video tape distortion
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("intensity", 0.5, 0.0, 1.0)
        self.add_param("speed", 1.0, 0.0, 5.0)
        self.add_param("scanline_amount", 0.3, 0.0, 1.0)
        self.add_param("tracking_error", 0.2, 0.0, 1.0)
        self.add_param("color_bleed", 0.3, 0.0, 1.0)

        # VHS glitch shader
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
            uniform float u_time;
            uniform float u_intensity;
            uniform float u_speed;
            uniform float u_scanline_amount;
            uniform float u_tracking_error;
            uniform float u_color_bleed;
            uniform vec2 u_resolution;

            // Hash function for noise
            float hash(vec2 p) {
                return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
            }

            float noise(vec2 p) {
                vec2 i = floor(p);
                vec2 f = fract(p);
                f = f * f * (3.0 - 2.0 * f);
                return mix(
                    mix(hash(i + vec2(0,0)), hash(i + vec2(1,0)), f.x),
                    mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), f.x),
                    f.y
                );
            }

            void main() {
                vec2 uv = v_uv;
                float time = u_time * u_speed;

                // Tracking error (horizontal shift)
                float tracking = noise(vec2(uv.y * 10.0 + time * 0.5, time)) * u_tracking_error * u_intensity;
                uv.x += tracking * 0.1;

                // Random scanline jumps
                float scanline_jump = step(0.98, noise(vec2(uv.y * 100.0, time * 2.0))) * u_intensity;
                uv.x += scanline_jump * 0.05;

                // RGB color bleed (chromatic aberration)
                vec2 offset = vec2(u_color_bleed * u_intensity * 0.005, 0.0);
                float r = texture(u_input, uv - offset).r;
                float g = texture(u_input, uv).g;
                float b = texture(u_input, uv + offset).b;
                vec3 color = vec3(r, g, b);

                // Scanlines
                float scanlines = sin(uv.y * u_resolution.y * 2.0) * 0.5 + 0.5;
                scanlines = mix(1.0, scanlines, u_scanline_amount);
                color *= scanlines;

                // Noise grain
                float grain = noise(uv * vec2(time * 100.0)) * 0.1 * u_intensity;
                color += grain;

                // VHS tape edge darkening
                float vignette = smoothstep(0.0, 0.3, uv.x) * smoothstep(1.0, 0.7, uv.x);
                vignette *= smoothstep(0.0, 0.2, uv.y) * smoothstep(1.0, 0.8, uv.y);
                color *= mix(1.0, vignette, 0.3);

                fragColor = vec4(color, 1.0);
            }
            """
        )

        # Create VAO
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

    def render(self):
        """Render VHS glitch effect"""
        input_tex = self.get_input_texture("input0")

        if not input_tex:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        self.fbo.use()
        input_tex.use(location=0)

        self.prog["u_input"].value = 0
        self.prog["u_time"].value = self.state.time if hasattr(self, 'state') else 0.0
        self.prog["u_intensity"].value = self.get_param_value("intensity", 0.5)
        self.prog["u_speed"].value = self.get_param_value("speed", 1.0)
        self.prog["u_scanline_amount"].value = self.get_param_value("scanline_amount", 0.3)
        self.prog["u_tracking_error"].value = self.get_param_value("tracking_error", 0.2)
        self.prog["u_color_bleed"].value = self.get_param_value("color_bleed", 0.3)
        self.prog["u_resolution"].value = self.resolution

        self.vao.render(moderngl.TRIANGLE_STRIP)
