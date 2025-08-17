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
    QToolButton,
    QFileDialog,
    QDialog,
    QDialogButtonBox,
    QCheckBox,
    QFormLayout,
    QSlider,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QIntValidator,
    QFont,
)

from pathlib import Path
import json
import logging

from .thumbnail_utils import generate_visual_thumbnail, set_custom_thumbnail_path
from utils.visual_properties import load_visual_properties, save_visual_properties

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
            visual_cell = create_visual_settings_cell_v2(self, visual_name, current_mappings)
            grid.addWidget(visual_cell, row, col)

        self.visual_settings_grid = grid
        self.visual_mappings = current_mappings
        logging.info(
            f"✅ Created visual settings grid: {len(visuals)} visuals in {rows}x{columns} grid"
        )
    except Exception as e:
        logging.error(f"❌ Error creating visual settings grid: {e}")
        create_fallback_visual_grid(container)




def create_visual_settings_cell_v2(self, visual_name, current_mappings):
    """Create a visual settings cell with editable MIDI note and controls."""
    cell = QFrame()
    cell.setFixedSize(300, 180)
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

    main_layout = QHBoxLayout(cell)
    main_layout.setContentsMargins(8, 8, 8, 8)
    main_layout.setSpacing(6)

    # Left side (thumbnail, name, MIDI)
    left_layout = QVBoxLayout()
    left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    left_layout.setSpacing(4)

    thumb_container = QFrame()
    thumb_container.setFixedSize(80, 60)
    thumb_container.setStyleSheet(
        """
        QFrame {
            background-color: #1a1a1a;
            border: 1px solid #666666;
            border-radius: 6px;
        }
        """
    )

    thumb_label = QLabel(thumb_container)
    thumb_label.setGeometry(0, 0, 80, 60)
    thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    thumb_label.setPixmap(generate_visual_thumbnail(visual_name, 80, 60))

    open_btn = QToolButton(thumb_container)
    open_btn.setText("📂")
    open_btn.setToolTip("Change thumbnail")
    open_btn.setAutoRaise(True)
    open_btn.move(60, 0)

    clear_btn = QToolButton(thumb_container)
    clear_btn.setText("✖")
    clear_btn.setToolTip("Remove thumbnail")
    clear_btn.setAutoRaise(True)
    clear_btn.move(40, 0)

    def choose_thumbnail():
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select Thumbnail",
            "",
            "Images (*.png *.jpg *.jpeg)",
        )
        if file_path:
            set_custom_thumbnail_path(visual_name, file_path)
            thumb_label.setPixmap(generate_visual_thumbnail(visual_name, 80, 60))
            if hasattr(self, "live_grid_cells"):
                for deck_cells in self.live_grid_cells.values():
                    cell = deck_cells.get(visual_name)
                    if cell and hasattr(cell, "thumb_label"):
                        cell.thumb_label.setPixmap(
                            generate_visual_thumbnail(visual_name, 96, 60)
                        )

    def remove_thumbnail():
        set_custom_thumbnail_path(visual_name, None)
        thumb_label.setPixmap(generate_visual_thumbnail(visual_name, 80, 60))
        if hasattr(self, "live_grid_cells"):
            for deck_cells in self.live_grid_cells.values():
                cell = deck_cells.get(visual_name)
                if cell and hasattr(cell, "thumb_label"):
                    cell.thumb_label.setPixmap(
                        generate_visual_thumbnail(visual_name, 96, 60)
                    )

    open_btn.clicked.connect(choose_thumbnail)
    clear_btn.clicked.connect(remove_thumbnail)

    left_layout.addWidget(thumb_container)

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
    left_layout.addWidget(name_label)

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
    left_layout.addWidget(midi_section)

    main_layout.addLayout(left_layout, 1)

    # Right side controls
    controls_frame = QFrame()
    controls_layout = QVBoxLayout(controls_frame)
    controls_layout.setContentsMargins(0, 0, 0, 0)
    controls_layout.setSpacing(4)

    saved_props = load_visual_properties(visual_name) or {}
    vis_class = None
    if hasattr(self, "visualizer_manager") and self.visualizer_manager:
        try:
            vis_class = self.visualizer_manager.get_visualizer_class(visual_name)
        except Exception:
            vis_class = None
    controls = {}
    if vis_class:
        try:
            visualizer = vis_class()
            controls = visualizer.get_controls() or {}
        except Exception:
            controls = {}

    def save_prop(name, value):
        props = load_visual_properties(visual_name) or {}
        props[name] = value
        save_visual_properties(visual_name, props)

    for name, info in controls.items():
        ctype = info.get("type")
        if ctype == "slider":
            row = QHBoxLayout()
            label = QLabel(name)
            label.setStyleSheet("color: #cccccc;")
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(int(info.get("min", 0)))
            slider.setMaximum(int(info.get("max", 100)))
            current = int(saved_props.get(name, info.get("value", 0)))
            slider.setValue(current)
            value_label = QLabel(str(current))
            value_label.setFixedWidth(24)
            slider.valueChanged.connect(
                lambda v, n=name, lbl=value_label: (lbl.setText(str(v)), save_prop(n, int(v)))
            )
            row.addWidget(label)
            row.addWidget(slider)
            row.addWidget(value_label)
            controls_layout.addLayout(row)
        elif ctype == "checkbox":
            check = QCheckBox(name)
            check.setChecked(bool(saved_props.get(name, info.get("value", False))))
            check.stateChanged.connect(lambda state, n=name: save_prop(n, bool(state)))
            controls_layout.addWidget(check)

    main_layout.addWidget(controls_frame, 1)

    cell.thumb_label = thumb_label
    return cell


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


def open_visual_properties_dialog(self, visual_name):
    """Open dialog to edit visual property values."""
    try:
        vis_class = None
        if hasattr(self, "visualizer_manager") and self.visualizer_manager:
            vis_class = self.visualizer_manager.get_visualizer_class(visual_name)
        if not vis_class:
            QMessageBox.warning(None, "Error", f"Visualizer not found: {visual_name}")
            return

        visualizer = vis_class()
        controls = visualizer.get_controls() or {}
        saved = load_visual_properties(visual_name) or {}

        dialog = QDialog()
        dialog.setWindowTitle(f"{visual_name} Properties")
        form = QFormLayout(dialog)

        widgets = {}
        for name, info in controls.items():
            ctype = info.get("type")
            if ctype == "slider":
                slider = QSlider(Qt.Orientation.Horizontal)
                slider.setMinimum(int(info.get("min", 0)))
                slider.setMaximum(int(info.get("max", 100)))
                slider.setValue(int(saved.get(name, info.get("value", 0))))
                form.addRow(QLabel(name), slider)
                widgets[name] = slider
            elif ctype == "checkbox":
                check = QCheckBox()
                check.setChecked(bool(saved.get(name, info.get("value", False))))
                form.addRow(check, QLabel(name))
                widgets[name] = check

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec():
            new_props = {}
            for name, widget in widgets.items():
                if isinstance(widget, QSlider):
                    new_props[name] = int(widget.value())
                elif isinstance(widget, QCheckBox):
                    new_props[name] = bool(widget.isChecked())
            save_visual_properties(visual_name, new_props)
    except Exception as e:
        logging.error(f"Error opening properties dialog for {visual_name}: {e}")


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

