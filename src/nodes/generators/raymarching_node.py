"""
RaymarchingNode - 3D Raymarching Generator
Generate 3D scenes using raymarching and signed distance functions (SDFs)
"""

import moderngl
from core.graph.node import GeneratorNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("generator.raymarching")
class RaymarchingNode(GeneratorNode):
    """
    3D raymarching generator with SDF primitives

    Creates 3D scenes using raymarching technique with signed distance functions.
    Similar to many Shadertoy 3D shaders.

    Parameters:
    - primitive: Shape type (0=Sphere, 1=Box, 2=Torus, 3=Capsule)
    - camera_distance: Camera distance from origin
    - camera_rotate: Auto-rotate camera
    - light_dir_x, light_dir_y, light_dir_z: Light direction
    - material_color: Base material color (vec3)
    - ambient: Ambient light intensity
    - diffuse: Diffuse light intensity
    - specular: Specular light intensity
    - shininess: Specular shininess exponent
    - max_steps: Maximum raymarch steps
    - max_dist: Maximum raymarch distance
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Parameters
        self.add_param('primitive', 0.0, 0.0, 3.0)  # 0=Sphere, 1=Box, 2=Torus, 3=Capsule
        self.add_param('camera_distance', 3.0, 1.0, 10.0)
        self.add_param('camera_rotate', 1.0, 0.0, 1.0)  # Auto-rotate camera
        self.add_param('light_dir_x', 1.0, -1.0, 1.0)
        self.add_param('light_dir_y', 1.0, -1.0, 1.0)
        self.add_param('light_dir_z', 1.0, -1.0, 1.0)
        self.add_param('material_color', [0.8, 0.4, 0.2], [0.0, 0.0, 0.0], [1.0, 1.0, 1.0])
        self.add_param('ambient', 0.3, 0.0, 1.0)
        self.add_param('diffuse', 0.7, 0.0, 1.0)
        self.add_param('specular', 0.5, 0.0, 1.0)
        self.add_param('shininess', 32.0, 1.0, 128.0)
        self.add_param('max_steps', 80.0, 10.0, 200.0)
        self.add_param('max_dist', 20.0, 5.0, 100.0)

        # Shader code
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
        uniform int u_primitive;
        uniform float u_camera_distance;
        uniform float u_camera_rotate;
        uniform vec3 u_light_dir;
        uniform vec3 u_material_color;
        uniform float u_ambient;
        uniform float u_diffuse;
        uniform float u_specular;
        uniform float u_shininess;
        uniform int u_max_steps;
        uniform float u_max_dist;

        // SDF primitives
        float sdSphere(vec3 p, float r) {
            return length(p) - r;
        }

        float sdBox(vec3 p, vec3 b) {
            vec3 q = abs(p) - b;
            return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
        }

        float sdTorus(vec3 p, vec2 t) {
            vec2 q = vec2(length(p.xz) - t.x, p.y);
            return length(q) - t.y;
        }

        float sdCapsule(vec3 p, vec3 a, vec3 b, float r) {
            vec3 pa = p - a, ba = b - a;
            float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
            return length(pa - ba * h) - r;
        }

        // Scene SDF
        float map(vec3 p) {
            if (u_primitive == 0) {
                return sdSphere(p, 1.0);
            } else if (u_primitive == 1) {
                return sdBox(p, vec3(0.8, 0.8, 0.8));
            } else if (u_primitive == 2) {
                return sdTorus(p, vec2(1.0, 0.3));
            } else {
                return sdCapsule(p, vec3(0.0, -0.5, 0.0), vec3(0.0, 0.5, 0.0), 0.3);
            }
        }

        // Calculate normal
        vec3 calcNormal(vec3 p) {
            float eps = 0.001;
            vec2 h = vec2(eps, 0.0);
            return normalize(vec3(
                map(p + h.xyy) - map(p - h.xyy),
                map(p + h.yxy) - map(p - h.yxy),
                map(p + h.yyx) - map(p - h.yyx)
            ));
        }

        // Raymarching
        float raymarch(vec3 ro, vec3 rd) {
            float t = 0.0;
            for (int i = 0; i < u_max_steps; i++) {
                vec3 p = ro + rd * t;
                float d = map(p);
                if (d < 0.001) return t;
                if (t > u_max_dist) return -1.0;
                t += d;
            }
            return -1.0;
        }

        // Rotate matrix
        mat2 rot(float a) {
            float c = cos(a);
            float s = sin(a);
            return mat2(c, -s, s, c);
        }

        void main() {
            // Normalized coordinates
            vec2 uv = (v_uv - 0.5) * 2.0;
            uv.x *= u_resolution.x / u_resolution.y;

            // Camera setup
            vec3 ro = vec3(0.0, 0.0, u_camera_distance);
            vec3 rd = normalize(vec3(uv, -1.0));

            // Rotate camera
            if (u_camera_rotate > 0.5) {
                float angle = u_time * 0.5;
                ro.xz = ro.xz * rot(angle);
                rd.xz = rd.xz * rot(angle);
            }

            // Raymarch
            float t = raymarch(ro, rd);

            vec3 col = vec3(0.0);

            if (t > 0.0) {
                // Hit! Calculate lighting
                vec3 p = ro + rd * t;
                vec3 normal = calcNormal(p);
                vec3 lightDir = normalize(u_light_dir);

                // Ambient
                vec3 ambient = u_material_color * u_ambient;

                // Diffuse
                float diff = max(dot(normal, lightDir), 0.0);
                vec3 diffuse = u_material_color * diff * u_diffuse;

                // Specular
                vec3 viewDir = normalize(-rd);
                vec3 reflectDir = reflect(-lightDir, normal);
                float spec = pow(max(dot(viewDir, reflectDir), 0.0), u_shininess);
                vec3 specular = vec3(spec) * u_specular;

                col = ambient + diffuse + specular;

                // Ambient occlusion (simple approximation)
                float ao = 1.0 - float(t) / u_max_dist;
                col *= ao;
            } else {
                // Background
                col = mix(
                    vec3(0.1, 0.1, 0.2),
                    vec3(0.0, 0.0, 0.0),
                    length(uv) * 0.5
                );
            }

            fragColor = vec4(col, 1.0);
        }
        """

        # Compile shader
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
            print(f"RaymarchingNode: Shader compilation failed: {e}")
            self.program = None
            self.vao = None

    def render(self):
        if not self.program or not self.vao:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return

        self.fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 0.0)

        # Set uniforms
        self.program['u_time'].value = self.time
        self.program['u_resolution'].value = self.resolution
        self.program['u_primitive'].value = int(self.get_param_value('primitive'))
        self.program['u_camera_distance'].value = self.get_param_value('camera_distance')
        self.program['u_camera_rotate'].value = self.get_param_value('camera_rotate')

        light_dir = (
            self.get_param_value('light_dir_x'),
            self.get_param_value('light_dir_y'),
            self.get_param_value('light_dir_z')
        )
        self.program['u_light_dir'].value = light_dir
        self.program['u_material_color'].value = tuple(self.get_param_value('material_color'))
        self.program['u_ambient'].value = self.get_param_value('ambient')
        self.program['u_diffuse'].value = self.get_param_value('diffuse')
        self.program['u_specular'].value = self.get_param_value('specular')
        self.program['u_shininess'].value = self.get_param_value('shininess')
        self.program['u_max_steps'].value = int(self.get_param_value('max_steps'))
        self.program['u_max_dist'].value = self.get_param_value('max_dist')

        self.vao.render(moderngl.TRIANGLE_STRIP)
