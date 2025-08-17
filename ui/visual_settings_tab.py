from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QScrollArea
)
from PyQt6.QtCore import Qt
from pathlib import Path
import json


def create_visual_settings_tab(self):
    """Tab for configuring visual presets and their MIDI mappings"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    layout.addWidget(scroll)

    container = QWidget()
    grid = QGridLayout(container)
    grid.setAlignment(Qt.AlignmentFlag.AlignTop)
    scroll.setWidget(container)

    mappings_path = Path('config/midi_mappings.json')
    try:
        with mappings_path.open('r', encoding='utf-8') as f:
            self.visual_midi_mappings = json.load(f)
    except Exception:
        self.visual_midi_mappings = {}

    visual_names = []
    try:
        visual_names = self.visualizer_manager.get_visualizer_names()
    except Exception:
        visual_names = []

    columns = 4

    def save_mapping(visual_name, line_edit):
        value = line_edit.text().strip()
        self.visual_midi_mappings[visual_name] = value
        try:
            with mappings_path.open('w', encoding='utf-8') as f:
                json.dump(self.visual_midi_mappings, f, indent=4)
        except Exception as e:
            print(f'Error saving midi mappings: {e}')

    for idx, name in enumerate(sorted(visual_names)):
        row = idx // columns
        col = idx % columns

        cell_widget = QWidget()
        cell_layout = QVBoxLayout(cell_widget)
        cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel(name)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cell_layout.addWidget(title)

        thumbnail = QLabel()
        thumbnail.setFixedSize(120, 90)
        thumbnail.setStyleSheet("background-color: #222; border: 1px solid #555;")
        cell_layout.addWidget(thumbnail)

        mapping_input = QLineEdit()
        mapping_input.setText(str(self.visual_midi_mappings.get(name, '')))
        cell_layout.addWidget(mapping_input)

        mapping_input.editingFinished.connect(
            lambda le=mapping_input, vn=name: save_mapping(vn, le)
        )

        grid.addWidget(cell_widget, row, col)

    return widget
