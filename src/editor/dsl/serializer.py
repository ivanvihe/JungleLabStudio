"""Graph to YAML serialization"""

import yaml
from typing import Dict, Any
from editor.graph.visual_graph import VisualGraph


class PresetSerializer:
    """Serialize visual graph to YAML"""

    @staticmethod
    def serialize(graph: VisualGraph) -> str:
        """Convert graph to YAML string"""
        data = graph.to_dict()
        return yaml.dump(data, default_flow_style=False, sort_keys=False, indent=2)

    @staticmethod
    def serialize_to_file(graph: VisualGraph, filepath: str):
        """Save graph to YAML file"""
        yaml_str = PresetSerializer.serialize(graph)
        with open(filepath, 'w') as f:
            f.write(yaml_str)


class PresetDeserializer:
    """Deserialize YAML to visual graph"""

    @staticmethod
    def deserialize(yaml_str: str) -> VisualGraph:
        """Convert YAML string to graph"""
        data = yaml.safe_load(yaml_str)
        graph = VisualGraph()

        if 'preset' not in data:
            raise ValueError("Invalid preset format: missing 'preset' key")

        preset = data['preset']

        # Load metadata
        graph.name = preset.get('name', 'Untitled')
        graph.description = preset.get('description', '')
        graph.author = preset.get('author', '')
        graph.version = preset.get('version', '1.0.0')
        graph.tags = preset.get('tags', [])

        # Load settings
        settings = preset.get('settings', {})
        graph.bpm = settings.get('bpm', 120.0)
        graph.audio_reactive = settings.get('audio_reactive', True)
        graph.midi_enabled = settings.get('midi_enabled', True)

        # Load nodes
        nodes_data = preset.get('nodes', [])
        # If nodes is a dict (runtime format), convert to list
        if isinstance(nodes_data, dict):
            nodes_list = []
            for nid, nconf in nodes_data.items():
                nconf['id'] = nid
                nodes_list.append(nconf)
            nodes_data = nodes_list
            
        PresetDeserializer._load_nodes(graph, nodes_data)

        # Load connections (from inputs)
        PresetDeserializer._load_connections(graph, nodes_data)

        # Load Global MIDI Mappings (Runtime Format)
        midi_data = preset.get('midi', {}).get('mappings', [])
        PresetDeserializer._load_global_triggers(graph, midi_data)

        return graph

    @staticmethod
    def deserialize_from_file(filepath: str) -> VisualGraph:
        """Load graph from YAML file"""
        with open(filepath, 'r') as f:
            yaml_str = f.read()
        return PresetDeserializer.deserialize(yaml_str)

    @staticmethod
    def _load_nodes(graph: VisualGraph, nodes_data: list):
        """Load nodes from data"""
        from editor.graph.visual_node import create_node, Vector2, AnimationBlock, TriggerBinding
        import uuid

        for node_data in nodes_data:
            node_id = node_data.get('id', f"node_{uuid.uuid4().hex[:8]}")
            node_type = node_data['type']
            position = node_data.get('position', [0, 0])

            # Create node
            node = create_node(node_type, Vector2(position[0], position[1]))
            node.id = node_id

            # Load parameters
            node.params = node_data.get('params', {}).copy()

            # Load custom attributes (Launcher / MIDI Listener)
            if 'midi_mapping' in node_data:
                from nodes.midi.midi_listener_node import MIDIMapping
                mapping_data = node_data['midi_mapping']
                # Reconstruct MIDIMapping object if data is a dict
                if isinstance(mapping_data, dict) and 'message_type' in mapping_data:
                    try:
                        node.midi_mapping = MIDIMapping(
                            message_type=mapping_data['message_type'],
                            channel=mapping_data.get('channel', 0),
                            note=mapping_data.get('note'),
                            cc=mapping_data.get('cc')
                        )
                    except Exception as e:
                        print(f"Error deserializing midi_mapping: {e}")
                        node.midi_mapping = mapping_data # Fallback
                else:
                    node.midi_mapping = mapping_data

            if 'target_generators' in node_data:
                node.target_generators = node_data['target_generators']

            if 'parameter_mappings' in node_data:
                node.parameter_mappings = node_data['parameter_mappings']

            # 1. Load Runtime Animations (params.animate)
            if 'animate' in node.params:
                runtime_anims = node.params.pop('animate') # Remove from params, move to animations
                for param_name, anim_cfg in runtime_anims.items():
                    if 'lfo' in anim_cfg:
                        lfo_cfg = anim_cfg['lfo']
                        anim = AnimationBlock(
                            id=f"anim_{uuid.uuid4().hex[:8]}",
                            target_param=param_name,
                            animation_type='lfo',
                            lfo_frequency=float(lfo_cfg.get('freq', 1.0)),
                            lfo_waveform=lfo_cfg.get('type', 'sine'),
                            lfo_amplitude=float(lfo_cfg.get('amp', 1.0)),
                            lfo_offset=lfo_cfg.get('offset', 0.0)
                        )
                        node.animations.append(anim)
                    # TODO: Add support for 'audio' modulation if AnimationBlock supports it

            # 2. Load Editor Animations (explicit list)
            animations_data = node_data.get('animations', [])
            for anim_data in animations_data:
                anim = AnimationBlock(
                    id=f"anim_{uuid.uuid4().hex[:8]}",
                    target_param=anim_data['target'],
                    animation_type=anim_data['type']
                )

                # Load type-specific properties
                if anim.animation_type == 'lfo':
                    anim.lfo_frequency = anim_data.get('frequency', 1.0)
                    anim.lfo_waveform = anim_data.get('waveform', 'sine')
                    anim.lfo_amplitude = anim_data.get('amplitude', 1.0)
                    anim.lfo_offset = anim_data.get('offset', 0.0)
                elif anim.animation_type == 'envelope':
                    anim.envelope_attack = anim_data.get('attack', 0.1)
                    anim.envelope_decay = anim_data.get('decay', 0.2)
                    anim.envelope_sustain = anim_data.get('sustain', 0.7)
                    anim.envelope_release = anim_data.get('release', 0.3)
                elif anim.animation_type == 'noise_walk':
                    anim.noise_scale = anim_data.get('scale', 1.0)
                    anim.noise_speed = anim_data.get('speed', 0.5)

                node.animations.append(anim)

            # Load triggers (Editor Format)
            triggers_data = node_data.get('triggers', [])
            for trig_data in triggers_data:
                action = trig_data.get('action', {})

                trigger = TriggerBinding(
                    id=f"trig_{uuid.uuid4().hex[:8]}",
                    trigger_type=trig_data['type'],
                    action_mode=action.get('mode', 'trigger'),
                    target_param=action.get('target', '')
                )

                # Load type-specific properties
                if trigger.trigger_type == 'midi_note':
                    trigger.midi_note = trig_data.get('note')
                    trigger.midi_channel = trig_data.get('channel', 1)
                elif trigger.trigger_type == 'midi_cc':
                    trigger.midi_cc = trig_data.get('cc')
                    trigger.midi_channel = trig_data.get('channel', 1)
                elif trigger.trigger_type == 'fft_band':
                    trigger.fft_band = trig_data.get('band')
                    trigger.fft_threshold = trig_data.get('threshold', 0.5)

                if trigger.action_mode == 'impulse':
                    trigger.impulse_amount = action.get('amount', 1.0)
                    trigger.impulse_decay = action.get('decay', 2.0)

                node.triggers.append(trigger)

            graph.add_node(node)

    @staticmethod
    def _load_global_triggers(graph: VisualGraph, mappings: list):
        """Load global MIDI mappings into node triggers"""
        from editor.graph.visual_node import TriggerBinding
        import uuid
        import re

        for mapping in mappings:
            target_path = mapping.get('target', '')
            trigger_str = mapping.get('trigger', '')
            
            # Parse target: "nodes.node_id.params.param_name"
            parts = target_path.split('.')
            if len(parts) < 4 or parts[0] != 'nodes':
                continue
            
            node_id = parts[1]
            param_name = parts[3]
            
            node = graph.get_node(node_id)
            if not node:
                continue
                
            # Parse trigger: "CC14", "NOTE_60"
            trig_type = 'midi_cc' if 'CC' in trigger_str else 'midi_note'
            
            val = 0
            try:
                val = int(re.search(r'\d+', trigger_str).group())
            except: pass
            
            trigger = TriggerBinding(
                id=f"trig_{uuid.uuid4().hex[:8]}",
                trigger_type=trig_type,
                action_mode='set', # Default to set value
                target_param=param_name
            )
            
            if trig_type == 'midi_cc':
                trigger.midi_cc = val
            else:
                trigger.midi_note = val
                
            node.triggers.append(trigger)

    @staticmethod
    def _load_connections(graph: VisualGraph, nodes_data: list):
        """Load connections from nodes' inputs"""
        from editor.graph.connection import Connection

        for node_data in nodes_data:
            target_id = node_data['id']
            inputs = node_data.get('inputs', {})

            for input_name, source_id in inputs.items():
                conn = Connection.create(
                    source_node_id=source_id,
                    source_port='output',
                    target_node_id=target_id,
                    target_port=input_name
                )
                graph.add_connection(conn)
