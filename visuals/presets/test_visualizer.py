# TODO: migrate to RenderBackend (ModernGL)
from OpenGL.GL import *
import math
import time
from visuals.base_visualizer import BaseVisualizer

class TestVisualizer(BaseVisualizer):
    visual_name = "Test Pattern"
    
    def __init__(self):
        super().__init__()
        self.time = 0
        self.color_r = 1.0
        self.color_g = 0.5
        self.color_b = 0.0
        self.speed = 1.0
        self.pattern = 0  # 0 = circle, 1 = square, 2 = triangle
        
    def initializeGL(self):
        # TRANSPARENT BACKGROUND FOR MIXING
        glClearColor(0.0, 0.0, 0.0, 0.0)  # Transparent background
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        print(f"TestVisualizer initialized")
        
    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        print(f"TestVisualizer resized to {w}x{h}")
        
    def paintGL(self):
        self.time += 0.016 * self.speed  # Assume 60 FPS
        
        # CLEAR WITH TRANSPARENT BACKGROUND - don't change clear color here
        glClear(GL_COLOR_BUFFER_BIT)
        
        # Draw animated pattern with transparency
        x = math.sin(self.time) * 0.5
        y = math.cos(self.time * 0.7) * 0.3
        size = 0.2 + 0.1 * math.sin(self.time * 2)
        
        # Use semi-transparent colors
        glColor4f(self.color_r, self.color_g, self.color_b, 0.8)
        
        if self.pattern == 0:  # Circle
            self.draw_circle(x, y, size)
        elif self.pattern == 1:  # Square
            self.draw_square(x, y, size)
        else:  # Triangle
            self.draw_triangle(x, y, size)
            
    def draw_circle(self, x, y, size):
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(x, y)
        for i in range(33):
            angle = 2.0 * math.pi * i / 32
            glVertex2f(x + size * math.cos(angle), y + size * math.sin(angle))
        glEnd()
        
    def draw_square(self, x, y, size):
        glBegin(GL_QUADS)
        glVertex2f(x - size, y - size)
        glVertex2f(x + size, y - size)
        glVertex2f(x + size, y + size)
        glVertex2f(x - size, y + size)
        glEnd()
        
    def draw_triangle(self, x, y, size):
        glBegin(GL_TRIANGLES)
        glVertex2f(x, y + size)
        glVertex2f(x - size, y - size)
        glVertex2f(x + size, y - size)
        glEnd()
        
    def get_controls(self):
        return {
            "Red": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.color_r * 100)
            },
            "Green": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.color_g * 100)
            },
            "Blue": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.color_b * 100)
            },
            "Speed": {
                "type": "slider",
                "min": 0,
                "max": 300,
                "value": int(self.speed * 100)
            },
            "Pattern": {
                "type": "dropdown",
                "options": ["Circle", "Square", "Triangle"],
                "value": self.pattern
            }
        }
        
    def update_control(self, name, value):
        print(f"TestVisualizer: updating {name} to {value}")
        if name == "Red":
            self.color_r = value / 100.0
        elif name == "Green":
            self.color_g = value / 100.0
        elif name == "Blue":
            self.color_b = value / 100.0
        elif name == "Speed":
            self.speed = value / 100.0
        elif name == "Pattern":
            self.pattern = value
            
    def cleanup(self):
        print("TestVisualizer cleaned up")