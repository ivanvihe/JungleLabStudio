class NodeRegistry:
    _registry = {}

    @classmethod
    def register(cls, name):
        def decorator(node_cls):
            cls._registry[name] = node_cls
            return node_cls
        return decorator

    @classmethod
    def get(cls, name):
        return cls._registry.get(name)
