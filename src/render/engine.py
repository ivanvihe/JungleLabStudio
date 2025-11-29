import json
import time
import sys
import os
import importlib
import inspect
from pathlib import Path
from typing import Callable, Optional, List

import glfw
import moderngl
import OpenGL
# Patch PyOpenGL to ignore context checking issues with GLFW/ModernGL
OpenGL.CHECK_CONTEXT = False
import OpenGL.contextdata
def get_context_patched(context=None):
    if context: return context
    return 1 # Dummy context ID
OpenGL.contextdata.getContext = get_context_patched

import OpenGL.GL as gl # Force PyOpenGL import
import numpy as np
from imgui_bundle import imgui, portable_file_dialogs as pfd

from core.config import Preferences, load_preferences, save_preferences
from core.osd import OSD
from core.utils import Clock, aspect_for_orientation
from core.preset_manager import PresetManager
from input_output.audio import AudioInput
from input_output.midi import MidiInput
from presets import PRESET_REGISTRY, VisualPreset, PresetState
from presets.graph_preset import GraphPreset
from presets.media_player import MediaPreset
from render.post import PostChain, QUAD_VERT
from render.fx import FXEngine
from render.geometry import FullscreenQuad
from render.resources import load_shader
from editor.app import VisualEditor

class VisualEngine:
    def __init__(self, preset_path: Optional[str] = None):
        self.prefs = load_preferences()
        self.window = None
        self.ctx: Optional[moderngl.Context] = None
        self.audio = AudioInput(device=self.prefs.audio_device)
        self.midi = MidiInput(device=self.prefs.midi_device)
        self.clock = Clock()
        self.osd: Optional[OSD] = None
        self.mode = "preset"
        self.last_midi_time = 0.0
        self.debug_midi = True

        self.fx_engine: Optional[FXEngine] = None
        self.learn_target = None
        self.post: Optional[PostChain] = None
        self.scene_fbo = None
        self.scene_tex = None
        self.audio_tex = None
        self.audio_bins = 512
        self.current_preset: Optional[VisualPreset] = None
        self.orientation = self.prefs.orientation
        self.fullscreen_size = (1280, 720)

        self.show_midi_monitor = False
        self.show_action_map = False

        self.preset_manager = PresetManager()
        self._ensure_builtins_migrated()

        # Visual Editor
        self.editor = None
        self.editor_mode = True

        # Store preset path to load after window creation
        self.initial_preset_path = preset_path

    def _ensure_builtins_migrated(self):
        # If library is empty or missing new presets, migrate built-in python presets to .preset files
        # Check if any preset is missing to trigger migration of new presets
        missing_presets = []
        for name in PRESET_REGISTRY.keys():
            if name not in self.preset_manager.presets:
                missing_presets.append(name)

        if missing_presets:
            print(f"Migrating {len(missing_presets)} built-in presets to .preset files...")
            for name, cls in PRESET_REGISTRY.items():
                if name in missing_presets:
                    try:
                        file_path = inspect.getfile(cls)
                        # Exclude GraphPreset from migration to avoid circular dependency
                        if name == "graph_preset":
                            continue
                        print(f"  Migrating: {name}")
                        self.preset_manager.migrate_builtin(name, cls, file_path)
                    except Exception as e:
                        print(f"  Skipping migration for {name}: {e}")
            # Reload library to pick up changes
            self.preset_manager.load_library()
            print(f"Migration complete. {len(self.preset_manager.presets)} presets available.")

    def _open_preset_file(self):
        """Open a preset file (.preset, .yaml, .yml) from file browser"""
        res = pfd.open_file("Open Preset", ".", ["Preset Files *.preset *.yaml *.yml"]).result()
        if res and len(res) > 0:
            import shutil
            preset_path = Path(res[0])
            name = preset_path.stem

            # Ensure unique name
            base_name = name
            c = 1
            while name in self.preset_manager.presets:
                name = f"{base_name}_{c}"
                c += 1

            # Copy preset file to presets directory
            dest_path = self.preset_manager.presets_dir / f"{name}.preset"
            shutil.copy(preset_path, dest_path)

            # Reload library and load the preset
            self.preset_manager.load_library()
            self.load_preset(name)
            print(f"Loaded preset: {name}")

    def _new_media_preset(self):
        res = pfd.open_file("Select Media", ".", ["Media Files *.mp4 *.mov *.avi *.jpg *.png *.jpeg"]).result()
        if res and len(res) > 0:
            path = res[0]
            name = Path(path).stem
            # Ensure unique name
            base_name = name
            c = 1
            while name in self.preset_manager.presets:
                name = f"{base_name}_{c}"
                c += 1

            if self.preset_manager.create_media_preset(name, path):
                self.load_preset(name)

    def load_preset(self, name: str):
        logic = self.preset_manager.load_preset_logic(name)
        if not logic:
            print(f"Preset {name} not found in library.")
            return

        if logic.get("class") == "MediaPreset":
            self.current_preset = MediaPreset(self.ctx, self.scene_tex.size, PresetState(), file_path=logic["file_path"])
        elif logic.get("class") == "GraphPreset":
            self.current_preset = GraphPreset(self.ctx, self.scene_tex.size, PresetState(), file_path=logic["file_path"])
        elif logic.get("class"):
            # It's a code preset class object
            cls = logic["class"]
            self.current_preset = cls(self.ctx, self.scene_tex.size, PresetState())
            
        self.prefs.preset = name

    def next_preset(self):
        keys = list(self.preset_manager.presets.keys())
        if not keys: return
        
        if self.current_preset:
            if self.current_preset.name in keys:
                 idx = (keys.index(self.current_preset.name) + 1) % len(keys)
                 self._enter_preset(keys[idx])
                 return
        
        self._enter_preset(keys[0])

    def _enter_preset(self, name: str):
        self.load_preset(name)

    def init_window(self):
        if not glfw.init():
            raise RuntimeError("Unable to init GLFW")
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        # Try to get monitor information safely
        monitor = None
        try:
            monitor = glfw.get_primary_monitor()
            print(f"DEBUG: Primary monitor object: {monitor}")
            if monitor:
                mode = glfw.get_video_mode(monitor)
                if mode:
                    self.fullscreen_size = (mode.size.width, mode.size.height)
                    print(f"DEBUG: Monitor mode: {mode.size.width}x{mode.size.height}")
                else:
                    print("WARNING: Could not get video mode, using default")
                    self.fullscreen_size = (1280, 720)
            else:
                print("WARNING: No primary monitor, using default size")
                self.fullscreen_size = (1280, 720)
        except Exception as e:
            print(f"WARNING: Error getting monitor info: {e}, using default size")
            self.fullscreen_size = (1280, 720)
            monitor = None

        w, h = self.prefs.resolution or self.fullscreen_size
        print(f"DEBUG: Creating window with size: {w}x{h}")

        # Always create windowed mode (not fullscreen)
        self.window = glfw.create_window(w, h, "JungleLabStudio", None, None)

        if not self.window:
            raise RuntimeError("Failed to create GLFW window")

        glfw.maximize_window(self.window)
        glfw.make_context_current(self.window)
        
        # Force PyOpenGL context initialization
        try:
            gl.glFlush()
        except Exception as e:
            print(f"PyOpenGL Init Warning: {e}")
        
        # Callbacks
        glfw.set_key_callback(self.window, self.on_key)
        glfw.set_window_size_callback(self.window, self.on_resize)
        glfw.set_char_callback(self.window, self.on_char)
        glfw.set_mouse_button_callback(self.window, self.on_mouse_button)
        glfw.set_scroll_callback(self.window, self.on_scroll)
        glfw.set_cursor_pos_callback(self.window, self.on_cursor_pos)
        
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE)
        
        self.osd = OSD(self.window, self.ctx, midi_input=self.midi)
        self.osd.draw_callback = self.draw_ui
        
        self.quad = FullscreenQuad(self.ctx)
        self.audio_tex = self.ctx.texture((self.audio_bins, 1), 1, dtype="f4")
        self.audio_tex.filter = (self.ctx.LINEAR, self.ctx.LINEAR)
        
        self._build_framebuffers()
        self.post = PostChain(self.ctx, self.scene_tex.size)
        self.fx_engine = FXEngine(self.ctx, self.scene_tex.size)

        # Initialize Visual Editor with context
        self.editor = VisualEditor(self.ctx, self.scene_tex.size)

        # Load initial preset
        if self.prefs.preset in PRESET_REGISTRY:
            self.load_preset(self.prefs.preset)
        else:
            self.next_preset()

    def _build_framebuffers(self):
        width, height = aspect_for_orientation(self.fullscreen_size[0], self.fullscreen_size[1], self.orientation)
        print(f"DEBUG: Creating framebuffer with size: {width}x{height}")
        print(f"DEBUG: Orientation: {self.orientation}, Fullscreen size: {self.fullscreen_size}")

        if width <= 0 or height <= 0:
            print(f"ERROR: Invalid framebuffer dimensions: {width}x{height}")
            width, height = 1280, 720
            print(f"DEBUG: Using fallback dimensions: {width}x{height}")

        self.scene_tex = self.ctx.texture((width, height), 4, dtype="f1")
        print(f"DEBUG: Texture created successfully: {self.scene_tex.size}")
        self.scene_tex.filter = (self.ctx.LINEAR, self.ctx.LINEAR)
        depth = self.ctx.depth_renderbuffer((width, height))
        print(f"DEBUG: Depth renderbuffer created")
        self.scene_fbo = self.ctx.framebuffer(color_attachments=[self.scene_tex], depth_attachment=depth)
        print(f"DEBUG: Framebuffer created successfully")

    def on_resize(self, window, width, height):
        self.fullscreen_size = (width, height)
        self._build_framebuffers()
        self.post.set_resolution(self.scene_tex.size)
        if self.fx_engine:
            self.fx_engine.set_size(self.scene_tex.size)
        if self.osd:
            self.osd.resize_callback(window, width, height)

    def on_key(self, window, key, scancode, action, mods):
        if self.osd:
            self.osd.key_callback(window, key, scancode, action, mods)
            if self.osd.io.want_capture_keyboard:
                return

        if action != glfw.PRESS: return

        if key == glfw.KEY_ESCAPE:
            # Perhaps toggle UI focus or just do nothing in Desktop mode
            pass
        elif key == glfw.KEY_E:
            self.editor_mode = not self.editor_mode
            print(f"Editor mode: {'ON' if self.editor_mode else 'OFF'}")
        elif key == glfw.KEY_F1:
            self.show_midi_monitor = not self.show_midi_monitor

        # Numeric keys to switch presets (1-9, 0 for 10th)
        preset_keys = {
            glfw.KEY_1: 0, glfw.KEY_2: 1, glfw.KEY_3: 2, glfw.KEY_4: 3, glfw.KEY_5: 4,
            glfw.KEY_6: 5, glfw.KEY_7: 6, glfw.KEY_8: 7, glfw.KEY_9: 8, glfw.KEY_0: 9
        }

        if key in preset_keys:
            preset_idx = preset_keys[key]
            preset_list = list(self.preset_manager.presets.keys())
            if preset_idx < len(preset_list):
                preset_name = preset_list[preset_idx]
                print(f"Hotkey: Loading preset {preset_idx + 1}: {preset_name}")
                self.load_preset(preset_name)

    def on_char(self, window, char):
        if self.osd: self.osd.char_callback(window, char)

    def on_mouse_button(self, window, button, action, mods):
        if self.osd: self.osd.mouse_button_callback(window, button, action, mods)

    def on_scroll(self, window, x_offset, y_offset):
        if self.osd: self.osd.scroll_callback(window, x_offset, y_offset)

    def on_cursor_pos(self, window, x, y):
        if self.osd: self.osd.cursor_pos_callback(window, x, y)

    def _reload_app(self):
        try:
            self.audio.stop()
            self.midi.stop()
            glfw.terminate()
        except: pass
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def _reload_presets(self):
        try:
            # Reload base preset module
            from ..presets import base
            importlib.reload(base)

            # Reload YAML preset loader
            from ..presets import yaml_preset
            importlib.reload(yaml_preset)

            # Rescan YAML templates and presets
            self.preset_manager.load_library()
            self.preset_manager.scan_templates()
            print("Presets reloaded successfully!")

            if self.current_preset:
                self.load_preset(self.current_preset.name)
        except Exception as e:
            print(f"Reload failed: {e}")

    def draw_ui(self):
        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File"):
                if imgui.menu_item("Open Preset...", "Ctrl+O", False)[0]:
                    self._open_preset_file()
                if imgui.menu_item("New Media Preset...", "", False)[0]:
                    self._new_media_preset()
                imgui.separator()
                if imgui.menu_item("Reload Library", "Ctrl+R", False)[0]:
                    self._reload_presets()
                if imgui.menu_item("Restart App", "Ctrl+Shift+R", False)[0]:
                    self._reload_app()
                imgui.separator()
                if imgui.menu_item("Quit", "Alt+F4", False)[0]:
                    glfw.set_window_should_close(self.window, True)
                imgui.end_menu()

            if imgui.begin_menu("Presets"):
                for name, info in self.preset_manager.presets.items():
                    selected = (self.current_preset and self.prefs.preset == name)
                    # Optional: Icon based on kind
                    kind_icon = "(M)" if info["kind"] == "media" else ("(G)" if info["kind"] == "graph" else "(C)")
                    if imgui.menu_item(f"{kind_icon} {name}", "", selected)[0]:
                        self._enter_preset(name)
                imgui.end_menu()

            if imgui.begin_menu("FX"):
                if self.fx_engine:
                    for name in self.fx_engine.fx_defs.keys():
                        if imgui.menu_item(f"Learn: {name}", "", False)[0]:
                            self.learn_target = ("fx", name)
                imgui.end_menu()

            if imgui.begin_menu("Input"):
                if imgui.begin_menu("Audio Device"):
                    devs = list(AudioInput.list_devices()) or ["Default"]
                    for d in devs:
                        if imgui.menu_item(d, "", self.prefs.audio_device == d)[0]:
                            self.prefs.audio_device = None if d == "Default" else d
                            self.restart_audio()
                    imgui.end_menu()

                if imgui.begin_menu("MIDI Device"):
                    devs = list(MidiInput.list_devices()) or ["None"]
                    for d in devs:
                        if imgui.menu_item(d, "", self.prefs.midi_device == d)[0]:
                            self.prefs.midi_device = d if d != "None" else None
                            self.restart_midi()
                    imgui.end_menu()

                if imgui.menu_item("Show Action Map", "", self.show_action_map)[0]:
                    self.show_action_map = not self.show_action_map
                imgui.end_menu()

            if imgui.begin_menu("Options"):
                if imgui.menu_item("Vertical Orientation", "", self.orientation == "vertical")[0]:
                    self.toggle_orientation()
                if imgui.menu_item("Save Config", "", False)[0]:
                    save_preferences(self.prefs)
                if imgui.menu_item("MIDI Monitor", "F1", self.show_midi_monitor)[0]:
                    self.show_midi_monitor = not self.show_midi_monitor
                imgui.end_menu()

            if imgui.begin_menu("Help"):
                imgui.text("NAVIGATION")
                imgui.separator()
                imgui.text("  Mouse: Click UI elements")
                imgui.text("  F1: Toggle MIDI Monitor")
                imgui.separator()
                imgui.text("PRESET HOTKEYS")
                imgui.separator()
                imgui.text("  1-9, 0: Switch to preset 1-10")
                preset_list = list(self.preset_manager.presets.keys())
                for i in range(min(10, len(preset_list))):
                    key = str(i + 1) if i < 9 else "0"
                    imgui.text(f"    {key}: {preset_list[i]}")
                imgui.end_menu()

            # Info on bar
            if self.learn_target:
                imgui.same_line()
                imgui.text_colored((1, 1, 0, 1), f"LEARNING: {self.learn_target[1]}")

            imgui.end_main_menu_bar()

        # MIDI Monitor Window
        if self.show_midi_monitor:
            imgui.set_next_window_size((400, 300), imgui.Cond_.FirstUseEver)
            if imgui.begin("MIDI Monitor", True)[1]:
                if imgui.button("Clear"):
                    self.osd.midi_log.clear()
                imgui.separator()
                imgui.begin_child("Log")
                for line in self.osd.midi_log:
                    imgui.text(line)
                    if self.learn_target and "note_on" in line:
                        imgui.same_line()
                        imgui.text_colored((0,1,0,1), "Captured!")
                imgui.end_child()
            else:
                self.show_midi_monitor = False
            imgui.end()

        # Action Map Window
        if self.show_action_map and self.current_preset:
            imgui.set_next_window_size((400, 400), imgui.Cond_.FirstUseEver)
            if imgui.begin(f"Actions: {self.current_preset.name}", True)[1]:
                imgui.text("Click Learn, then press MIDI key.")
                imgui.separator()
                for act in self.current_preset.actions:
                    note = self.prefs.preset_action_map.get(self.current_preset.name, {}).get(act, "-")
                    imgui.text(f"{act}")
                    imgui.same_line(200)
                    imgui.text(f"Note: {note}")
                    imgui.same_line()
                    if imgui.button(f"Learn##{act}"):
                        self.learn_target = ("preset_action", self.current_preset.name, act)
                imgui.end()
            else:
                self.show_action_map = False

        # Visual Editor
        if self.editor_mode and self.editor:
            self.editor.render()

    def restart_audio(self):
        try: self.audio.stop()
        except: pass
        self.audio = AudioInput(device=self.prefs.audio_device)
        self.audio.start()

    def restart_midi(self):
        try: self.midi.stop()
        except: pass
        self.midi = MidiInput(device=self.prefs.midi_device)
        self.midi.add_listener(self.on_midi)
        if self.osd:
            self.midi.add_listener(self.osd._on_midi_debug)
        self.midi.start()

    def on_midi(self, msg):
        # Delegate to Editor if active
        if self.editor_mode and self.editor:
            self.editor.handle_midi_message(msg)
            # Also dispatch to editor's render graph if available
            if self.editor.executor and self.editor.executor.render_graph:
                self.editor.executor.render_graph.dispatch_midi_to_listeners(msg)
            # If editor is in learn mode, consume the message and don't trigger other actions
            if self.editor.state.midi_learn_mode:
                return

        if msg.type == "note_on":
            # Learn Handling
            if self.learn_target:
                kind = self.learn_target[0]
                if kind == "fx":
                    fx_name = self.learn_target[1]
                    self.prefs.fx_assignments[fx_name] = msg.note
                elif kind == "preset_action":
                    pname, aname = self.learn_target[1], self.learn_target[2]
                    self.prefs.preset_action_map.setdefault(pname, {})[aname] = msg.note
                self.learn_target = None
                return

            # Trigger Handling
            velocity = msg.velocity
            # 1. Global FX
            for fx_name, note in self.prefs.fx_assignments.items():
                if msg.note == note:
                    self.fx_engine.trigger(fx_name, intensity=velocity/127.0, duration=0.5)

            # 2. Preset Actions
            if self.current_preset:
                pmap = self.prefs.preset_action_map.get(self.current_preset.name, {})
                for act, note in pmap.items():
                    if msg.note == note:
                        self.current_preset.trigger_action(act, {"velocity": velocity})

    def toggle_orientation(self):
        self.orientation = "vertical" if self.orientation == "horizontal" else "horizontal"
        self.prefs.orientation = self.orientation
        self._build_framebuffers()
        self.post.set_resolution(self.scene_tex.size)
        if self.fx_engine:
            self.fx_engine.set_size(self.scene_tex.size)

    def run(self):
        self.init_window()
        self.audio.start()
        self.midi.start()
        while not glfw.window_should_close(self.window):
            dt = self.clock.tick()
            self.draw(dt)
            glfw.swap_buffers(self.window)
            glfw.poll_events()
        self.shutdown()

    def draw(self, dt: float):
        # DO NOT clear the screen here - let post-processing handle it
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE)
        self.ctx.viewport = (0, 0, self.fullscreen_size[0], self.fullscreen_size[1])

        # Pump MIDI (Main Thread)
        midi_events = self.midi.consume()
        for msg in midi_events:
            self.on_midi(msg)
        
        # Audio
        audio_data = self.audio.fft_texture_data(self.audio_bins)
        bands = self.audio.band_levels()
        self.audio_tex.write(audio_data.tobytes())
        fft_gain = float(np.mean(audio_data) * 1.5)

        # Preset Render
        self.scene_fbo.use()
        self.ctx.clear(0.02, 0.01, 0.04, 1.0)

        # If in editor mode with nodes, render editor graph instead of preset
        if self.editor_mode and self.editor and self.editor.executor:
            # Check if graph needs rebuild
            if self.editor.executor.needs_rebuild(self.editor.state.graph):
                self.editor.executor.rebuild(self.editor.state.graph)

            # Update and render editor graph
            if self.editor.executor.has_graph():
                self.editor.executor.update(dt, bands)
                self.editor.executor.render()
                # Note: Editor graph renders to its own FBOs, we'll blit the output texture
                output_tex = self.editor.executor.get_output_texture()
                if output_tex:
                    # Blit to scene texture
                    if not hasattr(self, '_editor_blit_prog'):
                        # Create simple blit shader
                        self._editor_blit_prog = self.ctx.program(
                            vertex_shader="""
                            #version 330
                            in vec2 in_pos;
                            out vec2 uv;
                            void main() {
                                uv = (in_pos + 1.0) * 0.5;
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
                        # Create blit quad
                        self._editor_blit_vbo = self.ctx.buffer(np.array([
                            -1.0, -1.0,
                             1.0, -1.0,
                            -1.0,  1.0,
                             1.0,  1.0,
                        ], dtype='f4').tobytes())
                        self._editor_blit_vao = self.ctx.vertex_array(
                            self._editor_blit_prog,
                            [(self._editor_blit_vbo, '2f', 'in_pos')]
                        )

                    output_tex.use(location=0)
                    self._editor_blit_prog['tex0'].value = 0
                    self._editor_blit_vao.render(moderngl.TRIANGLE_STRIP)

            glitch = 0.0
            aberration = 0.0
        elif self.current_preset:
            self.current_preset.size = self.scene_tex.size
            self.current_preset.update_render(dt, self.audio_tex, fft_gain, bands, [], self.orientation)

            glitch = self.current_preset.state.glitch if self.current_preset else 0.0
            aberration = self.current_preset.state.aberration if self.current_preset else 0.0
        else:
            glitch = 0.0
            aberration = 0.0

        # FX Engine Update & Apply
        if self.fx_engine:
            self.fx_engine.update(dt)
            fx_tex = self.fx_engine.apply(self.scene_tex)
        else:
            fx_tex = self.scene_tex

        # Post Processing
        self.post.process(fx_tex, time.time(), glitch, aberration, self.fullscreen_size, self.orientation == "vertical")

        # OSD (ImGui)
        self.ctx.enable_only(moderngl.BLEND)
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
        
        self.osd.render()

    def shutdown(self):
        save_preferences(self.prefs)
        try:
            self.audio.stop()
            self.midi.stop()
            if self.osd: self.osd.shutdown()
        except: pass
        glfw.terminate()
