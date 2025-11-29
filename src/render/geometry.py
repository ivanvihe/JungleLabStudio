import numpy as np


class FullscreenQuad:
    def __init__(self, ctx):
        self.ctx = ctx
        self.vbo = ctx.buffer(np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype="f4").tobytes())
        self.ibo = ctx.buffer(np.array([0, 1, 2, 2, 1, 3], dtype="i4").tobytes())

    def render(self, program):
        vao = self.ctx.vertex_array(program, [(self.vbo, "2f 2f", "in_pos", "in_uv")], self.ibo)
        vao.render()
