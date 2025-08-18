from PySide6.QtWidgets import QWidget, QVBoxLayout
from .midi_config_widget import MidiConfigWidget


def create_midi_config_tab(self):
    """Tab de configuración MIDI completa"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    self.midi_config_widget = MidiConfigWidget(
        self.midi_engine,
        self.visualizer_manager,
        widget,
    )

    if hasattr(self.midi_config_widget, 'mapping_changed'):
        self.midi_config_widget.mapping_changed.connect(self.on_midi_mappings_changed)

    layout.addWidget(self.midi_config_widget)
    return widget
