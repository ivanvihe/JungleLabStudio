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
        glClearColor(0.0, 0.0, 0.0, 1.0)
        
    def resizeGL(self, w, h):
        print(f"SimpleTestVisualizer.resizeGL called: {w}x{h}")
        glViewport(0, 0, w, h)
        
    def paintGL(self):
        self.time += 0.05
        
        # Simple animated clear color
        r = 0.5 + 0.5 * math.sin(self.time * self.red)
        g = 0.5 + 0.5 * math.sin(self.time * 1.2)
        b = 0.5 + 0.5 * math.sin(self.time * 0.8)
        
        glClearColor(r, g, b, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        
        # Draw a simple triangle
        glColor3f(1.0 - r, 1.0 - g, 1.0 - b)
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