from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QPushButton,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator
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
            self._midi_data = json.load(f)
    except Exception:
        self._midi_data = {}
    self.visual_midi_mappings = self._midi_data.get('visual_mappings', {})

    visual_names = []
    try:
        visual_names = self.visualizer_manager.get_visualizer_names()
    except Exception:
        visual_names = []

    columns = 4
    self._mapping_inputs = {}

    def write_mappings():
        self._midi_data['visual_mappings'] = self.visual_midi_mappings
        try:
            with mappings_path.open('w', encoding='utf-8') as f:
                json.dump(self._midi_data, f, indent=4)
        except Exception as e:
            print(f'Error saving midi mappings: {e}')

    def on_edit(visual_name):
        line_edit = self._mapping_inputs[visual_name]
        value = line_edit.text().strip()
        if value == '':
            self.visual_midi_mappings.pop(visual_name, None)
        else:
            self.visual_midi_mappings[visual_name] = int(value)
        write_mappings()

    for idx, name in enumerate(sorted(visual_names)):
        row = idx // columns
        col = idx % columns

        cell_widget = QWidget()
        cell_widget.setFixedSize(140, 160)
        cell_layout = QVBoxLayout(cell_widget)
        cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel(name)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cell_layout.addWidget(title)

        thumbnail = QLabel()
        thumbnail.setFixedSize(140, 100)
        thumbnail.setStyleSheet("background-color: #222; border: 1px solid #555;")
        cell_layout.addWidget(thumbnail)

        mapping_input = QLineEdit()
        mapping_input.setValidator(QIntValidator(0, 127, mapping_input))
        mapping_input.setText(str(self.visual_midi_mappings.get(name, '')))
        mapping_input.textChanged.connect(lambda _, vn=name: on_edit(vn))
        cell_layout.addWidget(mapping_input)

        self._mapping_inputs[name] = mapping_input
        grid.addWidget(cell_widget, row, col)

    save_btn = QPushButton('Guardar Cambios')
    save_btn.clicked.connect(write_mappings)
    layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)

    return widget
