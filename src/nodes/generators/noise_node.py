"""
NoiseNode - Procedural noise generator (Perlin/Simplex/Value)
"""
import moderngl
from core.graph.node import GeneratorNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("generator.noise")
class NoiseNode(GeneratorNode):
    """
    Noise generator node - creates procedural noise patterns
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("scale", 5.0, 0.1, 20.0)
        self.add_param("octaves", 4.0, 1.0, 8.0)
        self.add_param("persistence", 0.5, 0.0, 1.0)
        self.add_param("lacunarity", 2.0, 1.0, 4.0)
        self.add_param("speed", 0.5, 0.0, 5.0)
        self.add_param("color_a", [0.0, 0.0, 0.0])
        self.add_param("color_b", [1.0, 1.0, 1.0])

        # Noise shader with Simplex noise implementation
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
            uniform float u_scale;
            uniform float u_octaves;
            uniform float u_persistence;
            uniform float u_lacunarity;
            uniform float u_speed;
            uniform float u_time;
            uniform vec3 u_color_a;
            uniform vec3 u_color_b;
            uniform vec2 u_resolution;

            // Simplex noise implementation
            vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
            vec2 mod289(vec2 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
            vec3 permute(vec3 x) { return mod289(((x*34.0)+1.0)*x); }

            float snoise(vec2 v) {
                const vec4 C = vec4(0.211324865405187,
                                    0.366025403784439,
                                   -0.577350269189626,
                                    0.024390243902439);

                vec2 i  = floor(v + dot(v, C.yy));
                vec2 x0 = v -   i + dot(i, C.xx);
                vec2 i1;
                i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
                vec4 x12 = x0.xyxy + C.xxzz;
                x12.xy -= i1;

                i = mod289(i);
                vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0))
                    + i.x + vec3(0.0, i1.x, 1.0));

                vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
                m = m*m;
                m = m*m;

                vec3 x = 2.0 * fract(p * C.www) - 1.0;
                vec3 h = abs(x) - 0.5;
                vec3 ox = floor(x + 0.5);
                vec3 a0 = x - ox;

                m *= 1.79284291400159 - 0.85373472095314 * (a0*a0 + h*h);

                vec3 g;
                g.x  = a0.x  * x0.x  + h.x  * x0.y;
                g.yz = a0.yz * x12.xz + h.yz * x12.yw;
                return 130.0 * dot(m, g);
            }

            float fbm(vec2 st, float time) {
                float value = 0.0;
                float amplitude = 1.0;
                float frequency = 1.0;

                int octaves = int(u_octaves);

                for (int i = 0; i < octaves; i++) {
                    value += amplitude * snoise(st * frequency + time);
                    frequency *= u_lacunarity;
                    amplitude *= u_persistence;
                }

                return value;
            }

            void main() {
                vec2 st = v_uv * u_scale;
                float time = u_time * u_speed;

                // Generate fractal brownian motion noise
                float noise = fbm(st, time);

                // Normalize to 0-1 range
                noise = noise * 0.5 + 0.5;

                // Mix between two colors
                vec3 color = mix(u_color_a, u_color_b, noise);

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
        """Render noise pattern"""
        self.fbo.use()

        self.prog["u_scale"].value = self.get_param_value("scale", 5.0)
        self.prog["u_octaves"].value = self.get_param_value("octaves", 4.0)
        self.prog["u_persistence"].value = self.get_param_value("persistence", 0.5)
        self.prog["u_lacunarity"].value = self.get_param_value("lacunarity", 2.0)
        self.prog["u_speed"].value = self.get_param_value("speed", 0.5)
        self.prog["u_time"].value = self.time

        color_a = self.get_param_value("color_a", [0.0, 0.0, 0.0])
        color_b = self.get_param_value("color_b", [1.0, 1.0, 1.0])
        self.prog["u_color_a"].value = tuple(color_a)
        self.prog["u_color_b"].value = tuple(color_b)

        self.prog["u_resolution"].value = self.resolution

        self.vao.render(moderngl.TRIANGLE_STRIP)
