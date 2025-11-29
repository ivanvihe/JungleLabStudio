"""Editor state management"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple, Set, List
from pathlib import Path

from editor.graph.visual_node import Vector2
from editor.graph.visual_graph import VisualGraph
from editor.commands import CommandHistory


class InteractionMode(Enum):
    SELECT = "select"
    PAN = "pan"
    CONNECT = "connect"
    CONNECTING = "connecting"  # Actively dragging a connection
    ADD_NODE = "add_node"


@dataclass
class EditorState:
    """Global editor state"""

    # Graph
    graph: VisualGraph = field(default_factory=VisualGraph)
    current_file: Optional[Path] = None
    is_modified: bool = False

    # Command history for undo/redo
    command_history: CommandHistory = field(default_factory=CommandHistory)

    # View
    canvas_offset: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    canvas_zoom: float = 1.0
    grid_size: float = 20.0
    show_grid: bool = True
    snap_to_grid: bool = True

    # Interaction
    interaction_mode: InteractionMode = InteractionMode.SELECT
    mode: InteractionMode = InteractionMode.SELECT  # Alias for compatibility
    is_panning: bool = False
    is_dragging: bool = False
    is_selecting_rect: bool = False

    # Connection state
    is_connecting: bool = False
    connection_start_node: Optional[object] = None  # The actual node object
    connection_start_port: int = 0  # Port index
    connection_start_port_name: str = ""  # Port name
    connection_start_is_output: bool = True  # Is the connection from an output port?
    connection_mouse_pos: Vector2 = field(default_factory=lambda: Vector2(0, 0))

    # Selection rectangle
    selection_rect_start: Optional[Vector2] = None
    selection_rect_end: Optional[Vector2] = None

    # Drag state
    drag_start_pos: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    drag_node_offsets: dict = field(default_factory=dict)

    # MIDI
    midi_learn_mode: bool = False
    midi_learn_target: Optional[Tuple[str, str]] = None  # (node_id, param_path)

    # Clipboard
    clipboard_nodes: List[dict] = field(default_factory=list)

    # UI state
    show_inspector: bool = True
    show_yaml_editor: bool = True
    show_node_library: bool = True
    inspector_width: float = 300.0
    yaml_editor_height: float = 250.0
    node_library_width: float = 200.0

    # Playback
    is_playing: bool = False
    current_time: float = 0.0

    # Recent files
    recent_files: List[Path] = field(default_factory=list)
    max_recent_files: int = 10

    def add_recent_file(self, path: Path):
        """Add to recent files"""
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:self.max_recent_files]

    def screen_to_canvas(self, screen_pos: Vector2) -> Vector2:
        """Convert screen coordinates to canvas coordinates"""
        return Vector2(
            (screen_pos.x - self.canvas_offset.x) / self.canvas_zoom,
            (screen_pos.y - self.canvas_offset.y) / self.canvas_zoom
        )

    def canvas_to_screen(self, canvas_pos: Vector2) -> Vector2:
        """Convert canvas coordinates to screen coordinates"""
        return Vector2(
            canvas_pos.x * self.canvas_zoom + self.canvas_offset.x,
            canvas_pos.y * self.canvas_zoom + self.canvas_offset.y
        )

    def snap_position(self, pos: Vector2) -> Vector2:
        """Snap position to grid if enabled"""
        if not self.snap_to_grid:
            return pos
        return Vector2(
            round(pos.x / self.grid_size) * self.grid_size,
            round(pos.y / self.grid_size) * self.grid_size
        )
