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
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import (
    QIntValidator,
    QFont,
    QPixmap,
    QPainter,
    QColor,
    QBrush,
    QPen,
    QPolygon,
)

from pathlib import Path
import json
import logging


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
        "💡 Edita las notas MIDI para cada visual. Los cambios se guardan "
        "automáticamente al salir del campo o al presionar 'Guardar Cambios'."
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
                visuals = ["Simple Test", "Abstract Lines", "Wire Terrain"]
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

    midi_label = QLabel("Nota MIDI:")
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

    pixmap = QPixmap(80, 60)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    color_hash = hash(visual_name) % 360
    primary_color = QColor.fromHsv(color_hash, 180, 220)
    secondary_color = QColor.fromHsv((color_hash + 120) % 360, 120, 180)

    if "particle" in visual_name.lower():
        painter.setBrush(QBrush(primary_color))
        for i in range(12):
            x = (i % 4) * 18 + 10
            y = (i // 4) * 18 + 6
            size = 4 + (i % 3) * 2
            painter.drawEllipse(x, y, size, size)
    elif "line" in visual_name.lower() or "wire" in visual_name.lower():
        painter.setPen(QPen(primary_color, 2))
        for i in range(6):
            y = i * 10 + 5
            painter.drawLine(5, y, 75, y)
            if i % 2 == 0:
                painter.setPen(QPen(secondary_color, 1))
            else:
                painter.setPen(QPen(primary_color, 2))
    elif "geometric" in visual_name.lower() or "abstract" in visual_name.lower():
        painter.setBrush(QBrush(primary_color))
        painter.drawRect(10, 10, 25, 25)
        painter.setBrush(QBrush(secondary_color))
        painter.drawEllipse(45, 15, 20, 20)
        painter.setBrush(QBrush(primary_color))
        polygon = QPolygon([
            QPoint(20, 40),
            QPoint(35, 45),
            QPoint(30, 55),
            QPoint(15, 50),
        ])
        painter.drawPolygon(polygon)
    elif "fluid" in visual_name.lower() or "flow" in visual_name.lower():
        painter.setPen(QPen(primary_color, 3))
        painter.drawPath(create_wave_path())
        painter.setPen(QPen(secondary_color, 2))
        painter.drawPath(create_wave_path(offset=10))
    else:
        painter.setBrush(QBrush(primary_color))
        painter.drawRect(15, 15, 50, 30)
        painter.setBrush(QBrush(secondary_color))
        painter.drawEllipse(25, 20, 30, 20)

    painter.end()
    thumbnail.setPixmap(pixmap)
    return thumbnail


def create_wave_path(offset=0):
    """Create a wave path for fluid visualizations."""
    from PyQt6.QtGui import QPainterPath
    import math

    path = QPainterPath()
    path.moveTo(0, 30 + offset)
    for x in range(80):
        y = 30 + offset + 10 * math.sin(x * 0.1)
        path.lineTo(x, y)
    return path


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
                        "Valor Inválido",
                        f"La nota MIDI debe estar entre 0 y 127.\nValor ingresado: {note_num}",
                    )
            else:
                save_visual_midi_mapping(visual_name, None)
        except ValueError:
            note_edit.setStyleSheet(note_edit.styleSheet() + "; border-color: #ff0000;")
            QMessageBox.warning(
                None,
                "Valor Inválido",
                "Por favor ingresa un número válido (0-127).",
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
                for action_id, mapping_data in data.items():
                    if isinstance(mapping_data, dict):
                        params = mapping_data.get("params", {})
                        preset_name = params.get("preset_name")
                        midi_key = mapping_data.get("midi", "")
                        if preset_name and "note" in midi_key:
                            try:
                                note_num = int(midi_key.split("note")[1])
                                mappings[preset_name] = note_num
                            except (ValueError, IndexError):
                                continue
                logging.info(
                    f"✅ Loaded {len(mappings)} visual MIDI mappings from config"
                )
        else:
            logging.info("📝 No existing MIDI mappings config found, starting fresh")
    except Exception as e:
        logging.error(f"❌ Error loading MIDI mappings: {e}")
    return mappings


def get_midi_note_from_mappings(visual_name, mappings):
    """Get MIDI note for a specific visual from mappings."""
    return mappings.get(visual_name)


def save_visual_midi_mapping(visual_name, note_num):
    """Save individual visual MIDI mapping to config file."""
    try:
        config_path = Path("config/midi_mappings.json")
        config_data = {}
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

        updated = False
        for action_id, mapping_data in config_data.items():
            if isinstance(mapping_data, dict):
                params = mapping_data.get("params", {})
                if params.get("preset_name") == visual_name:
                    if note_num is not None:
                        old_midi = mapping_data.get("midi", "")
                        if "ch" in old_midi:
                            channel_part = old_midi.split("_note")[0]
                            mapping_data["midi"] = f"{channel_part}_note{note_num}"
                        else:
                            mapping_data["midi"] = f"note_on_ch0_note{note_num}"
                    else:
                        mapping_data["midi"] = ""
                    updated = True

        if not updated and note_num is not None:
            for deck_id in ["A", "B"]:
                action_id = f"visual_{visual_name.replace(' ', '_').lower()}_{deck_id.lower()}"
                config_data[action_id] = {
                    "type": "load_preset",
                    "params": {
                        "deck_id": deck_id,
                        "preset_name": visual_name,
                        "custom_values": "",
                    },
                    "midi": f"note_on_ch{0 if deck_id == 'A' else 1}_note{note_num}",
                }
            updated = True

        if updated:
            config_path.parent.mkdir(exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            if note_num is not None:
                logging.info(
                    f"✅ Saved MIDI mapping: {visual_name} -> Note {note_num}"
                )
            else:
                logging.info(
                    f"🗑️ Removed MIDI mapping for: {visual_name}"
                )
    except Exception as e:
        logging.error(f"❌ Error saving visual MIDI mapping: {e}")


def save_all_midi_mappings(self):
    """Save all current MIDI mappings (called by Save button)."""
    try:
        saved_count = 0
        if hasattr(self, "visual_settings_grid"):
            for i in range(self.visual_settings_grid.count()):
                item = self.visual_settings_grid.itemAt(i)
                if item and item.widget():
                    cell = item.widget()
                    visual_name = None
                    note_value = None
                    for child in cell.findChildren(QLabel):
                        text = child.text()
                        if text and not text.startswith("Nota MIDI"):
                            visual_name = text
                            break
                    for child in cell.findChildren(QLineEdit):
                        note_text = child.text().strip()
                        if note_text:
                            try:
                                note_value = int(note_text)
                                break
                            except ValueError:
                                continue
                    if visual_name and note_value is not None:
                        save_visual_midi_mapping(visual_name, note_value)
                        saved_count += 1
        QMessageBox.information(
            self if hasattr(self, "parent") else None,
            "Guardado Exitoso",
            f"✅ Se guardaron {saved_count} mappings MIDI correctamente.\n"
            "Los cambios estarán disponibles inmediatamente.",
        )
        logging.info(f"✅ Bulk save completed: {saved_count} mappings saved")
    except Exception as e:
        logging.error(f"❌ Error in bulk save: {e}")
        QMessageBox.critical(
            self if hasattr(self, "parent") else None,
            "Error de Guardado",
            f"❌ Error guardando mappings: {str(e)}",
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
    error_label = QLabel("⚠️ Error creando grid de configuración visual")
    error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    error_label.setStyleSheet("color: #d32f2f; font-size: 16px; font-weight: bold;")
    error_layout.addWidget(error_label)
    help_label = QLabel(
        "Por favor verifica:\n"
        "• Que el directorio 'config' existe\n"
        "• Que tienes permisos de escritura\n"
        "• Que el visualizer_manager está funcionando"
    )
    help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    help_label.setStyleSheet("color: #666666; font-size: 12px;")
    error_layout.addWidget(help_label)
    layout.addWidget(error_frame)

