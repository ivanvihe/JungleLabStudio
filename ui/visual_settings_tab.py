# ui/visual_settings_tab.py - cleaned and feature-complete implementation
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QPushButton,
    QFrame,
    QHBoxLayout,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QIntValidator,
    QFont,
)

from pathlib import Path
import json
import logging

from .thumbnail_utils import generate_visual_thumbnail

# ---------------------------------------------------------------------------
# Visual settings tab
# ---------------------------------------------------------------------------

def create_visual_settings_tab(self):
    """Tab for configuring visual presets and their MIDI mappings."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(10)

    # Header ---------------------------------------------------------------
    header_layout = QHBoxLayout()

    header_label = QLabel("🖼️ CONFIGURACIÓN DE VISUALES Y MIDI")
    header_label.setStyleSheet(
        """
        QLabel {
            font-size: 16px;
            font-weight: bold;
            color: #ff6600;
            padding: 10px;
            background-color: #1a1a1a;
            border: 2px solid #ff6600;
            border-radius: 8px;
        }
        """
    )
    header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    header_layout.addWidget(header_label)

    save_button = QPushButton("💾 Guardar Cambios")
    save_button.setStyleSheet(
        """
        QPushButton {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        """
    )
    save_button.clicked.connect(lambda: save_all_midi_mappings(self))
    header_layout.addWidget(save_button)

    layout.addLayout(header_layout)

    # Instructions ---------------------------------------------------------
    instructions = QLabel(
        "💡 Edit the MIDI note for each visual. Changes are saved "
        "automatically when leaving the field or pressing 'Save Changes'."
    )
    instructions.setStyleSheet(
        """
        QLabel {
            background-color: #f0f8ff;
            color: #333333;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #0066cc;
        }
        """
    )
    instructions.setWordWrap(True)
    layout.addWidget(instructions)

    # Scroll area ----------------------------------------------------------
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    layout.addWidget(scroll)

    container = QWidget()
    scroll.setWidget(container)

    # Create grid
    create_visual_settings_grid(self, container)

    return widget


def create_visual_settings_grid(self, container):
    """Create grid of visual settings with editable MIDI notes."""
    try:
        visuals = []
        if hasattr(self, "visualizer_manager") and self.visualizer_manager:
            try:
                visuals = sorted(self.visualizer_manager.get_visualizer_names())
            except Exception as e:
                logging.error(f"Error getting visualizer names: {e}")
                visuals = ["Abstract Lines", "Wire Terrain"]
        if not visuals:
            create_fallback_visual_grid(container)
            return

        current_mappings = load_current_midi_mappings()

        columns = 4
        rows = (len(visuals) + columns - 1) // columns

        grid = QGridLayout(container)
        grid.setSpacing(12)
        grid.setContentsMargins(15, 15, 15, 15)

        for col in range(columns):
            grid.setColumnStretch(col, 1)

        for idx, visual_name in enumerate(visuals):
            row = idx // columns
            col = idx % columns
            visual_cell = create_visual_settings_cell(visual_name, current_mappings)
            grid.addWidget(visual_cell, row, col)

        self.visual_settings_grid = grid
        self.visual_mappings = current_mappings
        logging.info(
            f"✅ Created visual settings grid: {len(visuals)} visuals in {rows}x{columns} grid"
        )
    except Exception as e:
        logging.error(f"❌ Error creating visual settings grid: {e}")
        create_fallback_visual_grid(container)


def create_visual_settings_cell(visual_name, current_mappings):
    """Create a visual settings cell with editable MIDI note."""
    cell = QFrame()
    cell.setFixedSize(140, 160)
    cell.setFrameStyle(QFrame.Shape.StyledPanel)
    cell.setStyleSheet(
        """
        QFrame {
            background-color: #2a2a2a;
            border: 2px solid #666666;
            border-radius: 10px;
        }
        QFrame:hover {
            border-color: #ff6600;
            background-color: #3a3a3a;
        }
        """
    )

    layout = QVBoxLayout(cell)
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(4)

    thumbnail = create_visual_thumbnail_large(visual_name)
    thumbnail.setFixedSize(80, 60)
    thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(thumbnail)

    name_label = QLabel(visual_name)
    name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    name_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
    name_label.setStyleSheet(
        """
        QLabel {
            color: #ffffff;
            background-color: transparent;
            border: none;
            padding: 2px;
        }
        """
    )
    name_label.setWordWrap(True)
    name_label.setMaximumHeight(30)
    layout.addWidget(name_label)

    midi_section = QFrame()
    midi_layout = QVBoxLayout(midi_section)
    midi_layout.setContentsMargins(0, 0, 0, 0)
    midi_layout.setSpacing(2)

    midi_label = QLabel("MIDI Note:")
    midi_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    midi_label.setFont(QFont("Arial", 8))
    midi_label.setStyleSheet("color: #cccccc;")
    midi_layout.addWidget(midi_label)

    current_note = get_midi_note_from_mappings(visual_name, current_mappings)
    note_edit = create_midi_note_editor(visual_name, current_note)
    midi_layout.addWidget(note_edit)

    layout.addWidget(midi_section)

    return cell


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def create_visual_thumbnail_large(visual_name):
    """Create larger thumbnail for visual settings."""
    thumbnail = QLabel()
    thumbnail.setStyleSheet(
        """
        QLabel {
            background-color: #1a1a1a;
            border: 1px solid #666666;
            border-radius: 6px;
        }
        """
    )

    pixmap = generate_visual_thumbnail(visual_name, 80, 60)
    thumbnail.setPixmap(pixmap)
    return thumbnail


def create_midi_note_editor(visual_name, current_note):
    """Create editable MIDI note field with validation."""
    note_edit = QLineEdit(str(current_note) if current_note is not None else "")
    note_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
    note_edit.setFont(QFont("Arial", 10, QFont.Weight.Bold))
    note_edit.setStyleSheet(
        """
        QLineEdit {
            color: #ffffff;
            background-color: #444444;
            border: 2px solid #666666;
            border-radius: 5px;
            padding: 4px;
            min-height: 20px;
        }
        QLineEdit:focus {
            border-color: #ff6600;
            background-color: #555555;
        }
        QLineEdit:hover {
            border-color: #888888;
        }
        """
    )
    note_edit.setPlaceholderText("0-127")
    note_edit.setMaxLength(3)

    def validate_and_save():
        try:
            text = note_edit.text().strip()
            if text:
                note_num = int(text)
                if 0 <= note_num <= 127:
                    save_visual_midi_mapping(visual_name, note_num)
                    note_edit.setStyleSheet(
                        note_edit.styleSheet().replace(
                            "border-color: #ff0000", "border-color: #666666"
                        )
                    )
                else:
                    note_edit.setStyleSheet(note_edit.styleSheet() + "; border-color: #ff0000;")
                    QMessageBox.warning(
                        None,
                        "Invalid Value",
                        f"MIDI note must be between 0 and 127.\nEntered value: {note_num}",
                    )
            else:
                save_visual_midi_mapping(visual_name, None)
        except ValueError:
            note_edit.setStyleSheet(note_edit.styleSheet() + "; border-color: #ff0000;")
            QMessageBox.warning(
                None,
                "Invalid Value",
                "Please enter a valid number (0-127).",
            )

    note_edit.editingFinished.connect(validate_and_save)
    return note_edit


def load_current_midi_mappings():
    """Load current MIDI mappings from config file."""
    mappings = {}
    try:
        config_path = Path("config/midi_mappings.json")
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    for name, note in data.items():
                        if isinstance(note, int):
                            mappings[name] = note
            logging.info(f"Loaded {len(mappings)} visual MIDI mappings from config")
        else:
            logging.info("No existing MIDI mappings config found, starting fresh")
    except Exception as e:
        logging.error(f"Error loading MIDI mappings: {e}")
    return mappings


def get_midi_note_from_mappings(visual_name, mappings):
    """Get MIDI note for a specific visual from mappings."""
    return mappings.get(visual_name)


def save_visual_midi_mapping(visual_name, note_num):
    """Save individual visual MIDI mapping to config file."""
    try:
        config_path = Path("config/midi_mappings.json")
        mappings = {}
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                mappings = json.load(f)
        if not isinstance(mappings, dict):
            mappings = {}

        if note_num is not None:
            mappings = {v: n for v, n in mappings.items() if v != visual_name and n != note_num}
            mappings[visual_name] = note_num
            logging.info(f"Saved MIDI mapping: {visual_name} -> Note {note_num}")
        else:
            mappings.pop(visual_name, None)
            logging.info(f"Removed MIDI mapping for: {visual_name}")

        config_path.parent.mkdir(exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(mappings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error saving visual MIDI mapping: {e}")


def save_all_midi_mappings(self):
    """Save all current MIDI mappings (called by Save button)."""
    try:
        mappings = {}
        if hasattr(self, "visual_settings_grid"):
            for i in range(self.visual_settings_grid.count()):
                item = self.visual_settings_grid.itemAt(i)
                if item and item.widget():
                    cell = item.widget()
                    visual_name = None
                    note_value = None
                    for child in cell.findChildren(QLabel):
                        text = child.text()
                        if text:
                            visual_name = text
                            break
                    for child in cell.findChildren(QLineEdit):
                        note_text = child.text().strip()
                        if note_text:
                            try:
                                note_value = int(note_text)
                            except ValueError:
                                note_value = None
                            break
                    if visual_name and note_value is not None:
                        mappings[visual_name] = note_value
        config_path = Path("config/midi_mappings.json")
        config_path.parent.mkdir(exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(mappings, f, indent=2, ensure_ascii=False)
        QMessageBox.information(
            self if hasattr(self, "parent") else None,
            "Save Successful",
            f"Saved {len(mappings)} MIDI mappings successfully.",
        )
        logging.info(f"Bulk save completed: {len(mappings)} mappings saved")
    except Exception as e:
        logging.error(f"Error in bulk save: {e}")
        QMessageBox.critical(
            self if hasattr(self, "parent") else None,
            "Save Error",
            f"Error saving mappings: {str(e)}",
        )


def create_fallback_visual_grid(container):
    """Create simple fallback grid if main creation fails."""
    layout = QVBoxLayout(container)
    error_frame = QFrame()
    error_frame.setStyleSheet(
        """
        QFrame {
            background-color: #ffebee;
            border: 2px solid #f44336;
            border-radius: 8px;
            padding: 20px;
        }
        """
    )
    error_layout = QVBoxLayout(error_frame)
    error_label = QLabel("⚠️ Error creating visual settings grid")
    error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    error_label.setStyleSheet("color: #d32f2f; font-size: 16px; font-weight: bold;")
    error_layout.addWidget(error_label)
    help_label = QLabel(
        "Please check:\n"
        "• That the 'config' directory exists\n"
        "• That you have write permissions\n"
        "• That the visualizer_manager is running"
    )
    help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    help_label.setStyleSheet("color: #666666; font-size: 12px;")
    error_layout.addWidget(help_label)
    layout.addWidget(error_frame)

