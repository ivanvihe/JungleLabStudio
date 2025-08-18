# visuals/deck.py - FIXED TEXTURE BINDING ISSUES
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
        use_moderngl=None,  # Changed to None for auto-detection
        use_post=False,
        audio_analyzer=None,
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

        # Audio analyzer reference
        self.audio_analyzer = audio_analyzer

        # Backend selection logic - FIXED
        if use_moderngl is None:
            # Auto-detect from settings or environment
            try:
                from utils.settings_manager import SettingsManager
                settings = SettingsManager()
                backend_setting = settings.get_setting("visual_settings.backend", "OpenGL")
                use_moderngl = (backend_setting == "ModernGL")
            except:
                use_moderngl = os.getenv("USE_MODERNGL") == "1"

        self.use_moderngl = use_moderngl
        
        # Create backend
        try:
            if use_moderngl:
                logging.info(f"🎮 Deck {deck_id}: Creating ModernGL backend with GPU {gpu_index}")
                self.backend = ModernGLBackend(device_index=gpu_index)
            else:
                logging.info(f"🎮 Deck {deck_id}: Creating OpenGL backend")
                self.backend = GLBackend()
        except Exception as e:
            logging.error(f"❌ Deck {deck_id}: Failed to create backend: {e}")
            # Fallback to OpenGL
            logging.info(f"🔄 Deck {deck_id}: Falling back to OpenGL backend")
            self.backend = GLBackend()
            self.use_moderngl = False
            
        self.use_post = use_post

        logging.info(f"🎮 Deck {deck_id} initialized with size {self.size.width()}x{self.size.height()}, Backend: {'ModernGL' if self.use_moderngl else 'OpenGL'}")

    def _check_gl_context(self):
        """Check if OpenGL context is valid"""
        context = QOpenGLContext.currentContext()
        return context is not None

    def _clear_gl_errors(self):
        """Clear any existing OpenGL errors"""
        error_count = 0
        while glGetError() != GL_NO_ERROR:
            error_count += 1
            if error_count > 10:  # Prevent infinite loop
                break
        if error_count > 0:
            logging.debug(f"Deck {self.deck_id}: Cleared {error_count} GL errors")

    def _recreate_fbo(self):
        """Recreate the framebuffer object with the current size - FIXED"""
        try:
            # Check for valid context
            if not self._check_gl_context():
                logging.debug(f"Deck {self.deck_id}: No context for FBO creation")
                return
            
            # Clear any existing errors before we start
            self._clear_gl_errors()
            
            # Clean up old FBO
            if self.fbo:
                if self.fbo.isBound():
                    self.fbo.release()
                del self.fbo
                self.fbo = None
                
            # Create new FBO only if size is valid
            if self.size.width() > 0 and self.size.height() > 0:
                # Create FBO format with reduced multisampling for compatibility
                fbo_format = QOpenGLFramebufferObjectFormat()
                fbo_format.setAttachment(QOpenGLFramebufferObject.Attachment.CombinedDepthStencil)
                
                # Start with no multisampling and try to enable it if supported
                fbo_format.setSamples(0)

                # Create FBO
                self.fbo = QOpenGLFramebufferObject(self.size, fbo_format)

                if not self.fbo.isValid():
                    logging.error(f"❌ Deck {self.deck_id}: Failed to create valid FBO")
                    self.fbo = None
                    return

                # Get texture ID BEFORE attempting to modify it
                tex_id = self.fbo.texture()
                
                logging.debug(
                    f"✅ Deck {self.deck_id}: Created FBO {self.size.width()}x{self.size.height()}, Texture: {tex_id}"
                )
                
                # FIXED: Only apply texture filtering if we have a valid texture ID and context
                if tex_id and tex_id > 0 and self._check_gl_context():
                    try:
                        # Clear errors before texture operations
                        self._clear_gl_errors()
                        
                        # Check if texture actually exists
                        if glIsTexture(tex_id):
                            # Save current texture binding
                            current_texture = glGetIntegerv(GL_TEXTURE_BINDING_2D)
                            
                            # Bind our texture
                            glBindTexture(GL_TEXTURE_2D, tex_id)
                            
                            # Check for errors after binding
                            error = glGetError()
                            if error == GL_NO_ERROR:
                                # Apply texture parameters
                                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
                                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
                                
                                # Check for errors after setting parameters
                                error = glGetError()
                                if error == GL_NO_ERROR:
                                    logging.debug(f"✅ Deck {self.deck_id}: Applied texture filtering to FBO texture {tex_id}")
                                else:
                                    logging.warning(f"⚠️ Deck {self.deck_id}: Error setting texture parameters: {error}")
                            else:
                                logging.warning(f"⚠️ Deck {self.deck_id}: Error binding texture {tex_id}: {error}")
                            
                            # Restore previous texture binding
                            glBindTexture(GL_TEXTURE_2D, current_texture)
                        else:
                            logging.warning(f"⚠️ Deck {self.deck_id}: Texture {tex_id} is not a valid GL texture")
                            
                    except Exception as tex_e:
                        logging.error(f"❌ Deck {self.deck_id}: Exception during texture filtering: {tex_e}")
                        # Clear any errors that might have been set
                        self._clear_gl_errors()
                else:
                    if tex_id <= 0:
                        logging.warning(f"⚠️ Deck {self.deck_id}: Invalid texture ID: {tex_id}")
                    if not self._check_gl_context():
                        logging.warning(f"⚠️ Deck {self.deck_id}: No OpenGL context for texture operations")
                
                self._fbo_dirty = True
                    
        except Exception as e:
            logging.error(f"❌ Deck {self.deck_id}: Error recreating FBO: {e}")
            import traceback
            traceback.print_exc()
            self.fbo = None
            # Clear any errors that might have been set
            self._clear_gl_errors()

    def get_texture(self):
        """Return the texture ID of the framebuffer - FIXED"""
        with QMutexLocker(self._mutex):
            # Make sure we have a valid context
            if not self._check_gl_context():
                logging.debug(f"Deck {self.deck_id}: No GL context for get_texture")
                return 0
            
            # Make sure we have a valid FBO
            if not self.fbo or not self.fbo.isValid():
                # Try to recreate the FBO when invalid
                logging.debug(f"Deck {self.deck_id}: FBO invalid, trying to recreate")
                self._recreate_fbo()
                self._gl_initialized = False

            # Ensure the framebuffer has the latest rendering
            if self._fbo_dirty and self.fbo and self.fbo.isValid():
                # Only render if we have time budget
                current_time = time.time()
                if current_time - self._last_render_time >= self._render_interval:
                    self.render_to_fbo()

            if self.fbo and self.fbo.isValid():
                tex_id = self.fbo.texture()
                
                # Validate texture ID before returning it
                if tex_id and tex_id > 0:
                    # Additional validation: check if texture exists in OpenGL
                    if glIsTexture(tex_id):
                        return tex_id
                    else:
                        logging.debug(f"Deck {self.deck_id}: FBO texture {tex_id} is not a valid GL texture")
                        return 0
                else:
                    logging.debug(f"Deck {self.deck_id}: FBO valid but texture ID is {tex_id}")
                    return 0

            return 0

    # ... (rest of the methods remain the same as in the previous version)
    
    def ensure_fbo(self):
        """Ensure we have a valid FBO"""
        if not self.fbo or not self.fbo.isValid():
            self._recreate_fbo()
        return self.fbo and self.fbo.isValid()

    def set_gpu_index(self, index: int, backend_type: str = None) -> None:
        """Update GPU index and recreate backend context."""
        self.gpu_index = index
        
        # Update backend type if provided
        if backend_type:
            use_moderngl = (backend_type == "ModernGL")
            if use_moderngl != self.use_moderngl:
                self.use_moderngl = use_moderngl
                # Recreate backend with new type
                try:
                    if use_moderngl:
                        logging.info(f"🔄 Deck {self.deck_id}: Switching to ModernGL backend")
                        self.backend = ModernGLBackend(device_index=index)
                    else:
                        logging.info(f"🔄 Deck {self.deck_id}: Switching to OpenGL backend")
                        self.backend = GLBackend()
                except Exception as e:
                    logging.error(f"❌ Deck {self.deck_id}: Failed to switch backend: {e}")
                    # Keep current backend
                    return
        
        # Update GPU index for ModernGL backend
        if isinstance(self.backend, ModernGLBackend):
            try:
                self.backend = ModernGLBackend(device_index=index)
                logging.info(f"🎮 Deck {self.deck_id}: ModernGL backend updated to GPU {index}")
            except Exception as e:
                logging.error(f"❌ Deck {self.deck_id}: Failed to update ModernGL backend: {e}")
                
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

                    # Pass audio analyzer to visualizer if supported
                    if self.audio_analyzer and hasattr(self.current_visualizer, "set_audio_analyzer"):
                        self.current_visualizer.set_audio_analyzer(self.audio_analyzer)

                    # Apply saved visual properties
                    try:
                        from utils.visual_properties import load_visual_properties
                        props = load_visual_properties(visualizer_name)
                        for pname, pval in props.items():
                            try:
                                if hasattr(self.current_visualizer, "update_control"):
                                    self.current_visualizer.update_control(pname, pval)
                            except Exception as e:
                                logging.error(f"Error applying property {pname} for {visualizer_name}: {e}")
                    except Exception as e:
                        logging.error(f"Error loading visual properties for {visualizer_name}: {e}")

                    # Update controls cache after applying properties
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
                if hasattr(self.current_visualizer, 'set_audio_analyzer'):
                    self.current_visualizer.set_audio_analyzer(None)
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
            self._clear_gl_errors()

            # Ensure backend context
            self.backend.ensure_context()

            # Set viewport for FBO
            self.backend.set_viewport(0, 0, self.size.width(), self.size.height())

            # Log GL information once
            if self.gl_info is None:
                try:
                    if isinstance(self.backend, ModernGLBackend) and getattr(self.backend, 'ctx', None):
                        ctx_info = self.backend.ctx.info
                        self.gl_info = {
                            'vendor': ctx_info.get('GL_VENDOR'),
                            'renderer': ctx_info.get('GL_RENDERER'),
                            'version': ctx_info.get('GL_VERSION')
                        }
                    else:
                        self.gl_info = OpenGLSafety.get_gl_info()
                    
                    renderer = (self.gl_info.get('renderer') or '').lower()
                    logging.info(f"🎮 Deck {self.deck_id}: GPU Renderer: {self.gl_info.get('renderer')}")
                    
                    if 'llvmpipe' in renderer or 'software' in renderer:
                        logging.warning(
                            f"Deck {self.deck_id}: Software renderer detected ({self.gl_info.get('renderer')})"
                        )
                except Exception as info_e:
                    logging.error(f"Deck {self.deck_id}: Error obtaining GL info: {info_e}")

            # Initialize visualizer with proper parameters
            if hasattr(self.current_visualizer, 'initializeGL'):
                try:
                    # Try with backend first
                    if hasattr(self.current_visualizer.initializeGL, '__code__') and self.current_visualizer.initializeGL.__code__.co_argcount > 1:
                        self.current_visualizer.initializeGL(self.backend)
                    else:
                        self.current_visualizer.initializeGL()
                except Exception as init_e:
                    logging.error(f"❌ Deck {self.deck_id}: Error in initializeGL: {init_e}")
                    # Try without backend
                    try:
                        self.current_visualizer.initializeGL()
                    except Exception as fallback_e:
                        logging.error(f"❌ Deck {self.deck_id}: Fallback initializeGL also failed: {fallback_e}")
                        return False

            # Resize visualizer
            if hasattr(self.current_visualizer, 'resizeGL'):
                try:
                    # Try with backend and size parameters
                    if hasattr(self.current_visualizer.resizeGL, '__code__') and self.current_visualizer.resizeGL.__code__.co_argcount > 3:
                        self.current_visualizer.resizeGL(
                            self.size.width(), self.size.height(), self.backend
                        )
                    else:
                        self.current_visualizer.resizeGL(
                            self.size.width(), self.size.height()
                        )
                except Exception as resize_e:
                    logging.error(f"❌ Deck {self.deck_id}: Error in resizeGL: {resize_e}")
                    # Try basic resize
                    try:
                        self.current_visualizer.resizeGL(self.size.width(), self.size.height())
                    except Exception as fallback_resize_e:
                        logging.error(f"❌ Deck {self.deck_id}: Fallback resizeGL also failed: {fallback_resize_e}")
            
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

    # Continue with the rest of the methods from the previous fixed version...
    # (render_to_fbo, paint, _render_fallback, resize, get_controls, etc.)
    
    def render_to_fbo(self):
        """Render the visualizer to the FBO"""
        with QMutexLocker(self._mutex):
            # Ensure we have an FBO
            if not self.ensure_fbo():
                logging.debug(f"Deck {self.deck_id}: No valid FBO available")
                return False
                
            # Check if we have a valid context
            if not self._check_gl_context():
                logging.debug(f"Deck {self.deck_id}: No OpenGL context available")
                return False
                
            try:
                # Clear any errors before we start
                self._clear_gl_errors()
                
                # Ensure backend context is ready
                self.backend.ensure_context()

                # Save current FBO binding
                previous_fbo = glGetIntegerv(GL_FRAMEBUFFER_BINDING)

                # Bind our FBO
                if not self.fbo.bind():
                    logging.error(f"❌ Deck {self.deck_id}: Failed to bind FBO")
                    return False

                # Set viewport and begin target
                self.backend.begin_target((self.size.width(), self.size.height()))

                # Clear the FBO with black background
                self.backend.clear(0.0, 0.0, 0.0, 1.0)
                
                if self.current_visualizer:
                    # Initialize if needed
                    if not self._gl_initialized:
                        if not self._initialize_visualizer_in_fbo():
                            self._render_fallback()
                            self.fbo.release()
                            # Restore previous FBO safely
                            OpenGLSafety.safe_bind_framebuffer(GL_FRAMEBUFFER, previous_fbo)
                            return False
                    
                    # Render the visualizer
                    if hasattr(self.current_visualizer, 'paintGL'):
                        try:
                            current_time = time.time()
                            
                            # Determine paintGL signature and call appropriately
                            paintgl_func = self.current_visualizer.paintGL
                            argcount = paintgl_func.__code__.co_argcount if hasattr(paintgl_func, '__code__') else 1
                            
                            if argcount > 3:  # self, time, size, backend
                                self.current_visualizer.paintGL(
                                    current_time,
                                    (self.size.width(), self.size.height()),
                                    self.backend,
                                )
                            elif argcount > 2:  # self, time, size
                                self.current_visualizer.paintGL(
                                    current_time,
                                    (self.size.width(), self.size.height())
                                )
                            elif argcount > 1:  # self, time
                                self.current_visualizer.paintGL(current_time)
                            else:  # self only
                                self.current_visualizer.paintGL()

                            self._total_frames += 1
                            self._fps_frames += 1
                            
                            # Log frame info every 300 frames for debugging
                            if self._total_frames % 300 == 0:
                                logging.debug(
                                    f"🎬 Deck {self.deck_id}: {self.current_visualizer_name} - Frame {self._total_frames}"
                                )

                        except Exception as e:
                            current_time = time.time()
                            if current_time - self._last_error_log > 5.0:
                                logging.error(f"❌ Deck {self.deck_id}: Error in paintGL: {e}")
                                import traceback
                                traceback.print_exc()
                                self._last_error_log = current_time
                            self._render_fallback()
                        finally:
                            # Reset GL state that might be changed by visualizers
                            try:
                                glUseProgram(0)
                                glDisable(GL_DEPTH_TEST)
                                glDisable(GL_CULL_FACE)
                                glDepthMask(GL_TRUE)
                                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
                                # Clear any GL errors
                                self._clear_gl_errors()
                            except Exception:
                                pass
                else:
                    # No visualizer - render black (already cleared above)
                    logging.debug(f"Deck {self.deck_id}: No visualizer, rendering black")
                
                # Apply post-processing if enabled
                if self.use_post and isinstance(self.backend, ModernGLBackend):
                    # TODO: implement post-processing effects (FXAA/Bloom)
                    pass

                # End target
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

                # Restore previous FBO binding safely
                OpenGLSafety.safe_bind_framebuffer(GL_FRAMEBUFFER, previous_fbo)
                
                self._fbo_dirty = False
                return True
                
            except Exception as e:
                logging.error(f"❌ Deck {self.deck_id}: Error rendering to FBO: {e}")
                import traceback
                traceback.print_exc()
                if self.fbo and self.fbo.isBound():
                    self.fbo.release()
                # Clear any errors
                self._clear_gl_errors()
                return False

    def paint(self):
        """Main paint method - ensures FBO is rendered"""
        # Rate limiting
        current_time = time.time()
        if current_time - self._last_render_time < self._render_interval:
            return
        self._last_render_time = current_time
        
        # Render to FBO
        result = self.render_to_fbo()
        if not result:
            logging.debug(f"Deck {self.deck_id}: render_to_fbo failed")

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
                
            logging.debug(f"📏 Deck {self.deck_id}: Resizing from {self.size.width()}x{self.size.height()} to {size.width()}x{size.height()}")
            self.size = size
            self._recreate_fbo()
            
            # Mark as needing re-initialization
            if self.current_visualizer:
                self._gl_initialized = False
                self._fbo_dirty = True

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
                'gpu_renderer': (self.gl_info or {}).get('renderer'),
                'backend_type': 'ModernGL' if self.use_moderngl else 'OpenGL',
                'gpu_index': self.gpu_index
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
            
            # Clean up backend
            if hasattr(self.backend, 'cleanup'):
                try:
                    self.backend.cleanup()
                except Exception as e:
                    logging.error(f"❌ Deck {self.deck_id}: Error cleaning up backend: {e}")
            
            # Clear controls
            self.controls = {}

            logging.debug(f"✅ Deck {self.deck_id}: Cleanup completed")