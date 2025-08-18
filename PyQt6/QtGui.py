"""Proxy module mapping PyQt6.QtGui to PySide6.QtGui."""

from PySide6.QtGui import *  # type: ignore  # noqa: F401,F403

__all__ = [name for name in globals().keys() if not name.startswith('_')]

