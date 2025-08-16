# visuals/presets/intro_text_robotica.py
import logging
from OpenGL.GL import *
from ..base_visualizer import BaseVisualizer


class IntroTextRoboticaVisualizer(BaseVisualizer):
    """Overlay visualizer that displays the text 'R O B O T I C A' with a transparent background."""

    visual_name = "Intro Text ROBOTICA"

    # 5x7 block font patterns for required letters
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

    def __init__(self):
        super().__init__()
        self.text = "R O B O T I C A"
        self.initialized = False
        logging.info("IntroTextRoboticaVisualizer created")

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 0.0)  # transparent background
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_DEPTH_TEST)
        self.initialized = True
        logging.info("✅ IntroTextRoboticaVisualizer initialized successfully")

    def _draw_letter(self, ch, x, y, cell):
        pattern = self.LETTER_PATTERNS.get(ch)
        if not pattern:
            return 0.0
        for row, row_data in enumerate(pattern):
            for col, val in enumerate(row_data):
                if val == "1":
                    x0 = x + col * cell
                    y0 = y + (len(pattern) - row - 1) * cell
                    glBegin(GL_QUADS)
                    glVertex2f(x0, y0)
                    glVertex2f(x0 + cell, y0)
                    glVertex2f(x0 + cell, y0 + cell)
                    glVertex2f(x0, y0 + cell)
                    glEnd()
        return 5 * cell

    def paintGL(self):
        if not self.initialized:
            return
        glClear(GL_COLOR_BUFFER_BIT)
        glColor4f(1.0, 1.0, 1.0, 1.0)  # light letters

        letter_height = 1.2  # overall height of letters
        cell = letter_height / 7.0
        space = cell * 2.0

        total_width = 0.0
        for ch in self.text:
            if ch == " ":
                total_width += space
            else:
                total_width += 5 * cell + space
        start_x = -total_width / 2.0
        start_y = -letter_height / 2.0

        x = start_x
        for ch in self.text:
            if ch == " ":
                x += space
                continue
            letter_width = self._draw_letter(ch, x, start_y, cell)
            x += letter_width + space

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)

    def cleanup(self):
        self.initialized = False

    def get_controls(self):
        return {}
