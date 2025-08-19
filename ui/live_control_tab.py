# ui/live_control_tab.py - MODERNIZED VERSION WITH RESOLUME-STYLE GRID
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QGridLayout, QFrame, QPushButton,
    QSpinBox, QSlider, QHBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PySide6.QtGui import QFont, QPalette, QColor, QLinearGradient, QBrush

import json
import logging
from pathlib import Path
import mido

from .thumbnail_utils import generate_visual_thumbnail

# Modern color scheme inspired by Resolume
MODERN_COLORS = {
    'background_dark': '#0a0a0a',
    'background_medium': '#151515', 
    'background_light': '#1f1f1f',
    'accent_orange': '#ff6b35',
    'accent_blue': '#4a9eff',
    'accent_green': '#00d4aa',
    'accent_purple': '#8b5cf6',
    'text_primary': '#ffffff',
    'text_secondary': '#b0b0b0',
    'text_muted': '#666666',
    'border_normal': '#333333',
    'border_hover': '#555555',
    'border_active': '#ff6b35'
}

# Base modern cell style with thin borders and clean look
MODERN_CELL_STYLE = f"""
QFrame#visual-cell {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {MODERN_COLORS['background_light']},
        stop:1 {MODERN_COLORS['background_medium']});
    border: 1px solid {MODERN_COLORS['border_normal']};
    border-radius: 4px;
    margin: 1px;
}}
QFrame#visual-cell:hover {{
    border: 1px solid {MODERN_COLORS['border_hover']};
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #252525,
        stop:1 #1a1a1a);
}}
QLabel {{
    border: none;
    background: transparent;
    color: {MODERN_COLORS['text_primary']};
}}
"""

def create_live_control_tab(self):
    """Create modern live control tab with professional 4-layer grid."""
    widget = QWidget()
    widget.setStyleSheet(f"""
        QWidget {{
            background-color: {MODERN_COLORS['background_dark']};
            color: {MODERN_COLORS['text_primary']};
            font-family: 'Segoe UI', 'Arial', sans-serif;
        }}
    """)
    
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(6)

    # Modern header with fullscreen button
    header = create_modern_header(self)
    layout.addWidget(header)

    # Main grid scroll area
    scroll = create_modern_scroll_area()
    layout.addWidget(scroll)

    # Grid container
    container = QWidget()
    scroll.setWidget(container)
    
    # Create the modern 4-layer grid
    create_modern_4layer_grid(self, container)

    return widget

def create_modern_header(self):
    """Create modern header with professional styling."""
    header = QFrame()
    header.setFixedHeight(50)
    header.setStyleSheet(f"""
        QFrame {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {MODERN_COLORS['background_medium']},
                stop:1 {MODERN_COLORS['background_dark']});
            border-bottom: 1px solid {MODERN_COLORS['border_normal']};
            border-radius: 0px;
        }}
    """)
    
    layout = QHBoxLayout(header)
    layout.setContentsMargins(12, 0, 12, 0)
    
    # Title
    title = QLabel("LIVE CONTROL GRID")
    title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
    title.setStyleSheet(f"color: {MODERN_COLORS['text_primary']};")
    layout.addWidget(title)
    
    layout.addStretch()
    
    # Fullscreen button with modern styling
    fs_button = QPushButton(" FULLSCREEN")
    fs_button.setStyleSheet(f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {MODERN_COLORS['accent_orange']},
                stop:1 #e55a2b);
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
            font-size: 11px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #ff7a45,
                stop:1 {MODERN_COLORS['accent_orange']});
        }}
        QPushButton:pressed {{
            background: #d4501f;
        }}
    """)
    fs_button.clicked.connect(self.activate_fullscreen_mode)
    layout.addWidget(fs_button)
    
    return header

def create_modern_scroll_area():
    """Create modern scroll area with thin scrollbars."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setStyleSheet(f"""
        QScrollArea {{
            border: none;
            background-color: {MODERN_COLORS['background_dark']};
        }}
        QScrollBar:vertical {{
            border: none;
            background: {MODERN_COLORS['background_medium']};
            width: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {MODERN_COLORS['border_hover']};
            border-radius: 4px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {MODERN_COLORS['border_active']};
        }}
        QScrollBar:horizontal {{
            border: none;
            background: {MODERN_COLORS['background_medium']};
            height: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:horizontal {{
            background: {MODERN_COLORS['border_hover']};
            border-radius: 4px;
            min-width: 20px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {MODERN_COLORS['border_active']};
        }}
    """)
    return scroll

def create_modern_4layer_grid(self, container):
    """Create the modern 4-layer grid maintaining all original functionality."""
    try:
        # Get visuals from the visualizer manager
        visuals = []
        if hasattr(self, "visualizer_manager") and self.visualizer_manager:
            try:
                visuals = self.visualizer_manager.get_visualizer_names()
                logging.info(f"Found {len(visuals)} visuals for modern grid")
            except Exception as e:
                logging.error(f"Error getting visualizer names: {e}")
                visuals = ["Abstract Lines", "Wire Terrain", "Geometric Particles"]
        
        if not visuals:
            create_modern_fallback_grid(container)
            return

        # Load MIDI mappings
        midi_info = get_midi_mapping_info(self)
        
        # Sort visuals by MIDI note assignment
        visuals = sorted(visuals, key=lambda v: midi_info.get(v, 9999))

        # Modern 4-layer configuration
        layer_config = {
            "A": {"channel": 13, "color": MODERN_COLORS['accent_orange'], "name": "LAYER A"},
            "B": {"channel": 14, "color": MODERN_COLORS['accent_blue'], "name": "LAYER B"},
            "C": {"channel": 15, "color": MODERN_COLORS['accent_green'], "name": "LAYER C"},
            "D": {"channel": 16, "color": MODERN_COLORS['accent_purple'], "name": "LAYER D"},
        }

        # Store grid info for interactions
        self.live_grid_cells = {}
        self.live_grid_midi_info = midi_info
        self.live_grid_deck_channels = {}
        self.live_grid_deck_colors = {}

        # Main grid layout
        grid = QGridLayout(container)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        grid.setSpacing(2)  # Thin spacing for modern look
        grid.setContentsMargins(8, 8, 8, 8)

        # Create each layer (row)
        for row, (layer_id, cfg) in enumerate(layer_config.items()):
            self.live_grid_cells[layer_id] = {}
            self.live_grid_deck_channels[layer_id] = cfg["channel"]
            self.live_grid_deck_colors[layer_id] = cfg["color"]

            # Create modern layer header (first cell)
            header_cell = create_modern_layer_header(self, layer_id, cfg)
            grid.addWidget(header_cell, row, 0)

            # Create visual cells for this layer
            for col, visual_name in enumerate(visuals, 1):
                visual_cell = create_modern_visual_cell(self, layer_id, visual_name, midi_info, cfg["color"])
                self.live_grid_cells[layer_id][visual_name] = visual_cell
                grid.addWidget(visual_cell, row, col)

            # Modern clear button
            clear_btn = create_modern_clear_button(layer_id, cfg["color"])
            grid.addWidget(clear_btn, row, len(visuals) + 1)

    except Exception as e:
        logging.error(f"Error creating modern 4-layer grid: {e}")
        create_modern_fallback_grid(container)

def create_modern_layer_header(self, layer_id, config):
    """Create modern layer header cell with controls."""
    header = QFrame()
    header.setFixedSize(100, 100)
    header.setStyleSheet(f"""
        QFrame {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {config['color']},
                stop:1 {config['color']}AA);
            border: 1px solid {config['color']};
            border-radius: 4px;
        }}
    """)
    
    layout = QVBoxLayout(header)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setSpacing(2)

    # Layer name
    name_label = QLabel(config['name'])
    name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    name_label.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
    name_label.setStyleSheet("color: white; background: transparent;")
    layout.addWidget(name_label)

    # Channel info
    channel_label = QLabel(f"CH {config['channel']}")
    channel_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    channel_label.setFont(QFont("Segoe UI", 7))
    channel_label.setStyleSheet(f"""
        color: white;
        background: rgba(0,0,0,100);
        border-radius: 2px;
        padding: 1px;
    """)
    layout.addWidget(channel_label)

    # Fade time input (modern style)
    fade_input = QSpinBox()
    fade_input.setRange(0, 10000)
    fade_input.setSuffix(" ms")
    fade_input.setValue(2000)
    fade_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
    fade_input.setStyleSheet(f"""
        QSpinBox {{
            background: rgba(0,0,0,150);
            color: white;
            border: 1px solid rgba(255,255,255,50);
            border-radius: 2px;
            padding: 1px;
            font-size: 7px;
        }}
        QSpinBox:focus {{
            border: 1px solid white;
        }}
    """)
    layout.addWidget(fade_input)

    # Opacity slider (modern thin style)
    opacity_slider = QSlider(Qt.Orientation.Horizontal)
    opacity_slider.setRange(0, 100)
    opacity_slider.setValue(100)
    opacity_slider.setStyleSheet(f"""
        QSlider::groove:horizontal {{
            background: rgba(0,0,0,150);
            height: 4px;
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            background: white;
            border: 1px solid rgba(255,255,255,150);
            width: 8px;
            height: 8px;
            margin: -2px 0;
            border-radius: 4px;
        }}
        QSlider::sub-page:horizontal {{
            background: {config['color']};
            border-radius: 2px;
        }}
    """)
    layout.addWidget(opacity_slider)

    # Opacity percentage label
    opacity_label = QLabel("100%")
    opacity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    opacity_label.setFont(QFont("Segoe UI", 6))
    opacity_label.setStyleSheet("color: white; background: transparent;")
    layout.addWidget(opacity_label)

    # Store references for functionality
    if not hasattr(self, "deck_fade_inputs"):
        self.deck_fade_inputs = {}
    self.deck_fade_inputs[layer_id] = fade_input

    if not hasattr(self, "deck_opacity_sliders"):
        self.deck_opacity_sliders = {}
    self.deck_opacity_sliders[layer_id] = opacity_slider

    # Connect fade time functionality
    if hasattr(self, "mixer_window") and self.mixer_window:
        try:
            self.mixer_window.set_deck_fade_time(layer_id, fade_input.value())
            
            def on_fade_change(value, d=layer_id):
                try:
                    self.mixer_window.set_deck_fade_time(d, value)
                except Exception as e:
                    logging.error(f"Error setting fade time for layer {d}: {e}")
            
            fade_input.valueChanged.connect(on_fade_change)
        except Exception as e:
            logging.error(f"Error initializing fade input for layer {layer_id}: {e}")

    # Connect opacity functionality
    if hasattr(self, "mixer_window") and self.mixer_window:
        try:
            self.mixer_window.set_deck_opacity(layer_id, 1.0)
            
            def on_opacity_change(value, d=layer_id, lbl=opacity_label):
                try:
                    lbl.setText(f"{value}%")
                    self.mixer_window.set_deck_opacity(d, value / 100.0)
                except Exception as e:
                    logging.error(f"Error setting opacity for layer {d}: {e}")
            
            opacity_slider.valueChanged.connect(on_opacity_change)
        except Exception as e:
            logging.error(f"Error initializing opacity slider for layer {layer_id}: {e}")

    return header

def create_modern_visual_cell(parent, layer_id, visual_name, midi_info, layer_color):
    """Create modern visual cell with professional styling."""
    cell = QFrame()
    cell.setObjectName("visual-cell")
    cell.setFixedSize(100, 100)
    cell.setStyleSheet(MODERN_CELL_STYLE)

    layout = QVBoxLayout(cell)
    layout.setContentsMargins(2, 2, 2, 2)
    layout.setSpacing(1)

    # Modern thumbnail with subtle shadow effect
    thumb_container = QFrame()
    thumb_container.setFixedSize(96, 60)
    thumb_container.setStyleSheet(f"""
        QFrame {{
            background: {MODERN_COLORS['background_dark']};
            border: 1px solid {MODERN_COLORS['border_normal']};
            border-radius: 3px;
        }}
    """)
    
    thumb_label = QLabel(thumb_container)
    thumb_label.setGeometry(1, 1, 94, 58)
    thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    thumb_label.setPixmap(generate_visual_thumbnail(visual_name, 94, 58))
    
    layout.addWidget(thumb_container)
    cell.thumb_label = thumb_label

    # Modern visual name label
    name_label = QLabel(visual_name)
    name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    name_label.setFont(QFont("Segoe UI", 8, QFont.Weight.Medium))
    name_label.setStyleSheet(f"""
        color: {MODERN_COLORS['text_primary']};
        background: transparent;
        padding: 1px;
    """)
    name_label.setWordWrap(True)
    layout.addWidget(name_label)

    # Modern MIDI note indicator
    note = midi_info.get(visual_name)
    note_label = QLabel(f"NOTE {note}" if note is not None else "NO MIDI")
    note_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    note_label.setFont(QFont("Segoe UI", 6))
    note_label.setStyleSheet(f"""
        color: {MODERN_COLORS['text_muted']};
        background: rgba(0,0,0,100);
        border-radius: 2px;
        padding: 1px 3px;
    """)
    layout.addWidget(note_label)

    # Store base style for highlight functionality
    cell.base_style = MODERN_CELL_STYLE

    # Connect click functionality with modern animation
    def mouse_press(event, layer=layer_id, visual=visual_name):
        # Modern click animation
        animate_cell_click(cell, layer_color)
        trigger_visual_from_grid(parent, layer, visual)

    cell.mousePressEvent = mouse_press
    return cell

def create_modern_clear_button(layer_id, layer_color):
    """Create modern clear button for layer."""
    clear_btn = QPushButton(" CLEAR")
    clear_btn.setFixedSize(100, 100)
    clear_btn.setStyleSheet(f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {MODERN_COLORS['background_medium']},
                stop:1 {MODERN_COLORS['background_dark']});
            color: {MODERN_COLORS['text_secondary']};
            border: 1px solid {MODERN_COLORS['border_normal']};
            border-radius: 4px;
            font-weight: bold;
            font-size: 9px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #ff4444,
                stop:1 #cc3333);
            color: white;
            border: 1px solid #ff4444;
        }}
        QPushButton:pressed {{
            background: #aa2222;
        }}
    """)
    return clear_btn

def animate_cell_click(cell, color):
    """Add modern click animation to cell."""
    try:
        # Create visual feedback with color flash
        original_style = cell.styleSheet()
        
        # Flash with layer color
        flash_style = f"""
        QFrame#visual-cell {{
            background: {color};
            border: 2px solid white;
            border-radius: 4px;
        }}
        QLabel {{ border: none; background: transparent; color: white; }}
        """
        
        cell.setStyleSheet(flash_style)
        
        # Return to normal after short delay
        QTimer.singleShot(150, lambda: cell.setStyleSheet(original_style))
        
    except Exception as e:
        logging.error(f"Error in click animation: {e}")

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

def trigger_visual_from_grid(self, layer_id, visual_name):
    """Trigger visual with modern feedback."""
    try:
        note = getattr(self, "live_grid_midi_info", {}).get(visual_name)
        channel = getattr(self, "live_grid_deck_channels", {}).get(layer_id, 1) - 1
        
        if note is None or not hasattr(self, "midi_engine"):
            return
            
        # Send MIDI message
        msg = mido.Message("note_on", channel=channel, note=note, velocity=127)
        self.midi_engine.handle_midi_message(msg)
        
        # Modern visual feedback
        if hasattr(self, 'live_grid_cells') and layer_id in self.live_grid_cells:
            cell = self.live_grid_cells[layer_id].get(visual_name)
            if cell:
                color = getattr(self, 'live_grid_deck_colors', {}).get(layer_id, MODERN_COLORS['accent_orange'])
                animate_cell_click(cell, color)
        
        logging.info(f"Modern grid: Triggered {visual_name} on layer {layer_id}")
        
    except Exception as e:
        logging.error(f"Error triggering visual {visual_name} on layer {layer_id}: {e}")

def create_modern_fallback_grid(container):
    """Create modern fallback UI if visuals not found."""
    layout = QVBoxLayout(container)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    error_frame = QFrame()
    error_frame.setStyleSheet(f"""
        QFrame {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {MODERN_COLORS['background_medium']},
                stop:1 {MODERN_COLORS['background_dark']});
            border: 2px solid {MODERN_COLORS['accent_orange']};
            border-radius: 8px;
            padding: 20px;
        }}
    """)
    
    error_layout = QVBoxLayout(error_frame)
    
    error_label = QLabel(" NO VISUALS DETECTED")
    error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    error_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
    error_label.setStyleSheet(f"color: {MODERN_COLORS['accent_orange']};")
    error_layout.addWidget(error_label)
    
    help_label = QLabel("Please check that the visualizer manager is running correctly.")
    help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    help_label.setFont(QFont("Segoe UI", 10))
    help_label.setStyleSheet(f"color: {MODERN_COLORS['text_secondary']};")
    error_layout.addWidget(help_label)
    
    retry_btn = QPushButton(" RETRY")
    retry_btn.setStyleSheet(f"""
        QPushButton {{
            background: {MODERN_COLORS['accent_orange']};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background: #ff7a45;
        }}
    """)
    error_layout.addWidget(retry_btn, alignment=Qt.AlignmentFlag.AlignCenter)
    
    layout.addWidget(error_frame)