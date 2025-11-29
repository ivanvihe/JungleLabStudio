import time
from dataclasses import dataclass
from typing import Dict, Optional

import moderngl
import numpy as np

from render.resources import load_shader


@dataclass
class FXState:
    intensity: float = 0.0
    duration: float = 0.0
    decay: str = "exp"  # linear | exp
    timer: float = 0.0
    target: float = 0.0


class FXEngine:
    def __init__(self, ctx: moderngl.Context, size: tuple[int, int]):
        self.ctx = ctx
        self.size = size
        self.fx_defs = {
            "chromatic": FXState(),
            "pixelate": FXState(),
            "vhs": FXState(),
            "datamosh": FXState(), # Not impl in shader yet
            "crt": FXState(),      # Not impl
            "bloom_pulse": FXState(),
            "shockwave": FXState(),
            "color_glitch": FXState(), # Not impl
            "blur": FXState(),         # Not impl
            "smear": FXState(),        # Not impl
            "heat": FXState(),
        }
        self.fx_prog = ctx.program(
            vertex_shader="""
            #version 330
            in vec2 in_pos; in vec2 in_uv; out vec2 uv;
            void main(){ uv=in_uv; gl_Position=vec4(in_pos,0.0,1.0); }
            """,
            fragment_shader=load_shader("global_fx.glsl"),
        )
        self.vbo = ctx.buffer(np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype="f4").tobytes())
        self.ibo = ctx.buffer(np.array([0,1,2,2,1,3], dtype="i4").tobytes())
        self.vao = ctx.vertex_array(self.fx_prog, [(self.vbo, "2f 2f", "in_pos", "in_uv")], self.ibo)
        self.fbo = self.ctx.framebuffer(color_attachments=[self.ctx.texture(size, 4, dtype="f1")])
        self.fx_prog["resolution"].value = size

    def set_size(self, size: tuple[int, int]):
        self.size = size
        self.fbo = self.ctx.framebuffer(color_attachments=[self.ctx.texture(size, 4, dtype="f1")])
        self.fx_prog["resolution"].value = size

    def trigger(self, name: str, intensity: float = 1.0, duration: float = 1.0, decay: str = "exp"):
        if name not in self.fx_defs:
            return
        fx = self.fx_defs[name]
        fx.timer = duration
        fx.duration = duration
        fx.intensity = intensity
        fx.decay = decay

    def update(self, dt: float):
        for fx in self.fx_defs.values():
            if fx.timer > 0.0:
                fx.timer = max(0.0, fx.timer - dt)
                t = fx.timer / max(fx.duration, 1e-5)
                if fx.decay == "linear":
                    fx.target = t * fx.intensity
                else:
                    fx.target = (t * t) * fx.intensity
            else:
                fx.target = 0.0

    def apply(self, tex) -> moderngl.Texture:
        self.fbo.use()
        self.ctx.clear()
        tex.use(location=0)
        self.fx_prog["tex0"].value = 0
        
        # Map abstract FX names to shader uniforms
        # Shader: chromatic_aberration, pixelate, vhs_strength, distortion, bloom_intensity, heat_strength
        
        if "chromatic_aberration" in self.fx_prog:
            self.fx_prog["chromatic_aberration"].value = self.fx_defs["chromatic"].target
        
        if "pixelate" in self.fx_prog:
            self.fx_prog["pixelate"].value = self.fx_defs["pixelate"].target
            
        if "vhs_strength" in self.fx_prog:
            # Combine VHS and CRT
            self.fx_prog["vhs_strength"].value = self.fx_defs["vhs"].target + self.fx_defs["crt"].target

        if "distortion" in self.fx_prog:
            # Combine shockwave and heat
            self.fx_prog["distortion"].value = self.fx_defs["shockwave"].target + self.fx_defs["heat"].target

        if "bloom_intensity" in self.fx_prog:
             self.fx_prog["bloom_intensity"].value = self.fx_defs["bloom_pulse"].target

        if "heat_strength" in self.fx_prog:
             self.fx_prog["heat_strength"].value = self.fx_defs["heat"].target

        if "time" in self.fx_prog:
            self.fx_prog["time"].value = time.time()
            
        self.vao.render()
        return self.fbo.color_attachments[0]
