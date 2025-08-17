from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QGridLayout,
    QFrame,
)
from PyQt6.QtCore import Qt


def create_live_control_tab(self):
    """Create live control tab with four decks in vertical layout"""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    visuals = []
    if getattr(self, "visualizer_manager", None):
        visuals = sorted(self.visualizer_manager.get_visualizer_names())
    visuals = visuals[:6]  # show first six visuals

    for deck_index, deck_id in enumerate(["A", "B", "C", "D"]):
        deck_widget = create_deck_row(deck_id, deck_index, visuals)
        layout.addWidget(deck_widget)

    layout.addStretch()
    return widget


def create_deck_row(deck_id, default_channel, visuals):
    frame = QFrame()
    row_layout = QHBoxLayout(frame)

    channel_selector = QComboBox()
    channel_selector.addItems([f"Ch {i+1}" for i in range(16)])
    channel_selector.setCurrentIndex(default_channel)
    channel_selector.setFixedWidth(80)
    row_layout.addWidget(channel_selector)

    grid_widget = QWidget()
    grid_layout = QGridLayout(grid_widget)
    grid_layout.setContentsMargins(0, 0, 0, 0)
    grid_layout.setHorizontalSpacing(5)
    for i, visual in enumerate(visuals):
        button = QPushButton(visual)
        button.setFixedHeight(40)
        grid_layout.addWidget(button, 0, i)
    row_layout.addWidget(grid_widget)

    return frame
