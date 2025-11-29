from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class PresetState:
    params: Dict[str, Any] = field(default_factory=dict)
    glitch: float = 0.3
    bloom: float = 0.8
    aberration: float = 0.6
    midi_burst: float = 0.0


class VisualPreset(ABC):
    name: str = "base"

    def __init__(self, ctx, size: tuple[int, int], state: PresetState):
        self.ctx = ctx
        self.size = size
        self.state = state
        self.init()

    @abstractmethod
    def init(self) -> None:
        ...

    @abstractmethod
    def update_render(self, dt: float, audio_tex, fft_gain: float, bands, midi_events, orientation: str) -> None:
        ...

    def trigger(self) -> None:
        self.state.midi_burst = 1.0

    def trigger_action(self, action: str, payload=None) -> None:
        # Override in presets for custom actions
        pass

    @property
    def actions(self) -> list[str]:
        return []
