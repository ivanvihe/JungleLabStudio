"""Visual graph container"""

from typing import Dict, List, Set, Optional, Tuple
from editor.graph.visual_node import VisualNode, Vector2
from editor.graph.connection import Connection

class VisualGraph:
    """Container for the entire visual node graph"""

    def __init__(self):
        self.nodes: Dict[str, VisualNode] = {}
        self.connections: Dict[str, Connection] = {}
        self.selection: Set[str] = set()  # Selected node IDs

        # Metadata
        self.name: str = "Untitled Preset"
        self.description: str = ""
        self.author: str = ""
        self.version: str = "1.0.0"
        self.tags: List[str] = []

        # Settings
        self.bpm: float = 120.0
        self.audio_reactive: bool = True
        self.midi_enabled: bool = True

    def generate_unique_node_id(self, base_name: str) -> str:
        """Generate a unique ID for a new node based on a base name"""
        # Normalize base name (e.g., "particles" -> "gen_particles" if needed, but let caller handle prefix)
        # We assume base_name is like "gen_particles" or "effect_blur"
        
        # Find existing nodes starting with base_name
        count = 1
        while True:
            new_id = f"{base_name}_{count:03d}"
            if new_id not in self.nodes:
                return new_id
            count += 1

    # === Node Management ===

    def add_node(self, node: VisualNode) -> bool:
        """Add a node to the graph"""
        if node.id in self.nodes:
            return False
        self.nodes[node.id] = node
        return True

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all connected wires"""
        if node_id not in self.nodes:
            return False

        # Remove all connections to/from this node
        to_remove = [
            conn_id for conn_id, conn in self.connections.items()
            if conn.source_node_id == node_id or conn.target_node_id == node_id
        ]
        for conn_id in to_remove:
            del self.connections[conn_id]

        # Remove from selection
        self.selection.discard(node_id)

        # Remove node
        del self.nodes[node_id]
        return True

    def get_node(self, node_id: str) -> Optional[VisualNode]:
        """Get node by ID"""
        return self.nodes.get(node_id)

    # === Connection Management ===

    def add_connection(self, connection: Connection) -> bool:
        """Add a connection"""
        # Validate nodes exist
        if connection.source_node_id not in self.nodes:
            return False
        if connection.target_node_id not in self.nodes:
            return False

        # Check for duplicates
        for conn in self.connections.values():
            if (conn.source_node_id == connection.source_node_id and
                conn.source_port == connection.source_port and
                conn.target_node_id == connection.target_node_id and
                conn.target_port == connection.target_port):
                return False

        self.connections[connection.id] = connection

        # Update port connection status
        target_node = self.nodes[connection.target_node_id]
        for port in target_node.inputs:
            if port.name == connection.target_port:
                port.connected = True

        return True

    def remove_connection(self, connection_id: str) -> bool:
        """Remove a connection"""
        if connection_id not in self.connections:
            return False

        conn = self.connections[connection_id]

        # Update port connection status
        target_node = self.nodes[conn.target_node_id]
        for port in target_node.inputs:
            if port.name == conn.target_port:
                port.connected = False

        del self.connections[connection_id]
        return True

    def get_connections_for_node(self, node_id: str) -> List[Connection]:
        """Get all connections involving a node"""
        return [
            conn for conn in self.connections.values()
            if conn.source_node_id == node_id or conn.target_node_id == node_id
        ]

    def connect(self, source_node_id: str, source_port: str, target_node_id: str, target_port: str) -> bool:
        """Create a connection between two nodes"""
        import uuid

        # Validate nodes exist
        if source_node_id not in self.nodes or target_node_id not in self.nodes:
            raise ValueError("Source or target node not found")

        # Create connection
        from editor.graph.connection import Connection
        conn_id = f"conn_{uuid.uuid4().hex[:8]}"
        conn = Connection(
            id=conn_id,
            source_node_id=source_node_id,
            source_port=source_port,
            target_node_id=target_node_id,
            target_port=target_port
        )

        return self.add_connection(conn)

    # === Selection ===

    def select(self, node_ids: List[str], add_to_selection: bool = False):
        """Select nodes"""
        if not add_to_selection:
            self.clear_selection()

        for node_id in node_ids:
            if node_id in self.nodes:
                self.selection.add(node_id)
                self.nodes[node_id].selected = True

    def deselect(self, node_ids: List[str]):
        """Deselect nodes"""
        for node_id in node_ids:
            self.selection.discard(node_id)
            if node_id in self.nodes:
                self.nodes[node_id].selected = False

    def clear_selection(self):
        """Clear all selection"""
        for node_id in self.selection:
            if node_id in self.nodes:
                self.nodes[node_id].selected = False
        self.selection.clear()

    def get_selected_nodes(self) -> List[VisualNode]:
        """Get all selected nodes"""
        return [self.nodes[nid] for nid in self.selection if nid in self.nodes]

    # === Queries ===

    def get_node_at_position(self, position: Vector2) -> Optional[VisualNode]:
        """Get node at world position"""
        # Check in reverse order (top to bottom)
        for node in reversed(list(self.nodes.values())):
            if node.contains_point(position):
                return node
        return None

    def get_nodes_in_rect(self, x: float, y: float, w: float, h: float) -> List[VisualNode]:
        """Get all nodes within rectangle"""
        result = []
        for node in self.nodes.values():
            nx, ny, nw, nh = node.get_bounds()
            # Check if rectangles overlap
            if not (nx + nw < x or nx > x + w or ny + nh < y or ny > y + h):
                result.append(node)
        return result

    # === Graph Analysis ===

    def get_execution_order(self) -> List[str]:
        """Get topologically sorted node execution order"""
        # Build adjacency list
        in_degree = {nid: 0 for nid in self.nodes}
        adjacency = {nid: [] for nid in self.nodes}

        for conn in self.connections.values():
            adjacency[conn.source_node_id].append(conn.target_node_id)
            in_degree[conn.target_node_id] += 1

        # Kahn's algorithm
        queue = [nid for nid, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            for neighbor in adjacency[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for cycles
        if len(result) != len(self.nodes):
            print("Warning: Graph contains cycles!")
            return list(self.nodes.keys())

        return result

    def validate(self) -> List[str]:
        """Validate graph and return list of errors"""
        errors = []

        # Check for cycles
        try:
            self.get_execution_order()
        except Exception as e:
            errors.append(f"Graph validation error: {e}")

        # Check required inputs
        for node in self.nodes.values():
            for port in node.inputs:
                if port.required and not port.connected:
                    errors.append(f"Node '{node.id}' missing required input '{port.name}'")

        return errors

    # === Serialization ===

    def to_dict(self) -> dict:
        """Convert graph to dictionary for YAML serialization"""
        return {
            "preset": {
                "name": self.name,
                "description": self.description,
                "author": self.author,
                "version": self.version,
                "tags": self.tags,
                "settings": {
                    "bpm": self.bpm,
                    "audio_reactive": self.audio_reactive,
                    "midi_enabled": self.midi_enabled,
                },
                "nodes": [self._node_to_dict(node) for node in self.nodes.values()],
            }
        }

    def _node_to_dict(self, node: VisualNode) -> dict:
        """Convert node to dictionary"""
        node_dict = {
            "id": node.id,
            "type": node.node_type,
            "position": [node.position.x, node.position.y],
            "params": node.params.copy(),
        }

        # Serialize custom attributes (if present)
        if hasattr(node, "midi_mapping") and node.midi_mapping:
            # Ensure midi_mapping is serialized as a dict if it's an object
            mapping = node.midi_mapping
            if hasattr(mapping, "message_type"): # Check if it's a MIDIMapping object
                 node_dict["midi_mapping"] = {
                    "message_type": mapping.message_type,
                    "channel": mapping.channel,
                    "note": mapping.note,
                    "cc": mapping.cc
                 }
            else:
                 node_dict["midi_mapping"] = mapping

        if hasattr(node, "target_generators"):
            node_dict["target_generators"] = node.target_generators

        if hasattr(node, "parameter_mappings"):
            node_dict["parameter_mappings"] = node.parameter_mappings

        # Add inputs (connections)
        inputs = {}
        for conn in self.connections.values():
            if conn.target_node_id == node.id:
                inputs[conn.target_port] = conn.source_node_id
        if inputs:
            node_dict["inputs"] = inputs

        # Add animations
        if node.animations:
            node_dict["animations"] = [self._animation_to_dict(anim) for anim in node.animations]

        # Add triggers
        if node.triggers:
            node_dict["triggers"] = [self._trigger_to_dict(trig) for trig in node.triggers]

        return node_dict

    def _animation_to_dict(self, anim: 'AnimationBlock') -> dict:
        """Convert animation to dictionary"""
        result = {
            "target": anim.target_param,
            "type": anim.animation_type,
        }

        if anim.animation_type == "lfo":
            result.update({
                "frequency": anim.lfo_frequency,
                "waveform": anim.lfo_waveform,
                "amplitude": anim.lfo_amplitude,
                "offset": anim.lfo_offset,
            })
        elif anim.animation_type == "envelope":
            result.update({
                "attack": anim.envelope_attack,
                "decay": anim.envelope_decay,
                "sustain": anim.envelope_sustain,
                "release": anim.envelope_release,
            })
        elif anim.animation_type == "noise_walk":
            result.update({
                "scale": anim.noise_scale,
                "speed": anim.noise_speed,
            })

        return result

    def _trigger_to_dict(self, trigger: 'TriggerBinding') -> dict:
        """Convert trigger to dictionary"""
        result = {
            "type": trigger.trigger_type,
        }

        if trigger.trigger_type == "midi_note":
            result.update({
                "note": trigger.midi_note,
                "channel": trigger.midi_channel,
            })
        elif trigger.trigger_type == "midi_cc":
            result.update({
                "cc": trigger.midi_cc,
                "channel": trigger.midi_channel,
            })
        elif trigger.trigger_type == "fft_band":
            result.update({
                "band": trigger.fft_band,
                "threshold": trigger.fft_threshold,
            })

        result["action"] = {
            "mode": trigger.action_mode,
            "target": trigger.target_param,
        }

        if trigger.action_mode == "impulse":
            result["action"].update({
                "amount": trigger.impulse_amount,
                "decay": trigger.impulse_decay,
            })

        return result

    def clear(self):
        """Clear all nodes and connections"""
        self.nodes.clear()
        self.connections.clear()
        self.selection.clear()

    # === Layout & Organization ===

    def auto_organize(self):
        """
        Automatically organize nodes in a hierarchical layout
        Based on topological order with optimal spacing
        """
        if not self.nodes:
            return

        # Get topological order
        try:
            execution_order = self.get_execution_order()
        except:
            execution_order = list(self.nodes.keys())

        # Build dependency tree
        # Layer 0: nodes with no inputs
        # Layer 1: nodes that depend on layer 0
        # etc.
        layers = self._compute_node_layers()

        # Layout parameters
        NODE_SPACING_X = 300  # Horizontal spacing between columns
        NODE_SPACING_Y = 100  # Vertical spacing between rows
        START_X = 100
        START_Y = 100

        # Position nodes by layer
        for layer_idx, node_ids in enumerate(layers):
            x = START_X + layer_idx * NODE_SPACING_X

            # Center nodes vertically in this layer
            layer_height = len(node_ids) * NODE_SPACING_Y
            start_y = START_Y - (layer_height / 2)

            for node_idx, node_id in enumerate(node_ids):
                if node_id in self.nodes:
                    node = self.nodes[node_id]
                    node.position.x = x
                    node.position.y = start_y + node_idx * NODE_SPACING_Y

    def _compute_node_layers(self) -> List[List[str]]:
        """
        Compute hierarchical layers for nodes based on dependencies
        Returns list of layers, where each layer is a list of node IDs
        """
        # Build dependency graph (reverse of connections)
        dependencies = {nid: set() for nid in self.nodes}

        for conn in self.connections.values():
            # target depends on source
            dependencies[conn.target_node_id].add(conn.source_node_id)

        # Assign layers
        node_layers = {}  # node_id -> layer_index

        def get_layer(node_id: str) -> int:
            """Recursively compute layer for a node"""
            if node_id in node_layers:
                return node_layers[node_id]

            deps = dependencies[node_id]
            if not deps:
                # No dependencies, layer 0
                node_layers[node_id] = 0
                return 0

            # Layer is 1 + max layer of dependencies
            max_dep_layer = max(get_layer(dep) for dep in deps)
            node_layers[node_id] = max_dep_layer + 1
            return max_dep_layer + 1

        # Compute layers for all nodes
        for node_id in self.nodes:
            get_layer(node_id)

        # Group nodes by layer
        max_layer = max(node_layers.values()) if node_layers else 0
        layers = [[] for _ in range(max_layer + 1)]

        for node_id, layer in node_layers.items():
            layers[layer].append(node_id)

        # Sort nodes within each layer by type for consistency
        for layer in layers:
            layer.sort(key=lambda nid: self.nodes[nid].node_type if nid in self.nodes else "")

        return layers
