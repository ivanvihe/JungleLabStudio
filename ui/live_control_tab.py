# ui/live_control_tab.py - COMPLETE VERSION WITH ALL FUNCTIONS
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

    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QSizePolicy, QLineEdit
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QBrush, QPen
import logging
import json
from pathlib import Path


def create_live_control_tab(self):
    """Create live control tab with improved 1:1 grid layout"""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(10)
    
    # Header
    header_label = QLabel("🎛️ CONTROL EN VIVO - GRID DE VISUALES")
    header_label.setStyleSheet("""
        QLabel {
            font-size: 16px;
            font-weight: bold;
            color: #00ff00;
            padding: 10px;
            background-color: #1a1a1a;
            border: 2px solid #00ff00;
            border-radius: 8px;
        }
    """)
    header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(header_label)
    
    # Instructions
    instructions = QLabel(
        "💡 Vista de solo lectura del grid de control. Cada deck tiene su canal MIDI. "
        "Para editar notas MIDI, usa el tab 'Visual Settings'."
    )
    instructions.setStyleSheet("""
        QLabel {
            background-color: #e8f5e8;
            color: #2e7d32;
            padding: 8px;
            border-radius: 5px;
            border-left: 4px solid #4caf50;
            font-size: 11px;
        }
    """)
    instructions.setWordWrap(True)
    layout.addWidget(instructions)
    
    # Scroll area for the grid
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setStyleSheet("""
        QScrollArea {
            border: 1px solid #666666;
            border-radius: 5px;
            background-color: #1a1a1a;
        }
    """)
    layout.addWidget(scroll)
    
    # Container for the grid
    container = QWidget()
    scroll.setWidget(container)
    
    # Create the improved grid
    create_improved_deck_grid(self, container)
    
    return widget


def create_improved_deck_grid(self, container):
    """Create improved grid with 1:1 squares and thumbnails"""
    try:
        # Get available visuals
        visuals = []
        if hasattr(self, 'visualizer_manager') and self.visualizer_manager:
            try:
                visuals = sorted(self.visualizer_manager.get_visualizer_names())
                logging.info(f"🎨 Found {len(visuals)} visuals for live control grid")
            except Exception as e:
                logging.error(f"Error getting visualizer names: {e}")
                visuals = ["Simple Test", "Abstract Lines", "Wire Terrain", "Geometric Particles"]  # Fallback
        else:
            visuals = ["Simple Test", "Abstract Lines", "Wire Terrain", "Geometric Particles"]  # Fallback
            logging.warning("No visualizer manager available, using fallback visuals")
        
        # Get MIDI mappings info
        midi_info = get_midi_mapping_info(self)
        
        # Deck configuration (A, B, C, D with their MIDI channels)
        deck_config = {
            'A': {'channel': 0, 'color': '#ff6b6b', 'name': 'DECK A'},
            'B': {'channel': 1, 'color': '#4ecdc4', 'name': 'DECK B'}, 
            'C': {'channel': 2, 'color': '#45b7d1', 'name': 'DECK C'},
            'D': {'channel': 3, 'color': '#96ceb4', 'name': 'DECK D'}
        }
        
        # Calculate grid dimensions
        num_visuals = len(visuals)
        columns_per_deck = min(num_visuals + 1, 15)  # +1 for deck header, max 15 cols to fit screen
        total_columns = columns_per_deck
        total_rows = len(deck_config)
        
        # Create grid layout
        grid = QGridLayout(container)
        grid.setSpacing(8)
        grid.setContentsMargins(15, 15, 15, 15)
        
        # Set uniform column widths
        for col in range(total_columns):
            grid.setColumnStretch(col, 1)
        
        # Create grid cells
        for row, (deck_id, deck_info) in enumerate(deck_config.items()):
            # Column 0: Deck header
            deck_cell = create_deck_header_cell(deck_id, deck_info)
            grid.addWidget(deck_cell, row, 0)
            
            # Columns 1+: Visual cells (limit to available columns)
            visuals_to_show = visuals[:columns_per_deck-1]  # -1 for deck header column
            for col, visual_name in enumerate(visuals_to_show, 1):
                visual_cell = create_visual_cell(
                    visual_name, 
                    deck_id, 
                    deck_info, 
                    midi_info,
                    is_editable=False  # Live control tab is read-only
                )
                grid.addWidget(visual_cell, row, col)
        
        # Add clear button column at the end
        if len(visuals) < 14:  # Only if we have space
            for row, (deck_id, deck_info) in enumerate(deck_config.items()):
                clear_cell = create_clear_cell(deck_id, deck_info, midi_info)
                grid.addWidget(clear_cell, row, len(visuals_to_show) + 1)
        
        logging.info(f"✅ Created improved live control grid: {total_rows} rows x {total_columns} columns")
        
    except Exception as e:
        logging.error(f"❌ Error creating improved deck grid: {e}")
        # Fallback simple grid
        create_fallback_grid(container)


def create_deck_header_cell(deck_id, deck_info):
    """Create deck header cell (first column)"""
    cell = QFrame()
    cell.setFixedSize(120, 120)  # 1:1 square
    cell.setFrameStyle(QFrame.Shape.StyledPanel)
    cell.setStyleSheet(f"""
        QFrame {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {deck_info['color']}, stop:1 {darken_color(deck_info['color'])});
            border: 3px solid #ffffff;
            border-radius: 12px;
            color: #ffffff;
        }}
        QLabel {{
            color: #ffffff;
            font-weight: bold;
            background-color: transparent;
            border: none;
        }}
    """)
    
    layout = QVBoxLayout(cell)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(5)
    
    # Deck icon (simple geometric shape)
    icon_label = QLabel("🎛️")
    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon_label.setFont(QFont("Arial", 16))
    layout.addWidget(icon_label)
    
    # Deck name
    deck_label = QLabel(deck_info['name'])
    deck_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    deck_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
    layout.addWidget(deck_label)
    
    # MIDI channel
    channel_label = QLabel(f"Canal {deck_info['channel'] + 1}")
    channel_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    channel_label.setFont(QFont("Arial", 9))
    channel_label.setStyleSheet("color: #f0f0f0;")
    layout.addWidget(channel_label)
    
    return cell


def create_visual_cell(visual_name, deck_id, deck_info, midi_info, is_editable=False):
    """Create visual cell with thumbnail, name and MIDI note"""
    cell = QFrame()
    cell.setFixedSize(120, 120)  # 1:1 square
    cell.setFrameStyle(QFrame.Shape.StyledPanel)
    cell.setStyleSheet("""
        QFrame {
            background-color: #2a2a2a;
            border: 2px solid #555555;
            border-radius: 8px;
        }
        QFrame:hover {
            border-color: #00ff00;
            background-color: #3a3a3a;
            transform: scale(1.02);
        }
        QLabel {
            color: #ffffff;
            background-color: transparent;
            border: none;
        }
    """)
    
    layout = QVBoxLayout(cell)
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setSpacing(2)
    
    # Thumbnail (top 50% of cell)
    thumbnail = create_visual_thumbnail(visual_name)
    thumbnail.setFixedSize(70, 45)
    thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(thumbnail)
    
    # Visual name (truncated if too long)
    name_label = QLabel(truncate_text(visual_name, 14))
    name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    name_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
    name_label.setWordWrap(True)
    name_label.setMaximumHeight(25)
    layout.addWidget(name_label)
    
    # MIDI note info
    midi_note = get_midi_note_for_visual(visual_name, deck_id, midi_info)
    if is_editable:
        # Editable MIDI note (for visual settings tab)
        note_widget = create_editable_midi_note(visual_name, midi_note)
    else:
        # Read-only MIDI note (for live control tab)
        note_widget = create_readonly_midi_note(midi_note)
    
    layout.addWidget(note_widget)
    
    # Action buttons for live control (optional - can be commented out)
    action_layout = QHBoxLayout()
    action_layout.setContentsMargins(0, 0, 0, 0)
    action_layout.setSpacing(2)
    
    # Small load button
    load_btn = QPushButton("▶")
    load_btn.setFixedSize(16, 16)
    load_btn.setFont(QFont("Arial", 8))
    load_btn.setToolTip(f"Load {visual_name} on {deck_id}")
    load_btn.setStyleSheet("""
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3d8b40;
        }
    """)
    # Connect to actual load function if available
    if hasattr(self, 'mixer_window') and self.mixer_window:
        load_btn.clicked.connect(lambda: self.mixer_window.safe_set_deck_visualizer(deck_id, visual_name))
    
    action_layout.addWidget(load_btn)
    action_layout.addStretch()
    
    layout.addLayout(action_layout)
    
    return cell


def create_clear_cell(deck_id, deck_info, midi_info):
    """Create clear/stop cell for deck"""
    cell = QFrame()
    cell.setFixedSize(120, 120)  # 1:1 square
    cell.setFrameStyle(QFrame.Shape.StyledPanel)
    cell.setStyleSheet(f"""
        QFrame {{
            background-color: #3a1a1a;
            border: 2px solid #aa5555;
            border-radius: 8px;
        }}
        QFrame:hover {{
            border-color: #ff6666;
            background-color: #4a2a2a;
        }}
        QLabel {{
            color: #ffaaaa;
            background-color: transparent;
            border: none;
        }}
    """)
    
    layout = QVBoxLayout(cell)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setSpacing(5)
    
    # Clear icon
    icon_label = QLabel("⏹️")
    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon_label.setFont(QFont("Arial", 20))
    layout.addWidget(icon_label)
    
    # Clear label
    clear_label = QLabel("CLEAR")
    clear_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    clear_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
    layout.addWidget(clear_label)
    
    # MIDI note for clear action
    clear_note = get_midi_note_for_clear(deck_id, midi_info)
    note_widget = create_readonly_midi_note(clear_note, is_clear=True)
    layout.addWidget(note_widget)
    
    return cell


def create_visual_thumbnail(visual_name):
    """Create thumbnail for visual"""
    thumbnail = QLabel()
    thumbnail.setStyleSheet("""
        QLabel {
            background-color: #1a1a1a;
            border: 1px solid #666666;
            border-radius: 4px;
        }
    """)
    
    # Create a simple colored thumbnail based on visual name
    pixmap = QPixmap(70, 45)
    pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Generate color based on visual name hash
    color_hash = hash(visual_name) % 360
    primary_color = QColor.fromHsv(color_hash, 180, 200)
    secondary_color = QColor.fromHsv((color_hash + 120) % 360, 120, 160)
    
    # Draw patterns based on visual type
    painter.setBrush(QBrush(primary_color))
    painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
    
    visual_lower = visual_name.lower()
    
    if "particle" in visual_lower:
        # Draw particles
        for i in range(8):
            x = (i % 4) * 15 + 10
            y = (i // 4) * 15 + 8
            size = 4 + (i % 3) * 2
            painter.drawEllipse(x, y, size, size)
            
    elif "line" in visual_lower or "abstract" in visual_lower:
        # Draw lines
        painter.setPen(QPen(primary_color, 2))
        for i in range(4):
            y = i * 8 + 8
            painter.drawLine(5, y, 65, y)
            if i % 2 == 0:
                painter.setPen(QPen(secondary_color, 1))
            else:
                painter.setPen(QPen(primary_color, 2))
                
    elif "wire" in visual_lower or "terrain" in visual_lower:
        # Draw wire/terrain pattern
        painter.setPen(QPen(primary_color, 2))
        painter.drawLine(5, 20, 25, 8)
        painter.drawLine(25, 8, 45, 20)
        painter.drawLine(45, 20, 65, 8)
        painter.drawLine(5, 30, 25, 37)
        painter.drawLine(25, 37, 45, 30)
        painter.drawLine(45, 30, 65, 37)
        
    elif "geometric" in visual_lower or "shape" in visual_lower:
        # Draw geometric shapes
        painter.setBrush(QBrush(primary_color))
        painter.drawRect(10, 8, 20, 15)
        painter.setBrush(QBrush(secondary_color))
        painter.drawEllipse(35, 10, 15, 15)
        painter.setBrush(QBrush(primary_color))
        painter.drawPolygon([(15, 28), (25, 35), (20, 42), (10, 35)])
        
    elif "fluid" in visual_lower or "flow" in visual_lower:
        # Draw fluid/flow pattern
        painter.setPen(QPen(primary_color, 3))
        for i in range(3):
            painter.drawArc(5 + i*20, 5 + i*5, 20, 15, 0, 180*16)
            
    elif "test" in visual_lower or "simple" in visual_lower:
        # Simple test pattern
        painter.setBrush(QBrush(primary_color))
        painter.drawRect(20, 15, 30, 15)
        painter.setPen(QPen(secondary_color, 2))
        painter.drawLine(20, 22, 50, 22)
        
    else:
        # Default pattern - gradient rectangle
        painter.setBrush(QBrush(primary_color))
        painter.drawRect(15, 10, 40, 25)
        painter.setBrush(QBrush(secondary_color))
        painter.drawEllipse(25, 15, 20, 15)
    
    painter.end()
    thumbnail.setPixmap(pixmap)
    return thumbnail


def create_readonly_midi_note(midi_note, is_clear=False):
    """Create read-only MIDI note display"""
    if midi_note is not None:
        note_text = f"Note {midi_note}"
    else:
        note_text = "No MIDI"
    
    note_label = QLabel(note_text)
    note_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    note_label.setFont(QFont("Arial", 7))
    
    if is_clear:
        note_label.setStyleSheet("""
            QLabel {
                color: #ffaaaa;
                background-color: #2a1a1a;
                border: 1px solid #aa4444;
                border-radius: 3px;
                padding: 2px;
            }
        """)
    else:
        note_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                background-color: #1a1a1a;
                border: 1px solid #444444;
                border-radius: 3px;
                padding: 2px;
            }
        """)
    return note_label


def create_editable_midi_note(visual_name, current_note):
    """Create editable MIDI note field (for visual settings tab)"""
    note_edit = QLineEdit(str(current_note) if current_note else "")
    note_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
    note_edit.setFont(QFont("Arial", 7))
    note_edit.setStyleSheet("""
        QLineEdit {
            color: #ffffff;
            background-color: #333333;
            border: 1px solid #666666;
            border-radius: 3px;
            padding: 2px;
        }
        QLineEdit:focus {
            border-color: #00ff00;
        }
    """)
    note_edit.setPlaceholderText("Note")
    note_edit.setMaxLength(3)
    
    # Connect to save function
    note_edit.editingFinished.connect(
        lambda: save_midi_note_mapping(visual_name, note_edit.text())
    )
    
    return note_edit


def get_midi_mapping_info(self):
    """Get MIDI mapping information"""
    midi_info = {}
    try:
        if hasattr(self, 'midi_engine') and self.midi_engine:
            mappings = self.midi_engine.get_midi_mappings()
            for action_id, mapping_data in mappings.items():
                if isinstance(mapping_data, dict):
                    params = mapping_data.get('params', {})
                    preset_name = params.get('preset_name')
                    midi_key = mapping_data.get('midi', '')
                    
                    if preset_name and 'note' in midi_key:
                        try:
                            # Extract note number from MIDI key
                            note_num = int(midi_key.split('note')[1])
                            deck_id = params.get('deck_id', 'A')
                            
                            if preset_name not in midi_info:
                                midi_info[preset_name] = {}
                            midi_info[preset_name][deck_id] = note_num
                        except (ValueError, IndexError):
                            continue
                            
            logging.debug(f"Loaded MIDI info for {len(midi_info)} visuals")
    except Exception as e:
        logging.error(f"Error getting MIDI mapping info: {e}")
    
    return midi_info


def get_midi_note_for_visual(visual_name, deck_id, midi_info):
    """Get MIDI note for specific visual and deck"""
    try:
        return midi_info.get(visual_name, {}).get(deck_id)
    except Exception:
        return None


def get_midi_note_for_clear(deck_id, midi_info):
    """Get MIDI note for clear action of specific deck"""
    try:
        # Look for clear action mappings
        clear_actions = ["Clear", "clear", f"deck_{deck_id.lower()}_clear"]
        for clear_action in clear_actions:
            if clear_action in midi_info:
                return midi_info[clear_action].get(deck_id)
        return None
    except Exception:
        return None


def save_midi_note_mapping(visual_name, note_str):
    """Save MIDI note mapping to config file"""
    try:
        if not note_str.strip():
            return
            
        note_num = int(note_str.strip())
        if not (0 <= note_num <= 127):
            logging.warning(f"MIDI note {note_num} out of range (0-127)")
            return
        
        config_path = Path('config/midi_mappings.json')
        
        # Load existing mappings
        mappings = {}
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
        
        # Update mapping for this visual
        # This is a simplified approach - in practice you'd need to handle
        # deck-specific mappings and avoid conflicts
        visual_key = visual_name.replace(' ', '_').lower()
        mappings[visual_key] = f"note_on_ch0_note{note_num}"
        
        # Save back to file
        config_path.parent.mkdir(exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, indent=2, ensure_ascii=False)
        
        logging.info(f"✅ Saved MIDI mapping: {visual_name} -> Note {note_num}")
        
    except ValueError:
        logging.warning(f"Invalid MIDI note value: {note_str}")
    except Exception as e:
        logging.error(f"Error saving MIDI note mapping: {e}")


def truncate_text(text, max_length):
    """Truncate text to fit in cell"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def darken_color(hex_color):
    """Darken a hex color for gradients"""
    try:
        # Remove the # if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Darken by 30%
        r = max(0, int(r * 0.7))
        g = max(0, int(g * 0.7))
        b = max(0, int(b * 0.7))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    except:
        return "#333333"  # Fallback


def create_fallback_grid(container):
    """Create simple fallback grid if main creation fails"""
    layout = QVBoxLayout(container)
    
    error_frame = QFrame()
    error_frame.setStyleSheet("""
        QFrame {
            background-color: #2a1a1a;
            border: 2px solid #ff6b6b;
            border-radius: 8px;
            padding: 20px;
        }
    """)
    
    error_layout = QVBoxLayout(error_frame)
    
    # Error icon and message
    error_label = QLabel("⚠️ Error creando grid de control en vivo")
    error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    error_label.setStyleSheet("color: #ff6b6b; font-size: 16px; font-weight: bold;")
    error_layout.addWidget(error_label)
    
    # Help text
    help_label = QLabel(
        "Posibles causas:\n"
        "• El visualizer_manager no está disponible\n"
        "• Error cargando mappings MIDI\n"
        "• Problema de permisos de archivos\n\n"
        "Intenta:\n"
        "• Reiniciar la aplicación\n"
        "• Verificar el archivo config/midi_mappings.json\n"
        "• Revisar los logs para más detalles"
    )
    help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    help_label.setStyleSheet("color: #cccccc; font-size: 12px;")
    help_label.setWordWrap(True)
    error_layout.addWidget(help_label)
    
    # Simple retry button
    retry_btn = QPushButton("🔄 Reintentar")
    retry_btn.setStyleSheet("""
        QPushButton {
            background-color: #ff6b6b;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #ff5252;
        }
    """)
    retry_btn.clicked.connect(lambda: create_improved_deck_grid(container.parent(), container))
    error_layout.addWidget(retry_btn)
    
    layout.addWidget(error_frame)
    
    # Add some spacing
    layout.addStretch()
