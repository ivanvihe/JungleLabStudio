import time
from typing import Callable, Optional, List
import glfw
import moderngl
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer
from imgui_bundle.python_backends.opengl_backend_programmable import ProgrammablePipelineRenderer

class OSD:
    def __init__(self, window, ctx: moderngl.Context, midi_input=None):
        self.window = window
        self.ctx = ctx
        self.midi_input = midi_input
        
        # Init ImGui
        self.imgui_context = imgui.create_context()
        self.io = imgui.get_io()
        self.io.config_flags |= imgui.ConfigFlags_.nav_enable_keyboard
        
        # Style
        imgui.style_colors_dark()
        
        # Backends
        # install_callbacks=False allows us to manage callbacks in Engine and forward them
        self.backend = GlfwRenderer(window, attach_callbacks=False)
        self.renderer = ProgrammablePipelineRenderer()
        
        self.draw_callback: Optional[Callable[[], None]] = None
        
        # MIDI Debug Log
        self.midi_log: List[str] = []
        if self.midi_input:
            self.midi_input.add_listener(self._on_midi_debug)

    def _on_midi_debug(self, msg):
        ts = time.strftime("%H:%M:%S")
        # Filter clock to reduce noise
        if msg.type in ['clock', 'active_sensing']:
            return
        self.midi_log.append(f"[{ts}] {msg}")
        if len(self.midi_log) > 50:
            self.midi_log.pop(0)

    def render(self):
        self.backend.process_inputs()
        imgui.new_frame()
        
        if self.draw_callback:
            self.draw_callback()
            
        # Draw MIDI Monitor Window if enabled
        # We can make this a persistent toggle in the UI
        # For now, let's keep it simple or exposed via menu
        
        imgui.render()
        self.renderer.render(imgui.get_draw_data())

    def shutdown(self):
        self.renderer.shutdown()
        self.backend.shutdown()
        imgui.destroy_context(self.imgui_context)

    # Event forwarding methods
    def resize_callback(self, window, width, height):
        self.backend.resize_callback(window, width, height)

    def key_callback(self, window, key, scancode, action, mods):
        self.backend.keyboard_callback(window, key, scancode, action, mods)

    def char_callback(self, window, char):
        self.backend.char_callback(window, char)

    def mouse_button_callback(self, window, button, action, mods):
        self.backend.mouse_button_callback(window, button, action, mods)

    def scroll_callback(self, window, x_offset, y_offset):
        self.backend.scroll_callback(window, x_offset, y_offset)

    def cursor_pos_callback(self, window, x, y):
        self.backend.mouse_callback(window, x, y)
