from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QSplitter,
    QFrame,
    QGroupBox,
    QLabel,
    QTableWidget,
    QHeaderView,
    QProgressBar,
    QHBoxLayout,
)
from PyQt6.QtCore import Qt


def create_live_control_tab(self):
    """Tab de control en vivo (UI original optimizada)"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    content_splitter = QSplitter(Qt.Orientation.Horizontal)
    deck_a_widget = create_deck_section(self, 'A')
    content_splitter.addWidget(deck_a_widget)

    mix_widget = create_mix_section(self)
    content_splitter.addWidget(mix_widget)

    deck_b_widget = create_deck_section(self, 'B')
    content_splitter.addWidget(deck_b_widget)

    content_splitter.setSizes([500, 600, 500])
    layout.addWidget(content_splitter)
    return widget


def create_deck_section(self, deck_id):
    """Create a deck section (A or B) - ENHANCED"""
    deck_frame = QFrame()
    deck_frame.setFrameStyle(QFrame.Shape.StyledPanel)

    if deck_id == 'A':
        border_color = "#ff4444"
        deck_name = "DECK A"
    else:
        border_color = "#44ff44"
        deck_name = "DECK B"

    deck_frame.setStyleSheet(f"""
        QFrame {{
            background-color: #1a1a1a;
            border: 2px solid {border_color};
            border-radius: 8px;
            padding: 5px;
        }}
    """)

    deck_layout = QVBoxLayout(deck_frame)
    deck_layout.setSpacing(10)

    header_label = QLabel(f"<b>{deck_name}</b>")
    header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    header_label.setStyleSheet(
        f"color: {border_color}; font-size: 16px; font-weight: bold; padding: 5px;"
    )
    deck_layout.addWidget(header_label)

    status_group = create_deck_status_section(self, deck_id)
    deck_layout.addWidget(status_group)

    activity_group = create_deck_activity_section(self, deck_id)
    deck_layout.addWidget(activity_group)

    return deck_frame


def create_deck_status_section(self, deck_id):
    """Create deck status information section"""
    status_group = QGroupBox("📊 Estado Actual")
    status_group.setStyleSheet(
        """
        QGroupBox {
            font-weight: bold;
            color: #ffffff;
            border: 1px solid #666;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        """
    )

    status_layout = QVBoxLayout(status_group)

    if deck_id == 'A':
        self.deck_a_preset_label = QLabel("Preset: Ninguno")
        self.deck_a_activity_label = QLabel("Última actividad: --")
        self.deck_a_controls_label = QLabel("Controles: --")

        self.deck_a_preset_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        self.deck_a_activity_label.setStyleSheet("color: #888; font-size: 10px;")
        self.deck_a_controls_label.setStyleSheet("color: #00aaff; font-size: 10px;")

        status_layout.addWidget(self.deck_a_preset_label)
        status_layout.addWidget(self.deck_a_activity_label)
        status_layout.addWidget(self.deck_a_controls_label)
    else:
        self.deck_b_preset_label = QLabel("Preset: Ninguno")
        self.deck_b_activity_label = QLabel("Última actividad: --")
        self.deck_b_controls_label = QLabel("Controles: --")

        self.deck_b_preset_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        self.deck_b_activity_label.setStyleSheet("color: #888; font-size: 10px;")
        self.deck_b_controls_label.setStyleSheet("color: #00aaff; font-size: 10px;")

        status_layout.addWidget(self.deck_b_preset_label)
        status_layout.addWidget(self.deck_b_activity_label)
        status_layout.addWidget(self.deck_b_controls_label)

    return status_group


def create_deck_activity_section(self, deck_id):
    """Create MIDI activity section for a deck"""
    activity_group = QGroupBox("🎵 Actividad MIDI")
    activity_group.setStyleSheet(
        """
        QGroupBox {
            font-weight: bold;
            color: #ffffff;
            border: 1px solid #666;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        """
    )

    layout = QVBoxLayout(activity_group)

    table = QTableWidget()
    table.setColumnCount(3)
    table.setHorizontalHeaderLabels(["Tiempo", "Tipo", "Dato"])
    table.setMaximumHeight(150)

    header = table.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
    header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
    header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
    table.setColumnWidth(0, 70)
    table.setColumnWidth(1, 70)

    layout.addWidget(table)

    if deck_id == 'A':
        self.deck_a_activity_table = table
    else:
        self.deck_b_activity_table = table

    return activity_group


def create_mix_section(self):
    """Create mix section"""
    mix_frame = QFrame()
    mix_frame.setFrameStyle(QFrame.Shape.StyledPanel)
    mix_frame.setStyleSheet(
        """
        QFrame {
            background-color: #1a1a1a;
            border: 2px solid #ffaa00;
            border-radius: 8px;
            padding: 5px;
        }
        """
    )

    mix_layout = QVBoxLayout(mix_frame)
    mix_layout.setSpacing(10)

    header_label = QLabel("<b>🎚️ VISUAL MIX</b>")
    header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    header_label.setStyleSheet(
        "color: #ffaa00; font-size: 16px; font-weight: bold; padding: 5px;"
    )
    mix_layout.addWidget(header_label)

    status_group = create_mix_status_section(self)
    mix_layout.addWidget(status_group)

    future_group = QGroupBox("🚀 Próximamente")
    future_group.setStyleSheet(
        """
        QGroupBox {
            font-weight: bold;
            color: #00aaff;
            border: 1px solid #00aaff;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        """
    )

    future_layout = QVBoxLayout(future_group)
    features = [
        "• Efectos visuales RT",
        "• Control de colores MIDI",
        "• Sync con BPM",
        "• Macros visuales",
    ]
    for feature in features:
        label = QLabel(feature)
        label.setStyleSheet("color: #00aaff; font-size: 9px; padding: 1px;")
        future_layout.addWidget(label)

    mix_layout.addWidget(future_group)
    return mix_frame


def create_mix_status_section(self):
    """Create mix status section"""
    status_group = QGroupBox("📊 Estado del Mix")
    status_group.setStyleSheet(
        """
        QGroupBox {
            font-weight: bold;
            color: #ffffff;
            border: 1px solid #666;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        """
    )

    status_layout = QVBoxLayout(status_group)

    self.mix_value_label = QLabel("Crossfader: 50%")
    self.mix_value_label.setStyleSheet("color: #ffaa00; font-weight: bold;")
    status_layout.addWidget(self.mix_value_label)

    fader_widget = QWidget()
    fader_layout = QVBoxLayout(fader_widget)
    fader_layout.setContentsMargins(0, 0, 0, 0)

    labels_layout = QHBoxLayout()
    labels_layout.addWidget(QLabel("← A"))
    labels_layout.addStretch()
    labels_layout.addWidget(QLabel("B →"))
    fader_layout.addLayout(labels_layout)

    self.mix_progress_bar = QProgressBar()
    self.mix_progress_bar.setRange(0, 100)
    self.mix_progress_bar.setValue(50)
    self.mix_progress_bar.setMaximumHeight(20)
    self.mix_progress_bar.setStyleSheet(
        """
        QProgressBar {
            border: 2px solid #333;
            border-radius: 10px;
            background-color: #1a1a1a;
            text-align: center;
            color: white;
            font-weight: bold;
        }
        QProgressBar::chunk {
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #ff4444, stop:0.5 #ffaa00, stop:1 #44ff44);
            border-radius: 8px;
        }
        """
    )
    fader_layout.addWidget(self.mix_progress_bar)
    status_layout.addWidget(fader_widget)

    self.mix_activity_label = QLabel("Última actividad: --")
    self.mix_activity_label.setStyleSheet("color: #888; font-size: 10px;")
    status_layout.addWidget(self.mix_activity_label)

    return status_group
