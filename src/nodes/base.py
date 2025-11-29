"""Base classes for node-based visual system"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import numpy as np


class DataType(Enum):
    """Data types that can flow between nodes"""
    GEOMETRY = "geometry"      # 3D mesh, vertices, indices
    TEXTURE = "texture"        # 2D image/texture
    FIELD = "field"           # Vector or scalar field
    PARTICLES = "particles"    # Particle system data
    NUMBER = "number"         # Single float value
    VECTOR2 = "vector2"       # 2D vector
    VECTOR3 = "vector3"       # 3D vector
    COLOR = "color"           # RGB/RGBA color
    TRANSFORM = "transform"   # Transformation matrix
    SHADER = "shader"         # Shader code/reference
    ANY = "any"              # Accepts any type


class NodeType(Enum):
    """Categories of nodes"""
    GENERATOR = "generator"
    MODIFIER = "modifier"
    VFX = "vfx"
    ANIMATION = "animation"
    TRIGGER = "trigger"
    OUTPUT = "output"


@dataclass
class NodeOutput:
    """Output from a node"""
    data: Any
    data_type: DataType
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class NodeInput:
    """Input port definition for a node"""
    def __init__(self, name: str, data_type: Union[DataType, List[DataType]],
                 required: bool = True, default: Any = None):
        self.name = name
        self.data_type = data_type if isinstance(data_type, list) else [data_type]
        self.required = required
        self.default = default

    def accepts(self, data_type: DataType) -> bool:
        """Check if this input accepts the given data type"""
        return DataType.ANY in self.data_type or data_type in self.data_type


class NodeOutputPort:
    """Output port definition for a node"""
    def __init__(self, name: str, data_type: DataType):
        self.name = name
        self.data_type = data_type


class Node:
    """Base class for all nodes in the visual system"""

    node_type: NodeType = NodeType.GENERATOR

    def __init__(self, node_id: str, params: Dict[str, Any] = None):
        self.node_id = node_id
        self.params = params or {}
        self.inputs: Dict[str, NodeInput] = {}
        self.outputs: Dict[str, NodeOutputPort] = {}
        self.input_connections: Dict[str, Optional[Node]] = {}
        self._setup_ports()

    def _setup_ports(self):
        """Setup input and output ports - override in subclasses"""
        pass

    def add_input(self, name: str, data_type: Union[DataType, List[DataType]],
                  required: bool = True, default: Any = None):
        """Add an input port"""
        self.inputs[name] = NodeInput(name, data_type, required, default)
        self.input_connections[name] = None

    def add_output(self, name: str, data_type: DataType):
        """Add an output port"""
        self.outputs[name] = NodeOutputPort(name, data_type)

    def connect_input(self, input_name: str, source_node: 'Node'):
        """Connect an input to another node's output"""
        if input_name not in self.inputs:
            raise ValueError(f"Input '{input_name}' does not exist on node {self.node_id}")
        self.input_connections[input_name] = source_node

    def get_param(self, name: str, default: Any = None) -> Any:
        """Get a parameter value"""
        return self.params.get(name, default)

    def set_param(self, name: str, value: Any):
        """Set a parameter value"""
        self.params[name] = value

    def get_input_value(self, input_name: str, state: Any) -> Optional[NodeOutput]:
        """Get the value from a connected input"""
        if input_name in self.input_connections:
            source_node = self.input_connections[input_name]
            if source_node is not None:
                return source_node.execute(state)

        # Return default if available
        if input_name in self.inputs:
            return NodeOutput(
                data=self.inputs[input_name].default,
                data_type=self.inputs[input_name].data_type[0]
            )
        return None

    def validate_inputs(self) -> bool:
        """Validate that all required inputs are connected"""
        for input_name, input_port in self.inputs.items():
            if input_port.required and self.input_connections.get(input_name) is None:
                if input_port.default is None:
                    return False
        return True

    def execute(self, state: Any) -> NodeOutput:
        """Execute the node and return output - override in subclasses"""
        raise NotImplementedError("Subclasses must implement execute()")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.node_id})"


class GeneratorNode(Node):
    """Base class for generator nodes that create geometry/data"""
    node_type = NodeType.GENERATOR


class ModifierNode(Node):
    """Base class for modifier nodes that transform data"""
    node_type = NodeType.MODIFIER


class VFXNode(Node):
    """Base class for VFX nodes that apply effects"""
    node_type = NodeType.VFX


class TriggerNode(Node):
    """Base class for trigger nodes that control parameters"""
    node_type = NodeType.TRIGGER

    def evaluate(self, state: Any) -> float:
        """Evaluate trigger and return a value (0.0-1.0)"""
        raise NotImplementedError("Subclasses must implement evaluate()")
