from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QWidget, QVBoxLayout, QProgressBar
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
    """Compact header showing only MIDI status and audio level"""
    header_frame = QFrame()
    header_frame.setFrameStyle(QFrame.Shape.NoFrame)
    header_frame.setStyleSheet(
        """
        QFrame {
            background-color: #2a2a2a;
            border-bottom: 1px solid #444;
        }
        """
    )
    header_frame.setMaximumHeight(40)

    header_layout = QHBoxLayout(header_frame)
    header_layout.setContentsMargins(5, 2, 5, 2)
    header_layout.setSpacing(10)

    midi_activity = create_midi_activity_indicator(self)
    header_layout.addWidget(midi_activity)

    self.midi_status_label = QLabel("MIDI: Checking...")
    self.midi_status_label.setStyleSheet("font-weight: bold; padding: 2px; color: #ffaa00;")
    header_layout.addWidget(self.midi_status_label)

    header_layout.addStretch()

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
