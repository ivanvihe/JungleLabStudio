"""
GeometryNode - Procedural geometry generator
"""
import moderngl
import numpy as np
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("geometry")
class GeometryNode(RenderNode):
    """
    Geometry generator node - creates procedural geometric shapes
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Add parameters
        self.add_param("shape", 0.0, 0.0, 4.0)  # 0=circle, 1=square, 2=triangle, 3=hexagon, 4=star
        self.add_param("size", 0.5, 0.1, 1.0)
        self.add_param("thickness", 0.05, 0.0, 0.5)
        self.add_param("rotation", 0.0, 0.0, 6.28318)
        self.add_param("color", [1.0, 1.0, 1.0, 1.0])

        # Geometry shader
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
            uniform int u_shape;
            uniform float u_size;
            uniform float u_thickness;
            uniform float u_rotation;
            uniform vec4 u_color;

            #define PI 3.14159265359

            float sdCircle(vec2 p, float r) {
                return length(p) - r;
            }

            float sdBox(vec2 p, vec2 b) {
                vec2 d = abs(p) - b;
                return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
            }

            float sdTriangle(vec2 p, float r) {
                const float k = sqrt(3.0);
                p.x = abs(p.x) - r;
                p.y = p.y + r / k;
                if (p.x + k * p.y > 0.0) p = vec2(p.x - k * p.y, -k * p.x - p.y) / 2.0;
                p.x -= clamp(p.x, -2.0 * r, 0.0);
                return -length(p) * sign(p.y);
            }

            float sdHexagon(vec2 p, float r) {
                const vec3 k = vec3(-0.866025404, 0.5, 0.577350269);
                p = abs(p);
                p -= 2.0 * min(dot(k.xy, p), 0.0) * k.xy;
                p -= vec2(clamp(p.x, -k.z * r, k.z * r), r);
                return length(p) * sign(p.y);
            }

            float sdStar(vec2 p, float r, int n, float m) {
                float an = PI / float(n);
                float en = PI / m;
                vec2 acs = vec2(cos(an), sin(an));
                vec2 ecs = vec2(cos(en), sin(en));

                float bn = mod(atan(p.x, p.y), 2.0 * an) - an;
                p = length(p) * vec2(cos(bn), abs(sin(bn)));
                p -= r * acs;
                p += ecs * clamp(-dot(p, ecs), 0.0, r * acs.y / ecs.y);
                return length(p) * sign(p.x);
            }

            void main() {
                vec2 uv = v_uv - 0.5;

                // Apply rotation
                float c = cos(u_rotation);
                float s = sin(u_rotation);
                mat2 rot = mat2(c, -s, s, c);
                uv = rot * uv;

                float dist = 0.0;

                if (u_shape == 0) {
                    // Circle
                    dist = sdCircle(uv, u_size);
                } else if (u_shape == 1) {
                    // Square
                    dist = sdBox(uv, vec2(u_size));
                } else if (u_shape == 2) {
                    // Triangle
                    dist = sdTriangle(uv, u_size);
                } else if (u_shape == 3) {
                    // Hexagon
                    dist = sdHexagon(uv, u_size);
                } else {
                    // Star
                    dist = sdStar(uv, u_size, 5, 2.5);
                }

                // Create shape with thickness
                float alpha = 1.0 - smoothstep(u_thickness - 0.01, u_thickness + 0.01, abs(dist));

                fragColor = vec4(u_color.rgb, alpha * u_color.a);
            }
            """
        )

        # Create VAO
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )

    def render(self):
        """Render geometry"""
        self.fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 0.0)

        self.prog["u_shape"].value = int(self.get_param_value("shape", 0.0))
        self.prog["u_size"].value = self.get_param_value("size", 0.5)
        self.prog["u_thickness"].value = self.get_param_value("thickness", 0.05)
        self.prog["u_rotation"].value = self.get_param_value("rotation", 0.0)

        color = self.get_param_value("color", [1.0, 1.0, 1.0, 1.0])
        if isinstance(color, list) and len(color) >= 4:
            self.prog["u_color"].value = tuple(color)
        else:
            self.prog["u_color"].value = (1.0, 1.0, 1.0, 1.0)

        self.vao.render(moderngl.TRIANGLE_STRIP)
