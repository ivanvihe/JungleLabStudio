# visuals/deck.py
import logging
import time
import math
from PyQt6.QtOpenGL import QOpenGLFramebufferObject, QOpenGLFramebufferObjectFormat
from PyQt6.QtCore import QSize, QMutex, QMutexLocker
from PyQt6.QtGui import QOpenGLContext
from OpenGL.GL import *

class Deck:
    def __init__(self, visualizer_manager, deck_id=""):
        self.visualizer_manager = visualizer_manager
        self.deck_id = deck_id  # For debugging
        self.visualizer = None
        self.fbo = None
        self.visualizer_name = None
        self.size = QSize(800, 600)
        
        # State tracking
        self._gl_initialized = False
        self._frame_count = 0
        self._last_error_log = 0
        
        # Thread safety
        self._mutex = QMutex()
        
        # Render state
        self._last_render_time = 0
        self._render_interval = 1.0 / 60.0  # 60 FPS limit
        
        # Track if FBO has been rendered to
        self._fbo_dirty = True
        
        logging.debug(f"🎮 Deck {deck_id} initialized with size {self.size.width()}x{self.size.height()}")

    def ensure_fbo(self):
        """Ensure we have a valid FBO"""
        if not self.fbo or not self.fbo.isValid():
            self._recreate_fbo()
        return self.fbo and self.fbo.isValid()

    def set_visualizer(self, visualizer_name):
        """Set a new visualizer for this deck"""
        with QMutexLocker(self._mutex):
            logging.info(f"🎨 Deck {self.deck_id}: Setting visualizer to {visualizer_name}")
            
            # Clean up old visualizer first
            self._cleanup_current_visualizer()
            
            # Set new visualizer
            self.visualizer_name = visualizer_name
            visualizer_class = self.visualizer_manager.get_visualizer_class(visualizer_name)
            
            if visualizer_class:
                try:
                    # Create visualizer instance
                    self.visualizer = visualizer_class()
                    self._gl_initialized = False
                    self._fbo_dirty = True
                    logging.info(f"✅ Deck {self.deck_id}: Created visualizer instance: {visualizer_name}")
                    
                except Exception as e:
                    logging.error(f"❌ Deck {self.deck_id}: Error creating visualizer {visualizer_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    self.visualizer = None
            else:
                logging.error(f"❌ Deck {self.deck_id}: Visualizer class not found: {visualizer_name}")

    def _cleanup_current_visualizer(self):
        """Clean up current visualizer"""
        if self.visualizer:
            logging.debug(f"Deck {self.deck_id}: Cleaning up visualizer: {self.visualizer_name}")
            try:
                if hasattr(self.visualizer, 'cleanup'):
                    self.visualizer.cleanup()
            except Exception as e:
                logging.error(f"❌ Deck {self.deck_id}: Error cleaning up visualizer: {e}")
            
            self.visualizer = None
            self._gl_initialized = False

    def _initialize_visualizer_in_fbo(self):
        """Initialize the visualizer within the FBO context"""
        if not self.visualizer:
            return False
            
        try:
            logging.debug(f"🔧 Deck {self.deck_id}: Initializing visualizer {self.visualizer_name} in FBO")
            
            # Clear any existing GL errors
            while glGetError() != GL_NO_ERROR:
                pass
            
            # Set viewport for FBO
            glViewport(0, 0, self.size.width(), self.size.height())
            
            # Initialize visualizer
            if hasattr(self.visualizer, 'initializeGL'):
                self.visualizer.initializeGL()
            
            # Resize visualizer
            if hasattr(self.visualizer, 'resizeGL'):
                self.visualizer.resizeGL(self.size.width(), self.size.height())
            
            self._gl_initialized = True
            logging.info(f"✅ Deck {self.deck_id}: Visualizer {self.visualizer_name} initialized")
            return True
            
        except Exception as e:
            logging.error(f"❌ Deck {self.deck_id}: Error initializing visualizer: {e}")
            import traceback
            traceback.print_exc()
            return False

    def render_to_fbo(self):
        """Render the visualizer to the FBO"""
        with QMutexLocker(self._mutex):
            # Ensure we have an FBO
            if not self.ensure_fbo():
                return False
                
            # Check if we have a valid context
            context = QOpenGLContext.currentContext()
            if not context:
                logging.debug(f"Deck {self.deck_id}: No OpenGL context available")
                return False
                
            try:
                # Save current FBO binding
                previous_fbo = glGetIntegerv(GL_FRAMEBUFFER_BINDING)
                
                # Bind our FBO
                if not self.fbo.bind():
                    logging.error(f"❌ Deck {self.deck_id}: Failed to bind FBO")
                    return False
                
                # Set viewport for our FBO
                glViewport(0, 0, self.size.width(), self.size.height())
                
                # Clear the FBO
                glClearColor(0.0, 0.0, 0.0, 1.0)
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                
                if self.visualizer:
                    # Initialize if needed
                    if not self._gl_initialized:
                        if not self._initialize_visualizer_in_fbo():
                            self._render_fallback()
                            self.fbo.release()
                            # Restore previous FBO
                            glBindFramebuffer(GL_FRAMEBUFFER, previous_fbo)
                            return False
                    
                    # Render the visualizer
                    if hasattr(self.visualizer, 'paintGL'):
                        try:
                            # Paint visualizer directly without deprecated state saving
                            self.visualizer.paintGL()

                            self._frame_count += 1
                            if self._frame_count % 300 == 0:
                                logging.debug(f"🎬 Deck {self.deck_id}: {self.visualizer_name} - Frame {self._frame_count}")

                        except Exception as e:
                            current_time = time.time()
                            if current_time - self._last_error_log > 5.0:
                                logging.error(f"❌ Deck {self.deck_id}: Error in paintGL: {e}")
                                self._last_error_log = current_time
                            self._render_fallback()
                        finally:
                            # Reset GL state changed by visualizers
                            try:
                                glUseProgram(0)
                                glDisable(GL_DEPTH_TEST)
                                glDisable(GL_CULL_FACE)
                            except Exception:
                                pass
                else:
                    self._render_fallback()
                
                # Release our FBO
                self.fbo.release()
                
                # Restore previous FBO binding
                glBindFramebuffer(GL_FRAMEBUFFER, previous_fbo)
                
                self._fbo_dirty = False
                return True
                
            except Exception as e:
                logging.error(f"❌ Deck {self.deck_id}: Error rendering to FBO: {e}")
                if self.fbo and self.fbo.isBound():
                    self.fbo.release()
                return False

    def paint(self):
        """Main paint method - ensures FBO is rendered"""
        # Rate limiting
        current_time = time.time()
        if current_time - self._last_render_time < self._render_interval:
            return
        self._last_render_time = current_time
        
        # Render to FBO
        self.render_to_fbo()

    def _render_fallback(self):
        """Render a fallback pattern"""
        try:
            # Animated gradient based on deck ID
            t = time.time()
            if self.deck_id == "A":
                r = 0.1 + 0.05 * abs(math.sin(t * 0.5))
                g = 0.2 + 0.1 * abs(math.sin(t * 0.7))
                b = 0.1
            else:
                r = 0.1
                g = 0.1 + 0.05 * abs(math.sin(t * 0.7))
                b = 0.2 + 0.1 * abs(math.sin(t * 0.5))
            
            glClearColor(r, g, b, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        except Exception:
            pass

    def resize(self, size):
        """Resize the deck and recreate FBO if needed"""
        with QMutexLocker(self._mutex):
            if self.size == size:
                return
                
            logging.debug(f"📐 Deck {self.deck_id}: Resizing from {self.size.width()}x{self.size.height()} to {size.width()}x{size.height()}")
            self.size = size
            self._recreate_fbo()
            
            # Mark as needing re-initialization
            if self.visualizer:
                self._gl_initialized = False
                self._fbo_dirty = True

    def _recreate_fbo(self):
        """Recreate the framebuffer object with the current size"""
        try:
            # Check for valid context
            context = QOpenGLContext.currentContext()
            if not context:
                logging.debug(f"Deck {self.deck_id}: No context for FBO creation")
                return
            
            # Clean up old FBO
            if self.fbo:
                if self.fbo.isBound():
                    self.fbo.release()
                del self.fbo
                self.fbo = None
                
            # Create new FBO only if size is valid
            if self.size.width() > 0 and self.size.height() > 0:
                # Create FBO format
                fbo_format = QOpenGLFramebufferObjectFormat()
                fbo_format.setAttachment(QOpenGLFramebufferObject.Attachment.CombinedDepthStencil)
                fbo_format.setSamples(0)  # No multisampling
                
                # Create FBO
                self.fbo = QOpenGLFramebufferObject(self.size, fbo_format)
                
                if not self.fbo.isValid():
                    logging.error(f"❌ Deck {self.deck_id}: Failed to create valid FBO")
                    self.fbo = None
                else:
                    logging.debug(f"✅ Deck {self.deck_id}: Created FBO {self.size.width()}x{self.size.height()}, Texture: {self.fbo.texture()}")
                    self._fbo_dirty = True
                    
        except Exception as e:
            logging.error(f"❌ Deck {self.deck_id}: Error recreating FBO: {e}")
            self.fbo = None

    def get_texture(self):
        """Return the texture ID of the framebuffer"""
        with QMutexLocker(self._mutex):
            # Make sure we have a valid FBO
            if not self.fbo or not self.fbo.isValid():
                # Try to recreate the FBO when invalid – this can happen
                # when the context wasn't ready during initialization.
                self._recreate_fbo()
                self._gl_initialized = False

            # Ensure the framebuffer has the latest rendering
            if self._fbo_dirty and self.fbo and self.fbo.isValid():
                self.render_to_fbo()

            if self.fbo and self.fbo.isValid():
                return self.fbo.texture()
            return 0

    def get_controls(self):
        """Get available controls from the current visualizer"""
        with QMutexLocker(self._mutex):
            if self.visualizer and hasattr(self.visualizer, 'get_controls'):
                try:
                    return self.visualizer.get_controls() or {}
                except Exception as e:
                    logging.error(f"❌ Deck {self.deck_id}: Error getting controls: {e}")
            return {}

    def update_control(self, name, value):
        """Update a control parameter on the current visualizer"""
        with QMutexLocker(self._mutex):
            if self.visualizer and hasattr(self.visualizer, 'update_control'):
                try:
                    self.visualizer.update_control(name, value)
                    self._fbo_dirty = True
                    logging.debug(f"🎛️ Deck {self.deck_id}: Updated {name} = {value}")
                except Exception as e:
                    logging.error(f"❌ Deck {self.deck_id}: Error updating control {name}: {e}")

    def get_current_visualizer_name(self):
        """Get the name of the current visualizer"""
        with QMutexLocker(self._mutex):
            return self.visualizer_name or "None"

    def is_ready(self):
        """Check if deck is ready for rendering"""
        with QMutexLocker(self._mutex):
            return self.fbo and self.fbo.isValid()

    def cleanup(self):
        """Clean up resources"""
        with QMutexLocker(self._mutex):
            logging.debug(f"🧹 Deck {self.deck_id}: Cleaning up")
            
            # Clean up visualizer
            self._cleanup_current_visualizer()
            
            # Clean up FBO
            if self.fbo:
                if self.fbo.isBound():
                    self.fbo.release()
                del self.fbo
                self.fbo = None