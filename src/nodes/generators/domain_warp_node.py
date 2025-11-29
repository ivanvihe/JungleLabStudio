"""
DomainWarpNode - Domain Warping Effect Generator
Create organic patterns using domain warping technique
"""

import moderngl
from core.graph.node import GeneratorNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("generator.domain_warp")
class DomainWarpNode(GeneratorNode):
    """
    Domain warping generator

    Creates organic, flowing patterns by warping noise domains.
    Very popular technique in Shadertoy for creating marble, clouds, etc.

    Parameters:
    - scale: Overall pattern scale
    - warp_amount: Amount of domain warping
    - octaves: Number of noise octaves
    - lacunarity: Frequency multiplier per octave
    - persistence: Amplitude multiplier per octave
    - warp_octaves: Number of warping iterations
    - color_a, color_b: Color gradient
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        self.add_param('scale', 3.0, 0.5, 10.0)
        self.add_param('warp_amount', 1.0, 0.0, 5.0)
        self.add_param('octaves', 4.0, 1.0, 8.0)
        self.add_param('lacunarity', 2.0, 1.0, 4.0)
        self.add_param('persistence', 0.5, 0.0, 1.0)
        self.add_param('warp_octaves', 2.0, 1.0, 5.0)
        self.add_param('color_a', [0.0, 0.1, 0.3], [0.0, 0.0, 0.0], [1.0, 1.0, 1.0])
        self.add_param('color_b', [1.0, 0.8, 0.5], [0.0, 0.0, 0.0], [1.0, 1.0, 1.0])

        vertex_shader = """
        #version 330
        in vec2 in_pos;
        in vec2 in_uv;
        out vec2 v_uv;
        void main() {
            v_uv = in_uv;
            gl_Position = vec4(in_pos, 0.0, 1.0);
        }
        """

        fragment_shader = """
        #version 330
        in vec2 v_uv;
        out vec4 fragColor;

        uniform float u_time;
        uniform vec2 u_resolution;
        uniform float u_scale;
        uniform float u_warp_amount;
        uniform int u_octaves;
        uniform float u_lacunarity;
        uniform float u_persistence;
        uniform int u_warp_octaves;
        uniform vec3 u_color_a;
        uniform vec3 u_color_b;

        // Hash for noise
        vec2 hash22(vec2 p) {
            vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973));
            p3 += dot(p3, p3.yzx + 33.33);
            return fract((p3.xx + p3.yz) * p3.zy);
        }

        // Perlin noise
        float perlin(vec2 p) {
            vec2 i = floor(p);
            vec2 f = fract(p);
            vec2 u = f * f * (3.0 - 2.0 * f);

            return mix(
                mix(
                    dot(hash22(i + vec2(0.0, 0.0)) * 2.0 - 1.0, f - vec2(0.0, 0.0)),
                    dot(hash22(i + vec2(1.0, 0.0)) * 2.0 - 1.0, f - vec2(1.0, 0.0)),
                    u.x
                ),
                mix(
                    dot(hash22(i + vec2(0.0, 1.0)) * 2.0 - 1.0, f - vec2(0.0, 1.0)),
                    dot(hash22(i + vec2(1.0, 1.0)) * 2.0 - 1.0, f - vec2(1.0, 1.0)),
                    u.x
                ),
                u.y
            );
        }

        // FBM (Fractal Brownian Motion)
        float fbm(vec2 p) {
            float value = 0.0;
            float amplitude = 0.5;
            float frequency = 1.0;

            for (int i = 0; i < u_octaves; i++) {
                value += amplitude * perlin(p * frequency);
                frequency *= u_lacunarity;
                amplitude *= u_persistence;
            }

            return value;
        }

        // Domain warping
        float domainWarp(vec2 p) {
            vec2 q = vec2(
                fbm(p + vec2(0.0, 0.0)),
                fbm(p + vec2(5.2, 1.3))
            );

            // Apply warping iterations
            for (int i = 0; i < u_warp_octaves; i++) {
                vec2 r = vec2(
                    fbm(p + u_warp_amount * q + vec2(1.7 + float(i) * 2.0, 9.2)),
                    fbm(p + u_warp_amount * q + vec2(8.3 + float(i) * 1.5, 2.8))
                );
                q = r;
            }

            return fbm(p + u_warp_amount * q);
        }

        void main() {
            vec2 uv = v_uv * u_scale;
            uv.x *= u_resolution.x / u_resolution.y;

            // Add time animation
            uv += u_time * 0.05;

            // Domain warped noise
            float value = domainWarp(uv);

            // Normalize
            value = value * 0.5 + 0.5;

            // Colorize
            vec3 col = mix(u_color_a, u_color_b, value);

            // Add some contrast
            col = pow(col, vec3(1.2));

            fragColor = vec4(col, 1.0);
        }
        """

        try:
            self.program = self.ctx.program(
                vertex_shader=vertex_shader,
                fragment_shader=fragment_shader
            )
            self.vao = self.ctx.vertex_array(
                self.program,
                [(self.quad_vbo, '2f 2f', 'in_pos', 'in_uv')]
            )
        except Exception as e:
            print(f"DomainWarpNode: Shader compilation failed: {e}")
            self.program = None
            self.vao = None

    def render(self):
        if not self.program or not self.vao:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        self.fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 0.0)

        self.program['u_time'].value = self.time
        self.program['u_resolution'].value = self.resolution
        self.program['u_scale'].value = self.get_param_value('scale')
        self.program['u_warp_amount'].value = self.get_param_value('warp_amount')
        self.program['u_octaves'].value = int(self.get_param_value('octaves'))
        self.program['u_lacunarity'].value = self.get_param_value('lacunarity')
        self.program['u_persistence'].value = self.get_param_value('persistence')
        self.program['u_warp_octaves'].value = int(self.get_param_value('warp_octaves'))
        self.program['u_color_a'].value = tuple(self.get_param_value('color_a'))
        self.program['u_color_b'].value = tuple(self.get_param_value('color_b'))

        self.vao.render(moderngl.TRIANGLE_STRIP)
