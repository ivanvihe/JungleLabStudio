"""Compatibility package to run existing PyQt6-based code using PySide6."""

# Re-export commonly used modules so imports like ``from PyQt6.QtWidgets``
# continue to work when only PySide6 is installed.

# The submodules are implemented in separate files that proxy to PySide6.

__all__ = [
    'QtWidgets',
    'QtCore',
    'QtGui',
    'QtOpenGL',
    'QtOpenGLWidgets',
]

