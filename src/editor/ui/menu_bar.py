"""Menu bar implementation"""
from imgui_bundle import imgui, portable_file_dialogs as pfd
from pathlib import Path
from editor.state import EditorState
from editor.graph.visual_node import create_node, Vector2, VisualNode
from editor.dsl.serializer import PresetSerializer, PresetDeserializer
from editor.events import event_system, Events
from editor.commands import AddNodeCommand, RemoveNodeCommand, BatchCommand
import copy

class MenuBar:
    def __init__(self, state: EditorState):
        self.state = state
        self.show_node_picker = False
        self.node_search_query = ""

    def render(self):
        # Handle keyboard shortcuts
        self._handle_shortcuts()

        if imgui.begin_main_menu_bar():
            self._render_file_menu()
            self._render_edit_menu()
            self._render_view_menu()
            self._render_add_menu()

            # FPS Counter
            fps = imgui.get_io().framerate
            text = f"FPS: {fps:.1f}"
            # Simple right alignment
            width = imgui.get_window_width()
            text_width = imgui.calc_text_size(text).x
            # Ensure we don't overlap if window is too small
            if imgui.get_cursor_pos_x() + text_width + 20 < width:
                imgui.set_cursor_pos_x(width - text_width - 10)
                imgui.text(text)

            imgui.end_main_menu_bar()

        if self.show_node_picker:
            self._render_node_picker()

    def _handle_shortcuts(self):
        """Handle keyboard shortcuts"""
        io = imgui.get_io()

        # Check if Ctrl is pressed
        ctrl = io.key_ctrl

        if ctrl:
            # Ctrl+N - New
            if imgui.is_key_pressed(imgui.Key.n):
                self._new_preset()

            # Ctrl+O - Open
            elif imgui.is_key_pressed(imgui.Key.o):
                self._open_preset()

            # Ctrl+S - Save
            elif imgui.is_key_pressed(imgui.Key.s):
                self._save_preset()

            # Ctrl+Z - Undo
            elif imgui.is_key_pressed(imgui.Key.z):
                if not io.key_shift:
                    self._undo()
                else:
                    # Ctrl+Shift+Z - Redo (alternative)
                    self._redo()

            # Ctrl+Y - Redo
            elif imgui.is_key_pressed(imgui.Key.y):
                self._redo()

            # Ctrl+C - Copy
            elif imgui.is_key_pressed(imgui.Key.c):
                self._copy()

            # Ctrl+V - Paste
            elif imgui.is_key_pressed(imgui.Key.v):
                self._paste()

            # Ctrl+X - Cut
            elif imgui.is_key_pressed(imgui.Key.x):
                self._cut()

        # Delete key - Remove selected nodes
        if imgui.is_key_pressed(imgui.Key.delete):
            for node_id in list(self.state.graph.selection):
                self.state.graph.remove_node(node_id)

    def _render_file_menu(self):
        if imgui.begin_menu("File"):
            if imgui.menu_item("New", "Ctrl+N", False)[0]:
                self._new_preset()

            if imgui.menu_item("Open...", "Ctrl+O", False)[0]:
                self._open_preset()

            if imgui.menu_item("Save", "Ctrl+S", False)[0]:
                self._save_preset()

            if imgui.menu_item("Save As...", "", False)[0]:
                self._save_preset_as()

            imgui.separator()

            if imgui.menu_item("Exit", "", False)[0]:
                pass  # Handle exit

            imgui.end_menu()

    def _render_edit_menu(self):
        if imgui.begin_menu("Edit"):
            can_undo = self.state.command_history.can_undo()
            can_redo = self.state.command_history.can_redo()

            if imgui.menu_item("Undo", "Ctrl+Z", False, can_undo)[0]:
                self._undo()

            if imgui.menu_item("Redo", "Ctrl+Y", False, can_redo)[0]:
                self._redo()

            imgui.separator()

            has_selection = len(self.state.graph.selection) > 0
            has_clipboard = len(self.state.clipboard_nodes) > 0

            if imgui.menu_item("Cut", "Ctrl+X", False, has_selection)[0]:
                self._cut()

            if imgui.menu_item("Copy", "Ctrl+C", False, has_selection)[0]:
                self._copy()

            if imgui.menu_item("Paste", "Ctrl+V", False, has_clipboard)[0]:
                self._paste()

            imgui.separator()

            if imgui.menu_item("Delete", "Del", False, has_selection)[0]:
                for node_id in list(self.state.graph.selection):
                    cmd = RemoveNodeCommand(node_id)
                    self.state.command_history.execute(cmd, self.state.graph)
                    event_system.emit(Events.NODE_REMOVED, node_id)

            imgui.end_menu()

    def _render_view_menu(self):
        if imgui.begin_menu("View"):
            _, self.state.show_grid = imgui.menu_item("Show Grid", "", self.state.show_grid)
            _, self.state.snap_to_grid = imgui.menu_item("Snap to Grid", "", self.state.snap_to_grid)

            imgui.separator()

            if imgui.menu_item("Zoom In", "+", False)[0]:
                self.state.canvas_zoom = min(3.0, self.state.canvas_zoom + 0.1)

            if imgui.menu_item("Zoom Out", "-", False)[0]:
                self.state.canvas_zoom = max(0.1, self.state.canvas_zoom - 0.1)

            if imgui.menu_item("Reset Zoom", "0", False)[0]:
                self.state.canvas_zoom = 1.0

            imgui.end_menu()

    def _render_add_menu(self):
        if imgui.begin_menu("Add"):
            if imgui.menu_item("Init", "", False)[0]:
                self._add_node("init")
                
            if imgui.menu_item("Node...", "", False)[0]:
                self.show_node_picker = True
                self.node_search_query = "" # Reset search on open

            imgui.end_menu()

    def _render_node_picker(self):
        imgui.open_popup("Add Node")

        if imgui.begin_popup("Add Node"):
            # Search Filter
            imgui.set_next_item_width(200)
            _, self.node_search_query = imgui.input_text("Search", self.node_search_query, 32)
            imgui.separator()

            # Quick Add: Init
            if not self.node_search_query or "init" in self.node_search_query.lower():
                if imgui.selectable("Init", False)[0]:
                    self._add_node("init")
                    self.show_node_picker = False
                imgui.separator()

            # Categorized node types
            node_categories = {
                "MIDI Control": ["midi.listener", "midi.launcher"],
                "Generators": ["shader", "generator.noise", "generator.checkerboard", "particles", "geometry"],
                "Effects - Basic": ["effect.blur", "effect.glow", "effect.vignette", "effect.color", "effect.color_gradient", "effect.advanced_bloom"],
                "Effects - Distortion": ["effect.distort", "effect.transform", "effect.kaleidoscope", "effect.mirror", "effect.feedback"],
                "Effects - Stylize": ["effect.pixelate", "effect.edge_detect", "effect.posterize"],
                "Compositing": ["composite", "blend", "composite.blend_modes", "math.operation"],
                "Output": ["output", "preview"],
                "Utility": ["utility.buffer"]
            }

            for category, node_types in node_categories.items():
                # Filter nodes
                if self.node_search_query:
                    filtered = [n for n in node_types if self.node_search_query.lower() in n.lower()]
                    if not filtered:
                        continue
                    # Auto-expand if searching
                    imgui.set_next_item_open(True)
                    nodes_to_show = filtered
                else:
                    nodes_to_show = node_types

                if imgui.tree_node(category):
                    for node_type in nodes_to_show:
                        if imgui.selectable(f"  {node_type}", False)[0]:
                            self._add_node(node_type)
                            self.show_node_picker = False

                    imgui.tree_pop()

            imgui.end_popup()

    def _add_node(self, node_type: str):
        """Helper to add a node at the center of the screen"""
        # Calculate center of visible canvas area
        io = imgui.get_io()
        center_screen = Vector2(io.display_size.x / 2, io.display_size.y / 2)
        center = self.state.screen_to_canvas(center_screen)

        # Determine prefix
        prefix = "node_"
        if node_type == "init": prefix = "init"
        elif node_type in ["shader", "video", "particles", "geometry"]: prefix = f"gen_{node_type}"
        elif node_type.startswith("effect."): prefix = f"fx_{node_type.split('.')[1]}"
        elif node_type in ["composite", "blend", "mask"]: prefix = f"comp_{node_type}"
        elif node_type in ["output", "preview"]: prefix = f"out_{node_type}"

        # Generate unique ID
        new_id = self.state.graph.generate_unique_node_id(prefix)

        node = create_node(node_type, center, custom_id=new_id)
        cmd = AddNodeCommand(node)
        self.state.command_history.execute(cmd, self.state.graph)
        event_system.emit(Events.NODE_ADDED, node)

    def _new_preset(self):
        self.state.graph.clear()
        self.state.current_file = None
        self.state.is_modified = False
        event_system.emit(Events.FILE_NEW)

    def _open_preset(self):
        """Open preset with file dialog"""
        try:
            # Show open file dialog
            result = pfd.open_file(
                "Open Preset",
                "presets/templates",
                ["YAML Files (*.yaml *.yml)", "*.yaml *.yml", "All Files", "*"]
            )

            if result and result.result():
                files = result.result()
                if files:
                    path = Path(files[0])
                    graph = PresetDeserializer.deserialize_from_file(str(path))
                    self.state.graph = graph
                    self.state.current_file = path
                    self.state.is_modified = False
                    event_system.emit(Events.FILE_OPENED, path)
                    print(f"✓ Loaded: {path}")
        except Exception as e:
            print(f"✗ Error opening preset: {e}")
            pfd.message("Error", f"Failed to open preset:\n{e}", pfd.choice.ok)

    def _save_preset(self):
        if self.state.current_file:
            self._do_save(self.state.current_file)
        else:
            self._save_preset_as()

    def _save_preset_as(self):
        """Save preset as with file dialog"""
        try:
            # Show save file dialog
            result = pfd.save_file(
                "Save Preset As",
                "presets/my_preset.yaml",
                ["YAML Files (*.yaml *.yml)", "*.yaml *.yml"]
            )

            if result and result.result():
                path_str = result.result()
                if path_str:
                    path = Path(path_str)
                    # Ensure .yaml extension
                    if path.suffix not in ['.yaml', '.yml']:
                        path = path.with_suffix('.yaml')
                    self._do_save(path)
        except Exception as e:
            print(f"✗ Error saving preset: {e}")
            pfd.message("Error", f"Failed to save preset:\n{e}", pfd.choice.ok)

    def _do_save(self, path: Path):
        """Save preset to file"""
        try:
            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            PresetSerializer.serialize_to_file(self.state.graph, str(path))
            self.state.current_file = path
            self.state.is_modified = False
            event_system.emit(Events.FILE_SAVED, path)
            print(f"✓ Saved: {path}")

            # Show success notification
            pfd.notify("Preset Saved", f"Successfully saved to:\n{path}", pfd.icon.info)
        except Exception as e:
            print(f"✗ Error saving preset: {e}")
            pfd.message("Error", f"Failed to save preset:\n{e}", pfd.choice.ok)

    # === Undo/Redo ===

    def _undo(self):
        """Undo the last command"""
        if self.state.command_history.undo(self.state.graph):
            print(f"✓ Undo: {self.state.command_history.get_redo_description()}")
            event_system.emit(Events.FILE_MODIFIED)
        else:
            print("✗ Nothing to undo")

    def _redo(self):
        """Redo the last undone command"""
        if self.state.command_history.redo(self.state.graph):
            print(f"✓ Redo: {self.state.command_history.get_undo_description()}")
            event_system.emit(Events.FILE_MODIFIED)
        else:
            print("✗ Nothing to redo")

    # === Copy/Paste/Cut ===

    def _copy(self):
        """Copy selected nodes to clipboard"""
        selected_nodes = self.state.graph.get_selected_nodes()
        if not selected_nodes:
            print("✗ No nodes selected to copy")
            return

        # Serialize selected nodes
        self.state.clipboard_nodes = []
        for node in selected_nodes:
            node_data = {
                'node_type': node.node_type,
                'display_name': node.display_name,
                'params': copy.deepcopy(node.params),
                'animations': copy.deepcopy(node.animations),
                'triggers': copy.deepcopy(node.triggers),
                'position': (node.position.x, node.position.y),
                'size': (node.size.x, node.size.y),
                'color': (node.color.r, node.color.g, node.color.b),
            }
            self.state.clipboard_nodes.append(node_data)

        print(f"✓ Copied {len(selected_nodes)} node(s)")

    def _paste(self):
        """Paste nodes from clipboard"""
        if not self.state.clipboard_nodes:
            print("✗ Clipboard is empty")
            return

        # Clear current selection
        self.state.graph.clear_selection()

        # Create commands for all pasted nodes
        commands = []
        offset_x, offset_y = 50, 50  # Offset for pasted nodes

        for node_data in self.state.clipboard_nodes:
            # Generate unique ID
            base_name = node_data['node_type'].replace('.', '_')
            new_id = self.state.graph.generate_unique_node_id(base_name)

            # Create new node at offset position
            new_pos = Vector2(
                node_data['position'][0] + offset_x,
                node_data['position'][1] + offset_y
            )

            node = create_node(node_data['node_type'], new_pos, custom_id=new_id)
            node.display_name = node_data['display_name']
            node.params = copy.deepcopy(node_data['params'])
            node.animations = copy.deepcopy(node_data['animations'])
            node.triggers = copy.deepcopy(node_data['triggers'])

            commands.append(AddNodeCommand(node))

        # Execute as batch command
        batch = BatchCommand(commands, f"Paste {len(commands)} node(s)")
        if self.state.command_history.execute(batch, self.state.graph):
            print(f"✓ Pasted {len(commands)} node(s)")
            event_system.emit(Events.FILE_MODIFIED)
        else:
            print("✗ Failed to paste nodes")

    def _cut(self):
        """Cut selected nodes (copy + delete)"""
        selected_nodes = self.state.graph.get_selected_nodes()
        if not selected_nodes:
            print("✗ No nodes selected to cut")
            return

        # First copy
        self._copy()

        # Then delete with undo support
        commands = []
        for node in selected_nodes:
            commands.append(RemoveNodeCommand(node.id))

        batch = BatchCommand(commands, f"Cut {len(commands)} node(s)")
        if self.state.command_history.execute(batch, self.state.graph):
            print(f"✓ Cut {len(commands)} node(s)")
            event_system.emit(Events.FILE_MODIFIED)
        else:
            print("✗ Failed to cut nodes")
