"""Proxy module mapping PyQt6.QtOpenGL to PySide6.QtOpenGL."""

from PySide6.QtOpenGL import *  # type: ignore  # noqa: F401,F403

__all__ = [name for name in globals().keys() if not name.startswith('_')]

