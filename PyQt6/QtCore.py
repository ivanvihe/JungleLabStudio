"""Proxy module mapping PyQt6.QtCore to PySide6.QtCore."""

from PySide6.QtCore import *  # type: ignore  # noqa: F401,F403

# Provide PyQt6 style aliases
pyqtSignal = Signal  # type: ignore
pyqtSlot = Slot  # type: ignore

__all__ = [name for name in globals().keys() if not name.startswith('_')]

