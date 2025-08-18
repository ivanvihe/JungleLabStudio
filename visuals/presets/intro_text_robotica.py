import time
from typing import Tuple

import numpy as np
import taichi as ti

from visuals.base import TaichiVisual

# 5x7 block font for required letters
LETTER_PATTERNS = {
    "R": [
        "11110",
        "10001",
        "10001",
        "11110",
        "10100",
        "10010",
        "10001",
    ],
    "O": [
        "01110",
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "01110",
    ],
    "B": [
        "11110",
        "10001",
        "10001",
        "11110",
        "10001",
        "10001",
        "11110",
    ],
    "T": [
        "11111",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
    ],
    "I": [
        "11111",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "11111",
    ],
    "C": [
        "01110",
        "10001",
        "10000",
        "10000",
        "10000",
        "10001",
        "01110",
    ],
    "A": [
        "01110",
        "10001",
        "10001",
        "11111",
        "10001",
        "10001",
        "10001",
    ],
}


def _build_pattern(text: str) -> Tuple[np.ndarray, np.ndarray]:
    letters = [LETTER_PATTERNS[ch] for ch in text]
    height = len(letters[0])
    width = len(letters) * 6 - 1
    pattern = np.zeros((width, height), dtype=np.int32)
    idx = -np.ones((width, height), dtype=np.int32)
    x = 0
    for li, letter in enumerate(letters):
        for y, row in enumerate(letter):
            for x0, ch in enumerate(row):
                if ch == "1":
                    pattern[x + x0, y] = 1
                    idx[x + x0, y] = li
        x += 6
    return pattern, idx


@ti.kernel
def _clear(img: ti.template()):
    for i, j in img:
        img[i, j] = 0.0


@ti.kernel
def _update_alpha(alpha: ti.template(), idx: ti.template(), t: ti.f32, fade: ti.f32, delay: ti.f32):
    for i, j in alpha:
        k = idx[i, j]
        if k >= 0:
            start = delay * ti.cast(k, ti.f32)
            if t > start:
                alpha[i, j] = min((t - start) / fade, 1.0)
            else:
                alpha[i, j] = 0.0
        else:
            alpha[i, j] = 0.0


@ti.kernel
def _draw_text(
    img: ti.template(),
    pattern: ti.template(),
    alpha: ti.template(),
    ox: ti.i32,
    oy: ti.i32,
    scale: ti.i32,
):
    for i, j in pattern:
        if pattern[i, j] != 0:
            a = alpha[i, j]
            for dx, dy in ti.ndrange(scale, scale):
                x = ox + i * scale + dx
                y = oy + j * scale + dy
                if 0 <= x < img.shape[0] and 0 <= y < img.shape[1]:
                    img[x, y] = a


class IntroTextRoboticaVisualizer(TaichiVisual):
    """Displays the text 'ROBOTICA' with a fade-in animation."""

    visual_name = "Intro Text ROBOTICA"

    def __init__(self, *args, **kwargs):
        self.text = "ROBOTICA"
        self.scale = 8
        self.fade_duration = 1.5
        self.letter_delay = 0.2
        pattern_np, idx_np = _build_pattern(self.text)
        self.pattern = ti.field(dtype=ti.i32, shape=pattern_np.shape)
        self.pattern.from_numpy(pattern_np)
        self.index_map = ti.field(dtype=ti.i32, shape=idx_np.shape)
        self.index_map.from_numpy(idx_np)
        self.alpha = ti.field(dtype=ti.f32, shape=pattern_np.shape)
        self.start_time = time.time()
        super().__init__(*args, **kwargs)

    def setup(self):
        w, h = self.renderer.resolution
        pw, ph = self.pattern.shape
        self.offset_x = (w - pw * self.scale) // 2
        self.offset_y = (h - ph * self.scale) // 2
        self.renderer.add_pass("text", self._render_pass)

    def _render_pass(self, img):
        _clear(img)
        _update_alpha(
            self.alpha,
            self.index_map,
            ti.cast(self.elapsed, ti.f32),
            self.fade_duration,
            self.letter_delay,
        )
        _draw_text(img, self.pattern, self.alpha, self.offset_x, self.offset_y, self.scale)

    def render(self):
        self.elapsed = time.time() - self.start_time
        return super().render()
