class BaseVisualizer:
    visual_name = "Base Visualizer"

    def __init__(self):
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
        return {}

    def update_control(self, name, value):
        pass
