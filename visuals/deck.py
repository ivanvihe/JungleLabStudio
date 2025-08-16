# visuals/deck.py
import logging
import time
import math
import os
from PyQt6.QtOpenGL import QOpenGLFramebufferObject, QOpenGLFramebufferObjectFormat
from PyQt6.QtCore import QSize, QMutex, QMutexLocker
from PyQt6.QtGui import QOpenGLContext
from OpenGL.GL import *
from .render_backend import GLBackend, ModernGLBackend
from opengl_fixes import OpenGLSafety

class Deck:
    def __init__(
        self,
        visualizer_manager,
        deck_id="",
        gpu_index=0,
        use_moderngl=False,
        use_post=False,
    ):
        self.visualizer_manager = visualizer_manager
        self.deck_id = deck_id  # For debugging
        self.current_visualizer = None  # Renamed for clarity
        self.fbo = None
        self.current_visualizer_name = None  # Renamed for clarity
        self.size = QSize(800, 600)
        self.gpu_index = gpu_index
        
        # State tracking
        self._gl_initialized = False
        self._last_error_log = 0

        # Performance tracking
        self._total_frames = 0
        self._fps_frames = 0
        self._fps_start = time.time()
        self._fps = 0.0

        # GL info
        self.gl_info = None
        
        # Thread safety
        self._mutex = QMutex()
        
        # Render state
        self._last_render_time = 0
        self._render_interval = 1.0 / 60.0  # 60 FPS limit
        
        # Track if FBO has been rendered to
        self._fbo_dirty = True
        
        # Controls cache
        self.controls = {}

        use_moderngl = use_moderngl or os.getenv("USE_MODERNGL") == "1"
        self.backend = (
            ModernGLBackend(device_index=gpu_index)
            if use_moderngl
            else GLBackend()
        )
        self.use_post = use_post

        logging.debug(f"🎮 Deck {deck_id} initialized with size {self.size.width()}x{self.size.height()}")

    def ensure_fbo(self):
        """Ensure we have a valid FBO"""
        if not self.fbo or not self.fbo.isValid():
            self._recreate_fbo()
        return self.fbo and self.fbo.isValid()

    def set_gpu_index(self, index: int) -> None:
        """Update GPU index and recreate backend context."""
        self.gpu_index = index
        if isinstance(self.backend, ModernGLBackend):
            self.backend = ModernGLBackend(device_index=index)
            self._gl_initialized = False
            self._fbo_dirty = True
            self.gl_info = None

    def set_visualizer(self, visualizer_name):
        """Set a new visualizer for this deck"""
        with QMutexLocker(self._mutex):
            logging.info(f"🎨 Deck {self.deck_id}: Setting visualizer to {visualizer_name}")
            
            # Clean up old visualizer first
            self._cleanup_current_visualizer()
            
            # Set new visualizer
            self.current_visualizer_name = visualizer_name
            visualizer_class = self.visualizer_manager.get_visualizer_class(visualizer_name)
            
            if visualizer_class:
                try:
                    # Create visualizer instance
                    self.current_visualizer = visualizer_class()
                    self._gl_initialized = False
                    self._fbo_dirty = True
                    
                    # Update controls cache
                    self._update_controls_cache()
                    
                    logging.info(f"✅ Deck {self.deck_id}: Created visualizer instance: {visualizer_name}")
                    
                except Exception as e:
                    logging.error(f"❌ Deck {self.deck_id}: Error creating visualizer {visualizer_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    self.current_visualizer = None
                    self.controls = {}
            else:
                logging.error(f"❌ Deck {self.deck_id}: Visualizer class not found: {visualizer_name}")

    def clear_visualizer(self):
        """Clear the current visualizer and show nothing (black)"""
        with QMutexLocker(self._mutex):
            try:
                logging.info(f"🚫 Clearing visualizer for deck {self.deck_id}")
                
                # Cleanup current visualizer
                self._cleanup_current_visualizer()
                
                # Clear all references
                self.current_visualizer = None
                self.current_visualizer_name = None
                self.controls = {}
                self._gl_initialized = False
                self._fbo_dirty = True
                
                logging.info(f"✅ Deck {self.deck_id} visualizer cleared")
                
            except Exception as e:
                logging.error(f"❌ Error clearing visualizer for deck {self.deck_id}: {e}")

    def has_active_visualizer(self):
        """Check if deck has an active visualizer"""
        with QMutexLocker(self._mutex):
            return self.current_visualizer is not None

    def _cleanup_current_visualizer(self):
        """Clean up current visualizer"""
        if self.current_visualizer:
            logging.debug(f"🧹 Deck {self.deck_id}: Cleaning up visualizer: {self.current_visualizer_name}")
            try:
                if hasattr(self.current_visualizer, 'cleanup'):
                    self.current_visualizer.cleanup()
            except Exception as e:
                logging.error(f"❌ Deck {self.deck_id}: Error cleaning up visualizer: {e}")
            
            self.current_visualizer = None
            self._gl_initialized = False

    def _update_controls_cache(self):
        """Update the controls cache from current visualizer"""
        try:
            if self.current_visualizer and hasattr(self.current_visualizer, 'get_controls'):
                self.controls = self.current_visualizer.get_controls() or {}
                logging.debug(f"🎛️ Deck {self.deck_id}: Cached {len(self.controls)} controls")
            else:
                self.controls = {}
        except Exception as e:
            logging.error(f"❌ Deck {self.deck_id}: Error updating controls cache: {e}")
            self.controls = {}

    def _initialize_visualizer_in_fbo(self):
        """Initialize the visualizer within the FBO context"""
        if not self.current_visualizer:
            return False
            
        try:
            logging.debug(f"🔧 Deck {self.deck_id}: Initializing visualizer {self.current_visualizer_name} in FBO")
            
            # Clear any existing GL errors
            while glGetError() != GL_NO_ERROR:
                pass

            # Set viewport for FBO
            self.backend.set_viewport(0, 0, self.size.width(), self.size.height())

            # Log GL information once
            if self.gl_info is None:
                try:
                    self.backend.ensure_context()
                    if isinstance(self.backend, ModernGLBackend) and getattr(self.backend, 'ctx', None):
                        ctx_info = self.backend.ctx.info
                        self.gl_info = {
                            'vendor': ctx_info.get('GL_VENDOR'),
                            'renderer': ctx_info.get('GL_RENDERER'),
                            'version': ctx_info.get('GL_VERSION')
                        }
                    else:
                        self.gl_info = OpenGLSafety.get_gl_info()
                    OpenGLSafety.log_gl_info()
                    renderer = (self.gl_info.get('renderer') or '').lower()
                    if 'llvmpipe' in renderer or 'software' in renderer:
                        logging.warning(
                            f"Deck {self.deck_id}: Software renderer detected ({self.gl_info.get('renderer')})"
                        )
                except Exception as info_e:
                    logging.error(f"Deck {self.deck_id}: Error obtaining GL info: {info_e}")

            # Initialize visualizer
            if hasattr(self.current_visualizer, 'initializeGL'):
                try:
                    self.current_visualizer.initializeGL(self.backend)
                except TypeError:
                    self.current_visualizer.initializeGL()

            # Resize visualizer
            if hasattr(self.current_visualizer, 'resizeGL'):
                try:
                    self.current_visualizer.resizeGL(
                        self.size.width(), self.size.height(), self.backend
                    )
                except TypeError:
                    self.current_visualizer.resizeGL(
                        self.size.width(), self.size.height()
                    )
            
            self._gl_initialized = True
            
            # Update controls after initialization
            self._update_controls_cache()
            
            logging.info(f"✅ Deck {self.deck_id}: Visualizer {self.current_visualizer_name} initialized")
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
                self.backend.ensure_context()

                # Save current FBO binding
                previous_fbo = glGetIntegerv(GL_FRAMEBUFFER_BINDING)

                # Bind our FBO
                if not self.fbo.bind():
                    logging.error(f"❌ Deck {self.deck_id}: Failed to bind FBO")
                    return False

                self.backend.begin_target((self.size.width(), self.size.height()))

                # Clear the FBO
                self.backend.clear(0.0, 0.0, 0.0, 1.0)
                
                if self.current_visualizer:
                    # Initialize if needed
                    if not self._gl_initialized:
                        if not self._initialize_visualizer_in_fbo():
                            self._render_fallback()
                            self.fbo.release()
                            # Restore previous FBO
                            glBindFramebuffer(GL_FRAMEBUFFER, previous_fbo)
                            return False
                    
                    # Render the visualizer
                    if hasattr(self.current_visualizer, 'paintGL'):
                        try:
                            # Paint visualizer directly
                            try:
                                self.current_visualizer.paintGL(
                                    time.time(),
                                    (self.size.width(), self.size.height()),
                                    self.backend,
                                )
                            except TypeError:
                                self.current_visualizer.paintGL()

                            self._total_frames += 1
                            self._fps_frames += 1
                            if self._total_frames % 300 == 0:
                                logging.debug(
                                    f"🎬 Deck {self.deck_id}: {self.current_visualizer_name} - Frame {self._total_frames}"
                                )

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
                                glDepthMask(GL_TRUE)
                                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
                            except Exception:
                                pass
                else:
                    # No visualizer - render black (already cleared above)
                    pass
                
                if self.use_post and isinstance(self.backend, ModernGLBackend):
                    # TODO: implement post-processing effects (FXAA/Bloom)
                    pass

                self.backend.end_target()

                # Update FPS counters
                now = time.time()
                elapsed = now - self._fps_start
                if elapsed >= 1.0:
                    self._fps = self._fps_frames / elapsed
                    self._fps_frames = 0
                    self._fps_start = now

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
        """Render a fallback pattern when visualizer fails"""
        try:
            # Static dark pattern for failed visualizers
            if self.deck_id == "A":
                self.backend.clear(0.1, 0.0, 0.0, 1.0)  # Dark red
            else:
                self.backend.clear(0.0, 0.0, 0.1, 1.0)  # Dark blue
        except Exception:
            # Ultimate fallback - just black
            try:
                self.backend.clear(0.0, 0.0, 0.0, 1.0)
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
            if self.current_visualizer:
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
                # Enable multisampling for smoother visuals
                fbo_format.setSamples(4)

                # Create FBO
                self.fbo = QOpenGLFramebufferObject(self.size, fbo_format)

                if not self.fbo.isValid():
                    logging.error(f"❌ Deck {self.deck_id}: Failed to create valid FBO")
                    self.fbo = None
                else:
                    logging.debug(
                        f"✅ Deck {self.deck_id}: Created FBO {self.size.width()}x{self.size.height()}, Texture: {self.fbo.texture()}"
                    )
                    # Only apply filtering when not multisampled
                    if fbo_format.samples() <= 1:
                        glBindTexture(GL_TEXTURE_2D, self.fbo.texture())
                        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                        glBindTexture(GL_TEXTURE_2D, 0)
                    else:
                        logging.debug(
                            f"Deck {self.deck_id}: Multisampled FBO - skipping texture filtering"
                        )
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
            # Return cached controls for performance
            if self.controls:
                return self.controls.copy()
            
            # Fallback: get directly from visualizer if cache is empty
            if self.current_visualizer and hasattr(self.current_visualizer, 'get_controls'):
                try:
                    controls = self.current_visualizer.get_controls() or {}
                    self.controls = controls  # Update cache
                    return controls.copy()
                except Exception as e:
                    logging.error(f"❌ Deck {self.deck_id}: Error getting controls: {e}")
            
            return {}

    def update_control(self, name, value):
        """Update a control parameter on the current visualizer"""
        with QMutexLocker(self._mutex):
            if self.current_visualizer and hasattr(self.current_visualizer, 'update_control'):
                try:
                    self.current_visualizer.update_control(name, value)
                    self._fbo_dirty = True
                    
                    # Update cached control value
                    if name in self.controls:
                        self.controls[name]['value'] = value
                    
                    logging.debug(f"🎛️ Deck {self.deck_id}: Updated {name} = {value}")
                except Exception as e:
                    logging.error(f"❌ Deck {self.deck_id}: Error updating control {name}: {e}")

    def trigger_action(self, action_name):
        """Trigger a custom action on the current visualizer"""
        with QMutexLocker(self._mutex):
            if self.current_visualizer and hasattr(self.current_visualizer, 'trigger_action'):
                try:
                    self.current_visualizer.trigger_action(action_name)
                    self._fbo_dirty = True
                    logging.debug(f"🎬 Deck {self.deck_id}: Triggered action {action_name}")
                except Exception as e:
                    logging.error(f"❌ Deck {self.deck_id}: Error triggering action {action_name}: {e}")

    def get_current_visualizer_name(self):
        """Get the name of the current visualizer"""
        with QMutexLocker(self._mutex):
            return self.current_visualizer_name

    def is_ready(self):
        """Check if deck is ready for rendering"""
        with QMutexLocker(self._mutex):
            return self.fbo and self.fbo.isValid()

    def get_deck_info(self):
        """Get comprehensive deck information"""
        with QMutexLocker(self._mutex):
            return {
                'deck_id': self.deck_id,
                'has_visualizer': self.has_active_visualizer(),
                'visualizer_name': self.current_visualizer_name,
                'is_ready': self.is_ready(),
                'fbo_size': f"{self.size.width()}x{self.size.height()}",
                'frame_count': self._total_frames,
                'fps': round(self._fps, 1),
                'controls_count': len(self.controls),
                'gl_initialized': self._gl_initialized,
                'gpu_renderer': (self.gl_info or {}).get('renderer')
            }

    def force_refresh(self):
        """Force refresh of the visualizer (useful for parameter changes)"""
        with QMutexLocker(self._mutex):
            self._fbo_dirty = True
            if self.current_visualizer:
                # Update controls cache
                self._update_controls_cache()

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
            
            # Clear controls
            self.controls = {}

            logging.debug(f"✅ Deck {self.deck_id}: Cleanup completed")
