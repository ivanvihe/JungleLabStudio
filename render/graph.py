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
        self.compute(target)

@dataclass
class Layer:
    """A layer consisting of multiple passes."""
    passes: List[Pass] = field(default_factory=list)

    def add_pass(self, pass_: Pass) -> None:
        self.passes.append(pass_)

    def run(self, target: ti.Field) -> None:
        for p in self.passes:
            p.run(target)
