from PyQt6.QtOpenGLWidgets import QOpenGLWidget

class BaseVisualizer(QOpenGLWidget):
    """Common interface for all visualizers with runtime controls."""
    def __init__(self, parent=None):
        super().__init__(parent)

    def get_controls(self):
        """Return a dict describing available controls.
        Example: {"Name": {"type": "slider", "min":0, "max":100, "value":50}}
        """
        return {}

    def update_control(self, name, value):
        """Update internal parameter identified by name with new value."""
        pass
