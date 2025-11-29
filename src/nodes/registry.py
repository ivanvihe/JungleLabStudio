"""Node registry for tracking available node types"""

from typing import Dict, Type
from nodes.base import Node


NODE_REGISTRY: Dict[str, Type[Node]] = {}


def register_node(name: str):
    """Decorator to register a node class"""
    def decorator(cls: Type[Node]):
        NODE_REGISTRY[name] = cls
        cls.node_name = name
        return cls
    return decorator


def get_node_class(name: str) -> Type[Node]:
    """Get a node class by name"""
    if name not in NODE_REGISTRY:
        raise ValueError(f"Unknown node type: {name}")
    return NODE_REGISTRY[name]


def list_nodes() -> Dict[str, Type[Node]]:
    """Get all registered nodes"""
    return NODE_REGISTRY.copy()
