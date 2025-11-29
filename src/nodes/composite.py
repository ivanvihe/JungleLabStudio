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

BLEND_FRAG = """
#version 330
in vec2 uv;
out vec4 fragColor;
uniform sampler2D tex0;
uniform sampler2D tex1;
uniform float opacity;
uniform int mode; // 0=add, 1=mix, 2=mult

void main() {
    vec4 c0 = texture(tex0, uv);
    vec4 c1 = texture(tex1, uv);
    
    vec3 res = c0.rgb;
    if (mode == 0) {
        res = c0.rgb + c1.rgb * opacity;
    } else if (mode == 1) {
        res = mix(c0.rgb, c1.rgb, opacity);
    } else if (mode == 2) {
        res = c0.rgb * c1.rgb * opacity;
    }
    
    fragColor = vec4(res, 1.0);
}
"""

@NodeRegistry.register("composite")
class CompositeNode(RenderNode):
    def __init__(self, ctx, node_id, resolution):
        super().__init__(ctx, node_id, resolution)
        self.blend_mode = "add"
        self.add_param("opacity", 1.0)
        self.prog = self.ctx.program(vertex_shader=QUAD_VERT, fragment_shader=BLEND_FRAG)
        self.vao = self.ctx.vertex_array(self.prog, [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")])

    def render(self):
        self.fbo.use()
        self.ctx.clear()
        
        # Need at least two inputs usually, or background + 1 input
        tex0 = self.input_nodes.get("input0")
        tex1 = self.input_nodes.get("input1")
        
        if tex0:
            tex0.get_texture().use(location=0)
            self.prog['tex0'].value = 0
        
        if tex1:
            tex1.get_texture().use(location=1)
            self.prog['tex1'].value = 1
        else:
            # If only one input, just pass through? Or nothing.
            # For now assume composite needs 2 inputs or it acts as pass-through if logic added
            pass

        mode_map = {"add": 0, "mix": 1, "mult": 2}
        self.prog['mode'].value = mode_map.get(self.blend_mode, 0)
        self.prog['opacity'].value = self.params["opacity"].value
        
        self.vao.render(moderngl.TRIANGLE_STRIP)
