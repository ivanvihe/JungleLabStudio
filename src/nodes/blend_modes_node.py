"""
BlendModesNode - Advanced blending modes (Screen, Multiply, Overlay, etc.)
"""
import moderngl
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("composite.blend_modes")
class BlendModesNode(RenderNode):
    """
    Advanced blend modes node - supports multiple Photoshop-style blending modes
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("mode", 0.0, 0.0, 10.0)  # Blend mode selector
        self.add_param("opacity", 1.0, 0.0, 1.0)

        # Blend modes shader
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
            uniform sampler2D u_input0;  // Base layer
            uniform sampler2D u_input1;  // Blend layer
            uniform float u_mode;
            uniform float u_opacity;

            // Blend mode functions
            vec3 blend_normal(vec3 base, vec3 blend) {
                return blend;
            }

            vec3 blend_multiply(vec3 base, vec3 blend) {
                return base * blend;
            }

            vec3 blend_screen(vec3 base, vec3 blend) {
                return 1.0 - (1.0 - base) * (1.0 - blend);
            }

            vec3 blend_overlay(vec3 base, vec3 blend) {
                vec3 result;
                result.r = base.r < 0.5 ? 2.0 * base.r * blend.r : 1.0 - 2.0 * (1.0 - base.r) * (1.0 - blend.r);
                result.g = base.g < 0.5 ? 2.0 * base.g * blend.g : 1.0 - 2.0 * (1.0 - base.g) * (1.0 - blend.g);
                result.b = base.b < 0.5 ? 2.0 * base.b * blend.b : 1.0 - 2.0 * (1.0 - base.b) * (1.0 - blend.b);
                return result;
            }

            vec3 blend_add(vec3 base, vec3 blend) {
                return min(base + blend, vec3(1.0));
            }

            vec3 blend_subtract(vec3 base, vec3 blend) {
                return max(base - blend, vec3(0.0));
            }

            vec3 blend_difference(vec3 base, vec3 blend) {
                return abs(base - blend);
            }

            vec3 blend_darken(vec3 base, vec3 blend) {
                return min(base, blend);
            }

            vec3 blend_lighten(vec3 base, vec3 blend) {
                return max(base, blend);
            }

            vec3 blend_color_dodge(vec3 base, vec3 blend) {
                return base / (1.0 - blend + 0.001);
            }

            vec3 blend_color_burn(vec3 base, vec3 blend) {
                return 1.0 - (1.0 - base) / (blend + 0.001);
            }

            void main() {
                vec2 uv = v_uv;

                vec4 base = texture(u_input0, uv);
                vec4 blend = texture(u_input1, uv);

                vec3 result;
                int mode = int(u_mode);

                // Select blend mode
                if (mode == 0) {
                    result = blend_normal(base.rgb, blend.rgb);
                } else if (mode == 1) {
                    result = blend_multiply(base.rgb, blend.rgb);
                } else if (mode == 2) {
                    result = blend_screen(base.rgb, blend.rgb);
                } else if (mode == 3) {
                    result = blend_overlay(base.rgb, blend.rgb);
                } else if (mode == 4) {
                    result = blend_add(base.rgb, blend.rgb);
                } else if (mode == 5) {
                    result = blend_subtract(base.rgb, blend.rgb);
                } else if (mode == 6) {
                    result = blend_difference(base.rgb, blend.rgb);
                } else if (mode == 7) {
                    result = blend_darken(base.rgb, blend.rgb);
                } else if (mode == 8) {
                    result = blend_lighten(base.rgb, blend.rgb);
                } else if (mode == 9) {
                    result = blend_color_dodge(base.rgb, blend.rgb);
                } else {
                    result = blend_color_burn(base.rgb, blend.rgb);
                }

                // Apply opacity
                result = mix(base.rgb, result, u_opacity * blend.a);

                fragColor = vec4(result, base.a);
            }
            """
        )

        # Create VAO
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

        # Add second input for blend layer
        self.add_input("input1")

    def render(self):
        """Render blend modes"""
        input0_tex = self.get_input_texture("input0")
        input1_tex = self.get_input_texture("input1")

        if not input0_tex:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        # If no blend texture, just pass through base
        if not input1_tex:
            input1_tex = input0_tex

        self.fbo.use()
        input0_tex.use(location=0)
        input1_tex.use(location=1)

        self.prog["u_input0"].value = 0
        self.prog["u_input1"].value = 1
        self.prog["u_mode"].value = self.get_param_value("mode", 0.0)
        self.prog["u_opacity"].value = self.get_param_value("opacity", 1.0)

        self.vao.render(moderngl.TRIANGLE_STRIP)
