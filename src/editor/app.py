"""Main editor application"""
from imgui_bundle import imgui
from editor.state import EditorState
from editor.ui.canvas import NodeCanvas
from editor.ui.menu_bar import MenuBar
from editor.ui.inspector import Inspector
from editor.ui.preview import PreviewPanel
from editor.ui.yaml_editor import YamlEditor
from editor.ui.notifications import NotificationManager, NotificationType
from editor.events import event_system, Events
from editor.graph.executor import GraphExecutor
from typing import Optional
import moderngl
from core.error_handling import get_error_handler, ErrorSeverity, ErrorCategory

class VisualEditor:
    def __init__(self, ctx: Optional[moderngl.Context] = None, size: tuple = (800, 600)):
        self.state = EditorState()
        self.canvas = NodeCanvas(self.state)
        self.menu_bar = MenuBar(self.state)
        self.inspector = Inspector(self.state)
        self.preview = PreviewPanel()
        self.yaml_editor = YamlEditor(self.state)
        self.notifications = NotificationManager()

        # Graph executor for live preview
        self.ctx = ctx
        self.executor = GraphExecutor(ctx, size) if ctx else None
        self.show_preview = True

        # Subscribe to graph changes
        event_system.subscribe(Events.NODE_ADDED, self._on_graph_changed)
        event_system.subscribe(Events.NODE_REMOVED, self._on_graph_changed)
        event_system.subscribe(Events.CONNECTION_CREATED, self._on_graph_changed)
        event_system.subscribe(Events.CONNECTION_REMOVED, self._on_graph_changed)
        event_system.subscribe(Events.FILE_OPENED, self._on_graph_changed)

        # Register error handler callback to show notifications
        error_handler = get_error_handler()
        error_handler.register_callback(self._on_error_occurred)

    def _on_graph_changed(self, event):
        """Rebuild executor when graph changes"""
        if self.executor:
            self.executor.rebuild(self.state.graph)

        # Also refresh YAML if it's not dirty/focused?
        # We let YamlEditor handle its own refresh logic on render
        self.yaml_editor.needs_refresh = True

    def _on_error_occurred(self, message: str, severity: ErrorSeverity, category: ErrorCategory):
        """Callback for error handler to show notifications"""
        if severity == ErrorSeverity.ERROR or severity == ErrorSeverity.CRITICAL:
            self.notifications.error(f"[{category.value}] {message}")
        elif severity == ErrorSeverity.WARNING:
            self.notifications.warning(f"[{category.value}] {message}")
        elif severity == ErrorSeverity.INFO:
            # Only show INFO for certain categories
            if category in [ErrorCategory.FILE_IO, ErrorCategory.GRAPH]:
                self.notifications.info(f"[{category.value}] {message}")

    def render(self):
        """Render the editor"""
        # Menu bar
        self.menu_bar.render()

        # Main window with docking
        io = imgui.get_io()
        display_w, display_h = io.display_size.x, io.display_size.y
        
        menu_height = 20
        content_h = display_h - menu_height
        half_w = display_w * 0.5
        
        # Left Column Heights
        left_top_h = content_h * 0.7
        left_bottom_h = content_h * 0.3

        # 1. Editor Area (Left Top - 70%) - Tabs
        imgui.set_next_window_pos((0, menu_height))
        imgui.set_next_window_size((half_w, left_top_h))

        imgui.begin("Editor View", flags=imgui.WindowFlags_.no_title_bar | imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_collapse | imgui.WindowFlags_.no_bring_to_front_on_focus)
        
        if imgui.begin_tab_bar("EditorTabs"):
            if imgui.begin_tab_item("Visual Graph")[0]:
                self.canvas.render()
                imgui.end_tab_item()
            
            if imgui.begin_tab_item("YAML Code")[0]:
                self.yaml_editor.render()
                imgui.end_tab_item()
            
            imgui.end_tab_bar()
            
        imgui.end()

        # 2. Inspector (Left Bottom - 30%)
        imgui.set_next_window_pos((0, menu_height + left_top_h))
        imgui.set_next_window_size((half_w, left_bottom_h))

        self.inspector.render()

        # 3. Preview (Right Full Height)
        imgui.set_next_window_pos((half_w, menu_height))
        imgui.set_next_window_size((half_w, content_h))
        # Preview panel creates its own window, we just set pos/size for it
        self.preview.render(self.executor, self.state.graph, display_w)

        # 4. Render notifications (overlay on top)
        self.notifications.render((display_w, display_h))

    def update(self, dt: float, fft_bands=None):
        """Update editor state"""
        if self.state.is_playing:
            self.state.current_time += dt

        # Update executor if we have one
        if self.executor:
            # Check if rebuild needed
            if self.executor.needs_rebuild(self.state.graph):
                self.executor.rebuild(self.state.graph)
            else:
                # Sync parameters (Hot Update)
                self.executor.sync_parameters(self.state.graph)

            if self.executor.has_graph():
                self.executor.update(dt, fft_bands or [])

    def handle_midi_message(self, msg):
        """Handle incoming MIDI message"""
        # First, dispatch to all MIDI Listener nodes in the visual graph
        self._dispatch_midi_to_listeners(msg)

        # Then handle MIDI Learn mode for old trigger system
        if not self.state.midi_learn_mode or not self.state.midi_learn_target:
            return

        # We are in learn mode, find the target trigger
        target_id = self.state.midi_learn_target
        target_trigger = None

        # Search all nodes
        for node in self.state.graph.nodes.values():
            for trig in node.triggers:
                if trig.id == target_id:
                    target_trigger = trig
                    break
            if target_trigger:
                break

        if target_trigger:
            # Update trigger based on message type
            if msg.type == 'note_on':
                target_trigger.trigger_type = 'midi_note'
                target_trigger.midi_note = msg.note
                target_trigger.midi_channel = msg.channel + 1
                print(f"MIDI Learn: Set trigger {target_id} to Note {msg.note} Ch {msg.channel+1}")
                self.state.midi_learn_mode = False
                self.state.midi_learn_target = None

            elif msg.type == 'control_change':
                target_trigger.trigger_type = 'midi_cc'
                target_trigger.midi_cc = msg.control
                target_trigger.midi_channel = msg.channel + 1
                print(f"MIDI Learn: Set trigger {target_id} to CC {msg.control} Ch {msg.channel+1}")
                self.state.midi_learn_mode = False
                self.state.midi_learn_target = None

    def _dispatch_midi_to_listeners(self, msg):
        """Dispatch MIDI message to all MIDI Listener nodes"""
        for node in self.state.graph.nodes.values():
            if node.node_type == "midi.listener":
                # Call process_midi_message on the node
                if hasattr(node, 'process_midi_message'):
                    node.process_midi_message(msg)
