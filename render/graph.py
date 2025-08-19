from dataclasses import dataclass, field
from typing import Callable, List
import taichi as ti

@dataclass
class Pass:
    """A single compute pass in the rendering pipeline."""
    name: str
    compute: Callable[[ti.Field], None]

    def run(self, target: ti.Field) -> None:
        """Execute the compute function on the given field."""
        try:
            self.compute(target)
        except Exception as e:
            print(f"Error in pass '{self.name}': {e}")
            # Clear the target as fallback
            try:
                for i, j in target:
                    target[i, j] = 0.0
            except:
                pass  # If even clearing fails, just continue

@dataclass
class Layer:
    """A layer consisting of multiple passes."""
    passes: List[Pass] = field(default_factory=list)

    def add_pass(self, pass_: Pass) -> None:
        """Add a pass to this layer."""
        self.passes.append(pass_)

    def clear_passes(self) -> None:
        """Clear all passes from this layer."""
        self.passes.clear()

    def run(self, target: ti.Field) -> None:
        """Run all passes in this layer."""
        for p in self.passes:
            p.run(target)

# Alias for backward compatibility
RenderLayer = Layer