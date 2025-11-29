"""Node graph execution engine"""

from typing import Dict, List, Optional, Any
from nodes.base import Node, NodeOutput, DataType
from nodes.registry import get_node_class


class NodeGraph:
    """Manages a graph of connected nodes"""

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.execution_order: List[str] = []
        self._cache: Dict[str, NodeOutput] = {}

    def add_node(self, node_id: str, node_type: str, params: Dict[str, Any] = None) -> Node:
        """Add a node to the graph"""
        if node_id in self.nodes:
            raise ValueError(f"Node with id '{node_id}' already exists")

        node_class = get_node_class(node_type)
        node = node_class(node_id, params)
        self.nodes[node_id] = node
        self._invalidate_execution_order()
        return node

    def remove_node(self, node_id: str):
        """Remove a node from the graph"""
        if node_id not in self.nodes:
            raise ValueError(f"Node '{node_id}' not found")

        # Remove all connections to/from this node
        for node in self.nodes.values():
            for input_name, connected_node in node.input_connections.items():
                if connected_node and connected_node.node_id == node_id:
                    node.input_connections[input_name] = None

        del self.nodes[node_id]
        self._invalidate_execution_order()

    def connect(self, source_node_id: str, target_node_id: str, target_input: str,
                source_output: str = "output"):
        """Connect two nodes"""
        if source_node_id not in self.nodes:
            raise ValueError(f"Source node '{source_node_id}' not found")
        if target_node_id not in self.nodes:
            raise ValueError(f"Target node '{target_node_id}' not found")

        source_node = self.nodes[source_node_id]
        target_node = self.nodes[target_node_id]

        # Validate output exists
        if source_output not in source_node.outputs:
            raise ValueError(f"Output '{source_output}' not found on node '{source_node_id}'")

        # Validate input exists
        if target_input not in target_node.inputs:
            raise ValueError(f"Input '{target_input}' not found on node '{target_node_id}'")

        # Validate type compatibility
        source_type = source_node.outputs[source_output].data_type
        target_input_port = target_node.inputs[target_input]

        if not target_input_port.accepts(source_type):
            raise ValueError(
                f"Type mismatch: {source_type} from '{source_node_id}.{source_output}' "
                f"cannot connect to '{target_node_id}.{target_input}'"
            )

        # Make connection
        target_node.connect_input(target_input, source_node)
        self._invalidate_execution_order()

    def disconnect(self, target_node_id: str, target_input: str):
        """Disconnect an input"""
        if target_node_id not in self.nodes:
            raise ValueError(f"Node '{target_node_id}' not found")

        target_node = self.nodes[target_node_id]
        if target_input in target_node.input_connections:
            target_node.input_connections[target_input] = None
            self._invalidate_execution_order()

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID"""
        return self.nodes.get(node_id)

    def _invalidate_execution_order(self):
        """Mark execution order as needing recalculation"""
        self.execution_order = []

    def _calculate_execution_order(self):
        """Calculate topological sort order for execution"""
        # Kahn's algorithm for topological sorting
        in_degree = {node_id: 0 for node_id in self.nodes}
        adjacency = {node_id: [] for node_id in self.nodes}

        # Build graph
        for node_id, node in self.nodes.items():
            for input_name, source_node in node.input_connections.items():
                if source_node:
                    adjacency[source_node.node_id].append(node_id)
                    in_degree[node_id] += 1

        # Find all nodes with no incoming edges
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        execution_order = []

        while queue:
            current = queue.pop(0)
            execution_order.append(current)

            # Reduce in-degree for all neighbors
            for neighbor in adjacency[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for cycles
        if len(execution_order) != len(self.nodes):
            raise RuntimeError("Graph contains cycles")

        self.execution_order = execution_order

    def execute(self, state: Any, output_node_id: Optional[str] = None) -> Optional[NodeOutput]:
        """Execute the graph and return output from specified node (or last node)"""
        if not self.nodes:
            return None

        # Calculate execution order if needed
        if not self.execution_order:
            self._calculate_execution_order()

        # Clear cache
        self._cache.clear()

        # Execute nodes in order
        for node_id in self.execution_order:
            node = self.nodes[node_id]
            try:
                output = node.execute(state)
                self._cache[node_id] = output
            except Exception as e:
                print(f"Error executing node '{node_id}': {e}")
                raise

        # Return output from specified node or last node
        if output_node_id:
            if output_node_id not in self._cache:
                raise ValueError(f"Node '{output_node_id}' not found or not executed")
            return self._cache[output_node_id]
        elif self.execution_order:
            return self._cache[self.execution_order[-1]]

        return None

    def validate(self) -> List[str]:
        """Validate the graph and return list of errors"""
        errors = []

        for node_id, node in self.nodes.items():
            # Check required inputs
            if not node.validate_inputs():
                missing = [
                    name for name, port in node.inputs.items()
                    if port.required and node.input_connections.get(name) is None
                       and port.default is None
                ]
                errors.append(f"Node '{node_id}' missing required inputs: {missing}")

        # Check for cycles
        try:
            self._calculate_execution_order()
        except RuntimeError as e:
            errors.append(str(e))

        return errors

    def clear(self):
        """Clear all nodes from the graph"""
        self.nodes.clear()
        self.execution_order = []
        self._cache.clear()

    def __repr__(self):
        return f"NodeGraph(nodes={len(self.nodes)}, connections={sum(len([c for c in n.input_connections.values() if c]) for n in self.nodes.values())})"
