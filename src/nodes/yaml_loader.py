"""YAML DSL loader for node-based presets"""

import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path

from nodes.graph import NodeGraph
from nodes.base import Node
from presets.base import PresetState


class YAMLPresetLoader:
    """Loads and parses YAML-based visual presets"""

    def __init__(self):
        self.graphs: Dict[str, NodeGraph] = {}

    def load_from_file(self, path: Path) -> Dict[str, Any]:
        """Load a YAML preset file"""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid YAML preset: expected dict, got {type(data)}")

        return self._validate_preset(data)

    def load_from_string(self, yaml_str: str) -> Dict[str, Any]:
        """Load a YAML preset from string"""
        data = yaml.safe_load(yaml_str)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid YAML preset: expected dict, got {type(data)}")

        return self._validate_preset(data)

    def _validate_preset(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate preset structure"""
        required_fields = ['name', 'nodes']

        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Validate nodes section
        if not isinstance(data['nodes'], dict):
            raise ValueError("'nodes' must be a dictionary")

        return data

    def build_graph(self, preset_data: Dict[str, Any]) -> NodeGraph:
        """Build a NodeGraph from preset data"""
        graph = NodeGraph()

        # First pass: create all nodes
        nodes_data = preset_data['nodes']
        for node_id, node_config in nodes_data.items():
            if not isinstance(node_config, dict):
                raise ValueError(f"Node '{node_id}' configuration must be a dictionary")

            node_type = node_config.get('type')
            if not node_type:
                raise ValueError(f"Node '{node_id}' missing 'type' field")

            # Extract parameters (everything except 'type' and 'inputs')
            params = {k: v for k, v in node_config.items() if k not in ['type', 'inputs', 'outputs']}

            try:
                graph.add_node(node_id, node_type, params)
            except Exception as e:
                raise ValueError(f"Error creating node '{node_id}': {e}")

        # Second pass: create connections
        for node_id, node_config in nodes_data.items():
            inputs = node_config.get('inputs', {})
            if not isinstance(inputs, dict):
                raise ValueError(f"Node '{node_id}' inputs must be a dictionary")

            for input_name, connection in inputs.items():
                if isinstance(connection, str):
                    # Simple connection: "source_node_id"
                    source_node_id = connection
                    source_output = "output"
                elif isinstance(connection, dict):
                    # Detailed connection: {node: "source_id", output: "output_name"}
                    source_node_id = connection.get('node')
                    source_output = connection.get('output', 'output')
                else:
                    raise ValueError(
                        f"Node '{node_id}' input '{input_name}' has invalid connection format"
                    )

                if not source_node_id:
                    continue

                try:
                    graph.connect(source_node_id, node_id, input_name, source_output)
                except Exception as e:
                    raise ValueError(
                        f"Error connecting {source_node_id} to {node_id}.{input_name}: {e}"
                    )

        # Validate the graph
        errors = graph.validate()
        if errors:
            raise ValueError(f"Graph validation failed:\n" + "\n".join(errors))

        return graph

    def get_metadata(self, preset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from preset"""
        return {
            'name': preset_data.get('name', 'Unnamed'),
            'description': preset_data.get('description', ''),
            'author': preset_data.get('author', ''),
            'version': preset_data.get('version', '1.0'),
            'tags': preset_data.get('tags', []),
            'controls': preset_data.get('controls', {}),
            'triggers': preset_data.get('triggers', {}),
        }

    def get_controls(self, preset_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract UI controls configuration"""
        controls = preset_data.get('controls', {})
        if not isinstance(controls, dict):
            return {}

        # Validate control definitions
        validated_controls = {}
        for param_name, control_config in controls.items():
            if isinstance(control_config, dict):
                validated_controls[param_name] = {
                    'type': control_config.get('type', 'slider'),
                    'label': control_config.get('label', param_name),
                    'min': control_config.get('min', 0.0),
                    'max': control_config.get('max', 1.0),
                    'default': control_config.get('default', 0.5),
                    'step': control_config.get('step', 0.01),
                }

        return validated_controls

    def get_triggers(self, preset_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract trigger configuration"""
        triggers = preset_data.get('triggers', {})
        if not isinstance(triggers, dict):
            return {}

        return triggers

    def save_to_file(self, preset_data: Dict[str, Any], path: Path):
        """Save preset to YAML file"""
        with open(path, 'w') as f:
            yaml.dump(preset_data, f, default_flow_style=False, sort_keys=False)

    def graph_to_yaml(self, graph: NodeGraph, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a NodeGraph back to YAML format"""
        nodes_data = {}

        for node_id, node in graph.nodes.items():
            node_config = {
                'type': getattr(node.__class__, 'node_name', node.__class__.__name__),
                **node.params
            }

            # Add input connections
            inputs = {}
            for input_name, source_node in node.input_connections.items():
                if source_node:
                    inputs[input_name] = source_node.node_id

            if inputs:
                node_config['inputs'] = inputs

            nodes_data[node_id] = node_config

        preset_data = {
            **metadata,
            'nodes': nodes_data,
        }

        return preset_data


# Global loader instance
yaml_loader = YAMLPresetLoader()
