import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import glClearColor, glClear, GL_COLOR_BUFFER_BIT

class MinimalGLWidget(QOpenGLWidget):
    def initializeGL(self):
        glClearColor(0.2, 0.3, 0.3, 1.0)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)

    def resizeGL(self, w, h):
        pass # Not strictly necessary for this test

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minimal OpenGL Test")
        self.setGeometry(100, 100, 400, 300)
        self.gl_widget = MinimalGLWidget()
        self.setCentralWidget(self.gl_widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())