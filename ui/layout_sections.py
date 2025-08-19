# ui/layout_sections.py - MODERNIZED VERSION
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QWidget, QVBoxLayout, QProgressBar
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont

# Modern color scheme matching the grid
MODERN_COLORS = {
    'background_dark': '#0a0a0a',
    'background_medium': '#151515', 
    'background_light': '#1f1f1f',
    'accent_orange': '#ff6b35',
    'accent_blue': '#4a9eff',
    'accent_green': '#00d4aa',
    'text_primary': '#ffffff',
    'text_secondary': '#b0b0b0',
    'text_muted': '#666666',
    'border_normal': '#333333',
    'border_active': '#ff6b35',
    'success': '#00d4aa',
    'warning': '#ffaa00',
    'error': '#ff4444'
}

def create_midi_activity_indicator(self):
    """Create modern MIDI activity indicator with professional styling."""
    indicator_widget = QWidget()
    indicator_layout = QHBoxLayout(indicator_widget)
    indicator_layout.setContentsMargins(8, 4, 8, 4)
    indicator_layout.setSpacing(8)

    # Modern MIDI label
    midi_label = QLabel("MIDI")
    midi_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
    midi_label.setStyleSheet(f"""
        QLabel {{
            color: {MODERN_COLORS['text_secondary']};
            background: transparent;
            padding: 2px 4px;
        }}
    """)
    indicator_layout.addWidget(midi_label)

    # Modern LED indicator with glow effect
    self.midi_led = QLabel("*")
    self.midi_led.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
    self.midi_led.setStyleSheet(f"""
        QLabel {{
            color: {MODERN_COLORS['text_muted']};
            background: transparent;
            border-radius: 6px;
            min-width: 12px;
            max-width: 12px;
            text-align: center;
        }}
    """)
    indicator_layout.addWidget(self.midi_led)

    # Timer for LED auto-off
    self.midi_led_timer = QTimer()
    self.midi_led_timer.setSingleShot(True)
    self.midi_led_timer.timeout.connect(self.turn_off_midi_led)

    return indicator_widget

def create_header_section(self):
    """Create modern header with clean professional styling."""
    header_frame = QFrame()
    header_frame.setFrameStyle(QFrame.Shape.NoFrame)
    header_frame.setStyleSheet(f"""
        QFrame {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {MODERN_COLORS['background_medium']},
                stop:1 {MODERN_COLORS['background_dark']});
            border-bottom: 1px solid {MODERN_COLORS['border_normal']};
        }}
    """)
    header_frame.setMaximumHeight(45)

    header_layout = QHBoxLayout(header_frame)
    header_layout.setContentsMargins(12, 0, 12, 0)
    header_layout.setSpacing(16)

    # Modern MIDI activity section
    midi_activity = create_midi_activity_indicator(self)
    header_layout.addWidget(midi_activity)

    # Modern MIDI status with better typography
    self.midi_status_label = QLabel("MIDI: Checking...")
    self.midi_status_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
    self.midi_status_label.setStyleSheet(f"""
        QLabel {{
            color: {MODERN_COLORS['warning']};
            background: transparent;
            padding: 4px 8px;
            border-radius: 3px;
        }}
    """)
    header_layout.addWidget(self.midi_status_label)

    header_layout.addStretch()

    # Modern audio level section
    level_widget = create_modern_audio_level_widget(self)
    header_layout.addWidget(level_widget)

    return header_frame

def create_modern_audio_level_widget(self):
    """Create modern audio level widget with professional VU meter styling."""
    level_widget = QWidget()
    level_widget.setFixedWidth(140)
    
    level_layout = QVBoxLayout(level_widget)
    level_layout.setContentsMargins(0, 0, 0, 0)
    level_layout.setSpacing(2)

    # Modern label
    level_label = QLabel("AUDIO LEVEL")
    level_label.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
    level_label.setStyleSheet(f"""
        QLabel {{
            color: {MODERN_COLORS['text_secondary']};
            background: transparent;
        }}
    """)
    level_layout.addWidget(level_label)

    # Modern progress bar with professional VU meter styling
    self.audio_level_bar = QProgressBar()
    self.audio_level_bar.setRange(0, 100)
    self.audio_level_bar.setValue(0)
    self.audio_level_bar.setFixedHeight(12)
    self.audio_level_bar.setTextVisible(False)
    self.audio_level_bar.setStyleSheet(f"""
        QProgressBar {{
            border: 1px solid {MODERN_COLORS['border_normal']};
            border-radius: 6px;
            background-color: {MODERN_COLORS['background_dark']};
            text-align: center;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {MODERN_COLORS['success']},
                stop:0.6 {MODERN_COLORS['warning']}, 
                stop:0.8 {MODERN_COLORS['accent_orange']},
                stop:1 {MODERN_COLORS['error']});
            border-radius: 5px;
            margin: 1px;
        }}
    """)
    level_layout.addWidget(self.audio_level_bar)

    return level_widget

def create_footer_section(self):
    """Create modern footer with professional information display."""
    footer_frame = QFrame()
    footer_frame.setFrameStyle(QFrame.Shape.NoFrame)
    footer_frame.setStyleSheet(f"""
        QFrame {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {MODERN_COLORS['background_dark']},
                stop:1 {MODERN_COLORS['background_medium']});
            border-top: 1px solid {MODERN_COLORS['border_normal']};
            border-radius: 0px;
        }}
    """)
    footer_frame.setMaximumHeight(60)

    footer_layout = QHBoxLayout(footer_frame)
    footer_layout.setContentsMargins(12, 8, 12, 8)
    footer_layout.setSpacing(16)

    # Modern mappings info section
    mappings_section = create_modern_mappings_section(self)
    footer_layout.addWidget(mappings_section)

    footer_layout.addStretch()

    # Modern tips section
    tips_section = create_modern_tips_section()
    footer_layout.addWidget(tips_section)

    return footer_frame

def create_modern_mappings_section(self):
    """Create modern MIDI mappings information section."""
    mappings_widget = QWidget()
    mappings_layout = QVBoxLayout(mappings_widget)
    mappings_layout.setContentsMargins(0, 0, 0, 0)
    mappings_layout.setSpacing(2)

    # Title
    mappings_title = QLabel("MIDI MAPPINGS")
    mappings_title.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
    mappings_title.setStyleSheet(f"""
        QLabel {{
            color: {MODERN_COLORS['text_secondary']};
            background: transparent;
        }}
    """)
    mappings_layout.addWidget(mappings_title)

    # Count display
    self.footer_mappings_info = QLabel("0 mappings")
    self.footer_mappings_info.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
    self.footer_mappings_info.setStyleSheet(f"""
        QLabel {{
            color: {MODERN_COLORS['text_primary']};
            background: rgba(255, 255, 255, 10);
            padding: 2px 6px;
            border-radius: 3px;
            border: 1px solid {MODERN_COLORS['border_normal']};
        }}
    """)
    mappings_layout.addWidget(self.footer_mappings_info)

    return mappings_widget

def create_modern_tips_section():
    """Create modern tips section with professional styling."""
    tips_widget = QWidget()
    tips_layout = QVBoxLayout(tips_widget)
    tips_layout.setContentsMargins(0, 0, 0, 0)
    tips_layout.setSpacing(2)

    # Icon and label
    tip_header = QLabel("TIP")
    tip_header.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
    tip_header.setStyleSheet(f"""
        QLabel {{
            color: {MODERN_COLORS['accent_blue']};
            background: transparent;
        }}
    """)
    tips_layout.addWidget(tip_header)

    # Tip text with modern styling
    instructions = QLabel("Use MIDI Config to customize controls")
    instructions.setFont(QFont("Segoe UI", 9))
    instructions.setStyleSheet(f"""
        QLabel {{
            color: {MODERN_COLORS['text_muted']};
            background: transparent;
            font-style: italic;
        }}
    """)
    tips_layout.addWidget(instructions)

    return tips_widget

# Additional modern styling methods for the control panel

def update_midi_led_active(self):
    """Update MIDI LED to active state with modern glow effect."""
    try:
        if hasattr(self, 'midi_led'):
            self.midi_led.setStyleSheet(f"""
                QLabel {{
                    color: {MODERN_COLORS['success']};
                    background: radial-gradient(circle, 
                        rgba(0, 212, 170, 40) 0%, 
                        transparent 70%);
                    border-radius: 6px;
                    min-width: 12px;
                    max-width: 12px;
                    text-align: center;
                }}
            """)
            if hasattr(self, 'midi_led_timer'):
                self.midi_led_timer.start(200)  # Longer visibility for modern feel
    except Exception as e:
        logging.error(f"Error updating MIDI LED active state: {e}")

def update_midi_led_inactive(self):
    """Update MIDI LED to inactive state."""
    try:
        if hasattr(self, 'midi_led'):
            self.midi_led.setStyleSheet(f"""
                QLabel {{
                    color: {MODERN_COLORS['text_muted']};
                    background: transparent;
                    border-radius: 6px;
                    min-width: 12px;
                    max-width: 12px;
                    text-align: center;
                }}
            """)
    except Exception as e:
        logging.error(f"Error updating MIDI LED inactive state: {e}")

def update_midi_status_connected(self, device_name=""):
    """Update MIDI status to connected state with modern styling."""
    try:
        if hasattr(self, 'midi_status_label'):
            display_text = f"MIDI: {device_name}" if device_name else "MIDI: Connected"
            self.midi_status_label.setText(display_text)
            self.midi_status_label.setStyleSheet(f"""
                QLabel {{
                    color: {MODERN_COLORS['success']};
                    background: rgba(0, 212, 170, 20);
                    padding: 4px 8px;
                    border-radius: 3px;
                    border: 1px solid rgba(0, 212, 170, 100);
                }}
            """)
    except Exception as e:
        logging.error(f"Error updating MIDI status connected: {e}")

def update_midi_status_disconnected(self):
    """Update MIDI status to disconnected state."""
    try:
        if hasattr(self, 'midi_status_label'):
            self.midi_status_label.setText("MIDI: Disconnected")
            self.midi_status_label.setStyleSheet(f"""
                QLabel {{
                    color: {MODERN_COLORS['error']};
                    background: rgba(255, 68, 68, 20);
                    padding: 4px 8px;
                    border-radius: 3px;
                    border: 1px solid rgba(255, 68, 68, 100);
                }}
            """)
    except Exception as e:
        logging.error(f"Error updating MIDI status disconnected: {e}")

def update_midi_status_checking(self):
    """Update MIDI status to checking state."""
    try:
        if hasattr(self, 'midi_status_label'):
            self.midi_status_label.setText("MIDI: Checking...")
            self.midi_status_label.setStyleSheet(f"""
                QLabel {{
                    color: {MODERN_COLORS['warning']};
                    background: rgba(255, 170, 0, 20);
                    padding: 4px 8px;
                    border-radius: 3px;
                    border: 1px solid rgba(255, 170, 0, 100);
                }}
            """)
    except Exception as e:
        logging.error(f"Error updating MIDI status checking: {e}")

# Enhanced methods for the control panel to use modern styling
def turn_on_midi_led(self):
    """Turn on MIDI LED with modern styling."""
    update_midi_led_active(self)

def turn_off_midi_led(self):
    """Turn off MIDI LED with modern styling."""
    update_midi_led_inactive(self)