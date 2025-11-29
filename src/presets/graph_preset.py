from presets.base import VisualPreset, PresetState
from core.graph.loader import GraphLoader
import moderngl
import numpy as np

# Import to register nodes - this triggers @NodeRegistry.register decorators
try:
    import nodes  # Import nodes package to trigger registration
    from core.graph.registry import NodeRegistry
    print(f"DEBUG: Registered nodes: {list(NodeRegistry._registry.keys())}")
except ImportError as e:
    print(f"Warning: Could not import nodes: {e}")

class GraphPreset(VisualPreset):
    name = "graph_preset"

    def __init__(self, ctx: moderngl.Context, size: tuple[int, int], state: PresetState, file_path: str = ""):
        self.file_path = file_path
        super().__init__(ctx, size, state)

    def init(self) -> None:
        self.loader = GraphLoader(self.ctx, self.size)
        self.graph = self.loader.load_file(self.file_path)

        # Debug: print graph info
        print(f"GraphPreset: Loaded {len(self.graph.nodes)} nodes from {self.file_path}")
        for node_id, node in self.graph.nodes.items():
            print(f"  - {node_id}: {type(node).__name__}")
        
        # Blit shader - generate UVs from vertex position to avoid optimizer issues
        self.blit_prog = self.ctx.program(
            vertex_shader="""
            #version 330
            in vec2 in_pos;
            out vec2 uv;
            void main() {
                // Generate UVs from position (-1..1 -> 0..1)
                uv = in_pos * 0.5 + 0.5;
                gl_Position = vec4(in_pos, 0.0, 1.0);
            }
            """,
            fragment_shader="""
            #version 330
            in vec2 uv;
            out vec4 fragColor;
            uniform sampler2D tex0;
            void main() {
                fragColor = texture(tex0, uv);
            }
            """
        )

        # Create blit quad - only position attribute needed
        self.blit_quad = self.ctx.vertex_array(
            self.blit_prog,
            [(self.ctx.buffer(np.array([
                -1.0, -1.0,
                 1.0, -1.0,
                -1.0,  1.0,
                 1.0,  1.0,
            ], dtype="f4").tobytes()), "2f", "in_pos")],
            self.ctx.buffer(np.array([0, 1, 2, 2, 1, 3], dtype="i4").tobytes())
        )
        print(f"GraphPreset: Blit shader and VAO created successfully")

    def update_render(self, dt: float, audio_tex, fft_gain: float, bands, midi_events, orientation: str) -> None:
        # 1. Apply MIDI
        for msg in midi_events:
            self.graph.apply_midi(msg)

        # 2. Update Graph (pass audio bands for audio-reactive params)
        self.graph.update(dt, bands)

        # 3. Render Graph
        self.graph.render()

        # 4. Blit Final Output to current framebuffer (Engine already bound scene_fbo)
        # The Engine calls `self.scene_fbo.use()` before `update_render()`, so the
        # current framebuffer is already the correct target. We just blit to it.

        final_tex = self.graph.get_final_texture()
        if final_tex:
            # Debug first blit
            if not hasattr(self, '_first_blit'):
                print(f"GraphPreset: First blit, final texture size: {final_tex.size}")
                self._first_blit = True

            # Blit to currently bound framebuffer (scene_fbo)
            # DO NOT bind self.fbo - just draw to whatever is currently bound
            final_tex.use(location=0)
            self.blit_prog['tex0'].value = 0
            self.blit_quad.render(moderngl.TRIANGLES)
        else:
            # Debug: no final texture
            if not hasattr(self, '_warned_no_tex'):
                print(f"WARNING: GraphPreset has no final texture! Nodes: {len(self.graph.nodes)}, Execution order: {len(self.graph.execution_order)}")
                self._warned_no_tex = True

    @property
    def actions(self) -> list[str]:
        # TODO: Introspect graph for triggers?
        return []
