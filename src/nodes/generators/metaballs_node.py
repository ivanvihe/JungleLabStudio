"""
MetaballsNode - Metaballs/Blob Effect Generator
Generate organic blob effects using metaballs
"""

import moderngl
from core.graph.node import GeneratorNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("generator.metaballs")
class MetaballsNode(GeneratorNode):
    """
    Metaballs/blob effect generator

    Creates organic liquid blob effects using metaballs technique.
    Very popular in Shadertoy for creating organic, flowing visuals.

    Parameters:
    - num_balls: Number of metaballs (2-8)
    - threshold: Blob merge threshold
    - ball_size: Individual ball size
    - animation_speed: Ball movement speed
    - animation_chaos: Movement randomness
    - color_a, color_b: Color gradient for blobs
    - glow: Glow/soft edge amount
    - smoothness: Edge smoothness
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        self.add_param('num_balls', 5.0, 2.0, 8.0)
        self.add_param('threshold', 1.0, 0.3, 3.0)
        self.add_param('ball_size', 0.3, 0.1, 1.0)
        self.add_param('animation_speed', 1.0, 0.0, 3.0)
        self.add_param('animation_chaos', 1.0, 0.0, 2.0)
        self.add_param('color_a', [0.1, 0.2, 0.5], [0.0, 0.0, 0.0], [1.0, 1.0, 1.0])
        self.add_param('color_b', [0.9, 0.4, 0.7], [0.0, 0.0, 0.0], [1.0, 1.0, 1.0])
        self.add_param('glow', 0.5, 0.0, 2.0)
        self.add_param('smoothness', 0.1, 0.01, 0.5)

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
        uniform int u_num_balls;
        uniform float u_threshold;
        uniform float u_ball_size;
        uniform float u_animation_speed;
        uniform float u_animation_chaos;
        uniform vec3 u_color_a;
        uniform vec3 u_color_b;
        uniform float u_glow;
        uniform float u_smoothness;

        // Hash function for pseudo-random numbers
        float hash(float n) {
            return fract(sin(n) * 43758.5453123);
        }

        vec2 hash2(float n) {
            return vec2(
                hash(n),
                hash(n + 1.0)
            );
        }

        // Smooth minimum for organic blending
        float smin(float a, float b, float k) {
            float h = max(k - abs(a - b), 0.0) / k;
            return min(a, b) - h * h * k * 0.25;
        }

        // Get metaball position
        vec2 getBallPosition(int id, float time) {
            float seed = float(id);

            // Different movement patterns for each ball
            float angle = time * u_animation_speed + seed * 6.28;
            float radius = 0.3 + hash(seed) * 0.4;

            // Add some chaos
            vec2 offset = hash2(seed + 10.0) * 2.0 - 1.0;
            float chaosAngle = time * u_animation_speed * (hash(seed + 20.0) * 2.0 - 1.0) * u_animation_chaos;

            vec2 pos = vec2(
                cos(angle) * radius + offset.x * 0.2 * sin(chaosAngle),
                sin(angle * 1.3) * radius + offset.y * 0.2 * cos(chaosAngle * 0.7)
            );

            return pos;
        }

        // Metaball field calculation
        float metaballField(vec2 uv, float time) {
            float sum = 0.0;

            for (int i = 0; i < 8; i++) {
                if (i >= u_num_balls) break;

                vec2 ballPos = getBallPosition(i, time);
                float dist = length(uv - ballPos);

                // Metaball influence (1/r falloff)
                float influence = u_ball_size / (dist + 0.001);
                sum += influence;
            }

            return sum;
        }

        // Color palette
        vec3 palette(float t) {
            return mix(u_color_a, u_color_b, t);
        }

        void main() {
            // Normalized coordinates (-1 to 1)
            vec2 uv = (v_uv - 0.5) * 2.0;
            uv.x *= u_resolution.x / u_resolution.y;

            float time = u_time;

            // Calculate metaball field
            float field = metaballField(uv, time);

            // Apply threshold for blob shape
            float blob = smoothstep(u_threshold - u_smoothness, u_threshold + u_smoothness, field);

            // Color based on field strength
            float colorMix = clamp((field - u_threshold) / u_threshold, 0.0, 1.0);
            vec3 col = palette(colorMix);

            // Apply blob mask
            col *= blob;

            // Add glow
            float glow = smoothstep(u_threshold * 0.3, u_threshold, field) * (1.0 - blob);
            col += palette(colorMix * 0.5) * glow * u_glow;

            // Add some highlight on edges
            float edge = smoothstep(u_threshold, u_threshold + u_smoothness * 2.0, field);
            col += vec3(1.0) * edge * (1.0 - edge) * 4.0 * u_glow * 0.3;

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
            print(f"MetaballsNode: Shader compilation failed: {e}")
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
        self.program['u_num_balls'].value = int(self.get_param_value('num_balls'))
        self.program['u_threshold'].value = self.get_param_value('threshold')
        self.program['u_ball_size'].value = self.get_param_value('ball_size')
        self.program['u_animation_speed'].value = self.get_param_value('animation_speed')
        self.program['u_animation_chaos'].value = self.get_param_value('animation_chaos')
        self.program['u_color_a'].value = tuple(self.get_param_value('color_a'))
        self.program['u_color_b'].value = tuple(self.get_param_value('color_b'))
        self.program['u_glow'].value = self.get_param_value('glow')
        self.program['u_smoothness'].value = self.get_param_value('smoothness')

        self.vao.render(moderngl.TRIANGLE_STRIP)
