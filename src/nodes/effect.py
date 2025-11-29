import moderngl
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry

QUAD_VERT = """
#version 330
in vec2 in_pos;
in vec2 in_uv;
out vec2 uv;
void main() {
    uv = in_uv;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""

DISTORT_FRAG = """
#version 330
in vec2 uv;
out vec4 fragColor;
uniform sampler2D tex0;
uniform float intensity;
uniform float time;

void main() {
    vec2 p = uv;
    p.x += sin(p.y * 10.0 + time) * 0.1 * intensity;
    p.y += cos(p.x * 10.0 + time) * 0.1 * intensity;
    fragColor = texture(tex0, p);
}
"""

@NodeRegistry.register("effect.distort")
class DistortNode(RenderNode):
    def __init__(self, ctx, node_id, resolution):
        super().__init__(ctx, node_id, resolution)
        self.add_param("intensity", 0.5)
        self.time = 0.0
        self.prog = self.ctx.program(vertex_shader=QUAD_VERT, fragment_shader=DISTORT_FRAG)
        self.vao = self.ctx.vertex_array(self.prog, [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")])

    def update(self, dt: float, fft_bands=None):
        super().update(dt, fft_bands)
        self.time += dt

    def render(self):
        self.fbo.use()
        self.ctx.clear()
        
        input_node = self.input_nodes.get("input0")
        if input_node:
            input_node.get_texture().use(location=0)
            self.prog['tex0'].value = 0
            self.prog['intensity'].value = self.params['intensity'].value
            self.prog['time'].value = self.time
            self.vao.render(moderngl.TRIANGLE_STRIP)
