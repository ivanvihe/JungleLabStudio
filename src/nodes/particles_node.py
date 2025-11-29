"""
ParticlesNode - Particle system generator
"""
import moderngl
import numpy as np
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("particles")
class ParticlesNode(RenderNode):
    """
    Particles generator node - creates particle effects
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("count", 1000.0, 100.0, 10000.0)
        self.add_param("speed", 1.0, 0.1, 5.0)
        self.add_param("size", 2.0, 0.5, 10.0)
        self.add_param("color", [1.0, 1.0, 1.0, 1.0])

        # Simple particle shader
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
            uniform float u_time;
            uniform float u_count;
            uniform float u_speed;
            uniform float u_size;
            uniform vec4 u_color;

            // Simple noise function
            float hash(vec2 p) {
                return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
            }

            void main() {
                vec3 color = vec3(0.0);
                vec2 uv = v_uv;

                // Create particles
                int count = int(u_count);
                for (int i = 0; i < min(count, 200); i++) {
                    float fi = float(i);
                    float angle = hash(vec2(fi * 0.1)) * 6.28318;
                    float radius = hash(vec2(fi * 0.2)) * 0.5;
                    float speed_var = hash(vec2(fi * 0.3));

                    // Particle position
                    float t = u_time * u_speed * (0.5 + speed_var);
                    vec2 pos = vec2(
                        0.5 + cos(angle + t) * radius,
                        0.5 + sin(angle + t) * radius
                    );

                    // Distance to particle
                    float dist = length(uv - pos);
                    float particle = smoothstep(u_size / 100.0, 0.0, dist);

                    color += u_color.rgb * particle * u_color.a;
                }

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
        """Render particles"""
        self.fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)

        # Update uniforms
        self.prog["u_time"].value = self.time
        self.prog["u_count"].value = self.get_param_value("count", 1000.0)
        self.prog["u_speed"].value = self.get_param_value("speed", 1.0)
        self.prog["u_size"].value = self.get_param_value("size", 2.0)

        color = self.get_param_value("color", [1.0, 1.0, 1.0, 1.0])
        if isinstance(color, list) and len(color) >= 4:
            self.prog["u_color"].value = tuple(color)
        else:
            self.prog["u_color"].value = (1.0, 1.0, 1.0, 1.0)

        # Render
        self.vao.render(moderngl.TRIANGLE_STRIP)
