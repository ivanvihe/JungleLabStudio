class BaseVisualizer:
    visual_name = "Base Visualizer"

    def __init__(self, *args, **kwargs):
        # Accept any arguments to prevent constructor errors
        # No longer inherit from QOpenGLWidget - just pure Python class
        pass

    def initializeGL(self):
        """Initialize OpenGL state - called when visualizer is first set up"""
        pass

    def resizeGL(self, width, height):
        """Handle resize events - called when the viewport changes size"""
        pass

    def paintGL(self):
        """Main rendering function - called every frame"""
        pass

    def cleanup(self):
        """Clean up OpenGL resources - called when visualizer is destroyed"""
        pass

    def get_controls(self):
        """Return dictionary of available controls for this visualizer"""
        return {}

    def update_control(self, name, value):
        """Update a control parameter"""
        pass