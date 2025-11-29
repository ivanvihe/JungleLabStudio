
import sys
import os
import unittest
import yaml
from unittest.mock import MagicMock

# Mock moderngl and nodes before importing serializer
sys.modules["moderngl"] = MagicMock()

# Mock nodes package and submodules
mock_nodes = MagicMock()
sys.modules["nodes"] = mock_nodes
sys.modules["nodes.midi"] = MagicMock()
sys.modules["nodes.midi.midi_listener_node"] = MagicMock()

# Define MIDIMapping for the mock
class MIDIMapping:
    def __init__(self, message_type, channel, note=None, cc=None):
        self.message_type = message_type
        self.channel = channel
        self.note = note
        self.cc = cc

sys.modules["nodes.midi.midi_listener_node"].MIDIMapping = MIDIMapping

# Add src to path
sys.path.insert(0, os.path.abspath("src"))

from editor.graph.visual_node import VisualNode, NodeCategory, Vector2
from editor.graph.visual_graph import VisualGraph
from editor.dsl.serializer import PresetSerializer, PresetDeserializer

# Mock MIDIMapping since we can't easily import from nodes.midi... without full setup
# We use the one injected into sys.modules above for consistency
class MockMIDIMapping:
    def __init__(self, message_type, channel, note=None, cc=None):
        self.message_type = message_type
        self.channel = channel
        self.note = note
        self.cc = cc

class TestMidiSerialization(unittest.TestCase):
    def test_midi_listener_serialization(self):
        # 1. Create a VisualNode with midi_mapping (as if added by Editor)
        node = VisualNode(
            id="midi_listener_001",
            node_type="midi.listener",
            category=NodeCategory.TRIGGER,
            position=Vector2(0, 0)
        )
        
        # Manually attach the mapping (simulating dynamic attachment)
        # Use the class we defined in the test, which mimics the runtime object
        mapping = MockMIDIMapping(message_type="note_on", channel=0, note=60)
        node.midi_mapping = mapping
        
        # 2. Add to Graph
        graph = VisualGraph()
        graph.add_node(node)
        
        # 3. Serialize
        yaml_str = PresetSerializer.serialize(graph)
        print("\nSerialized YAML:")
        print(yaml_str)
        
        # 4. Deserialize
        # This triggers the import inside serializer.py, which will use our mocked sys.modules
        new_graph = PresetDeserializer.deserialize(yaml_str)
        new_node = new_graph.get_node("midi_listener_001")
        
        # 5. Verify
        self.assertIsNotNone(new_node)
        self.assertTrue(hasattr(new_node, "midi_mapping"))
        self.assertIsNotNone(new_node.midi_mapping)
        
        # Check values
        # The deserialized object should be an instance of our mocked MIDIMapping (from sys.modules)
        self.assertEqual(new_node.midi_mapping.message_type, "note_on")
        self.assertEqual(new_node.midi_mapping.note, 60)

    def test_launcher_serialization(self):
        # 1. Create a VisualNode with midi_mapping (as if added by Editor)
        node = VisualNode(
            id="midi_listener_001",
            node_type="midi.listener",
            category=NodeCategory.TRIGGER,
            position=Vector2(0, 0)
        )
        
        # Manually attach the mapping (simulating dynamic attachment)
        mapping = MockMIDIMapping(message_type="note_on", channel=0, note=60)
        node.midi_mapping = mapping
        
        # 2. Add to Graph
        graph = VisualGraph()
        graph.add_node(node)
        
        # 3. Serialize
        yaml_str = PresetSerializer.serialize(graph)
        print("\nSerialized YAML:")
        print(yaml_str)
        
        # 4. Deserialize
        new_graph = PresetDeserializer.deserialize(yaml_str)
        new_node = new_graph.get_node("midi_listener_001")
        
        # 5. Verify
        self.assertIsNotNone(new_node)
        self.assertTrue(hasattr(new_node, "midi_mapping"))
        self.assertIsNotNone(new_node.midi_mapping)
        
        # Check values
        # deserializer creates a real MIDIMapping or dict? 
        # My code in deserializer imports MIDIMapping from nodes.midi.midi_listener_node
        # If that import fails (due to moderngl dependency), it falls back to dict.
        # Since we are running this test likely without moderngl, it might fail import or succeed if nodes don't import moderngl at top level?
        # src/nodes/midi/midi_listener_node.py imports moderngl at top level.
        # So import might fail if no context? No, import usually works, instantiation fails.
        # But moderngl module must be installed. 
        
        if isinstance(new_node.midi_mapping, dict):
            self.assertEqual(new_node.midi_mapping['message_type'], "note_on")
            self.assertEqual(new_node.midi_mapping['note'], 60)
        else:
            self.assertEqual(new_node.midi_mapping.message_type, "note_on")
            self.assertEqual(new_node.midi_mapping.note, 60)

    def test_launcher_serialization(self):
        # 1. Create Launcher Node
        node = VisualNode(
            id="launcher_001",
            node_type="midi.launcher",
            category=NodeCategory.TRIGGER,
            position=Vector2(100, 0)
        )
        
        # Attach launcher data
        node.target_generators = ["gen_001", "gen_002"]
        node.parameter_mappings = {"gen_001": ["speed", "size"]}
        
        graph = VisualGraph()
        graph.add_node(node)
        
        # 2. Serialize
        yaml_str = PresetSerializer.serialize(graph)
        print("\nSerialized Launcher YAML:")
        print(yaml_str)
        
        # 3. Deserialize
        new_graph = PresetDeserializer.deserialize(yaml_str)
        new_node = new_graph.get_node("launcher_001")
        
        # 4. Verify
        self.assertTrue(hasattr(new_node, "target_generators"))
        self.assertEqual(new_node.target_generators, ["gen_001", "gen_002"])
        
        self.assertTrue(hasattr(new_node, "parameter_mappings"))
        self.assertEqual(new_node.parameter_mappings, {"gen_001": ["speed", "size"]})

if __name__ == '__main__':
    unittest.main()
