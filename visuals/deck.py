import logging
import time
from PyQt6.QtOpenGL import QOpenGLFramebufferObject
from PyQt6.QtCore import QSize
from OpenGL.GL import *

class Deck:
    def __init__(self, visualizer_manager):
        self.visualizer_manager = visualizer_manager
        self.visualizer = None
        self.fbo = None
        self.visualizer_name = None
        self.size = QSize(800, 600)
        self._needs_init = True
        self._gl_initialized = False
        self._frame_count = 0
        
        logging.debug(f"🎮 Deck initialized with size {self.size.width()}x{self.size.height()}")

    def set_visualizer(self, visualizer_name):
        """Set a new visualizer for this deck"""
        logging.debug(f"🎨 Setting deck visualizer to: {visualizer_name}")
        
        # Clean up old visualizer
        if self.visualizer:
            logging.debug(f"Cleaning up existing visualizer: {self.visualizer_name}")
            if hasattr(self.visualizer, 'cleanup'):
                try:
                    self.visualizer.cleanup()
                    logging.debug(f"✅ Cleaned up old visualizer")
                except Exception as e:
                    logging.error(f"❌ Error cleaning up visualizer: {e}")
            self.visualizer = None
            self._gl_initialized = False

        self.visualizer_name = visualizer_name
        visualizer_class = self.visualizer_manager.get_visualizer_class(visualizer_name)
        
        if visualizer_class:
            try:
                # Create visualizer instance
                self.visualizer = visualizer_class()
                self._needs_init = True
                self._gl_initialized = False
                logging.debug(f"✅ Created visualizer instance: {visualizer_name}")
                
                # If we have a valid FBO, initialize the visualizer immediately
                if self.fbo and self.fbo.isValid():
                    logging.debug(f"FBO valid, attempting immediate initialization for {visualizer_name}")
                    self._initialize_visualizer()
                else:
                    logging.debug(f"FBO not valid or not created yet for {visualizer_name}, will initialize later")
                    
            except Exception as e:
                logging.error(f"❌ Error creating visualizer {visualizer_name}: {e}")
                import traceback
                traceback.print_exc()
                self.visualizer = None
        else:
            logging.error(f"❌ Visualizer class not found: {visualizer_name}")

    def _initialize_visualizer(self):
        """Initialize the visualizer with OpenGL context"""
        if not self.visualizer or not self.fbo or not self.fbo.isValid():
            logging.debug(f"Skipping _initialize_visualizer: visualizer={self.visualizer is not None}, fbo_valid={self.fbo and self.fbo.isValid()}")
            return False
            
        try:
            logging.debug(f"🔧 Initializing visualizer: {self.visualizer_name}")
            
            # Bind FBO to ensure we have GL context
            if not self.fbo.bind():
                logging.error("❌ Failed to bind FBO for initialization")
                return False
            
            # Set viewport
            glViewport(0, 0, self.size.width(), self.size.height())
            
            # Initialize visualizer
            if hasattr(self.visualizer, 'initializeGL'):
                logging.debug(f"Calling initializeGL on {self.visualizer_name}")
                self.visualizer.initializeGL()
                logging.debug(f"✅ Called initializeGL on {self.visualizer_name}")
            
            # Resize visualizer
            if hasattr(self.visualizer, 'resizeGL'):
                logging.debug(f"Calling resizeGL on {self.visualizer_name}")
                self.visualizer.resizeGL(self.size.width(), self.size.height())
                logging.debug(f"✅ Called resizeGL on {self.visualizer_name}")
            
            self._needs_init = False
            self._gl_initialized = True
            
            # Do a test render to verify it works
            self._test_render()
            
            self.fbo.release()
            
            logging.debug(f"✅ Visualizer {self.visualizer_name} initialized successfully")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error initializing visualizer {self.visualizer_name}: {e}")
            import traceback
            traceback.print_exc()
            self.fbo.release()
            return False

    def _test_render(self):
        """Do a test render to verify the visualizer works"""
        try:
            logging.debug(f"Performing test render for {self.visualizer_name}")
            # Clear with a test color
            glClearColor(0.1, 0.0, 0.1, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # Try to paint the visualizer
            if hasattr(self.visualizer, 'paintGL'):
                self.visualizer.paintGL()
                logging.debug(f"✅ Test render successful for {self.visualizer_name}")
            
        except Exception as e:
            logging.error(f"❌ Test render failed for {self.visualizer_name}: {e}")

    def paint(self):
        """Render the visualizer to the framebuffer"""
        if not self.visualizer:
            logging.debug(f"Deck has no visualizer, skipping paint")
            return
            
        if not self.fbo or not self.fbo.isValid():
            logging.debug(f"Deck has no valid FBO, skipping paint")
            return
            
        try:
            # Bind to framebuffer
            if not self.fbo.bind():
                logging.error("❌ Failed to bind framebuffer")
                return
            
            # Initialize if needed
            if self._needs_init and not self._gl_initialized:
                logging.debug(f"Visualizer {self.visualizer_name} needs initialization. Attempting now.")
                if not self._initialize_visualizer():
                    logging.error(f"❌ Failed to initialize visualizer {self.visualizer_name} during paint.")
                    self.fbo.release()
                    return
            
            # Set viewport
            glViewport(0, 0, self.size.width(), self.size.height())
            
            # Clear with transparent black (for proper mixing)
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # Paint the visualizer
            if self._gl_initialized and hasattr(self.visualizer, 'paintGL'):
                try:
                    self.visualizer.paintGL()
                    
                    # Log occasionally to show it's working
                    self._frame_count += 1
                    if self._frame_count % 60 == 0:  # Every ~1 second at 60fps
                        logging.debug(f"🎬 Deck rendering {self.visualizer_name} - Frame {self._frame_count}")
                        
                except Exception as e:
                    logging.error(f"❌ Error in visualizer {self.visualizer_name} paintGL: {e}")
                    # Don't crash, just clear to a color
                    glClearColor(0.2, 0.0, 0.0, 1.0)
                    glClear(GL_COLOR_BUFFER_BIT)
            else:
                logging.debug(f"Visualizer {self.visualizer_name} not GL initialized or no paintGL. Drawing test pattern.")
                # No visualizer ready, show a test pattern
                self._draw_test_pattern()
            
            # Release framebuffer
            self.fbo.release()
            
        except Exception as e:
            logging.error(f"❌ Error painting deck: {e}")
            import traceback
            traceback.print_exc()
            if self.fbo:
                self.fbo.release()

    def _draw_test_pattern(self):
        """Draw a test pattern when no visualizer is available"""
        try:
            # Animated color based on time
            t = time.time()
            r = 0.5 + 0.5 * abs(math.sin(t))
            g = 0.5 + 0.5 * abs(math.sin(t + 2.094))
            b = 0.5 + 0.5 * abs(math.sin(t + 4.189))
            
            # Just clear to an animated color - don't use legacy OpenGL
            glClearColor(r * 0.3, g * 0.3, b * 0.3, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
        except Exception as e:
            logging.debug(f"Test pattern error: {e}")
            # If even that fails, just clear to a solid color
            glClearColor(0.1, 0.1, 0.2, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def resize(self, size):
        """Resize the deck and recreate FBO if needed"""
        if self.size == size and self.fbo and self.fbo.isValid():
            logging.debug(f"Deck already at size {size.width()}x{size.height()} and FBO valid. Skipping resize.")
            return
            
        logging.debug(f"📐 Resizing deck from {self.size.width()}x{self.size.height()} to {size.width()}x{size.height()}")
        self.size = size
        self.recreate_fbo()
        
        # Reinitialize visualizer with new size
        if self.visualizer and self.fbo and self.fbo.isValid():
            try:
                logging.debug(f"Re-initializing visualizer {self.visualizer_name} after resize.")
                if self.fbo.bind():
                    if hasattr(self.visualizer, 'resizeGL'):
                        self.visualizer.resizeGL(size.width(), size.height())
                        logging.debug(f"✅ Resized visualizer to {size.width()}x{size.height()}")
                    self.fbo.release()
            except Exception as e:
                logging.error(f"❌ Error resizing visualizer: {e}")

    def recreate_fbo(self):
        """Recreate the framebuffer object with the current size"""
        try:
            logging.debug(f"Attempting to recreate FBO for size {self.size.width()}x{self.size.height()}")
            # Clean up old FBO
            if self.fbo:
                logging.debug(f"Releasing old FBO: {self.fbo.texture()}")
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
                    logging.error(f"❌ Failed to create valid FBO for {self.size.width()}x{self.size.height()}")
                    self.fbo = None
                else:
                    logging.debug(f"✅ Created FBO: {self.size.width()}x{self.size.height()}, Texture ID: {self.fbo.texture()}")
                    
                    # Initialize visualizer if we have one
                    if self.visualizer and not self._gl_initialized:
                        logging.debug(f"Visualizer {self.visualizer_name} exists and not GL initialized. Calling _initialize_visualizer.")
                        self._initialize_visualizer()
            else:
                logging.error(f"❌ Invalid size for FBO: {self.size.width()}x{self.size.height()}")
                
        except Exception as e:
            logging.error(f"❌ Error recreating FBO: {e}")
            import traceback
            traceback.print_exc()
            self.fbo = None

    def get_texture(self):
        """Return the texture ID of the framebuffer"""
        if self.fbo and self.fbo.isValid():
            texture_id = self.fbo.texture()
            logging.debug(f"Returning FBO texture ID: {texture_id} for visualizer {self.visualizer_name}")
            if texture_id > 0:
                return texture_id
            else:
                logging.warning(f"⚠️ FBO has invalid texture ID: {texture_id} for visualizer {self.visualizer_name}")
        else:
            logging.debug(f"No valid FBO for texture for visualizer {self.visualizer_name}")
        return 0

    def get_controls(self):
        """Get available controls from the current visualizer"""
        if self.visualizer and hasattr(self.visualizer, 'get_controls'):
            try:
                controls = self.visualizer.get_controls()
                logging.debug(f"📋 Got controls from {self.visualizer_name}: {list(controls.keys()) if controls else 'None'}")
                return controls
            except Exception as e:
                logging.error(f"❌ Error getting controls: {e}")
        return {}

    def update_control(self, name, value):
        """Update a control parameter on the current visualizer"""
        if self.visualizer and hasattr(self.visualizer, 'update_control'):
            try:
                # Ensure OpenGL context is current before updating visualizer control
                if self.fbo and self.fbo.isValid():
                    self.fbo.bind()
                    self.visualizer.update_control(name, value)
                    self.fbo.release()
                    logging.debug(f"🎛️ Updated {self.visualizer_name}.{name} = {value}")
                else:
                    logging.warning(f"⚠️ Cannot update control {name} for {self.visualizer_name}: FBO not valid.")
            except Exception as e:
                logging.error(f"❌ Error updating control {name}: {e}")

    def get_current_visualizer_name(self):
        """Get the name of the current visualizer"""
        return self.visualizer_name or "None"

    def cleanup(self):
        """Clean up resources"""
        logging.debug(f"🧹 Cleaning up deck")
        
        if self.visualizer and hasattr(self.visualizer, 'cleanup'):
            try:
                self.visualizer.cleanup()
            except Exception as e:
                logging.error(f"❌ Error cleaning up visualizer: {e}")
        
        if self.fbo:
            logging.debug(f"Releasing FBO: {self.fbo.texture()}")
            self.fbo.release()
            del self.fbo
            self.fbo = None

# Add missing import at the top
import math