"""
PatternNode - Procedural Pattern Generator
Generate geometric patterns, tiles, and kaleidoscope effects
"""

import moderngl
from core.graph.node import GeneratorNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("generator.pattern")
class PatternNode(GeneratorNode):
    """
    Procedural pattern generator

    Creates geometric patterns, tiles, and kaleidoscope effects.
    Very popular in Shadertoy for creating hypnotic, repeating visuals.

    Parameters:
    - pattern_type: Pattern (0=Grid, 1=Hexagon, 2=Kaleidoscope, 3=Truchet, 4=Spiral)
    - scale: Pattern scale/tile size
    - rotation: Pattern rotation
    - symmetry: Symmetry amount (for kaleidoscope)
    - thickness: Line/shape thickness
    - animate: Animate pattern
    - color_mode: Coloring mode (0=Monochrome, 1=Gradient, 2=Rainbow)
    - color_a, color_b: Color gradient
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        self.add_param('pattern_type', 0.0, 0.0, 4.0)
        self.add_param('scale', 5.0, 1.0, 20.0)
        self.add_param('rotation', 0.0, 0.0, 6.28)
        self.add_param('symmetry', 6.0, 2.0, 12.0)
        self.add_param('thickness', 0.1, 0.01, 0.5)
        self.add_param('animate', 1.0, 0.0, 1.0)
        self.add_param('color_mode', 1.0, 0.0, 2.0)
        self.add_param('color_a', [0.0, 0.1, 0.3], [0.0, 0.0, 0.0], [1.0, 1.0, 1.0])
        self.add_param('color_b', [1.0, 0.6, 0.2], [0.0, 0.0, 0.0], [1.0, 1.0, 1.0])

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
        uniform int u_pattern_type;
        uniform float u_scale;
        uniform float u_rotation;
        uniform float u_symmetry;
        uniform float u_thickness;
        uniform float u_animate;
        uniform int u_color_mode;
        uniform vec3 u_color_a;
        uniform vec3 u_color_b;

        #define PI 3.14159265359

        // Rotation matrix
        mat2 rot(float a) {
            float c = cos(a);
            float s = sin(a);
            return mat2(c, -s, s, c);
        }

        // Rainbow palette
        vec3 palette(float t) {
            vec3 a = vec3(0.5, 0.5, 0.5);
            vec3 b = vec3(0.5, 0.5, 0.5);
            vec3 c = vec3(1.0, 1.0, 1.0);
            vec3 d = vec3(0.0, 0.33, 0.67);
            return a + b * cos(6.28318 * (c * t + d));
        }

        // Grid pattern
        float gridPattern(vec2 uv) {
            vec2 grid = fract(uv) - 0.5;
            float d = max(abs(grid.x), abs(grid.y));
            return smoothstep(0.5 - u_thickness, 0.5, d);
        }

        // Hexagon tiling
        float hexPattern(vec2 uv) {
            // Hexagonal coordinates
            vec2 r = vec2(1.0, 1.732);
            vec2 h = r * 0.5;

            vec2 a = mod(uv, r) - h;
            vec2 b = mod(uv - h, r) - h;

            vec2 gv = length(a) < length(b) ? a : b;

            float d = length(gv);
            return smoothstep(0.3 + u_thickness, 0.3, d);
        }

        // Kaleidoscope pattern
        float kaleidoscopePattern(vec2 uv) {
            float angle = atan(uv.y, uv.x);
            float radius = length(uv);

            // Create symmetry
            float slice = PI * 2.0 / u_symmetry;
            angle = mod(angle, slice);
            angle = abs(angle - slice * 0.5);

            // Convert back to cartesian
            vec2 kaleido = vec2(cos(angle), sin(angle)) * radius;

            // Create pattern in the slice
            vec2 grid = fract(kaleido * 2.0) - 0.5;
            float d = length(grid);

            return smoothstep(0.3 + u_thickness, 0.3, d);
        }

        // Truchet tiles
        float truchetPattern(vec2 uv) {
            vec2 grid = floor(uv);
            vec2 local = fract(uv);

            // Pseudo-random rotation per tile
            float random = fract(sin(dot(grid, vec2(12.9898, 78.233))) * 43758.5453);

            if (random > 0.5) {
                local = 1.0 - local;
            }

            // Circle arc in each tile
            vec2 center1 = vec2(0.0, 0.0);
            vec2 center2 = vec2(1.0, 1.0);

            float d1 = abs(length(local - center1) - 0.5);
            float d2 = abs(length(local - center2) - 0.5);

            float d = min(d1, d2);
            return smoothstep(u_thickness, 0.0, d);
        }

        // Spiral pattern
        float spiralPattern(vec2 uv) {
            float angle = atan(uv.y, uv.x);
            float radius = length(uv);

            // Logarithmic spiral
            float spiral = angle + log(radius + 0.1) * 2.0;

            float pattern = sin(spiral * u_scale * 0.5) * 0.5 + 0.5;
            return smoothstep(0.5 - u_thickness, 0.5 + u_thickness, pattern);
        }

        void main() {
            // Normalized coordinates
            vec2 uv = (v_uv - 0.5) * 2.0;
            uv.x *= u_resolution.x / u_resolution.y;

            // Animation
            float time = u_animate > 0.5 ? u_time : 0.0;

            // Apply rotation
            float angle = u_rotation + time * 0.2;
            uv = uv * rot(angle);

            // Scale
            uv *= u_scale;

            // Add time-based transformation for some patterns
            if (u_animate > 0.5) {
                uv += vec2(sin(time * 0.3), cos(time * 0.4)) * 0.5;
            }

            // Calculate pattern
            float pattern = 0.0;

            if (u_pattern_type == 0) {
                pattern = gridPattern(uv);
            } else if (u_pattern_type == 1) {
                pattern = hexPattern(uv);
            } else if (u_pattern_type == 2) {
                pattern = kaleidoscopePattern(uv);
            } else if (u_pattern_type == 3) {
                pattern = truchetPattern(uv);
            } else {
                pattern = spiralPattern(uv);
            }

            // Apply coloring
            vec3 col = vec3(0.0);

            if (u_color_mode == 0) {
                // Monochrome
                col = vec3(pattern);
            } else if (u_color_mode == 1) {
                // Gradient
                col = mix(u_color_a, u_color_b, pattern);
            } else {
                // Rainbow
                float t = pattern + time * 0.1;
                col = palette(t);
            }

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
            print(f"PatternNode: Shader compilation failed: {e}")
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
        self.program['u_pattern_type'].value = int(self.get_param_value('pattern_type'))
        self.program['u_scale'].value = self.get_param_value('scale')
        self.program['u_rotation'].value = self.get_param_value('rotation')
        self.program['u_symmetry'].value = self.get_param_value('symmetry')
        self.program['u_thickness'].value = self.get_param_value('thickness')
        self.program['u_animate'].value = self.get_param_value('animate')
        self.program['u_color_mode'].value = int(self.get_param_value('color_mode'))
        self.program['u_color_a'].value = tuple(self.get_param_value('color_a'))
        self.program['u_color_b'].value = tuple(self.get_param_value('color_b'))

        self.vao.render(moderngl.TRIANGLE_STRIP)
