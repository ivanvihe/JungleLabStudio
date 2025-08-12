from PyQt6.QtOpenGL import QOpenGLFramebufferObject
from PyQt6.QtCore import QSize
from OpenGL.GL import *
import logging

class Deck:
    def __init__(self, visualizer_manager):
        self.visualizer_manager = visualizer_manager
        self.visualizer = None
        self.fbo = None
        self.visualizer_name = None
        self.size = QSize(800, 600)
        self._needs_init_and_resize = True

    def set_visualizer(self, visualizer_name):
        logging.debug(f"Setting visualizer for deck to: {visualizer_name}")
        if self.visualizer:
            if hasattr(self.visualizer, 'cleanup'):
                self.visualizer.cleanup()
            self.visualizer = None

        self.visualizer_name = visualizer_name
        visualizer_class = self.visualizer_manager.get_visualizer_class(visualizer_name)
        if visualizer_class:
            self.visualizer = visualizer_class()
            self._needs_init_and_resize = True

    def paint(self):
        logging.debug(f"Painting deck with visualizer: {self.visualizer_name}")
        if self.visualizer and self.fbo:
            if self._needs_init_and_resize:
                self.visualizer.initializeGL()
                self.visualizer.resizeGL(self.size.width(), self.size.height())
                self._needs_init_and_resize = False

            self.fbo.bind()
            glViewport(0, 0, self.size.width(), self.size.height())
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.visualizer.paintGL()
            self.fbo.release()
        else:
            logging.debug("Deck has no visualizer or FBO")

    def resize(self, size):
        self.size = size
        self.recreate_fbo()
        self._needs_init_and_resize = True

    def recreate_fbo(self):
        if self.fbo:
            self.fbo.release()
        self.fbo = QOpenGLFramebufferObject(self.size, QOpenGLFramebufferObject.Attachment.CombinedDepthStencil)

    def get_texture(self):
        return self.fbo.texture() if self.fbo else 0

    def get_controls(self):
        if self.visualizer:
            return self.visualizer.get_controls()
        return {}

    def update_control(self, name, value):
        if self.visualizer:
            self.visualizer.update_control(name, value)
