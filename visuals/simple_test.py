from OpenGL.GL import *
import math
from visuals.base_visualizer import BaseVisualizer

class SimpleTestVisualizer(BaseVisualizer):
    visual_name = "Simple Test"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time = 0
        self.red = 1.0
        print("SimpleTestVisualizer created!")
        
    def initializeGL(self):
        print("SimpleTestVisualizer.initializeGL called")
        # TRANSPARENT BACKGROUND FOR MIXING
        glClearColor(0.0, 0.0, 0.0, 0.0)  # Transparent background
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
    def resizeGL(self, w, h):
        print(f"SimpleTestVisualizer.resizeGL called: {w}x{h}")
        glViewport(0, 0, w, h)
        
    def paintGL(self):
        self.time += 0.05
        
        # CLEAR WITH TRANSPARENT BACKGROUND - don't change clear color here
        glClear(GL_COLOR_BUFFER_BIT)
        
        # Simple animated triangle with transparency
        r = 0.5 + 0.5 * math.sin(self.time * self.red)
        g = 0.5 + 0.5 * math.sin(self.time * 1.2)
        b = 0.5 + 0.5 * math.sin(self.time * 0.8)
        
        # Draw a simple triangle with transparency
        glColor4f(r, g, b, 0.8)  # Semi-transparent
        glBegin(GL_TRIANGLES)
        glVertex2f(0.0, 0.5)
        glVertex2f(-0.5, -0.5)
        glVertex2f(0.5, -0.5)
        glEnd()
        
    def get_controls(self):
        return {
            "Red Speed": {
                "type": "slider",
                "min": 1,
                "max": 500,
                "value": int(self.red * 100)
            }
        }
        
    def update_control(self, name, value):
        print(f"SimpleTestVisualizer: updating {name} to {value}")
        if name == "Red Speed":
            self.red = value / 100.0
            
    def cleanup(self):
        print("SimpleTestVisualizer cleaned up")