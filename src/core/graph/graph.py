from typing import Dict, List
from core.graph.node import RenderNode

class RenderGraph:
    def __init__(self):
        self.nodes: Dict[str, RenderNode] = {}
        self.execution_order: List[RenderNode] = []
        
        # MIDI Mapping: { (channel, note/cc): [ (node_id, param_name, range_func) ] }
        # Simplified: just storing configs for now
        self.midi_mappings = [] 

    def add_node(self, node: RenderNode):
        self.nodes[node.id] = node

    def get_node(self, node_id: str) -> RenderNode:
        return self.nodes.get(node_id)

    def build_execution_order(self):
        """
        Perform topological sort to determine render order.
        """
        visited = set()
        order = []

        def visit(node_id):
            if node_id in visited: return
            if node_id not in self.nodes: return
            
            node = self.nodes[node_id]
            # Visit inputs first
            for input_node in node.input_nodes.values():
                if input_node:
                    visit(input_node.id)
            
            visited.add(node_id)
            order.append(node)

        # Visit all nodes to ensure coverage
        for nid in self.nodes:
            visit(nid)
            
        self.execution_order = order

    def update(self, dt: float, fft_bands: List[float] = None):
        for node in self.execution_order:
            node.update(dt, fft_bands)

    def render(self):
        # Render each node in order
        # Each node renders to its own FBO
        for node in self.execution_order:
            node.render()
            
    def get_final_texture(self):
        if not self.execution_order:
            return None
            
        # Search backwards for a valid output node
        for i in range(len(self.execution_order) - 1, -1, -1):
            node = self.execution_order[i]
            # Check if it is an Output or Preview node
            # We check class name to avoid circular imports
            cls_name = node.__class__.__name__
            if cls_name in ["OutputNode", "PreviewNode"]:
                return node.get_texture()
                
        # No output node found
        return None
        
    def apply_midi(self, midi_msg):
        # Simple MIDI mapping logic
        # mapping: {"target": "nodes.id.param", "trigger": "NOTE_60"}
        if not self.midi_mappings: return

        # Parse msg
        msg_key = ""
        val = 0.0

        if midi_msg.type == 'control_change':
            msg_key = f"CC{midi_msg.control}"
            val = midi_msg.value / 127.0
        elif midi_msg.type == 'note_on':
            msg_key = f"NOTE_C{midi_msg.note // 12 - 1}" # Approximate C3 notation
            # Better: just NOTE_{number} for robustness or use note name map
            # Let's stick to simple int check or string mapping in future
            # For now, support raw "NOTE_{val}"
            msg_key = f"NOTE_{midi_msg.note}"
            val = midi_msg.velocity / 127.0

        for m in self.midi_mappings:
            if m['trigger'] == msg_key:
                # Target: "nodes.node_id.param_name"
                parts = m['target'].split('.')
                if len(parts) == 3 and parts[0] == 'nodes':
                    nid, param = parts[1], parts[2]
                    node = self.nodes.get(nid)
                    if node and param in node.params:
                        node.params[param].set_midi_value(val)

    def dispatch_midi_to_listeners(self, midi_msg):
        """Dispatch MIDI message to all MIDI Listener nodes"""
        for node in self.nodes.values():
            # Check if node is a MIDI Listener by checking for process_midi_message method
            if hasattr(node, 'process_midi_message'):
                try:
                    node.process_midi_message(midi_msg)
                except Exception as e:
                    print(f"Error dispatching MIDI to node {node.id}: {e}")
