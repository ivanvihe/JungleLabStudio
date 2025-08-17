# ui/live_control_tab.py - cleaned and feature-complete implementation
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QGridLayout,
    QPushButton,
    QFrame,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QIcon, QPainterPath, QPen, QBrush

import json
import logging
from pathlib import Path


def create_live_control_tab(self):
    """Create live control tab with a grid of four decks by N visuals."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(10)

    # Header
    header_label = QLabel("🎛️ CONTROL EN VIVO - GRID DE VISUALES")
    header_label.setStyleSheet(
        """
        QLabel {
            font-size: 16px;
            font-weight: bold;
            color: #00ff00;
            padding: 10px;
            background-color: #1a1a1a;
            border: 2px solid #00ff00;
            border-radius: 8px;
        }
        """
    )
    header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(header_label)

    # Instructions
    instructions = QLabel(
        "💡 Vista de solo lectura del grid de control. Cada deck tiene su canal MIDI. "
        "Para editar notas MIDI, usa el tab 'Visual Settings'."
    )
    instructions.setStyleSheet(
        """
        QLabel {
            background-color: #e8f5e8;
            color: #2e7d32;
            padding: 8px;
            border-radius: 5px;
            border-left: 4px solid #4caf50;
            font-size: 11px;
        }
        """
    )
    instructions.setWordWrap(True)
    layout.addWidget(instructions)

    # Scroll area
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
                visuals = sorted(self.visualizer_manager.get_visualizer_names())
                logging.info(f"🎨 Found {len(visuals)} visuals for live control grid")
            except Exception as e:
                logging.error(f"Error getting visualizer names: {e}")
                visuals = ["Simple Test", "Abstract Lines", "Wire Terrain", "Geometric Particles"]
        if not visuals:
            create_fallback_grid(container)
            return

        midi_info = get_midi_mapping_info(self)

        deck_config = {
            "A": {"channel": 1, "color": "#ff6b6b", "name": "DECK A"},
            "B": {"channel": 2, "color": "#4ecdc4", "name": "DECK B"},
            "C": {"channel": 3, "color": "#45b7d1", "name": "DECK C"},
            "D": {"channel": 4, "color": "#96ceb4", "name": "DECK D"},
        }

        grid = QGridLayout(container)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        grid.setHorizontalSpacing(5)
        grid.setVerticalSpacing(5)

        for row, (deck_id, cfg) in enumerate(deck_config.items()):
            header = QLabel(f"{cfg['name']}\nCh {cfg['channel']}")
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header.setFixedSize(120, 120)
            header.setStyleSheet(
                f"border: 2px solid #333; border-radius: 8px; background-color: {cfg['color']};"
                "color: #000; font-weight: bold;"
            )
            grid.addWidget(header, row, 0)

            for col, visual_name in enumerate(visuals):
                cell = create_visual_cell(deck_id, col, visual_name, midi_info)
                grid.addWidget(cell, row, col + 1)

            # Clear column
            clear_btn = QPushButton("CLEAR")
            clear_btn.setFixedSize(120, 120)
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
            key_clear = f"deck_{deck_id.lower()}_clear"
            mapping = midi_info.get(key_clear)
            if mapping and isinstance(mapping, dict):
                ch, note = parse_midi_string(mapping.get("midi", ""))
                if ch is not None:
                    clear_btn.setToolTip(f"MIDI Ch {ch} Note {note}")
            else:
                clear_btn.setToolTip("No MIDI mapping")
            grid.addWidget(clear_btn, row, len(visuals) + 1)

    except Exception as e:
        logging.error(f"❌ Error creating live control grid: {e}")
        create_fallback_grid(container)


def create_visual_cell(deck_id, index, visual_name, midi_info):
    """Create a single 1:1 cell with thumbnail and quick-load button."""
    cell = QFrame()
    cell.setFixedSize(120, 120)
    cell.setStyleSheet(
        """
        QFrame {
            background-color: #1a1a1a;
            border: 2px solid #444444;
            border-radius: 8px;
        }
        QFrame:hover {
            border-color: #00ff00;
        }
        """
    )

    layout = QVBoxLayout(cell)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setSpacing(2)

    thumb_label = QLabel()
    thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    thumb_label.setFixedSize(112, 90)
    pix = create_thumbnail(visual_name)
    thumb_label.setPixmap(pix)
    layout.addWidget(thumb_label)

    play_btn = QPushButton("▶")
    play_btn.setFixedSize(24, 24)
    play_btn.setStyleSheet(
        """
        QPushButton {
            background-color: #333333;
            color: #00ff00;
            border: none;
            border-radius: 12px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #444444;
        }
        """
    )
    layout.addWidget(play_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

    key = f"deck_{deck_id.lower()}_preset_{index}"
    mapping = midi_info.get(key)
    if mapping and isinstance(mapping, dict):
        ch, note = parse_midi_string(mapping.get("midi", ""))
        if ch is not None:
            play_btn.setToolTip(f"MIDI Ch {ch} Note {note}")
    else:
        play_btn.setToolTip("No MIDI mapping")

    return cell


def create_thumbnail(visual_name: str) -> QPixmap:
    """Create a simple thumbnail based on the visual name."""
    pix = QPixmap(120, 120)
    pix.fill(QColor("#222"))

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(Qt.GlobalColor.white, 2))
    painter.setBrush(QBrush(Qt.GlobalColor.white))

    name = visual_name.lower()
    if "particle" in name:
        painter.drawEllipse(40, 40, 40, 40)
    elif "line" in name:
        for i in range(5):
            painter.drawLine(20, 20 + i * 15, 100, 20 + i * 15)
    elif "wire" in name or "terrain" in name:
        path = QPainterPath()
        path.moveTo(20, 100)
        path.lineTo(40, 60)
        path.lineTo(70, 80)
        path.lineTo(90, 40)
        path.lineTo(110, 70)
        painter.drawPath(path)
    elif "geom" in name or "geometric" in name:
        painter.drawRect(35, 35, 50, 50)
    elif "fluid" in name:
        painter.drawArc(30, 30, 60, 60, 0, 180 * 16)
    else:
        painter.drawRect(30, 30, 60, 60)

    painter.end()
    return pix


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


def parse_midi_string(midi_str):
    """Parse MIDI string and return (channel, note)."""
    try:
        parts = midi_str.split("_")
        ch_part = next(p for p in parts if p.startswith("ch"))
        note_part = next(p for p in parts if p.startswith("note"))
        ch = int(ch_part[2:]) + 1
        note = int(note_part[4:])
        return ch, note
    except Exception:
        return None, None


def create_fallback_grid(container):
    """Create fallback UI if no visuals are found."""
    layout = QVBoxLayout(container)
    error_label = QLabel("⚠️ No se encontraron visuales disponibles")
    error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(error_label)
    retry_btn = QPushButton("Reintentar")
    layout.addWidget(retry_btn, alignment=Qt.AlignmentFlag.AlignCenter)

