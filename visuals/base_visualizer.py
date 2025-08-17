import logging
from OpenGL.GL import glGetError, GL_NO_ERROR
from OpenGL.GLU import gluErrorString


class BaseVisualizer:
    visual_name = "Base Visualizer"

    def __init__(self, *args, **kwargs):
        # Accept any arguments to prevent constructor errors
        # Pure Python class, presets may extend this.
        pass

    def _check_gl_error(self, context: str = ""):
        """Checks for OpenGL errors and logs them."""
        error = glGetError()
        if error != GL_NO_ERROR:
            error_str = f"OpenGL Error ({error}) in {context}: {gluErrorString(error).decode()}"
            logging.error(error_str)
            return True
        return False

    def initializeGL(self, backend=None):
        """Initialize OpenGL state.

        If *backend* is provided, use the RenderBackend API. Otherwise legacy
        gl* calls are expected for backwards compatibility."""
        pass

    def resizeGL(self, width: int, height: int, backend=None):
        """Handle resize events."""
        pass

    def paintGL(self, time: float = 0.0, size: tuple[int, int] | None = None, backend=None):
        """Main rendering function."""
        pass

    def cleanup(self):
        """Clean up OpenGL resources."""
        pass

    def get_controls(self):
        """Return dictionary of available controls for this visualizer"""
        return {}

    def update_control(self, name, value):
        """Update a control parameter"""
        pass