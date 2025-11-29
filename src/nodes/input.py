import cv2
import moderngl
import numpy as np
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry
from render.resources import load_shader

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

DEFAULT_FRAG = """
#version 330
in vec2 uv;
out vec4 fragColor;
uniform sampler2D tex0;
void main() {
    fragColor = texture(tex0, uv);
}
"""

@NodeRegistry.register("video")
class VideoNode(RenderNode):
    def __init__(self, ctx, node_id, resolution):
        super().__init__(ctx, node_id, resolution)
        self.src = ""
        self.cap = None
        # Input texture (from video)
        self.vid_texture = self.ctx.texture(resolution, 3, dtype="f1")
        self.prog = self.ctx.program(vertex_shader=QUAD_VERT, fragment_shader=DEFAULT_FRAG)
        self.vao = self.ctx.vertex_array(self.prog, [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")])

    def update(self, dt: float, fft_bands=None):
        super().update(dt, fft_bands)
        if self.src and self.cap is None:
            self.cap = cv2.VideoCapture(self.src)
        
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, self.resolution)
                self.vid_texture.write(frame.tobytes())

    def render(self):
        self.fbo.use()
        self.ctx.clear()
        self.vid_texture.use(location=0)
        self.prog['tex0'].value = 0
        self.vao.render(moderngl.TRIANGLE_STRIP)

@NodeRegistry.register("shader_input")
class ShaderNode(RenderNode):
    def __init__(self, ctx, node_id, resolution):
        super().__init__(ctx, node_id, resolution)
        self.shader_path = ""
        self.prog = None
        self.vao = None
        
        # Standard params
        self.add_param("speed", 1.0)
        self.add_param("complexity", 1.0)
        self.time = 0.0

    def _load_prog(self):
        if self.shader_path:
            try:
                # Assuming shader path is relative to project root or shaders dir
                # Simple loader:
                code = load_shader(self.shader_path) if "glsl" in self.shader_path else self.shader_path
                # If load_shader fails or returns None, we might need full path logic
                # Fallback to direct read if load_shader assumes specific dir
                if not code and Path(self.shader_path).exists():
                    code = Path(self.shader_path).read_text()
                    
                if code:
                    self.prog = self.ctx.program(vertex_shader=QUAD_VERT, fragment_shader=code)
                    self.vao = self.ctx.vertex_array(self.prog, [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")])
            except Exception as e:
                print(f"ShaderNode Error {self.id}: {e}")

    def update(self, dt: float, fft_bands=None):
        super().update(dt, fft_bands)
        self.time += dt * self.params["speed"].value

    def render(self):
        if not self.prog and self.shader_path:
            self._load_prog()
            
        if self.prog:
            self.fbo.use()
            self.ctx.clear()
            
            # Set uniforms
            if 'time' in self.prog: self.prog['time'].value = self.time
            if 'resolution' in self.prog: self.prog['resolution'].value = self.resolution
            if 'complexity' in self.prog: self.prog['complexity'].value = self.params["complexity"].value
            
            # Bind inputs if shader expects them
            for i, (slot, input_node) in enumerate(self.input_nodes.items()):
                tex = input_node.get_texture()
                tex.use(location=i)
                if f"tex{i}" in self.prog:
                    self.prog[f"tex{i}"].value = i
            
            self.vao.render(moderngl.TRIANGLE_STRIP)
