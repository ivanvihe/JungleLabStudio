"""AudioVisualizer - Grid Interface with 4 MIDI-controlled layers."""

import sys
import os
import logging
import json
from pathlib import Path
from typing import Optional, Dict

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QComboBox, QSlider, QGroupBox, QTabWidget, 
    QFrame, QSplitter, QScrollArea, QSpinBox, QCheckBox, QProgressBar, 
    QTextEdit, QSizePolicy, QStyleFactory, QGridLayout, QLineEdit
)
from PySide6.QtCore import Qt, QTimer, QSize, Signal, QThread, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (
    QFont, QColor, QPalette, QLinearGradient, QBrush, QPainter,
    QPixmap, QSurfaceFormat, QPen, QFontMetrics
)

# Project imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from visuals.visualizer_manager import VisualizerManager
from utils.settings_manager import SettingsManager
from audio.audio_analyzer import AudioAnalyzer
from midi.midi_engine import MidiEngine


class GridLayerWidget(QFrame):
    """Grid Layer Widget - Each represents one of the 4 layers."""
    
    layer_triggered = Signal(int, str)  # layer_number, visualizer_name
    layer_opacity_changed = Signal(int, float)
    
    def __init__(self, layer_number: int, midi_channel: int, visualizer_manager: VisualizerManager, parent=None):
        super().__init__(parent)
        self.layer_number = layer_number
        self.midi_channel = midi_channel
        self.visualizer_manager = visualizer_manager
        self.current_visualizer = None
        self.current_visual_name = "NO VISUAL"
        self.is_active = False
        self.opacity = 100
        
        # MIDI mappings cache
        self.midi_mappings = self.load_midi_mappings()
        
        self.setup_ui()
        self.apply_grid_styling()
        
        # Update timer for visual feedback
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_visual_feedback)
        self.update_timer.start(50)  # 20 FPS for smooth animation
        
    def load_midi_mappings(self) -> Dict:
        """Load MIDI mappings from config file."""
        try:
            config_path = project_root / "config" / "midi_mappings.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    return data.get('mappings', {})
        except Exception as e:
            logging.error(f"Failed to load MIDI mappings: {e}")
        return {}
        
    def setup_ui(self):
        """Set up the layer UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(8)
        
        # Header with layer info
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Visual display area
        visual_area = self.create_visual_area()
        main_layout.addWidget(visual_area, 1)
        
        # Controls
        controls = self.create_controls()
        main_layout.addWidget(controls)
        
    def create_header(self) -> QWidget:
        """Create layer header."""
        header = QFrame()
        header.setFixedHeight(40)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Layer label
        layer_name = chr(ord('A') + self.layer_number - 1)  # A, B, C, D
        self.layer_label = QLabel(f"LAYER {layer_name}")
        self.layer_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(self.layer_label)
        
        layout.addStretch()
        
        # MIDI channel indicator
        midi_label = QLabel(f"CH {self.midi_channel}")
        midi_label.setFont(QFont("Arial", 9))
        midi_label.setStyleSheet("color: #888; background: rgba(0,0,0,50); padding: 2px 6px; border-radius: 3px;")
        layout.addWidget(midi_label)
        
        # Active indicator
        self.active_indicator = QLabel("*")
        self.active_indicator.setFont(QFont("Arial", 16))
        self.active_indicator.setStyleSheet("color: #444;")
        layout.addWidget(self.active_indicator)
        
        return header
        
    def create_visual_area(self) -> QWidget:
        """Create visual display area."""
        visual_frame = QFrame()
        visual_frame.setMinimumHeight(120)
        
        layout = QVBoxLayout(visual_frame)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Visual name display
        self.visual_name_label = QLabel("NO VISUAL")
        self.visual_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.visual_name_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.visual_name_label.setWordWrap(True)
        layout.addWidget(self.visual_name_label)
        
        # Intensity/Activity bar
        self.activity_bar = QProgressBar()
        self.activity_bar.setFixedHeight(12)
        self.activity_bar.setRange(0, 100)
        self.activity_bar.setValue(0)
        self.activity_bar.setTextVisible(False)
        layout.addWidget(self.activity_bar)
        
        # Last triggered info
        self.last_note_label = QLabel("Waiting for MIDI...")
        self.last_note_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.last_note_label.setFont(QFont("Arial", 9))
        self.last_note_label.setStyleSheet("color: #666;")
        layout.addWidget(self.last_note_label)
        
        return visual_frame
        
    def create_controls(self) -> QWidget:
        """Create layer controls."""
        controls = QFrame()
        controls.setFixedHeight(80)
        
        layout = QGridLayout(controls)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Opacity control
        layout.addWidget(QLabel("Opacity:"), 0, 0)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        layout.addWidget(self.opacity_slider, 0, 1)
        
        self.opacity_label = QLabel("100%")
        self.opacity_label.setFixedWidth(40)
        layout.addWidget(self.opacity_label, 0, 2)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("CLEAR")
        self.clear_btn.setFixedHeight(25)
        self.clear_btn.clicked.connect(self.clear_layer)
        btn_layout.addWidget(self.clear_btn)
        
        self.solo_btn = QPushButton("SOLO")
        self.solo_btn.setFixedHeight(25)
        self.solo_btn.setCheckable(True)
        btn_layout.addWidget(self.solo_btn)
        
        layout.addLayout(btn_layout, 1, 0, 1, 3)
        
        return controls
        
    def apply_grid_styling(self):
        """Apply Grid interface styling."""
        layer_colors = {
            1: "255, 100, 100",    # Red
            2: "100, 255, 100",    # Green
            3: "100, 150, 255",    # Blue
            4: "255, 255, 100"     # Yellow
        }
        
        color = layer_colors.get(self.layer_number, "150, 150, 150")
        
        self.setStyleSheet(f"""
            GridLayerWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba({color}, 30),
                    stop:1 rgba({color}, 10));
                border: 2px solid rgba({color}, 100);
                border-radius: 8px;
                margin: 2px;
            }}
            QLabel {{
                color: #ffffff;
                background: transparent;
            }}
            QProgressBar {{
                border: 1px solid #444;
                border-radius: 4px;
                background: rgba(30, 30, 30, 200);
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({color}, 200),
                    stop:1 rgba({color}, 255));
                border-radius: 3px;
            }}
            QPushButton {{
                background: rgba(50, 50, 60, 200);
                border: 1px solid #666;
                padding: 4px 8px;
                border-radius: 4px;
                color: white;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(70, 70, 80, 220);
            }}
            QPushButton:pressed {{
                background: rgba(30, 30, 40, 200);
            }}
            QPushButton:checked {{
                background: rgba({color}, 150);
                border: 1px solid rgba({color}, 255);
            }}
            QSlider::groove:horizontal {{
                border: 1px solid #444;
                height: 6px;
                background: rgba(30, 30, 30, 200);
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: rgba({color}, 200);
                border: 1px solid rgba({color}, 255);
                width: 16px;
                margin: -2px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: rgba({color}, 120);
                border-radius: 3px;
            }}
        """)
        
    def trigger_visual_by_midi_note(self, note: int):
        """Trigger a visual based on MIDI note."""
        # Find the visual mapped to this note
        visual_name = None
        for mapping in self.midi_mappings:
            if mapping.get('note') == note:
                visual_name = mapping.get('visual_name')
                break
                
        if visual_name:
            self.trigger_visual(visual_name, note)
        else:
            logging.warning(f"No visual mapped to MIDI note {note}")
            
    def trigger_visual(self, visual_name: str, note: int = None):
        """Trigger a specific visual."""
        try:
            # Create visualizer instance
            self.current_visualizer = self.visualizer_manager.create_visualizer(visual_name)
            
            if self.current_visualizer:
                self.current_visual_name = visual_name
                self.visual_name_label.setText(visual_name.upper())
                self.is_active = True
                
                # Update UI
                self.active_indicator.setStyleSheet("color: #44ff44;")
                self.activity_bar.setValue(100)
                
                if note:
                    self.last_note_label.setText(f"Note {note} triggered")
                    
                # Emit signal
                self.layer_triggered.emit(self.layer_number, visual_name)
                
                logging.info(f"Layer {self.layer_number}: Triggered '{visual_name}' (Note: {note})")
                
            else:
                self.visual_name_label.setText("FAILED TO LOAD")
                self.active_indicator.setStyleSheet("color: #ff4444;")
                
        except Exception as e:
            logging.error(f"Layer {self.layer_number}: Error triggering visual: {e}")
            self.visual_name_label.setText("ERROR")
            self.active_indicator.setStyleSheet("color: #ff4444;")
            
    def clear_layer(self):
        """Clear the layer."""
        self.current_visualizer = None
        self.current_visual_name = "NO VISUAL"
        self.visual_name_label.setText("NO VISUAL")
        self.is_active = False
        self.active_indicator.setStyleSheet("color: #444;")
        self.activity_bar.setValue(0)
        self.last_note_label.setText("Layer cleared")
        
        logging.info(f"Layer {self.layer_number}: Cleared")
        
    def on_opacity_changed(self, value):
        """Handle opacity change."""
        self.opacity = value
        self.opacity_label.setText(f"{value}%")
        self.layer_opacity_changed.emit(self.layer_number, value / 100.0)
        
    def update_visual_feedback(self):
        """Update visual feedback and animations."""
        if self.is_active and self.current_visualizer:
            # Simulate activity animation
            import time
            import math
            
            t = time.time() * 2
            intensity = int((math.sin(t) + 1) * 50)
            self.activity_bar.setValue(intensity)
            
            # Try to render if possible
            try:
                if hasattr(self.current_visualizer, 'render'):
                    self.current_visualizer.render()
            except Exception as e:
                logging.debug(f"Layer {self.layer_number} render error: {e}")
        else:
            # Fade out activity bar when not active
            current = self.activity_bar.value()
            if current > 0:
                self.activity_bar.setValue(max(0, current - 2))


class GridControlPanel(QWidget):
    """Grid Control Panel with master controls."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up control panel."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("GRID CONTROL")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #4080ff; padding: 8px;")
        layout.addWidget(title)
        
        # Master controls
        master_group = QGroupBox("Master")
        master_layout = QGridLayout(master_group)
        
        # Master opacity
        master_layout.addWidget(QLabel("Master Opacity:"), 0, 0)
        self.master_opacity = QSlider(Qt.Orientation.Horizontal)
        self.master_opacity.setRange(0, 100)
        self.master_opacity.setValue(100)
        master_layout.addWidget(self.master_opacity, 0, 1)
        
        # Crossfader
        master_layout.addWidget(QLabel("Crossfader:"), 1, 0)
        self.crossfader = QSlider(Qt.Orientation.Horizontal)
        self.crossfader.setRange(-100, 100)
        self.crossfader.setValue(0)
        master_layout.addWidget(self.crossfader, 1, 1)
        
        layout.addWidget(master_group)
        
        # Grid actions
        actions_group = QGroupBox("Grid Actions")
        actions_layout = QGridLayout(actions_group)
        
        # Action buttons
        actions = [
            ("CLEAR ALL", 0, 0), ("SYNC ALL", 0, 1),
            ("RANDOM A", 1, 0), ("RANDOM B", 1, 1),
            ("BLACKOUT", 2, 0), ("STROBE", 2, 1),
            ("BEAT SYNC", 3, 0), ("AUTO MIX", 3, 1)
        ]
        
        for text, row, col in actions:
            btn = QPushButton(text)
            btn.setMinimumHeight(30)
            actions_layout.addWidget(btn, row, col)
            
        layout.addWidget(actions_group)
        
        # MIDI status
        midi_group = QGroupBox("MIDI Status")
        midi_layout = QVBoxLayout(midi_group)
        
        self.midi_status = QLabel("MIDI: Connected")
        self.midi_status.setStyleSheet("color: #44ff44; font-weight: bold;")
        midi_layout.addWidget(self.midi_status)
        
        self.last_midi = QLabel("Last: None")
        self.last_midi.setStyleSheet("color: #888;")
        midi_layout.addWidget(self.last_midi)
        
        layout.addWidget(midi_group)
        
        layout.addStretch()


class VisualSettingsPanel(QWidget):
    """Visual Settings Panel for managing visualizers."""
    
    def __init__(self, visualizer_manager: VisualizerManager, parent=None):
        super().__init__(parent)
        self.visualizer_manager = visualizer_manager
        self.setup_ui()
        
    def setup_ui(self):
        """Set up visual settings panel."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("VISUAL SETTINGS")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #4080ff; padding: 8px;")
        layout.addWidget(title)
        
        # Visual library
        library_group = QGroupBox("Visual Library")
        library_layout = QVBoxLayout(library_group)
        
        # Search
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search visuals...")
        library_layout.addWidget(self.search_box)
        
        # Visual list
        self.visual_list = QScrollArea()
        self.visual_list.setMinimumHeight(300)
        self.populate_visual_list()
        library_layout.addWidget(self.visual_list)
        
        layout.addWidget(library_group)
        
        # MIDI mapping
        midi_group = QGroupBox("MIDI Mapping")
        midi_layout = QVBoxLayout(midi_group)
        
        mapping_info = QLabel(
            "Channel 13 -> Layer A\n"
            "Channel 14 -> Layer B\n"
            "Channel 15 -> Layer C\n"
            "Channel 16 -> Layer D"
        )
        mapping_info.setStyleSheet("color: #ccc; font-family: monospace;")
        midi_layout.addWidget(mapping_info)
        
        layout.addWidget(midi_group)
        
        layout.addStretch()
        
    def populate_visual_list(self):
        """Populate the visual list."""
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        if self.visualizer_manager:
            visualizers = self.visualizer_manager.get_visualizer_names()
            
            for viz_name in visualizers:
                viz_widget = QFrame()
                viz_widget.setFixedHeight(40)
                viz_widget.setStyleSheet("""
                    QFrame {
                        background: rgba(50, 50, 60, 150);
                        border: 1px solid #666;
                        border-radius: 4px;
                        margin: 1px;
                    }
                    QFrame:hover {
                        background: rgba(70, 70, 80, 180);
                    }
                """)
                
                viz_layout = QHBoxLayout(viz_widget)
                viz_layout.setContentsMargins(8, 4, 8, 4)
                
                name_label = QLabel(viz_name)
                name_label.setStyleSheet("color: white; background: transparent;")
                viz_layout.addWidget(name_label)
                
                viz_layout.addStretch()
                
                test_btn = QPushButton("TEST")
                test_btn.setFixedSize(50, 25)
                viz_layout.addWidget(test_btn)
                
                content_layout.addWidget(viz_widget)
                
        self.visual_list.setWidget(content_widget)


class AudioVisualizerGridApp(QMainWindow):
    """Main AudioVisualizer application with Grid interface."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AudioVisualizer - Grid Interface")
        self.setGeometry(100, 100, 1600, 900)
        
        # Initialize components
        self.settings_manager = SettingsManager()
        self.visualizer_manager = VisualizerManager()
        self.audio_analyzer = AudioAnalyzer()
        self.midi_engine = MidiEngine(self.settings_manager, self.visualizer_manager)
        
        # Grid layers with MIDI channel mapping
        self.grid_layers = {}
        
        self.setup_ui()
        self.setup_midi_routing()
        self.apply_modern_theme()
        
    def setup_ui(self):
        """Set up the main UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Live Control tab (Grid)
        live_control_tab = self.create_live_control_tab()
        self.tab_widget.addTab(live_control_tab, "Live Control")
        
        # Visual Settings tab
        visual_settings_tab = VisualSettingsPanel(self.visualizer_manager)
        self.tab_widget.addTab(visual_settings_tab, "Visual Settings")
        
        main_layout.addWidget(self.tab_widget)
        
    def create_live_control_tab(self) -> QWidget:
        """Create the Live Control tab with Grid."""
        tab_widget = QWidget()
        layout = QHBoxLayout(tab_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Grid area (4 layers)
        grid_area = self.create_grid_area()
        layout.addWidget(grid_area, 3)  # Takes most space
        
        # Control panel
        control_panel = GridControlPanel()
        control_panel.setMaximumWidth(300)
        layout.addWidget(control_panel, 1)
        
        return tab_widget
        
    def create_grid_area(self) -> QWidget:
        """Create the 4-layer grid."""
        grid_widget = QWidget()
        grid_layout = QVBoxLayout(grid_widget)
        grid_layout.setSpacing(8)
        
        # MIDI channel mapping: 13=A, 14=B, 15=C, 16=D
        layer_configs = [
            (1, 13, "A"),  # Layer 1, MIDI Channel 13
            (2, 14, "B"),  # Layer 2, MIDI Channel 14  
            (3, 15, "C"),  # Layer 3, MIDI Channel 15
            (4, 16, "D")   # Layer 4, MIDI Channel 16
        ]
        
        for layer_num, midi_ch, letter in layer_configs:
            layer_widget = GridLayerWidget(layer_num, midi_ch, self.visualizer_manager)
            layer_widget.layer_triggered.connect(self.on_layer_triggered)
            layer_widget.layer_opacity_changed.connect(self.on_layer_opacity_changed)
            
            self.grid_layers[layer_num] = layer_widget
            grid_layout.addWidget(layer_widget)
            
        return grid_widget
        
    def setup_midi_routing(self):
        """Set up MIDI routing to Grid layers."""
        # Connect MIDI engine to layer triggers
        if hasattr(self.midi_engine, 'note_on_signal'):
            self.midi_engine.note_on_signal.connect(self.handle_midi_note)
            
    def handle_midi_note(self, channel: int, note: int, velocity: int):
        """Handle incoming MIDI note and route to appropriate layer."""
        # Map MIDI channels to layers
        channel_to_layer = {
            13: 1,  # Channel 13 -> Layer A
            14: 2,  # Channel 14 -> Layer B  
            15: 3,  # Channel 15 -> Layer C
            16: 4   # Channel 16 -> Layer D
        }
        
        layer_num = channel_to_layer.get(channel)
        if layer_num and layer_num in self.grid_layers:
            layer = self.grid_layers[layer_num]
            layer.trigger_visual_by_midi_note(note)
            
            logging.info(f"MIDI: Note {note} on Channel {channel} -> Layer {layer_num}")
        else:
            logging.debug(f"MIDI: Note {note} on unmapped Channel {channel}")
            
    def on_layer_triggered(self, layer_number: int, visual_name: str):
        """Handle layer trigger event."""
        logging.info(f"Grid: Layer {layer_number} triggered with '{visual_name}'")
        
    def on_layer_opacity_changed(self, layer_number: int, opacity: float):
        """Handle layer opacity change."""
        logging.debug(f"Grid: Layer {layer_number} opacity: {opacity:.2f}")
        
    def apply_modern_theme(self):
        """Apply modern dark theme."""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(25, 25, 30))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.Base, QColor(20, 20, 25))
        palette.setColor(QPalette.ColorRole.Text, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 55))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(80, 120, 200))
        
        self.setPalette(palette)
        
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(20, 20, 25, 255),
                    stop:1 rgba(15, 15, 20, 255));
            }
            QTabWidget::pane {
                border: 1px solid #444;
                border-radius: 8px;
                background: rgba(30, 30, 40, 200);
            }
            QTabBar::tab {
                background: rgba(50, 50, 60, 150);
                border: 1px solid #555;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: rgba(80, 120, 200, 200);
            }
            QTabBar::tab:hover {
                background: rgba(70, 70, 80, 180);
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background: rgba(40, 40, 50, 100);
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 8px 0 8px;
                color: #4080ff;
                background: rgba(80, 120, 200, 180);
                border-radius: 4px;
            }
        """)


def main():
    """Main entry point for Grid interface."""
    
    # Configure OpenGL
    format = QSurfaceFormat()
    format.setVersion(3, 3)
    format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    format.setDepthBufferSize(24)
    QSurfaceFormat.setDefaultFormat(format)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("AudioVisualizer")
    app.setStyle("Fusion")
    
    # Create and show main window
    window = AudioVisualizerGridApp()
    window.show()
    
    print("AudioVisualizer Grid Interface started!")
    print("4-layer Grid active")
    print("MIDI channels: 13->A, 14->B, 15->C, 16->D")
    print("Visual Settings panel ready")
    
    return app.exec()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    sys.exit(main())