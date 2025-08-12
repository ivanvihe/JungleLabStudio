class BaseVisualizer:
    visual_name = "Base Visualizer"

    def __init__(self, *args, **kwargs):
        # Accept any arguments to prevent constructor errors
        pass

    def initializeGL(self):
        pass

    def resizeGL(self, w, h):
        pass

    def paintGL(self):
        pass

    def cleanup(self):
        pass

    def get_controls(self):
        # Return empty controls by default
        return {}

    def update_control(self, name, value):
        pass