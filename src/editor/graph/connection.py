"""Connection between nodes"""

from dataclasses import dataclass
from editor.graph.visual_node import Color
import uuid

@dataclass
class Connection:
    """Wire connecting two nodes"""
    id: str
    source_node_id: str
    source_port: str
    target_node_id: str
    target_port: str

    # Visual
    color: Color = None
    thickness: float = 2.0
    selected: bool = False

    # Data
    data_type: str = "any"

    def __post_init__(self):
        if self.color is None:
            self.color = Color(0.8, 0.8, 0.8, 1.0)

    @staticmethod
    def create(source_node_id: str, source_port: str,
               target_node_id: str, target_port: str) -> 'Connection':
        """Factory function"""
        return Connection(
            id=f"conn_{uuid.uuid4().hex[:8]}",
            source_node_id=source_node_id,
            source_port=source_port,
            target_node_id=target_node_id,
            target_port=target_port
        )
