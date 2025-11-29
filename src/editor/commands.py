"""Command pattern for undo/redo functionality"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from editor.graph.visual_graph import VisualGraph
from editor.graph.visual_node import VisualNode, Vector2
from editor.graph.connection import Connection


class Command(ABC):
    """Base command interface"""

    @abstractmethod
    def execute(self, graph: VisualGraph) -> bool:
        """Execute the command. Returns True if successful."""
        pass

    @abstractmethod
    def undo(self, graph: VisualGraph) -> bool:
        """Undo the command. Returns True if successful."""
        pass

    def get_description(self) -> str:
        """Get human-readable description of the command"""
        return self.__class__.__name__


class AddNodeCommand(Command):
    """Command to add a node to the graph"""

    def __init__(self, node: VisualNode):
        self.node = node

    def execute(self, graph: VisualGraph) -> bool:
        return graph.add_node(self.node)

    def undo(self, graph: VisualGraph) -> bool:
        return graph.remove_node(self.node.id)

    def get_description(self) -> str:
        return f"Add node '{self.node.id}'"


class RemoveNodeCommand(Command):
    """Command to remove a node from the graph"""

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.node: Optional[VisualNode] = None
        self.removed_connections: List[Connection] = []

    def execute(self, graph: VisualGraph) -> bool:
        # Store the node and its connections before removing
        self.node = graph.get_node(self.node_id)
        if not self.node:
            return False

        # Store all connections involving this node
        self.removed_connections = graph.get_connections_for_node(self.node_id)

        return graph.remove_node(self.node_id)

    def undo(self, graph: VisualGraph) -> bool:
        if not self.node:
            return False

        # Re-add the node
        if not graph.add_node(self.node):
            return False

        # Re-add all connections
        for conn in self.removed_connections:
            graph.add_connection(conn)

        return True

    def get_description(self) -> str:
        return f"Remove node '{self.node_id}'"


class MoveNodeCommand(Command):
    """Command to move one or more nodes"""

    def __init__(self, node_positions: Dict[str, tuple]):
        """
        Args:
            node_positions: Dict mapping node_id -> (old_pos, new_pos)
        """
        self.node_positions = node_positions

    def execute(self, graph: VisualGraph) -> bool:
        for node_id, (old_pos, new_pos) in self.node_positions.items():
            node = graph.get_node(node_id)
            if node:
                node.position = Vector2(new_pos[0], new_pos[1])
        return True

    def undo(self, graph: VisualGraph) -> bool:
        for node_id, (old_pos, new_pos) in self.node_positions.items():
            node = graph.get_node(node_id)
            if node:
                node.position = Vector2(old_pos[0], old_pos[1])
        return True

    def get_description(self) -> str:
        count = len(self.node_positions)
        return f"Move {count} node{'s' if count > 1 else ''}"


class AddConnectionCommand(Command):
    """Command to add a connection"""

    def __init__(self, connection: Connection):
        self.connection = connection

    def execute(self, graph: VisualGraph) -> bool:
        return graph.add_connection(self.connection)

    def undo(self, graph: VisualGraph) -> bool:
        return graph.remove_connection(self.connection.id)

    def get_description(self) -> str:
        return f"Connect {self.connection.source_node_id} → {self.connection.target_node_id}"


class RemoveConnectionCommand(Command):
    """Command to remove a connection"""

    def __init__(self, connection_id: str):
        self.connection_id = connection_id
        self.connection: Optional[Connection] = None

    def execute(self, graph: VisualGraph) -> bool:
        # Store the connection before removing
        self.connection = graph.connections.get(self.connection_id)
        if not self.connection:
            return False

        return graph.remove_connection(self.connection_id)

    def undo(self, graph: VisualGraph) -> bool:
        if not self.connection:
            return False
        return graph.add_connection(self.connection)

    def get_description(self) -> str:
        return f"Remove connection '{self.connection_id}'"


class BatchCommand(Command):
    """Command that executes multiple commands as one atomic operation"""

    def __init__(self, commands: List[Command], description: str = "Batch operation"):
        self.commands = commands
        self.description = description

    def execute(self, graph: VisualGraph) -> bool:
        for cmd in self.commands:
            if not cmd.execute(graph):
                # If any command fails, undo all previous ones
                for prev_cmd in reversed(self.commands[:self.commands.index(cmd)]):
                    prev_cmd.undo(graph)
                return False
        return True

    def undo(self, graph: VisualGraph) -> bool:
        # Undo in reverse order
        for cmd in reversed(self.commands):
            if not cmd.undo(graph):
                return False
        return True

    def get_description(self) -> str:
        return self.description


class ChangeParameterCommand(Command):
    """Command to change a node parameter"""

    def __init__(self, node_id: str, param_path: str, old_value: Any, new_value: Any):
        self.node_id = node_id
        self.param_path = param_path
        self.old_value = old_value
        self.new_value = new_value

    def execute(self, graph: VisualGraph) -> bool:
        node = graph.get_node(self.node_id)
        if not node:
            return False
        node.params[self.param_path] = self.new_value
        return True

    def undo(self, graph: VisualGraph) -> bool:
        node = graph.get_node(self.node_id)
        if not node:
            return False
        node.params[self.param_path] = self.old_value
        return True

    def get_description(self) -> str:
        return f"Change {self.node_id}.{self.param_path}"


class CommandHistory:
    """Manages undo/redo history"""

    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []

    def execute(self, command: Command, graph: VisualGraph) -> bool:
        """Execute a command and add it to history"""
        if command.execute(graph):
            self.undo_stack.append(command)
            # Clear redo stack when a new command is executed
            self.redo_stack.clear()

            # Limit history size
            if len(self.undo_stack) > self.max_history:
                self.undo_stack.pop(0)

            return True
        return False

    def undo(self, graph: VisualGraph) -> bool:
        """Undo the last command"""
        if not self.can_undo():
            return False

        command = self.undo_stack.pop()
        if command.undo(graph):
            self.redo_stack.append(command)
            return True
        else:
            # If undo fails, put it back
            self.undo_stack.append(command)
            return False

    def redo(self, graph: VisualGraph) -> bool:
        """Redo the last undone command"""
        if not self.can_redo():
            return False

        command = self.redo_stack.pop()
        if command.execute(graph):
            self.undo_stack.append(command)
            return True
        else:
            # If redo fails, put it back
            self.redo_stack.append(command)
            return False

    def can_undo(self) -> bool:
        """Check if undo is available"""
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available"""
        return len(self.redo_stack) > 0

    def clear(self):
        """Clear all history"""
        self.undo_stack.clear()
        self.redo_stack.clear()

    def get_undo_description(self) -> Optional[str]:
        """Get description of the command that will be undone"""
        if self.can_undo():
            return self.undo_stack[-1].get_description()
        return None

    def get_redo_description(self) -> Optional[str]:
        """Get description of the command that will be redone"""
        if self.can_redo():
            return self.redo_stack[-1].get_description()
        return None
