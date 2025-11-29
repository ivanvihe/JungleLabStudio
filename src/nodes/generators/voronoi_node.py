"""
VoronoiNode - Voronoi/Cellular Pattern Generator
Generate Voronoi diagrams and cellular patterns
"""

import moderngl
from core.graph.node import GeneratorNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("generator.voronoi")
class VoronoiNode(GeneratorNode):
    """
    Voronoi/Cellular pattern generator

    Creates Voronoi diagrams and cellular patterns commonly seen in Shadertoy.

    Parameters:
    - scale: Pattern scale
    - mode: Visualization mode (0=Distance, 1=Cells, 2=Edges, 3=Both)
    - color_mode: Coloring (0=Distance, 1=Random, 2=Gradient)
    - animate: Animate cells
    - edge_thickness: Edge line thickness
    - distance_power: Distance function power
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        self.add_param('scale', 5.0, 1.0, 20.0)
        self.add_param('mode', 0.0, 0.0, 3.0)
        self.add_param('color_mode', 0.0, 0.0, 2.0)
        self.add_param('animate', 1.0, 0.0, 1.0)
        self.add_param('edge_thickness', 0.05, 0.01, 0.2)
        self.add_param('distance_power', 2.0, 1.0, 4.0)

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
        uniform int u_mode;
        uniform int u_color_mode;
        uniform float u_animate;
        uniform float u_edge_thickness;
        uniform float u_distance_power;

        // Hash function for random cell points
        vec2 hash22(vec2 p) {
            vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973));
            p3 += dot(p3, p3.yzx + 33.33);
            return fract((p3.xx + p3.yz) * p3.zy);
        }

        // Color palette
        vec3 palette(float t) {
            vec3 a = vec3(0.5, 0.5, 0.5);
            vec3 b = vec3(0.5, 0.5, 0.5);
            vec3 c = vec3(1.0, 1.0, 1.0);
            vec3 d = vec3(0.0, 0.33, 0.67);
            return a + b * cos(6.28318 * (c * t + d));
        }

        // Voronoi distance field
        vec3 voronoi(vec2 uv) {
            vec2 i = floor(uv);
            vec2 f = fract(uv);

            float minDist = 1.0;
            float minDist2 = 1.0;
            vec2 minPoint = vec2(0.0);
            vec2 minCell = vec2(0.0);

            // Check neighboring cells (3x3 grid)
            for (int y = -1; y <= 1; y++) {
                for (int x = -1; x <= 1; x++) {
                    vec2 neighbor = vec2(float(x), float(y));
                    vec2 cell = i + neighbor;

                    // Random point in this cell
                    vec2 point = hash22(cell);

                    // Animate
                    if (u_animate > 0.5) {
                        point += sin(u_time + point * 6.28) * 0.2;
                    }

                    vec2 diff = neighbor + point - f;
                    float dist = pow(length(diff), u_distance_power);

                    if (dist < minDist) {
                        minDist2 = minDist;
                        minDist = dist;
                        minPoint = point;
                        minCell = cell;
                    } else if (dist < minDist2) {
                        minDist2 = dist;
                    }
                }
            }

            // Return (minDist, minDist2, cellId)
            return vec3(minDist, minDist2, hash22(minCell).x);
        }

        void main() {
            vec2 uv = v_uv * u_scale;

            // Calculate Voronoi
            vec3 vor = voronoi(uv);
            float minDist = vor.x;
            float minDist2 = vor.y;
            float cellId = vor.z;

            vec3 col = vec3(0.0);

            // Visualization modes
            if (u_mode == 0) {
                // Distance field
                col = vec3(minDist);
            } else if (u_mode == 1) {
                // Cells colored
                if (u_color_mode == 0) {
                    col = vec3(minDist);
                } else if (u_color_mode == 1) {
                    col = palette(cellId);
                } else {
                    col = palette(minDist * 3.0);
                }
            } else if (u_mode == 2) {
                // Edges only
                float edge = smoothstep(0.0, u_edge_thickness, minDist2 - minDist);
                col = vec3(1.0 - edge);
            } else {
                // Cells + Edges
                if (u_color_mode == 0) {
                    col = vec3(minDist);
                } else if (u_color_mode == 1) {
                    col = palette(cellId);
                } else {
                    col = palette(minDist * 3.0);
                }

                // Add edges
                float edge = smoothstep(0.0, u_edge_thickness, minDist2 - minDist);
                col = mix(vec3(0.0), col, edge);
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
            print(f"VoronoiNode: Shader compilation failed: {e}")
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
        self.program['u_mode'].value = int(self.get_param_value('mode'))
        self.program['u_color_mode'].value = int(self.get_param_value('color_mode'))
        self.program['u_animate'].value = self.get_param_value('animate')
        self.program['u_edge_thickness'].value = self.get_param_value('edge_thickness')
        self.program['u_distance_power'].value = self.get_param_value('distance_power')

        self.vao.render(moderngl.TRIANGLE_STRIP)
