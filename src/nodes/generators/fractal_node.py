"""
FractalNode - Fractal Generator
Generate Mandelbrot, Julia sets and other fractals
"""

import moderngl
from core.graph.node import GeneratorNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("generator.fractal")
class FractalNode(GeneratorNode):
    """
    Fractal generator (Mandelbrot, Julia, etc.)

    Generates various fractal patterns similar to many Shadertoy fractals.

    Parameters:
    - fractal_type: Type (0=Mandelbrot, 1=Julia, 2=Burning Ship)
    - zoom: Zoom level
    - center_x, center_y: View center
    - julia_c_x, julia_c_y: Julia set parameter (for Julia fractal)
    - max_iterations: Maximum iterations for escape
    - color_intensity: Color intensity
    - color_offset: Color phase offset
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Parameters
        self.add_param('fractal_type', 0.0, 0.0, 2.0)
        self.add_param('zoom', 1.0, 0.1, 100.0)
        self.add_param('center_x', 0.0, -2.0, 2.0)
        self.add_param('center_y', 0.0, -2.0, 2.0)
        self.add_param('julia_c_x', -0.7, -2.0, 2.0)
        self.add_param('julia_c_y', 0.27015, -2.0, 2.0)
        self.add_param('max_iterations', 100.0, 10.0, 500.0)
        self.add_param('color_intensity', 1.0, 0.0, 5.0)
        self.add_param('color_offset', 0.0, 0.0, 6.28)

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
        uniform int u_fractal_type;
        uniform float u_zoom;
        uniform vec2 u_center;
        uniform vec2 u_julia_c;
        uniform int u_max_iterations;
        uniform float u_color_intensity;
        uniform float u_color_offset;

        // Color palette (iq's palette function)
        vec3 palette(float t) {
            vec3 a = vec3(0.5, 0.5, 0.5);
            vec3 b = vec3(0.5, 0.5, 0.5);
            vec3 c = vec3(1.0, 1.0, 1.0);
            vec3 d = vec3(0.0, 0.33, 0.67);
            return a + b * cos(6.28318 * (c * t + d + u_color_offset));
        }

        // Mandelbrot fractal
        float mandelbrot(vec2 c) {
            vec2 z = vec2(0.0);
            int iterations = 0;

            for (int i = 0; i < u_max_iterations; i++) {
                // z = z^2 + c
                float x = z.x * z.x - z.y * z.y + c.x;
                float y = 2.0 * z.x * z.y + c.y;
                z = vec2(x, y);

                if (length(z) > 2.0) break;
                iterations = i;
            }

            if (iterations == u_max_iterations - 1) return 0.0;
            return float(iterations) / float(u_max_iterations);
        }

        // Julia fractal
        float julia(vec2 z) {
            int iterations = 0;

            for (int i = 0; i < u_max_iterations; i++) {
                // z = z^2 + c (where c is constant)
                float x = z.x * z.x - z.y * z.y + u_julia_c.x;
                float y = 2.0 * z.x * z.y + u_julia_c.y;
                z = vec2(x, y);

                if (length(z) > 2.0) break;
                iterations = i;
            }

            if (iterations == u_max_iterations - 1) return 0.0;
            return float(iterations) / float(u_max_iterations);
        }

        // Burning Ship fractal
        float burningShip(vec2 c) {
            vec2 z = vec2(0.0);
            int iterations = 0;

            for (int i = 0; i < u_max_iterations; i++) {
                // z = (abs(z))^2 + c
                z = abs(z);
                float x = z.x * z.x - z.y * z.y + c.x;
                float y = 2.0 * z.x * z.y + c.y;
                z = vec2(x, y);

                if (length(z) > 2.0) break;
                iterations = i;
            }

            if (iterations == u_max_iterations - 1) return 0.0;
            return float(iterations) / float(u_max_iterations);
        }

        void main() {
            // Complex plane coordinates
            vec2 uv = (v_uv - 0.5) * 2.0;
            uv.x *= u_resolution.x / u_resolution.y;

            // Apply zoom and center
            vec2 c = uv / u_zoom + u_center;

            // Calculate fractal value
            float value = 0.0;

            if (u_fractal_type == 0) {
                value = mandelbrot(c);
            } else if (u_fractal_type == 1) {
                value = julia(c);
            } else {
                value = burningShip(c);
            }

            // Colorize
            vec3 col = vec3(0.0);
            if (value > 0.0) {
                col = palette(value * u_color_intensity);
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
            print(f"FractalNode: Shader compilation failed: {e}")
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
        self.program['u_fractal_type'].value = int(self.get_param_value('fractal_type'))
        self.program['u_zoom'].value = self.get_param_value('zoom')
        self.program['u_center'].value = (
            self.get_param_value('center_x'),
            self.get_param_value('center_y')
        )
        self.program['u_julia_c'].value = (
            self.get_param_value('julia_c_x'),
            self.get_param_value('julia_c_y')
        )
        self.program['u_max_iterations'].value = int(self.get_param_value('max_iterations'))
        self.program['u_color_intensity'].value = self.get_param_value('color_intensity')
        self.program['u_color_offset'].value = self.get_param_value('color_offset')

        self.vao.render(moderngl.TRIANGLE_STRIP)
