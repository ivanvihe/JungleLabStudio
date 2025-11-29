"""
DistortNode - UV distortion effects
"""
import moderngl
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("effect.distort")
class DistortNode(RenderNode):
    """
    Distortion effect node - warps UV coordinates
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("amount", 0.1, 0.0, 1.0)
        self.add_param("frequency", 5.0, 0.1, 20.0)
        self.add_param("speed", 1.0, 0.0, 5.0)
        self.add_param("type", 0.0, 0.0, 3.0)  # 0=wave, 1=swirl, 2=bulge, 3=ripple

        # Distortion shader
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
            uniform float u_amount;
            uniform float u_frequency;
            uniform float u_speed;
            uniform float u_type;
            uniform float u_time;
            uniform vec2 u_resolution;

            #define PI 3.14159265359

            vec2 wave_distort(vec2 uv, float time) {
                float wave_x = sin(uv.y * u_frequency + time * u_speed) * u_amount;
                float wave_y = cos(uv.x * u_frequency + time * u_speed) * u_amount;
                return uv + vec2(wave_x, wave_y);
            }

            vec2 swirl_distort(vec2 uv, float time) {
                vec2 center = vec2(0.5);
                vec2 offset = uv - center;
                float dist = length(offset);
                float angle = atan(offset.y, offset.x);

                angle += dist * u_frequency * u_amount + time * u_speed;

                return center + dist * vec2(cos(angle), sin(angle));
            }

            vec2 bulge_distort(vec2 uv, float time) {
                vec2 center = vec2(0.5);
                vec2 offset = uv - center;
                float dist = length(offset);

                float bulge = 1.0 + u_amount * sin(dist * u_frequency + time * u_speed);
                return center + offset * bulge;
            }

            vec2 ripple_distort(vec2 uv, float time) {
                vec2 center = vec2(0.5);
                float dist = distance(uv, center);

                float ripple = sin(dist * u_frequency - time * u_speed * 5.0) * u_amount;
                vec2 dir = normalize(uv - center);

                return uv + dir * ripple;
            }

            void main() {
                vec2 uv = v_uv;

                // Apply distortion based on type
                int distort_type = int(u_type);

                if (distort_type == 0) {
                    uv = wave_distort(uv, u_time);
                } else if (distort_type == 1) {
                    uv = swirl_distort(uv, u_time);
                } else if (distort_type == 2) {
                    uv = bulge_distort(uv, u_time);
                } else {
                    uv = ripple_distort(uv, u_time);
                }

                // Sample with distorted coordinates
                vec4 color = texture(u_input, uv);

                fragColor = color;
            }
            """
        )

        # Create VAO
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

    def render(self):
        """Render distortion effect"""
        input_tex = self.get_input_texture("input0")

        if not input_tex:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        self.fbo.use()
        input_tex.use(location=0)

        self.prog["u_input"].value = 0
        self.prog["u_amount"].value = self.get_param_value("amount", 0.1)
        self.prog["u_frequency"].value = self.get_param_value("frequency", 5.0)
        self.prog["u_speed"].value = self.get_param_value("speed", 1.0)
        self.prog["u_type"].value = self.get_param_value("type", 0.0)
        self.prog["u_time"].value = self.time
        self.prog["u_resolution"].value = self.resolution

        self.vao.render(moderngl.TRIANGLE_STRIP)
