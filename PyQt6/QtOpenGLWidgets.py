"""Proxy module mapping PyQt6.QtOpenGLWidgets to PySide6.QtOpenGLWidgets."""

from PySide6.QtOpenGLWidgets import *  # type: ignore  # noqa: F401,F403

__all__ = [name for name in globals().keys() if not name.startswith('_')]

