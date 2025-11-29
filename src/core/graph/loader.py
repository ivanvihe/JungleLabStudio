import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple
import moderngl

from core.graph.graph import RenderGraph
from core.graph.registry import NodeRegistry
from core.graph.node import LFO, AudioModulation
from core.error_handling import get_error_handler, ErrorCategory, ErrorSeverity

# Import nodes package to register all node types
try:
    import nodes
except ImportError:
    get_error_handler().log(
        "GraphLoader: Could not import nodes package",
        ErrorSeverity.WARNING,
        ErrorCategory.GRAPH
    )

class GraphLoader:
    def __init__(self, ctx: moderngl.Context, resolution: tuple[int, int]):
        self.ctx = ctx
        self.resolution = resolution
        self.error_handler = get_error_handler()
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def load_file(self, path: str) -> RenderGraph:
        self.errors.clear()
        self.warnings.clear()

        file_path = Path(path)
        if not file_path.exists():
            self.error_handler.handle_graph_error(
                file_path,
                f"File not found: {path}"
            )
            return RenderGraph()

        try:
            data = yaml.safe_load(file_path.read_text())
            graph = self.build_graph(data)
            self._report_results(file_path)
            return graph
        except yaml.YAMLError as e:
            self.error_handler.handle_graph_error(
                file_path,
                f"YAML parsing error: {e}"
            )
            return RenderGraph()
        except Exception as e:
            self.error_handler.handle_graph_error(
                file_path,
                f"Unexpected error loading graph: {e}"
            )
            import traceback
            traceback.print_exc()
            return RenderGraph()

    def load_from_yaml(self, yaml_str: str) -> RenderGraph:
        """Load graph from YAML string"""
        self.errors.clear()
        self.warnings.clear()

        try:
            data = yaml.safe_load(yaml_str)
            graph = self.build_graph(data)
            self._report_results(None)
            return graph
        except yaml.YAMLError as e:
            self.error_handler.handle_graph_error(
                None,
                f"YAML parsing error: {e}"
            )
            import traceback
            traceback.print_exc()
            return RenderGraph()
        except Exception as e:
            self.error_handler.handle_graph_error(
                None,
                f"Unexpected error loading graph from YAML string: {e}"
            )
            import traceback
            traceback.print_exc()
            return RenderGraph()

    def _report_results(self, file_path: Path = None):
        """Report errors and warnings from loading"""
        if self.errors:
            error_msg = f"Graph loading completed with {len(self.errors)} error(s)"
            if file_path:
                error_msg += f" in {file_path.name}"
            self.error_handler.log(error_msg, ErrorSeverity.ERROR, ErrorCategory.GRAPH)
            for error in self.errors:
                self.error_handler.log(f"  - {error}", ErrorSeverity.ERROR, ErrorCategory.GRAPH)

        if self.warnings:
            warning_msg = f"Graph loading completed with {len(self.warnings)} warning(s)"
            if file_path:
                warning_msg += f" in {file_path.name}"
            self.error_handler.log(warning_msg, ErrorSeverity.WARNING, ErrorCategory.GRAPH)
            for warning in self.warnings:
                self.error_handler.log(f"  - {warning}", ErrorSeverity.WARNING, ErrorCategory.GRAPH)

        if not self.errors and not self.warnings:
            success_msg = "Graph loaded successfully"
            if file_path:
                success_msg += f": {file_path.name}"
            self.error_handler.log(success_msg, ErrorSeverity.INFO, ErrorCategory.GRAPH)

    def build_graph(self, data: Dict[str, Any]) -> RenderGraph:
        graph = RenderGraph()
        preset_data = data.get('preset', {})
        nodes_data = preset_data.get('nodes', [])
        midi_data = preset_data.get('midi', {}).get('mappings', [])
        
        # 1. Create Instances
        for nd in nodes_data:
            n_type = nd.get('type')
            n_id = nd.get('id')
            
            if not n_type or not n_id: continue
            
            # Factory creation
            node_cls = NodeRegistry.get(n_type)
            if not node_cls:
                self.warnings.append(f"Node type '{n_type}' not registered (node '{n_id}' skipped)")
                continue

            try:
                node = node_cls(self.ctx, n_id, self.resolution)
            except Exception as e:
                self.errors.append(f"Failed to create node '{n_id}' of type '{n_type}': {e}")
                continue
            
            # Config Loading
            # Handle shader_path first (ShaderNode needs this before params)
            if 'params' in nd and 'shader_path' in nd['params']:
                shader_path = nd['params']['shader_path']
                print(f"GraphLoader: Setting shader_path for {n_id}: {shader_path}")
                if hasattr(node, 'set_shader_path'):
                    node.set_shader_path(shader_path)
                    print(f"GraphLoader: Called set_shader_path() for {n_id}")
                else:
                    print(f"GraphLoader: WARNING - {n_id} does not have set_shader_path method!")

            # General params
            if 'params' in nd:
                for k, v in nd['params'].items():
                    if k == 'animate': continue
                    if k == 'shader_path': continue  # Already handled

                    # Add parameter if it doesn't exist
                    if k not in node.params:
                        # Determine parameter type and add it
                        if isinstance(v, list):
                            node.add_param(k, v)
                        elif isinstance(v, (int, float)):
                            node.add_param(k, float(v))
                        else:
                            # Direct attribute setting for non-param types
                            if hasattr(node, k):
                                setattr(node, k, v)
                    else:
                        # Update existing parameter
                        node.params[k].update(v)

            # Specific attributes (legacy support)
            for attr in ['src', 'blend']:
                if attr in nd:
                    setattr(node, attr, nd[attr])

            # Custom attributes (Launcher / MIDI Listener)
            if 'midi_mapping' in nd:
                # Check if node expects a MIDIMapping object or dict
                # If it's MIDIListenerNode, it might handle dict in from_dict, but here we set directly
                if hasattr(node, 'midi_mapping'):
                    # Import here to avoid circular dependency if possible, or check type
                    mapping_data = nd['midi_mapping']
                    
                    # We need to construct the object if the node expects one
                    # But we don't want to import MIDIMapping from the node file here if we can avoid it
                    # Let's try to use from_dict if available (and if it works despite my doubts)
                    if hasattr(node, 'from_dict'):
                         # Create a partial dict for from_dict
                         node.from_dict({'midi_mapping': mapping_data})
                    else:
                        # Fallback: generic set or reconstruction
                        # If mapping_data is a dict and node.midi_mapping is None, we might need to create the object.
                        # For now, let's assign whatever we have, assuming the node can handle it or we construct it manually
                         if isinstance(mapping_data, dict) and 'message_type' in mapping_data:
                             # Try to instantiate MIDIMapping if we can import it, or dynamic construction
                             try:
                                 from nodes.midi.midi_listener_node import MIDIMapping
                                 node.midi_mapping = MIDIMapping(
                                    message_type=mapping_data['message_type'],
                                    channel=mapping_data.get('channel', 0),
                                    note=mapping_data.get('note'),
                                    cc=mapping_data.get('cc')
                                 )
                             except ImportError:
                                 # If we can't import, assign dict and hope node handles it
                                 node.midi_mapping = mapping_data
                         else:
                             node.midi_mapping = mapping_data

            if 'target_generators' in nd and hasattr(node, 'target_generators'):
                node.target_generators = nd['target_generators']

            if 'parameter_mappings' in nd and hasattr(node, 'parameter_mappings'):
                node.parameter_mappings = nd['parameter_mappings']

            # Handle legacy 'shader' attribute as shader_path
            if 'shader' in nd and hasattr(node, 'set_shader_path'):
                shader_path = nd['shader']
                print(f"GraphLoader: Setting shader_path (legacy 'shader' attr) for {n_id}: {shader_path}")
                node.set_shader_path(shader_path)

            # Animations
            if 'params' in nd and 'animate' in nd['params']:
                anim_data = nd['params']['animate']
                for param_name, anim_cfg in anim_data.items():
                    if 'lfo' in anim_cfg:
                        lfo_cfg = anim_cfg['lfo']
                        lfo = LFO(
                            type=lfo_cfg.get('type', 'sine'),
                            freq=float(lfo_cfg.get('freq', 1.0)),
                            amp=float(lfo_cfg.get('amp', 1.0))
                        )
                        node.animators[param_name] = lfo
                    elif 'audio' in anim_cfg:
                        audio_cfg = anim_cfg['audio']
                        audio_mod = AudioModulation(
                            band=int(audio_cfg.get('band', 0)),
                            min_value=float(audio_cfg.get('min_value', 0.0)),
                            max_value=float(audio_cfg.get('max_value', 1.0)),
                            smoothing=float(audio_cfg.get('smoothing', 0.5))
                        )
                        # Attach to parameter
                        if param_name in node.params:
                            node.params[param_name].audio_mod = audio_mod

            graph.add_node(node)

        # 2. Connect Inputs with validation
        for nd in nodes_data:
            n_id = nd.get('id')
            if 'inputs' in nd:
                target_node = graph.get_node(n_id)
                if not target_node:
                    self.warnings.append(f"Target node '{n_id}' not found when connecting inputs")
                    continue

                inputs = nd['inputs']

                # Support both list format (legacy) and dict format (from visual editor)
                if isinstance(inputs, list):
                    # Legacy format: ["source_id1", "source_id2"]
                    for i, src_id in enumerate(inputs):
                        if not self._validate_and_connect(graph, src_id, n_id, f"input{i}"):
                            continue

                elif isinstance(inputs, dict):
                    # Visual editor format: {"input0": "source_id1", "texture": "source_id2"}
                    for slot_name, src_id in inputs.items():
                        if not self._validate_and_connect(graph, src_id, n_id, slot_name):
                            continue
                            
        # 3. MIDI Bindings
        graph.midi_mappings = midi_data

        # 4. Build execution order and validate graph
        try:
            graph.build_execution_order()
        except Exception as e:
            self.errors.append(f"Failed to build execution order: {e}")

        # 5. Validate graph for cycles and missing connections
        validation_errors = self._validate_graph(graph)
        self.warnings.extend(validation_errors)

        return graph

    def _validate_and_connect(self, graph: RenderGraph, src_id: str, target_id: str, slot_name: str) -> bool:
        """Validate and create a connection between nodes"""
        # Check if source node exists
        src_node = graph.get_node(src_id)
        if not src_node:
            self.warnings.append(f"Connection failed: Source node '{src_id}' not found (target: {target_id}.{slot_name})")
            return False

        # Check if target node exists
        target_node = graph.get_node(target_id)
        if not target_node:
            self.warnings.append(f"Connection failed: Target node '{target_id}' not found (source: {src_id})")
            return False

        # Check for self-connection
        if src_id == target_id:
            self.warnings.append(f"Connection failed: Self-connection detected on node '{src_id}'")
            return False

        # Attempt connection
        try:
            target_node.set_input(slot_name, src_node)
            self.error_handler.log(
                f"Connected {src_id} → {target_id}.{slot_name}",
                ErrorSeverity.DEBUG,
                ErrorCategory.GRAPH
            )
            return True
        except Exception as e:
            self.errors.append(f"Connection failed: {src_id} → {target_id}.{slot_name}: {e}")
            return False

    def _validate_graph(self, graph: RenderGraph) -> List[str]:
        """Validate graph structure and return list of warnings"""
        warnings = []

        # Check for disconnected nodes (no inputs and no outputs connected)
        for node_id, node in graph.nodes.items():
            # Check if node has any connected inputs
            has_inputs = False
            if hasattr(node, 'input_nodes') and node.input_nodes:
                has_inputs = any(node.input_nodes.values())

            has_consumers = False

            # Check if this node is used as input by any other node
            for other_id, other_node in graph.nodes.items():
                if other_id == node_id:
                    continue
                if hasattr(other_node, 'input_nodes') and other_node.input_nodes:
                    for input_node in other_node.input_nodes.values():
                        if input_node == node:
                            has_consumers = True
                            break
                if has_consumers:
                    break

            # Generator nodes don't need inputs, but should have consumers
            if not has_consumers and node_id not in ['init', 'output']:
                if not node_id.startswith('out_'):  # Allow output nodes without consumers
                    warnings.append(f"Node '{node_id}' has no consumers (may be unused)")

        return warnings
