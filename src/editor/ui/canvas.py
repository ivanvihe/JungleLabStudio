"""Complete node canvas implementation"""
from imgui_bundle import imgui
from editor.state import EditorState, InteractionMode
from editor.graph.visual_node import Vector2, create_node
from editor.events import event_system, Events
from editor.commands import AddNodeCommand, RemoveNodeCommand, MoveNodeCommand

class NodeCanvas:
    def __init__(self, state: EditorState):
        self.state = state
        self.show_context_menu = False
        self.context_menu_pos = Vector2(0, 0)
        self.rename_buffers = {} # node_id -> string buffer
        self.drag_start_positions = {} # node_id -> (x, y) for undo/redo

    def render(self):
        # Get available space
        canvas_pos = imgui.get_cursor_screen_pos()
        canvas_size = imgui.get_content_region_avail()

        # Use window hover state since we don't have an invisible button anymore
        is_hovered = imgui.is_window_hovered()

        # Get draw list
        draw_list = imgui.get_window_draw_list()

        # Background
        draw_list.add_rect_filled(
            imgui.ImVec2(canvas_pos[0], canvas_pos[1]),
            imgui.ImVec2(canvas_pos[0] + canvas_size[0], canvas_pos[1] + canvas_size[1]),
            imgui.get_color_u32(imgui.ImVec4(0.15, 0.15, 0.15, 1.0))
        )

        # Draw grid if enabled
        if self.state.show_grid:
            self._draw_grid(draw_list, canvas_pos, canvas_size)

        # Draw all connections
        for conn in self.state.graph.connections.values():
            self._draw_connection(draw_list, canvas_pos, conn)

        # Draw all nodes
        for node in self.state.graph.nodes.values():
            self._draw_node(draw_list, canvas_pos, node)
            
        # Handle mouse input (After drawing nodes to detect widget clicks)
        if is_hovered:
            self._handle_mouse(canvas_pos)
            
        # Render node menus
        self._render_node_menus()

        # Context menu (Right click on canvas)
        self._render_context_menu()

    def _draw_grid(self, draw_list, canvas_pos, canvas_size):
        grid_size = self.state.grid_size * self.state.canvas_zoom
        grid_color = imgui.get_color_u32(imgui.ImVec4(0.2, 0.2, 0.2, 0.4))

        # Vertical lines
        offset_x = self.state.canvas_offset.x % grid_size
        x = canvas_pos[0] + offset_x
        while x < canvas_pos[0] + canvas_size[0]:
            draw_list.add_line(
                imgui.ImVec2(x, canvas_pos[1]),
                imgui.ImVec2(x, canvas_pos[1] + canvas_size[1]),
                grid_color
            )
            x += grid_size

        # Horizontal lines
        offset_y = self.state.canvas_offset.y % grid_size
        y = canvas_pos[1] + offset_y
        while y < canvas_pos[1] + canvas_size[1]:
            draw_list.add_line(
                imgui.ImVec2(canvas_pos[0], y),
                imgui.ImVec2(canvas_pos[0] + canvas_size[0], y),
                grid_color
            )
            y += grid_size

    def _draw_node(self, draw_list, canvas_pos, node):
        # Convert to screen space
        screen_x = canvas_pos[0] + node.position.x * self.state.canvas_zoom + self.state.canvas_offset.x
        screen_y = canvas_pos[1] + node.position.y * self.state.canvas_zoom + self.state.canvas_offset.y
        width = node.size.x * self.state.canvas_zoom
        height = node.size.y * self.state.canvas_zoom

        # Node color
        if node.selected:
            color = imgui.get_color_u32(imgui.ImVec4(
                min(node.color.r * 1.3, 1.0),
                min(node.color.g * 1.3, 1.0),
                min(node.color.b * 1.3, 1.0), 1.0
            ))
            border = imgui.get_color_u32(imgui.ImVec4(1.0, 1.0, 0.3, 1.0))
        else:
            color = imgui.get_color_u32(imgui.ImVec4(node.color.r, node.color.g, node.color.b, 1.0))
            border = imgui.get_color_u32(imgui.ImVec4(0.3, 0.3, 0.3, 1.0))

        # Draw node body
        draw_list.add_rect_filled(
            imgui.ImVec2(screen_x, screen_y),
            imgui.ImVec2(screen_x + width, screen_y + height),
            color, 4.0
        )
        draw_list.add_rect(
            imgui.ImVec2(screen_x, screen_y),
            imgui.ImVec2(screen_x + width, screen_y + height),
            border, 4.0, thickness=2.0 if node.selected else 1.0
        )

        # Draw header
        header_h = 24
        draw_list.add_rect_filled(
            imgui.ImVec2(screen_x, screen_y),
            imgui.ImVec2(screen_x + width, screen_y + header_h),
            imgui.get_color_u32(imgui.ImVec4(0.0, 0.0, 0.0, 0.3)), 4.0
        )

        # Draw title
        draw_list.add_text(
            imgui.ImVec2(screen_x + 8, screen_y + 4),
            imgui.get_color_u32(imgui.ImVec4(1, 1, 1, 1)),
            node.display_name
        )
        
        # Draw Menu Button (Triangle/Arrow)
        menu_btn_size = 16
        menu_btn_x = screen_x + width - menu_btn_size - 4
        menu_btn_y = screen_y + 4
        
        # Use ImGui button logic for interaction
        imgui.set_cursor_screen_pos(imgui.ImVec2(menu_btn_x, menu_btn_y))
        
        # Fix: Use unique ID directly to avoid scope mismatch with begin_popup
        if imgui.arrow_button(f"btn_{node.id}", imgui.Dir_.down):
            imgui.open_popup(f"node_menu_{node.id}")
        
        # Draw port labels (Inputs Left, Outputs Right) - No circles
        
        # LEFT = inputs
        for i, port in enumerate(node.inputs):
            port_y = screen_y + header_h + 12 + i * 20
            
            # Draw port label
            draw_list.add_text(
                imgui.ImVec2(screen_x + 8, port_y - 6),
                imgui.get_color_u32(imgui.ImVec4(0.9, 0.9, 0.9, 1)),
                port.name
            )

        # RIGHT = outputs
        for i, port in enumerate(node.outputs):
            port_y = screen_y + header_h + 12 + i * 20
            
            # Draw port label (aligned to right)
            text_size = imgui.calc_text_size(port.name)
            draw_list.add_text(
                imgui.ImVec2(screen_x + width - text_size.x - 8, port_y - 6),
                imgui.get_color_u32(imgui.ImVec4(0.9, 0.9, 0.9, 1)),
                port.name
            )

    def _render_node_menus(self):
        """Render context menus for all nodes"""
        nodes_to_delete = []
        
        for node in self.state.graph.nodes.values():
            if imgui.begin_popup(f"node_menu_{node.id}"):
                imgui.text(f"Node: {node.id}")
                imgui.separator()
                
                # Rename
                if node.id not in self.rename_buffers:
                    self.rename_buffers[node.id] = node.display_name
                    
                changed, new_name = imgui.input_text("Rename", self.rename_buffers[node.id])
                if changed:
                    self.rename_buffers[node.id] = new_name
                    node.display_name = new_name
                
                # Connect To...
                if imgui.begin_menu("Connect to..."):
                    # List other nodes
                    for target_node in self.state.graph.nodes.values():
                        if target_node.id == node.id: continue # Skip self
                        
                        # Check if target has inputs
                        if not target_node.inputs: continue
                        
                        # Show menu item
                        # Use display name + ID for clarity
                        label = f"{target_node.display_name} ({target_node.id})"
                        if imgui.menu_item(label, "", False)[0]:
                            self._connect_nodes_smart(node, target_node)
                            
                    imgui.end_menu()
                
                imgui.separator()
                
                if imgui.menu_item("Delete", "", False)[0]:
                    nodes_to_delete.append(node.id)

                imgui.end_popup()

        # Apply deletions using command pattern
        for node_id in nodes_to_delete:
            cmd = RemoveNodeCommand(node_id)
            self.state.command_history.execute(cmd, self.state.graph)
            event_system.emit(Events.NODE_REMOVED, node_id)

    def _connect_nodes_smart(self, source, target):
        """Connect primary output of source to first free input of target"""
        if not source.outputs: 
            print(f"Cannot connect: {source.id} has no outputs")
            return
            
        source_port = source.outputs[0].name
        
        # Find first unconnected input if possible, or just the first compatible one
        target_port = None
        for port in target.inputs:
            if not port.connected:
                target_port = port.name
                break
        
        # If all connected, just take the first one (maybe replace?)
        if not target_port and target.inputs:
            target_port = target.inputs[0].name
            
        if target_port:
            self.state.graph.connect(source.id, source_port, target.id, target_port)
            event_system.emit(Events.CONNECTION_CREATED)
            print(f"Connected {source.id} -> {target.id}")

    def _draw_connection(self, draw_list, canvas_pos, conn):
        source = self.state.graph.get_node(conn.source_node_id)
        target = self.state.graph.get_node(conn.target_node_id)
        if not source or not target:
            return

        # Get port positions
        # Recalculate positions matching _draw_node logic
        header_h = 24
        
        # Source Output
        src_port_idx = 0
        for i, p in enumerate(source.outputs):
            if p.name == conn.source_port: src_port_idx = i; break
            
        start_x = canvas_pos[0] + (source.position.x + source.size.x) * self.state.canvas_zoom + self.state.canvas_offset.x
        start_y = canvas_pos[1] + (source.position.y + header_h + 12 + src_port_idx * 20) * self.state.canvas_zoom + self.state.canvas_offset.y

        # Target Input
        tgt_port_idx = 0
        for i, p in enumerate(target.inputs):
            if p.name == conn.target_port: tgt_port_idx = i; break

        end_x = canvas_pos[0] + target.position.x * self.state.canvas_zoom + self.state.canvas_offset.x
        end_y = canvas_pos[1] + (target.position.y + header_h + 12 + tgt_port_idx * 20) * self.state.canvas_zoom + self.state.canvas_offset.y

        # Draw bezier curve
        ctrl_offset = abs(end_x - start_x) * 0.5
        draw_list.add_bezier_cubic(
            imgui.ImVec2(start_x, start_y),
            imgui.ImVec2(start_x + ctrl_offset, start_y),
            imgui.ImVec2(end_x - ctrl_offset, end_y),
            imgui.ImVec2(end_x, end_y),
            imgui.get_color_u32(imgui.ImVec4(0.8, 0.8, 0.8, 1.0)), 2.0
        )

    def _handle_mouse(self, canvas_pos):
        # Prevent canvas interaction if interacting with UI items (like the arrow button)
        if imgui.is_any_item_hovered() or imgui.is_any_item_active():
            return

        io = imgui.get_io()
        mouse_pos = Vector2(io.mouse_pos.x - canvas_pos[0], io.mouse_pos.y - canvas_pos[1])

        # Delete selected nodes with Delete/Backspace key
        if imgui.is_key_pressed(imgui.Key.delete) or imgui.is_key_pressed(imgui.Key.backspace):
            for node_id in list(self.state.graph.selection):
                cmd = RemoveNodeCommand(node_id)
                self.state.command_history.execute(cmd, self.state.graph)
                event_system.emit(Events.NODE_REMOVED, node_id)

        # Pan with middle mouse
        if imgui.is_mouse_dragging(2):  # Middle mouse
            delta = imgui.get_mouse_drag_delta(2)
            self.state.canvas_offset.x += delta[0]
            self.state.canvas_offset.y += delta[1]
            imgui.reset_mouse_drag_delta(2)

        # Zoom with wheel
        if io.mouse_wheel != 0:
            zoom_delta = io.mouse_wheel * 0.1
            self.state.canvas_zoom = max(0.1, min(3.0, self.state.canvas_zoom + zoom_delta))

        # Right click - context menu
        if imgui.is_mouse_clicked(1):  # Right mouse button
            canvas_mouse = self.state.screen_to_canvas(mouse_pos)
            self.context_menu_pos = canvas_mouse
            self.show_context_menu = True
            imgui.open_popup("canvas_context_menu")

        # Handle left click (Selection & Dragging)
        if imgui.is_mouse_clicked(0):
            # Node selection
            canvas_mouse = self.state.screen_to_canvas(mouse_pos)
            clicked_node = self.state.graph.get_node_at_position(canvas_mouse)

            if clicked_node:
                if not io.key_shift:
                    self.state.graph.clear_selection()
                self.state.graph.select([clicked_node.id], add_to_selection=io.key_shift)
                self.state.is_dragging = True
                self.state.drag_start_pos = canvas_mouse
                # Store initial positions for undo
                self.drag_start_positions = {
                    node.id: (node.position.x, node.position.y)
                    for node in self.state.graph.get_selected_nodes()
                }
            else:
                self.state.graph.clear_selection()

        # Drag selected nodes
        if imgui.is_mouse_dragging(0) and self.state.is_dragging:
            canvas_mouse = self.state.screen_to_canvas(mouse_pos)
            delta = Vector2(
                canvas_mouse.x - self.state.drag_start_pos.x,
                canvas_mouse.y - self.state.drag_start_pos.y
            )

            for node in self.state.graph.get_selected_nodes():
                node.position.x += delta.x
                node.position.y += delta.y
                if self.state.snap_to_grid:
                    node.position = self.state.snap_position(node.position)

            self.state.drag_start_pos = canvas_mouse

        # Handle mouse release - create MoveNodeCommand for undo/redo
        if imgui.is_mouse_released(0):
            if self.state.is_dragging and self.drag_start_positions:
                # Create move command with old and new positions
                node_positions = {}
                for node_id, old_pos in self.drag_start_positions.items():
                    node = self.state.graph.get_node(node_id)
                    if node:
                        new_pos = (node.position.x, node.position.y)
                        # Only add if position actually changed
                        if old_pos != new_pos:
                            node_positions[node_id] = (old_pos, new_pos)

                if node_positions:
                    cmd = MoveNodeCommand(node_positions)
                    self.state.command_history.execute(cmd, self.state.graph)
                    event_system.emit(Events.NODE_MOVED)

                self.drag_start_positions = {}

            self.state.is_dragging = False

    def _create_node_at_context_pos(self, node_type: str):
        """Helper to create node with unique ID at context menu position"""
        # Determine prefix
        prefix = "node_"
        if node_type == "init":
            prefix = "init"
        elif node_type == "shadertoy":
            prefix = "shadertoy"
        elif node_type in ["shader", "video", "particles", "geometry"]:
            prefix = f"gen_{node_type}"
        elif node_type.startswith("generator."):
            prefix = f"gen_{node_type.split('.')[1]}"
        elif node_type.startswith("effect."):
            prefix = f"fx_{node_type.split('.')[1]}"
        elif node_type.startswith("vfx."):
            # vfx.glitch.vhs -> vfx_glitch_vhs
            prefix = node_type.replace(".", "_")
        elif node_type.startswith("midi."):
            prefix = f"midi_{node_type.split('.')[1]}"
        elif node_type.startswith("composite"):
            prefix = "comp"
        elif node_type == "blend":
            prefix = "blend"
        elif node_type.startswith("math."):
            prefix = f"math_{node_type.split('.')[1]}"
        elif node_type in ["output", "preview"]:
            prefix = f"out_{node_type}"

        # Generate unique ID
        new_id = self.state.graph.generate_unique_node_id(prefix)

        node = create_node(node_type, self.context_menu_pos, custom_id=new_id)
        cmd = AddNodeCommand(node)
        self.state.command_history.execute(cmd, self.state.graph)
        event_system.emit(Events.NODE_ADDED, node.id)

    def _render_context_menu(self):
        """Render right-click context menu for adding nodes"""
        if imgui.begin_popup("canvas_context_menu"):
            # Auto-Organize option
            if imgui.selectable("⚡ Auto-Organize", False)[0]:
                self.state.graph.auto_organize()
                imgui.close_current_popup()
                self.show_context_menu = False

            imgui.separator()
            imgui.text("Add Node")
            imgui.separator()

            node_categories = {
                "Core / Setup": {
                    "init": "Init",
                    "output": "Output",
                    "preview": "Preview",
                },
                "MIDI Control": {
                    "midi.listener": "MIDI Listener",
                    "midi.launcher": "MIDI Launcher",
                },
                "Generators": {
                    "shadertoy": "Shadertoy Shader",
                    "shader": "Custom Shader",
                    "generator.noise": "Noise Pattern",
                    "generator.checkerboard": "Checkerboard",
                    "particles": "Particle System",
                    "geometry": "Geometry",
                },
                "Effects": {
                    "effect.blur": "Blur",
                    "effect.glow": "Glow / Bloom",
                    "effect.advanced_bloom": "Advanced Bloom",
                    "effect.vignette": "Vignette",
                    "effect.color": "Color Adjust",
                    "effect.color_gradient": "Color Gradient",
                    "effect.distort": "Distort (Wave/Swirl)",
                    "effect.transform": "Transform (Rotate/Scale)",
                    "effect.kaleidoscope": "Kaleidoscope",
                    "effect.mirror": "Mirror",
                    "effect.feedback": "Feedback / Trails",
                    "effect.pixelate": "Pixelate",
                    "effect.edge_detect": "Edge Detect",
                    "effect.posterize": "Posterize",
                },
                "VFX / Glitch": {
                    "vfx.glitch.vhs": "Glitch VHS",
                    "vfx.glitch.rgb": "Glitch RGB Split",
                    "vfx.glitch.scanlines": "Glitch Scanlines",
                    "vfx.glitch.noise": "Glitch Noise",
                    "vfx.glitch.blocks": "Glitch Blocks",
                    "vfx.glitch.displacement": "Glitch Displacement",
                    "vfx.crt": "CRT Monitor",
                    "vfx.datamosh": "Datamosh",
                },
                "Compositing": {
                    "blend": "Blend",
                    "composite.blend_modes": "Blend Modes (Screen/Multiply/etc)",
                    "composite": "Composite",
                    "math.operation": "Math Operation",
                },
            }

            for category, nodes in node_categories.items():
                if imgui.tree_node(category):
                    for node_type, display_name in nodes.items():
                        if imgui.selectable(f"  {display_name}", False)[0]:
                            self._create_node_at_context_pos(node_type)
                            imgui.close_current_popup()
                            self.show_context_menu = False

                    imgui.tree_pop()

            imgui.end_popup()
        else:
            self.show_context_menu = False
