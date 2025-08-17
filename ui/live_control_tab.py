from PyQt6.QtWidgets import (
    QWidget,
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QIcon

def create_live_control_tab(self):
    """Create live control tab with a grid of four decks by N visuals"""
    container = QWidget()
    outer_layout = QVBoxLayout(container)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    outer_layout.addWidget(scroll)

    grid_widget = QWidget()
    grid_layout = QGridLayout(grid_widget)
    grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    grid_layout.setHorizontalSpacing(5)
    grid_layout.setVerticalSpacing(5)
    scroll.setWidget(grid_widget)

    visuals = []
    if getattr(self, "visualizer_manager", None):
        visuals = sorted(self.visualizer_manager.get_visualizer_names())

    # Load MIDI mappings for tooltip info
    midi_map = {}
    try:
        import json
        from pathlib import Path
        mappings_path = Path("config/midi_mappings.json")
        if mappings_path.exists():
            with mappings_path.open("r", encoding="utf-8") as f:
                midi_map = json.load(f)
    except Exception:
        midi_map = {}

    def parse_midi_string(midi_str):
        try:
            parts = midi_str.split("_")
            ch_part = next(p for p in parts if p.startswith("ch"))
            note_part = next(p for p in parts if p.startswith("note"))
            ch = int(ch_part[2:]) + 1  # convert to 1-indexed
            note = int(note_part[4:])
            return ch, note
        except Exception:
            return None, None

    def thumbnail_for(name: str) -> QPixmap:
        pix = QPixmap(120, 120)
        pix.fill(QColor("#222"))
        painter = QPainter(pix)
        painter.setPen(Qt.GlobalColor.white)
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, name[:10])
        painter.end()
        return pix

    for row, deck_id in enumerate(["A", "B", "C", "D"]):
        header = QLabel(f"Deck {deck_id}\nCh {row + 1}")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFixedSize(120, 120)
        header.setStyleSheet("border: 1px solid #555; background-color: #333; color: #fff;")
        grid_layout.addWidget(header, row, 0)

        for col, visual_name in enumerate(visuals):
            btn = QPushButton()
            btn.setFixedSize(120, 120)
            pix = thumbnail_for(visual_name)
            btn.setIcon(QIcon(pix))
            btn.setIconSize(QSize(120, 120))

            key = f"deck_{deck_id.lower()}_preset_{col}"
            ch, note = None, None
            mapping = midi_map.get(key)
            if mapping and isinstance(mapping, dict):
                midi_str = mapping.get("midi", "")
                ch, note = parse_midi_string(midi_str)
            if ch is not None and note is not None:
                btn.setToolTip(f"MIDI Ch {ch} Note {note}")
            else:
                btn.setToolTip("No MIDI mapping")

            grid_layout.addWidget(btn, row, col + 1)

    return container

