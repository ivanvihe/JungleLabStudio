import moderngl
import numpy as np

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


class PostChain:
    def __init__(self, ctx: moderngl.Context, size: tuple[int, int]):
        self.ctx = ctx
        self.size = size
        self.vbo, self.ibo = self._make_quad()
        self.fbo_a = self._make_fbo()
        self.fbo_b = self._make_fbo()
        self.prog_bloom = ctx.program(vertex_shader=QUAD_VERT, fragment_shader=load_shader("post_bloom.glsl"))
        self.prog_glitch = ctx.program(vertex_shader=QUAD_VERT, fragment_shader=load_shader("post_glitch.glsl"))
        self.prog_global_fx = ctx.program(vertex_shader=QUAD_VERT, fragment_shader=load_shader("global_fx.glsl"))
        self.prog_aberration = ctx.program(vertex_shader=QUAD_VERT, fragment_shader=load_shader("post_aberration.glsl"))
        self.prog_osd = ctx.program(vertex_shader=QUAD_VERT, fragment_shader=load_shader("osd.glsl"))
        self.prog_feedback = ctx.program(vertex_shader=QUAD_VERT, fragment_shader=load_shader("feedback.glsl"))
        self.vao_bloom = self.ctx.vertex_array(self.prog_bloom, [(self.vbo, "2f 2f", "in_pos", "in_uv")], self.ibo)
        self.vao_glitch = self.ctx.vertex_array(self.prog_glitch, [(self.vbo, "2f 2f", "in_pos", "in_uv")], self.ibo)
        self.vao_global_fx = self.ctx.vertex_array(self.prog_global_fx, [(self.vbo, "2f 2f", "in_pos", "in_uv")], self.ibo)
        self.vao_aberration = self.ctx.vertex_array(self.prog_aberration, [(self.vbo, "2f 2f", "in_pos", "in_uv")], self.ibo)
        self.vao_osd = self.ctx.vertex_array(self.prog_osd, [(self.vbo, "2f 2f", "in_pos", "in_uv")], self.ibo)
        self.vao_feedback = self.ctx.vertex_array(self.prog_feedback, [(self.vbo, "2f 2f", "in_pos", "in_uv")], self.ibo)
        self.set_resolution(size)

    def _make_quad(self):
        vbo = self.ctx.buffer(np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype="f4").tobytes())
        ibo = self.ctx.buffer(np.array([0, 1, 2, 2, 1, 3], dtype="i4").tobytes())
        return vbo, ibo

    def _make_fbo(self):
        tex = self.ctx.texture(self.size, 4, dtype="f1")
        tex.filter = (self.ctx.LINEAR, self.ctx.LINEAR)
        tex.repeat_x = False
        tex.repeat_y = False
        depth = self.ctx.depth_renderbuffer(self.size)
        return self.ctx.framebuffer(color_attachments=[tex], depth_attachment=depth)

    def set_resolution(self, size: tuple[int, int]):
        self.size = size
        self.fbo_a = self._make_fbo()
        self.fbo_b = self._make_fbo()
        self.history_tex = self.ctx.texture(self.size, 4, dtype="f1")
        self.history_tex.filter = (self.ctx.LINEAR, self.ctx.LINEAR)
        self.fbo_history = self.ctx.framebuffer(color_attachments=[self.history_tex])
        self.prog_bloom["resolution"].value = size
        self.prog_global_fx["resolution"].value = size

    def process(self, tex, time: float, glitch: float, aberration: float, screen_size: tuple[int, int], vertical: bool, fx_params: dict = None):
        if fx_params is None:
            fx_params = {}

        if not hasattr(self, '_first_process'):
            print(f"PostChain: First process call")
            print(f"  Input texture size: {tex.size}")
            print(f"  Screen size: {screen_size}")
            print(f"  FBO size: {self.fbo_a.size}")
            self._first_process = True

        # Feedback blend current scene with history -> FBO A
        self.fbo_a.use()
        self.ctx.clear()
        tex.use(location=0)
        self.history_tex.use(location=1)
        self.prog_feedback["tex0"].value = 0
        self.prog_feedback["tex1"].value = 1
        self.prog_feedback["feedback"].value = 0.08
        self.vao_feedback.render()

        # Global FX Pass -> FBO B
        self.fbo_b.use()
        self.ctx.clear()
        self.fbo_a.color_attachments[0].use(location=0)
        self.prog_global_fx["tex0"].value = 0
        self.prog_global_fx["time"].value = time
        self.prog_global_fx["chromatic_aberration"].value = fx_params.get("chromatic_aberration", 0.0)
        self.prog_global_fx["pixelate"].value = fx_params.get("pixelate", 0.0)
        self.prog_global_fx["vhs_strength"].value = fx_params.get("vhs_strength", 0.0)
        self.prog_global_fx["distortion"].value = fx_params.get("distortion", 0.0)
        self.prog_global_fx["bloom_intensity"].value = fx_params.get("bloom_intensity", 0.0)
        self.prog_global_fx["heat_strength"].value = fx_params.get("heat_strength", 0.0)
        self.vao_global_fx.render()

        # Bloom pass -> FBO A
        self.fbo_a.use()
        self.ctx.clear()
        self.fbo_b.color_attachments[0].use(location=0)
        self.prog_bloom["tex0"].value = 0
        self.prog_bloom["intensity"].value = glitch * 0.4 + 0.6
        self.prog_bloom["threshold"].value = 0.55
        self.prog_bloom["resolution"].value = self.size
        self.vao_bloom.render()

        # Glitch pass -> FBO B
        self.fbo_b.use()
        self.ctx.clear()
        self.fbo_a.color_attachments[0].use(location=0)
        self.prog_glitch["tex0"].value = 0
        self.prog_glitch["time"].value = time
        self.prog_glitch["strength"].value = glitch
        self.prog_glitch["pixel_sort"].value = 1.0
        self.vao_glitch.render()

        # Update history from latest image (FBO B)
        self.fbo_history.use()
        self.ctx.clear()
        self.fbo_b.color_attachments[0].use(location=0)
        self.prog_feedback["tex0"].value = 0
        self.prog_feedback["tex1"].value = 0
        self.prog_feedback["feedback"].value = 0.0
        self.vao_feedback.render()

        # Chromatic aberration to screen (from FBO B)
        if not hasattr(self, '_first_screen_render'):
            print(f"PostChain: First screen render")
            print(f"  Screen framebuffer: {self.ctx.screen}")
            print(f"  Rendering from FBO B size: {self.fbo_b.size}")
            print(f"  Screen size parameter: {screen_size}")
            self._first_screen_render = True

        self.ctx.disable(moderngl.BLEND)
        self.ctx.screen.use()

        # Set viewport to match screen size for proper stretching
        self.ctx.viewport = (0, 0, screen_size[0], screen_size[1])

        self.fbo_b.color_attachments[0].use(location=0)
        self.prog_aberration["tex0"].value = 0
        self.prog_aberration["intensity"].value = aberration
        self.prog_aberration["screen_size"].value = screen_size
        self.prog_aberration["vertical"].value = 1 if vertical else 0
        self.vao_aberration.render()
        return self.ctx.screen
