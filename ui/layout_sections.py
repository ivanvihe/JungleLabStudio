from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QWidget, QVBoxLayout, QProgressBar
)
from PyQt6.QtCore import QTimer, Qt


def create_midi_activity_indicator(self):
    """Crear indicador visual de actividad MIDI"""
    indicator_widget = QWidget()
    indicator_layout = QHBoxLayout(indicator_widget)
    indicator_layout.setContentsMargins(5, 2, 5, 2)
    indicator_layout.setSpacing(5)

    midi_label = QLabel("MIDI:")
    midi_label.setStyleSheet("color: #ffffff; font-size: 10px;")
    indicator_layout.addWidget(midi_label)

    self.midi_led = QLabel("●")
    self.midi_led.setStyleSheet(
        """
        QLabel {
            color: #333333;
            font-size: 16px;
            font-weight: bold;
            background-color: transparent;
            border-radius: 8px;
            min-width: 16px;
            max-width: 16px;
            text-align: center;
        }
        """
    )
    indicator_layout.addWidget(self.midi_led)

    self.midi_led_timer = QTimer()
    self.midi_led_timer.setSingleShot(True)
    self.midi_led_timer.timeout.connect(self.turn_off_midi_led)

    return indicator_widget


def create_header_section(self):
    """Create header with status information including MIDI indicator and debug button"""
    header_frame = QFrame()
    header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
    header_frame.setStyleSheet(
        """
        QFrame {
            background-color: #1a1a1a;
            border: 2px solid #00ff00;
            border-radius: 8px;
            padding: 10px;
        }
        """
    )
    header_layout = QHBoxLayout(header_frame)

    title_label = QLabel("<b>🎛️ AUDIO VISUALIZER PRO - CONTROL CENTER</b>")
    title_label.setStyleSheet("font-size: 18px; color: #00ff00; font-weight: bold;")
    header_layout.addWidget(title_label)

    header_layout.addStretch()

    midi_activity = create_midi_activity_indicator(self)
    header_layout.addWidget(midi_activity)

    self.midi_status_label = QLabel("MIDI: Checking...")
    self.midi_status_label.setStyleSheet("font-weight: bold; padding: 5px; color: #ffaa00;")
    header_layout.addWidget(self.midi_status_label)

    quick_midi_btn = QPushButton("🎹 MIDI")
    quick_midi_btn.setMaximumWidth(80)
    quick_midi_btn.setStyleSheet("background-color: #6600cc; color: white; padding: 5px;")
    quick_midi_btn.clicked.connect(self.show_midi_config)
    header_layout.addWidget(quick_midi_btn)

    debug_btn = QPushButton("🔧 Debug")
    debug_btn.setMaximumWidth(80)
    debug_btn.setStyleSheet("background-color: #0066cc; color: white; padding: 5px;")
    debug_btn.clicked.connect(self.run_midi_debug)
    header_layout.addWidget(debug_btn)

    level_widget = QWidget()
    level_layout = QVBoxLayout(level_widget)
    level_layout.setContentsMargins(0, 0, 0, 0)
    level_layout.setSpacing(2)

    level_label = QLabel("Audio Level:")
    level_label.setStyleSheet("font-size: 10px; color: #ffffff;")
    level_layout.addWidget(level_label)

    self.audio_level_bar = QProgressBar()
    self.audio_level_bar.setRange(0, 100)
    self.audio_level_bar.setValue(0)
    self.audio_level_bar.setMaximumHeight(15)
    self.audio_level_bar.setMaximumWidth(120)
    self.audio_level_bar.setStyleSheet(
        """
        QProgressBar {
            border: 1px solid #333;
            border-radius: 3px;
            background-color: #1a1a1a;
            text-align: center;
            font-size: 9px;
            color: white;
        }
        QProgressBar::chunk {
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #00ff00, stop:0.7 #ffff00, stop:1 #ff0000);
            border-radius: 2px;
        }
        """
    )
    level_layout.addWidget(self.audio_level_bar)

    header_layout.addWidget(level_widget)

    return header_frame


def create_footer_section(self):
    """Create footer with compact information"""
    footer_frame = QFrame()
    footer_frame.setFrameStyle(QFrame.Shape.StyledPanel)
    footer_frame.setStyleSheet(
        """
        QFrame {
            background-color: #2a2a2a;
            border: 1px solid #666;
            border-radius: 5px;
            padding: 10px;
        }
        """
    )
    footer_frame.setMaximumHeight(80)

    footer_layout = QHBoxLayout(footer_frame)

    self.footer_mappings_info = QLabel("MIDI Mappings: 0")
    self.footer_mappings_info.setStyleSheet("color: #ffffff; font-weight: bold;")
    footer_layout.addWidget(self.footer_mappings_info)

    footer_layout.addStretch()

    instructions = QLabel("💡 Tip: Usa el tab 'Configuración MIDI' para personalizar controles")
    instructions.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
    footer_layout.addWidget(instructions)

    return footer_frame
