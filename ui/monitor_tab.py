from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QGroupBox, QTableWidget, QHeaderView,
    QPushButton, QHBoxLayout, QLabel, QTextEdit
)
from PySide6.QtCore import Qt


def create_monitor_tab(self):
    """Tab de monitoreo y debug"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    splitter = QSplitter(Qt.Orientation.Horizontal)
    midi_activity_section = create_midi_activity_section(self)
    splitter.addWidget(midi_activity_section)

    system_section = create_system_info_section(self)
    splitter.addWidget(system_section)

    layout.addWidget(splitter)
    return widget


def create_midi_activity_section(self):
    """Crear sección de actividad MIDI para el tab de monitoreo"""
    section = QGroupBox("🎵 Actividad MIDI en Tiempo Real")
    section.setStyleSheet(
        """
        QGroupBox {
            font-weight: bold;
            color: #ffffff;
            border: 2px solid #6600cc;
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

    layout = QVBoxLayout(section)

    self.midi_activity_table = QTableWidget()
    self.midi_activity_table.setColumnCount(4)
    self.midi_activity_table.setHorizontalHeaderLabels(["Tiempo", "Tipo", "Dato", "Deck"])
    self.midi_activity_table.setMaximumHeight(200)

    header = self.midi_activity_table.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
    header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
    header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
    header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)

    self.midi_activity_table.setColumnWidth(0, 80)
    self.midi_activity_table.setColumnWidth(1, 80)
    self.midi_activity_table.setColumnWidth(3, 100)

    layout.addWidget(self.midi_activity_table)

    controls_layout = QHBoxLayout()

    clear_activity_btn = QPushButton("🗑️ Limpiar")
    clear_activity_btn.clicked.connect(self.clear_midi_activity)
    controls_layout.addWidget(clear_activity_btn)

    pause_activity_btn = QPushButton("⏸️ Pausar")
    pause_activity_btn.clicked.connect(self.toggle_midi_activity_monitoring)
    controls_layout.addWidget(pause_activity_btn)

    controls_layout.addStretch()

    self.midi_stats_label = QLabel("Mensajes: 0 | Últimos 60s: 0")
    self.midi_stats_label.setStyleSheet("color: #ffffff; font-size: 10px;")
    controls_layout.addWidget(self.midi_stats_label)

    layout.addLayout(controls_layout)

    self.midi_activity_data = []
    self.midi_monitoring_paused = False
    self.midi_message_count = 0

    return section


def create_system_info_section(self):
    """Crear sección de información del sistema"""
    section = QGroupBox("📊 Información del Sistema")
    section.setStyleSheet(
        """
        QGroupBox {
            font-weight: bold;
            color: #ffffff;
            border: 2px solid #ff6600;
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

    layout = QVBoxLayout(section)

    self.system_info_text = QTextEdit()
    self.system_info_text.setMaximumHeight(150)
    self.system_info_text.setReadOnly(True)
    self.system_info_text.setStyleSheet(
        """
        QTextEdit {
            background-color: #1a1a1a;
            color: #ffffff;
            border: 1px solid #666;
            font-family: 'Courier New', monospace;
            font-size: 10px;
        }
        """
    )
    layout.addWidget(self.system_info_text)

    events_label = QLabel("📝 Log de Eventos:")
    events_label.setStyleSheet("color: #ffffff; font-weight: bold; margin-top: 10px;")
    layout.addWidget(events_label)

    self.events_log = QTextEdit()
    self.events_log.setMaximumHeight(100)
    self.events_log.setReadOnly(True)
    self.events_log.setStyleSheet(
        """
        QTextEdit {
            background-color: #0a0a0a;
            color: #00ff00;
            border: 1px solid #666;
            font-family: 'Courier New', monospace;
            font-size: 9px;
        }
        """
    )
    layout.addWidget(self.events_log)

    log_controls = QHBoxLayout()

    clear_log_btn = QPushButton("🗑️ Limpiar Log")
    clear_log_btn.clicked.connect(self.clear_events_log)
    log_controls.addWidget(clear_log_btn)

    export_log_btn = QPushButton("💾 Exportar Log")
    export_log_btn.clicked.connect(self.export_events_log)
    log_controls.addWidget(export_log_btn)

    log_controls.addStretch()
    layout.addLayout(log_controls)

    self.update_system_info()
    return section
