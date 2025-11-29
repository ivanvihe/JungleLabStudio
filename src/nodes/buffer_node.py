"""
BufferNode - Frame buffer for feedback loops and delay
"""
import moderngl
import numpy as np
from core.graph.node import RenderNode
from core.graph.registry import NodeRegistry


@NodeRegistry.register("utility.buffer")
class BufferNode(RenderNode):
    """
    Buffer node - stores the input frame and outputs it in the next frame.
    Essential for creating feedback loops without graph cycle errors.
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        # Internal storage for the buffered frame
        self.stored_texture = self.ctx.texture(resolution, 4, dtype="f1")
        self.stored_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.stored_texture.repeat_x = False
        self.stored_texture.repeat_y = False
        
        # FBO to write to the stored texture
        self.stored_fbo = self.ctx.framebuffer(color_attachments=[self.stored_texture])

        # Simple copy shader
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
            uniform sampler2D u_texture;

            void main() {
                fragColor = texture(u_texture, v_uv);
            }
            """
        )

        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.quad_vbo, "2f 2f", "in_pos", "in_uv")]
        )
        
        # Clear stored texture initially
        self.stored_fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 0.0)
        
        self.first_frame = True

    def render(self):
        """
        1. Output the *previously stored* frame to self.fbo (downstream nodes see this).
        2. Read the current input and write it to *stored_fbo* (for the next frame).
        """
        
        # --- Step 1: Output Stored Frame ---
        self.fbo.use()
        if self.first_frame:
            self.ctx.clear(0.0, 0.0, 0.0, 0.0)
            self.first_frame = False
        else:
            self.stored_texture.use(location=0)
            self.prog["u_texture"].value = 0
            self.vao.render(moderngl.TRIANGLE_STRIP)
            
        # --- Step 2: Capture Input Frame ---
        # We do this *after* outputting, so we effectively delay by 1 frame
        input_tex = self.get_input_texture("input0")
        
        self.stored_fbo.use()
        if input_tex:
            input_tex.use(location=0)
            self.prog["u_texture"].value = 0
            self.vao.render(moderngl.TRIANGLE_STRIP)
        else:
            # If no input, clear buffer (or keep last frame? usually clear)
            self.ctx.clear(0.0, 0.0, 0.0, 0.0)

    def resize(self, resolution: tuple[int, int]):
        super().resize(resolution)
        # Recreate stored texture on resize
        self.stored_texture = self.ctx.texture(resolution, 4, dtype="f1")
        self.stored_fbo = self.ctx.framebuffer(color_attachments=[self.stored_texture])
