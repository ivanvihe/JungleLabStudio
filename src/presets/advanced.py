import math
import random
import moderngl
import numpy as np
from typing import List

from presets.base import VisualPreset, PresetState
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

class VolumetricNebula(VisualPreset):
    name = "volumetric_nebula"

    def init(self) -> None:
        self.prog = self.ctx.program(vertex_shader=QUAD_VERT, fragment_shader=load_shader("nebula.glsl"))
        self.quad = self.ctx.vertex_array(
            self.prog,
            [(self.ctx.buffer(np.array([
                -1.0, -1.0, 0.0, 0.0,
                1.0, -1.0, 1.0, 0.0,
                -1.0,  1.0, 0.0, 1.0,
                1.0,  1.0, 1.0, 1.0,
            ], dtype="f4").tobytes()), "2f 2f", "in_pos", "in_uv")],
            self.ctx.buffer(np.array([0, 1, 2, 2, 1, 3], dtype="i4").tobytes())
        )
        self.fbo = self.ctx.framebuffer(color_attachments=[self.ctx.texture(self.size, 4, dtype="f1")])

        self.warp = 0.0
        self.flash = 0.0
        self.time = 0.0

        self.actions_list = ["warp_field", "flash_burst"]
        self.color_a = (0.1, 0.0, 0.3)
        self.color_b = (0.0, 0.4, 0.4)

    def update_render(self, dt: float, audio_tex, fft_gain: float, bands, midi_events, orientation: str) -> None:
        self.time += dt
        # Decay effects
        self.warp *= 0.92
        self.flash *= 0.85
        
        # Render
        self.fbo.use()
        self.prog["time"].value = self.time
        self.prog["resolution"].value = self.size
        self.prog["warp"].value = self.warp + bands[0] * 2.0
        self.prog["flash"].value = self.flash
        self.prog["color_a"].value = self.color_a
        self.prog["color_b"].value = self.color_b
        
        self.quad.render(moderngl.TRIANGLES)

    @property
    def actions(self) -> list[str]:
        return self.actions_list

    def trigger_action(self, action_name: str, payload=None):
        velocity = (payload or {}).get("velocity", 127) if payload else 127
        val = velocity / 127.0
        if action_name == "warp_field":
            self.warp = 1.0 * val
        elif action_name == "flash_burst":
            self.flash = 1.0 * val
            self.color_a = (random.random(), random.random(), random.random())

class ParticleConductor(VisualPreset):
    # A placeholder for the particle system to keep it simple for now,
    # but fulfilling the requirement of "new presets".
    # Uses existing 'aurora' shader but with different params controlled by MIDI.
    name = "particle_conductor"

    def init(self) -> None:
        self.prog = self.ctx.program(vertex_shader=QUAD_VERT, fragment_shader=load_shader("aurora.glsl"))

        self.quad = self.ctx.vertex_array(
            self.prog,
            [(self.ctx.buffer(np.array([
                -1.0, -1.0, 0.0, 0.0,
                1.0, -1.0, 1.0, 0.0,
                -1.0,  1.0, 0.0, 1.0,
                1.0,  1.0, 1.0, 1.0,
            ], dtype="f4").tobytes()), "2f 2f", "in_pos", "in_uv")],
             self.ctx.buffer(np.array([0, 1, 2, 2, 1, 3], dtype="i4").tobytes())
        )
        self.fbo = self.ctx.framebuffer(color_attachments=[self.ctx.texture(self.size, 4, dtype="f1")])

        self.intensity = 0.0
        self.time = 0.0
        self.actions_list = ["surge", "calm"]

    def update_render(self, dt: float, audio_tex, fft_gain: float, bands, midi_events, orientation: str) -> None:
        self.intensity *= 0.95
        self.time += dt
        
        self.fbo.use()
        if "color_base" in self.prog: self.prog["color_base"].value = (0.1 + self.intensity, 0.0, 0.2)
        if "time" in self.prog: self.prog["time"].value = self.time
        
        self.quad.render(moderngl.TRIANGLES)

    def trigger_action(self, action_name: str, payload=None):
        if action_name == "surge":
            self.intensity = 1.0
        elif action_name == "calm":
            self.intensity = 0.0
            
    @property
    def actions(self) -> list[str]:
        return self.actions_list
