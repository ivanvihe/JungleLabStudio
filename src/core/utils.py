import time
from typing import Tuple


class Clock:
    def __init__(self) -> None:
        self.last = time.perf_counter()

    def tick(self) -> float:
        now = time.perf_counter()
        dt = now - self.last
        self.last = now
        return dt


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def aspect_for_orientation(width: int, height: int, orientation: str) -> Tuple[int, int]:
    target_aspect = 9 / 16 if orientation == "vertical" else 16 / 9
    w, h = width, height
    desired_h = int(w / target_aspect)
    if desired_h > h:
        w = int(h * target_aspect)
        desired_h = h
    return w, desired_h
