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
        self._gl_initialized = False

    def set_visualizer(self, visualizer_name):
        logging.debug(f"Setting visualizer for deck to: {visualizer_name}")
        
        # Clean up old visualizer
        if self.visualizer:
            if hasattr(self.visualizer, 'cleanup'):
                try:
                    self.visualizer.cleanup()
                except Exception as e:
                    logging.error(f"Error cleaning up visualizer: {e}")
            self.visualizer = None

        self.visualizer_name = visualizer_name
        visualizer_class = self.visualizer_manager.get_visualizer_class(visualizer_name)
        
        if visualizer_class:
            try:
                # Create visualizer instance
                self.visualizer = visualizer_class()
                self._needs_init_and_resize = True
                self._gl_initialized = False
                logging.debug(f"Created visualizer instance: {visualizer_name}")
                
                # If we already have an FBO, mark for initialization
                if self.fbo and self.fbo.isValid():
                    self._needs_init_and_resize = True
                    
            except Exception as e:
                logging.error(f"Error creating visualizer {visualizer_name}: {e}")
                self.visualizer = None
        else:
            logging.error(f"Visualizer class not found: {visualizer_name}")

    def paint(self):
        if not self.visualizer or not self.fbo:
            logging.debug("Deck has no visualizer or FBO, skipping paint")
            return
            
        try:
            # Bind to framebuffer
            if not self.fbo.bind():
                logging.error("Failed to bind framebuffer")
                return
            
            # Initialize if needed
            if self._needs_init_and_resize:
                logging.debug(f"Initializing visualizer: {self.visualizer_name}")
                
                # Set viewport first
                glViewport(0, 0, self.size.width(), self.size.height())
                
                # Initialize OpenGL state for visualizer
                if hasattr(self.visualizer, 'initializeGL'):
                    try:
                        self.visualizer.initializeGL()
                        logging.debug(f"Visualizer {self.visualizer_name} initializeGL completed")
                    except Exception as e:
                        logging.error(f"Error in visualizer initializeGL: {e}")
                        self.fbo.release()
                        return
                
                # Resize visualizer
                if hasattr(self.visualizer, 'resizeGL'):
                    try:
                        self.visualizer.resizeGL(self.size.width(), self.size.height())
                        logging.debug(f"Visualizer {self.visualizer_name} resized to {self.size.width()}x{self.size.height()}")
                    except Exception as e:
                        logging.error(f"Error in visualizer resizeGL: {e}")
                
                self._needs_init_and_resize = False
                self._gl_initialized = True
                logging.debug(f"Visualizer {self.visualizer_name} initialization completed")

            # Set viewport and clear with transparent background
            glViewport(0, 0, self.size.width(), self.size.height())
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # Paint the visualizer
            if hasattr(self.visualizer, 'paintGL') and self._gl_initialized:
                try:
                    self.visualizer.paintGL()
                except Exception as e:
                    logging.error(f"Error in visualizer paintGL: {e}")
            
            # Release framebuffer
            self.fbo.release()
            
        except Exception as e:
            logging.error(f"Error painting deck {self.visualizer_name}: {e}")
            if self.fbo:
                self.fbo.release()

    def resize(self, size):
        if self.size == size and self.fbo and self.fbo.isValid():
            return
            
        logging.debug(f"Resizing deck to: {size.width()}x{size.height()}")
        self.size = size
        self.recreate_fbo()
        
        # Mark for reinitialization if we have a visualizer
        if self.visualizer:
            self._needs_init_and_resize = True

    def recreate_fbo(self):
        """Recreate the framebuffer object with the current size"""
        try:
            # Clean up old FBO
            if self.fbo:
                self.fbo.release()
                del self.fbo
                self.fbo = None
                
            # Create new FBO only if size is valid
            if self.size.width() > 0 and self.size.height() > 0:
                self.fbo = QOpenGLFramebufferObject(
                    self.size, 
                    QOpenGLFramebufferObject.Attachment.CombinedDepthStencil
                )
                
                if not self.fbo.isValid():
                    logging.error(f"Failed to create valid framebuffer object {self.size.width()}x{self.size.height()}")
                    self.fbo = None
                else:
                    logging.debug(f"Created FBO: {self.size.width()}x{self.size.height()}")
            else:
                logging.error(f"Invalid size for FBO: {self.size.width()}x{self.size.height()}")
                
        except Exception as e:
            logging.error(f"Error recreating FBO: {e}")
            self.fbo = None

    def get_texture(self):
        """Return the texture ID of the framebuffer"""
        if self.fbo and self.fbo.isValid():
            return self.fbo.texture()
        return 0

    def get_controls(self):
        """Get available controls from the current visualizer"""
        if self.visualizer and hasattr(self.visualizer, 'get_controls'):
            try:
                controls = self.visualizer.get_controls()
                logging.debug(f"Got controls from {self.visualizer_name}: {list(controls.keys()) if controls else 'None'}")
                return controls
            except Exception as e:
                logging.error(f"Error getting controls from visualizer: {e}")
        return {}

    def update_control(self, name, value):
        """Update a control parameter on the current visualizer"""
        if self.visualizer and hasattr(self.visualizer, 'update_control'):
            try:
                self.visualizer.update_control(name, value)
                logging.debug(f"Updated control {name} to {value} on {self.visualizer_name}")
            except Exception as e:
                logging.error(f"Error updating control {name}: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        if self.visualizer and hasattr(self.visualizer, 'cleanup'):
            try:
                self.visualizer.cleanup()
            except Exception as e:
                logging.error(f"Error cleaning up visualizer: {e}")
        
        if self.fbo:
            self.fbo.release()
            del self.fbo
            self.fbo = None