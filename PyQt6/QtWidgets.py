"""Proxy module mapping PyQt6.QtWidgets to PySide6.QtWidgets."""

from PySide6.QtWidgets import *  # type: ignore  # noqa: F401,F403

__all__ = [name for name in globals().keys() if not name.startswith('_')]

