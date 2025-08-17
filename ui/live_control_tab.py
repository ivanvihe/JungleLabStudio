# ui/live_control_tab.py - cleaned and feature-complete implementation
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QGridLayout,
    QFrame,
    QPushButton,
    QSpinBox,
    QSlider,
)
from PyQt6.QtCore import Qt

import json
import logging
from pathlib import Path
import mido

from .thumbnail_utils import generate_visual_thumbnail

# Base style for visual cells
# Only the outer cell frame should display a border. Child widgets like the
# thumbnail, title and note labels inherit from QFrame (e.g. QLabel) and would
# otherwise also render a border. We scope the style to a specific object name
# and explicitly clear borders on any QLabel children so the inner elements
# appear as a single, unified container.
BASE_CELL_STYLE = """
QFrame#visual-cell {
    background-color: #1a1a1a;
    border: 2px solid #444444;
    border-radius: 8px;
}
QFrame#visual-cell:hover {
    border-color: #00ff00;
}
QLabel {
    border: none;
    background: transparent;
}
"""
def create_live_control_tab(self):
    """Create live control tab with a grid of four decks by N visuals."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(5, 5, 5, 5)
    layout.setSpacing(5)

    # Scroll area
    # Scroll area for the visual grid
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setStyleSheet(
        """
        QScrollArea {
            border: 1px solid #666666;
            border-radius: 5px;
            background-color: #1a1a1a;
        }
        """
    )
    layout.addWidget(scroll)

    container = QWidget()
    scroll.setWidget(container)

    create_improved_deck_grid(self, container)

    return widget


def create_improved_deck_grid(self, container):
    """Create improved grid with 1:1 squares and thumbnails."""
    try:
        visuals = []
        if hasattr(self, "visualizer_manager") and self.visualizer_manager:
            try:
                visuals = self.visualizer_manager.get_visualizer_names()
                logging.info(f"🎨 Found {len(visuals)} visuals for live control grid")
            except Exception as e:
                logging.error(f"Error getting visualizer names: {e}")
                visuals = ["Abstract Lines", "Wire Terrain", "Geometric Particles"]
        if not visuals:
            create_fallback_grid(container)
            return

        midi_info = get_midi_mapping_info(self)
        # Sort visuals by assigned MIDI note, falling back to high value
        visuals = sorted(visuals, key=lambda v: midi_info.get(v, 9999))

        deck_channels = {"A": 12, "B": 13, "C": 14, "D": 15}
        if (
            hasattr(self, "midi_engine")
            and self.midi_engine
            and getattr(self.midi_engine, "visual_mapper", None)
        ):
            deck_channels = self.midi_engine.visual_mapper.config.get(
                "deck_channels", deck_channels
            )

        deck_config = {
            "A": {"channel": deck_channels.get("A", 0) + 1, "color": "#ff6b6b", "name": "DECK A"},
            "B": {"channel": deck_channels.get("B", 1) + 1, "color": "#4ecdc4", "name": "DECK B"},
            "C": {"channel": deck_channels.get("C", 2) + 1, "color": "#45b7d1", "name": "DECK C"},
            "D": {"channel": deck_channels.get("D", 3) + 1, "color": "#96ceb4", "name": "DECK D"},
        }

        # Store grid info for interactions
        self.live_grid_cells = {}
        self.live_grid_midi_info = midi_info
        self.live_grid_deck_channels = {}
        self.live_grid_deck_colors = {}

        grid = QGridLayout(container)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        grid.setHorizontalSpacing(5)
        grid.setVerticalSpacing(5)

        for row, (deck_id, cfg) in enumerate(deck_config.items()):
            self.live_grid_cells[deck_id] = {}
            self.live_grid_deck_channels[deck_id] = cfg["channel"]
            self.live_grid_deck_colors[deck_id] = cfg["color"]

            header_widget = QWidget()
            header_widget.setFixedSize(100, 100)
            header_widget.setStyleSheet(
                f"border: 2px solid #333; border-radius: 8px; background-color: {cfg['color']};"
            )
            header_layout = QVBoxLayout(header_widget)
            header_layout.setContentsMargins(2, 2, 2, 2)
            header_layout.setSpacing(2)

            header_label = QLabel(f"{cfg['name']}\nCh {cfg['channel']}")
            header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_label.setStyleSheet("color: #000; font-weight: bold;")
            header_layout.addWidget(header_label)

            fade_input = QSpinBox()
            fade_input.setRange(0, 10000)
            fade_input.setSuffix(" ms")
            fade_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fade_input.setValue(2000)
            header_layout.addWidget(fade_input)

            if not hasattr(self, "deck_fade_inputs"):
                self.deck_fade_inputs = {}
            self.deck_fade_inputs[deck_id] = fade_input

            if hasattr(self, "mixer_window") and self.mixer_window:
                try:
                    self.mixer_window.set_deck_fade_time(deck_id, fade_input.value())

                    def on_fade_change(value, d=deck_id):
                        try:
                            self.mixer_window.set_deck_fade_time(d, value)
                        except Exception as e:
                            logging.error(f"Error setting fade time for deck {d}: {e}")

                    fade_input.valueChanged.connect(on_fade_change)
                except Exception as e:
                    logging.error(f"Error initializing fade input for deck {deck_id}: {e}")

            opacity_slider = QSlider(Qt.Orientation.Horizontal)
            opacity_slider.setRange(0, 100)
            opacity_slider.setValue(100)
            header_layout.addWidget(opacity_slider)

            opacity_label = QLabel("100%")
            opacity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(opacity_label)

            if not hasattr(self, "deck_opacity_sliders"):
                self.deck_opacity_sliders = {}
            self.deck_opacity_sliders[deck_id] = opacity_slider

            if hasattr(self, "mixer_window") and self.mixer_window:
                try:
                    self.mixer_window.set_deck_opacity(deck_id, 1.0)

                    def on_opacity_change(value, d=deck_id, lbl=opacity_label):
                        try:
                            lbl.setText(f"{value}%")
                            self.mixer_window.set_deck_opacity(d, value / 100.0)
                        except Exception as e:
                            logging.error(f"Error setting opacity for deck {d}: {e}")

                    opacity_slider.valueChanged.connect(on_opacity_change)
                except Exception as e:
                    logging.error(
                        f"Error initializing opacity slider for deck {deck_id}: {e}"
                    )

            grid.addWidget(header_widget, row, 0)

            for col, visual_name in enumerate(visuals):
                cell = create_visual_cell(self, deck_id, visual_name, midi_info, cfg["color"])
                self.live_grid_cells[deck_id][visual_name] = cell
                grid.addWidget(cell, row, col + 1)

            clear_btn = QPushButton("CLEAR")
            clear_btn.setFixedSize(100, 100)
            clear_btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #222222;
                    color: #ffffff;
                    border: 2px solid #444444;
                    border-radius: 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    border-color: #00ff00;
                }
                """
            )
            grid.addWidget(clear_btn, row, len(visuals) + 1)

    except Exception as e:
        logging.error(f"❌ Error creating live control grid: {e}")

        existing_layout = container.layout()
        if existing_layout is not None:
            while existing_layout.count():
                item = existing_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
            existing_layout.deleteLater()

        create_fallback_grid(container)


def create_visual_cell(parent, deck_id, visual_name, midi_info, deck_color):
    """Create a 100x100 cell with thumbnail, name and MIDI note."""
    cell = QFrame()
    cell.setObjectName("visual-cell")
    cell.setFixedSize(100, 100)
    cell.setStyleSheet(BASE_CELL_STYLE)

    layout = QVBoxLayout(cell)
    layout.setContentsMargins(2, 2, 2, 2)
    layout.setSpacing(1)

    thumb_label = QLabel()
    thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    thumb_label.setFixedSize(96, 60)
    thumb_label.setPixmap(generate_visual_thumbnail(visual_name, 96, 60))
    layout.addWidget(thumb_label)
    cell.thumb_label = thumb_label

    name_label = QLabel(visual_name)
    name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    name_label.setStyleSheet("color: #ffffff; font-size:10px;")
    layout.addWidget(name_label)

    note = midi_info.get(visual_name)
    note_label = QLabel(f"Note {note}" if note is not None else "Note -")
    note_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    note_label.setStyleSheet("color: #cccccc; font-size:9px;")
    layout.addWidget(note_label)

    # Store base style for future resets
    cell.base_style = BASE_CELL_STYLE

    # Connect click to trigger visual
    def mouse_press(event, d=deck_id, v=visual_name):
        trigger_visual_from_grid(parent, d, v)

    cell.mousePressEvent = mouse_press

    return cell


def get_midi_mapping_info(self):
    """Load MIDI mapping information from config file."""
    mappings_path = Path("config/midi_mappings.json")
    if mappings_path.exists():
        try:
            with mappings_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            logging.error(f"Error reading MIDI mappings: {e}")
    return {}


def create_fallback_grid(container):
    """Create fallback UI if no visuals are found."""
    layout = QVBoxLayout(container)
    error_label = QLabel("⚠️ No visuals found")
    error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(error_label)
    retry_btn = QPushButton("Retry")
    layout.addWidget(retry_btn, alignment=Qt.AlignmentFlag.AlignCenter)


def trigger_visual_from_grid(self, deck_id, visual_name):
    """Simulate MIDI note to trigger a visual on a deck."""
    try:
        note = getattr(self, "live_grid_midi_info", {}).get(visual_name)
        channel = getattr(self, "live_grid_deck_channels", {}).get(deck_id, 1) - 1
        if note is None or not hasattr(self, "midi_engine"):
            return
        msg = mido.Message("note_on", channel=channel, note=note, velocity=127)
        self.midi_engine.handle_midi_message(msg)
    except Exception as e:
        logging.error(f"Error triggering visual {visual_name} on deck {deck_id}: {e}")

