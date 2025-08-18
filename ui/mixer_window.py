# ui/mixer_window.py - FIXED VERSION
from opengl_fixes import init_opengl_debug
import logging
import numpy as np
import ctypes
import time
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSlot, pyqtSignal, QMutex, QMutexLocker
from PyQt6.QtGui import QOpenGLContext
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *

from visuals.deck import Deck
from opengl_fixes import OpenGLSafety


class MixerWindow(QMainWindow):
    # Custom signals for thread-safe communication
    signal_set_mix_value = pyqtSignal(int)
    signal_set_deck_visualizer = pyqtSignal(str, object)  # Changed to object to handle None
    signal_update_deck_control = pyqtSignal(str, str, object)
    signal_set_deck_opacity = pyqtSignal(str, float)
    signal_trigger_deck_action = pyqtSignal(str, str)
    exit_fullscreen = pyqtSignal()
    # Signal emitted after the OpenGL context is fully initialized
    gl_ready = pyqtSignal()

    def __init__(self, visualizer_manager, settings_manager=None, audio_analyzer=None):
        super().__init__()
        self.setWindowTitle("Audio Visualizer Pro - Main Output")
        self.setGeometry(100, 100, 800, 600)
        self.visualizer_manager = visualizer_manager
        self.settings_manager = settings_manager
        self.audio_analyzer = audio_analyzer

        # Thread safety
        self._mutex = QMutex()
        
        # Initialize variables first
        self.mix_value = 0.5
        self.deck_a_opacity = 1.0  # Individual deck opacity
        self.deck_b_opacity = 1.0
        self.global_brightness = 1.0  # Global brightness control
        self.deck_a = None
        self.deck_b = None
        self.deck_fade_times = {"A": 2000, "B": 2000}
        self._fade_timers = []

        
        # OpenGL widget setup
        self.gl_widget = QOpenGLWidget(self)
        self.setCentralWidget(self.gl_widget)

        # Bind GL widget methods
        self.gl_widget.initializeGL = self.initializeGL
        self.gl_widget.paintGL = self.paintGL
        self.gl_widget.resizeGL = self.resizeGL
        
        # State tracking
        self.gl_initialized = False
        self.shader_program = None
        self.quad_vao = None
        self.quad_vbo = None
        
        # Performance tracking
        self.frame_count = 0
        self.last_fps_time = time.time()
        
        # Connect internal signals to slots
        self.signal_set_mix_value.connect(self.set_mix_value)
        self.signal_set_deck_visualizer.connect(self.set_deck_visualizer)
        self.signal_update_deck_control.connect(self.update_deck_control)
        self.signal_set_deck_opacity.connect(self.set_deck_opacity)
        self.signal_trigger_deck_action.connect(self.trigger_deck_action)
        
        # Set up timer for continuous animation
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(16)  # ~60 FPS

        logging.info("🖥️ MixerWindow initialized with transparency support")

    def initializeGL(self):
        """Initialize OpenGL context and resources"""
        with QMutexLocker(self._mutex):
            try:
                logging.info("🎮 MixerWindow.initializeGL called")
                
                # Make context current
                self.gl_widget.makeCurrent()
                init_opengl_debug()

                # Log GL info for main context
                try:
                    OpenGLSafety.log_gl_info()
                    info = OpenGLSafety.get_gl_info()
                    renderer = (info.get('renderer') or '').lower()
                    if 'llvmpipe' in renderer or 'software' in renderer:
                        logging.warning(
                            f"MixerWindow: Software renderer detected ({info.get('renderer')})"
                        )
                    else:
                        logging.info(f"🎮 MixerWindow: Using GPU renderer: {info.get('renderer')}")
                except Exception as e:
                    logging.warning(f"Could not log GL info: {e}")

                # Clear any existing GL errors
                while glGetError() != GL_NO_ERROR:
                    pass
                
                # Basic OpenGL setup
                glClearColor(0.0, 0.0, 0.0, 1.0)
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                glDisable(GL_DEPTH_TEST)
                glEnable(GL_MULTISAMPLE)
                
                # Load shaders and setup geometry
                if not self.load_shaders():
                    logging.error("❌ Failed to load mixer shaders")
                    return
                    
                if not self.setup_quad():
                    logging.error("❌ Failed to setup quad geometry")
                    return
                
                # Create decks with proper configuration
                logging.info("🎨 Creating decks...")
                
                # Get GPU settings
                gpu_index = 0
                use_moderngl = False
                if self.settings_manager:
                    gpu_index = self.settings_manager.get_setting("visual_settings.gpu_index", 0)
                    backend = self.settings_manager.get_setting("visual_settings.backend", "OpenGL")
                    use_moderngl = (backend == "ModernGL")
                    logging.info(f"🎮 Using GPU {gpu_index} with {backend} backend")

                # Get the current OpenGL context for sharing
                current_gl_context = QOpenGLContext.currentContext()
                share_context_handle = None
                if current_gl_context:
                    share_context_handle = current_gl_context.rawHandle()
                    logging.debug(f"🎮 MixerWindow: Sharing OpenGL context handle: {share_context_handle}")
                else:
                    logging.warning("⚠️ MixerWindow: No current OpenGL context to share.")

                # Create decks
                self.deck_a = Deck(
                    self.visualizer_manager,
                    "A",
                    gpu_index=gpu_index,
                    use_moderngl=use_moderngl,
                    audio_analyzer=self.audio_analyzer,
                    share_context=share_context_handle, # Pass the shared context
                )
                self.deck_b = Deck(
                    self.visualizer_manager,
                    "B",
                    gpu_index=gpu_index,
                    use_moderngl=use_moderngl,
                    audio_analyzer=self.audio_analyzer,
                    share_context=share_context_handle, # Pass the shared context
                )
                
                # Initialize deck FBOs
                # Consider device pixel ratio to avoid black bars on high-DPI displays
                pixel_ratio = self.gl_widget.devicePixelRatio()
                current_size = QSize(
                    max(int(self.gl_widget.width() * pixel_ratio), 800),
                    max(int(self.gl_widget.height() * pixel_ratio), 600)
                )
                
                logging.info(f"📏 Initializing decks with size: {current_size.width()}x{current_size.height()}")
                self.deck_a.resize(current_size)
                self.deck_b.resize(current_size)
                
                # Verify deck initialization
                if not self.deck_a.is_ready():
                    logging.warning("⚠️ Deck A not ready after initialization")
                if not self.deck_b.is_ready():
                    logging.warning("⚠️ Deck B not ready after initialization")

                self.gl_initialized = True
                logging.info("✅ MixerWindow OpenGL initialized successfully")
                # Notify listeners that the GL context is ready
                self.gl_ready.emit()

                # Force initial render
                QTimer.singleShot(100, self.force_initial_render)
                
            except Exception as e:
                logging.error(f"❌ Error in initializeGL: {e}")
                import traceback
                traceback.print_exc()
                self.gl_initialized = False

    def force_initial_render(self):
        """Force an initial render to avoid black screen"""
        try:
            if self.gl_initialized and self.deck_a and self.deck_b:
                # Force both decks to render even if they don't have visualizers
                self.deck_a._fbo_dirty = True
                self.deck_b._fbo_dirty = True
                self.gl_widget.update()
                logging.debug("🔄 Forced initial render")
        except Exception as e:
            logging.error(f"❌ Error in force_initial_render: {e}")

    def load_shaders(self):
        """Load and compile enhanced shaders for mixing with transparency support"""
        try:
            vs_src = """
            #version 330 core
            layout (location = 0) in vec2 aPos;
            layout (location = 1) in vec2 aTexCoord;
            out vec2 TexCoord;
            void main()
            {
                gl_Position = vec4(aPos.x, aPos.y, 0.0, 1.0);
                TexCoord = aTexCoord;
            }
            """
            
            fs_src = """
            #version 330 core
            out vec4 FragColor;
            in vec2 TexCoord;
            uniform sampler2D texture1;
            uniform sampler2D texture2;
            uniform float deck_a_opacity;
            uniform float deck_b_opacity;
            uniform float global_brightness;
            uniform bool deck_a_active;
            uniform bool deck_b_active;
            
            void main()
            {
                vec4 color1 = vec4(0.0, 0.0, 0.0, 1.0);  // Default black
                vec4 color2 = vec4(0.0, 0.0, 0.0, 1.0);  // Default black
                
                // Only sample texture if deck is active
                if (deck_a_active) {
                    color1 = texture(texture1, TexCoord);
                    color1.rgb *= deck_a_opacity;  // Apply deck opacity
                }

                if (deck_b_active) {
                    color2 = texture(texture2, TexCoord);
                    color2.rgb *= deck_b_opacity;  // Apply deck opacity
                }
                
                vec4 mixed_color = color1 + color2;
                mixed_color.rgb *= global_brightness;
                mixed_color.rgb = clamp(mixed_color.rgb, 0.0, 1.0);
                mixed_color.a = 1.0;
                FragColor = mixed_color;
            }
            """

            return self.compile_shader_program(vs_src, fs_src)
            
        except Exception as e:
            logging.error(f"❌ Failed to load mixer shaders: {e}")
            return False

    def compile_shader_program(self, vs_src, fs_src):
        """Compile shader program"""
        try:
            # Compile vertex shader
            vs = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vs, vs_src)
            glCompileShader(vs)
            
            if not glGetShaderiv(vs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(vs).decode()
                logging.error(f"❌ Vertex shader compilation failed: {error}")
                return False

            # Compile fragment shader
            fs = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fs, fs_src)
            glCompileShader(fs)
            
            if not glGetShaderiv(fs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(fs).decode()
                logging.error(f"❌ Fragment shader compilation failed: {error}")
                return False

            # Link program
            self.shader_program = glCreateProgram()
            glAttachShader(self.shader_program, vs)
            glAttachShader(self.shader_program, fs)
            glLinkProgram(self.shader_program)
            
            if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(self.shader_program).decode()
                logging.error(f"❌ Shader program linking failed: {error}")
                return False

            # Clean up individual shaders
            glDeleteShader(vs)
            glDeleteShader(fs)
            logging.debug("✅ Enhanced mixer shaders compiled successfully")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error compiling shader program: {e}")
            return False

    def setup_quad(self):
        """Setup geometry for full-screen quad"""
        try:
            quad_vertices = np.array([
                # positions   # texCoords
                -1.0,  1.0,  0.0, 1.0,
                -1.0, -1.0,  0.0, 0.0,
                 1.0, -1.0,  1.0, 0.0,

                -1.0,  1.0,  0.0, 1.0,
                 1.0, -1.0,  1.0, 0.0,
                 1.0,  1.0,  1.0, 1.0
            ], dtype=np.float32)

            self.quad_vao = glGenVertexArrays(1)
            self.quad_vbo = glGenBuffers(1)
            
            glBindVertexArray(self.quad_vao)
            glBindBuffer(GL_ARRAY_BUFFER, self.quad_vbo)
            glBufferData(GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, GL_STATIC_DRAW)
            
            # Position attribute
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
            
            # Texture coordinate attribute
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(2 * 4))
            
            glBindVertexArray(0)
            logging.debug("✅ Quad geometry setup complete")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error setting up quad geometry: {e}")
            return False

    def animate(self):
        """Called by timer to trigger repaints"""
        if self.gl_widget and self.gl_initialized:
            self.gl_widget.update()

    def paintGL(self):
        """Render the mixed output with enhanced transparency support"""
        try:
            if not self.gl_initialized:
                glClearColor(0.0, 0.0, 0.0, 1.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return
                
            # Make sure we have the current context
            self.gl_widget.makeCurrent()
            
            # First, render both decks to their FBOs
            deck_a_rendered = False
            deck_b_rendered = False
            
            if self.deck_a:
                try:
                    self.deck_a.paint()
                    deck_a_rendered = True
                except Exception as e:
                    logging.error(f"❌ Error painting deck A: {e}")
                finally:
                    # ModernGL renders can change the current context; make sure
                    # our Qt context is current again before continuing
                    self.gl_widget.makeCurrent()

            if self.deck_b:
                try:
                    self.deck_b.paint()
                    deck_b_rendered = True
                except Exception as e:
                    logging.error(f"❌ Error painting deck B: {e}")
                finally:
                    # Ensure Qt's GL context remains current after ModernGL calls
                    self.gl_widget.makeCurrent()
            
            # Now composite them in the main framebuffer
            self.gl_widget.makeCurrent() # Ensure context is current before binding framebuffer
            OpenGLSafety.safe_bind_framebuffer(
                GL_FRAMEBUFFER, self.gl_widget.defaultFramebufferObject()
            )
            pixel_ratio = self.gl_widget.devicePixelRatio()
            glViewport(0, 0, int(self.gl_widget.width() * pixel_ratio), int(self.gl_widget.height() * pixel_ratio))

            # Clear main framebuffer and reset state that might be changed by visualizers
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_CULL_FACE)
            glDepthMask(GL_FALSE)
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glDepthMask(GL_TRUE)

            if not self.shader_program or not self.quad_vao:
                logging.debug("Shader program or quad VAO not available")
                return
                
            # Use the enhanced mixing shader
            glUseProgram(self.shader_program)
            
            # Check if decks are active (have visualizers) and rendered successfully
            deck_a_active = (self.deck_a and 
                           self.deck_a.has_active_visualizer() and 
                           deck_a_rendered)
            deck_b_active = (self.deck_b and 
                           self.deck_b.has_active_visualizer() and 
                           deck_b_rendered)
            
            # Get textures from decks
            texture_a = 0
            texture_b = 0
            
            if deck_a_active:
                texture_a = self.deck_a.get_texture()
                if texture_a == 0:
                    logging.debug("Deck A has active visualizer but texture is 0")
                    deck_a_active = False
                    
            if deck_b_active:
                texture_b = self.deck_b.get_texture()
                if texture_b == 0:
                    logging.debug("Deck B has active visualizer but texture is 0")
                    deck_b_active = False

            # Debug logging
            if self.frame_count % 300 == 0:  # Every 5 seconds at 60fps
                logging.debug(
                    f"🎬 Frame {self.frame_count}: A_active={deck_a_active}, B_active={deck_b_active}, "
                    f"A_tex={texture_a}, B_tex={texture_b}"
                )

            # Bind textures
            glActiveTexture(GL_TEXTURE0)
            if texture_a > 0:
                glBindTexture(GL_TEXTURE_2D, texture_a)
            else:
                glBindTexture(GL_TEXTURE_2D, 0)

            glActiveTexture(GL_TEXTURE1)
            if texture_b > 0:
                glBindTexture(GL_TEXTURE_2D, texture_b)
            else:
                glBindTexture(GL_TEXTURE_2D, 0)
            
            # Set shader uniforms
            try:
                glUniform1i(glGetUniformLocation(self.shader_program, "texture1"), 0)
                glUniform1i(glGetUniformLocation(self.shader_program, "texture2"), 1)
                glUniform1f(glGetUniformLocation(self.shader_program, "deck_a_opacity"), self.deck_a_opacity)
                glUniform1f(glGetUniformLocation(self.shader_program, "deck_b_opacity"), self.deck_b_opacity)
                glUniform1f(glGetUniformLocation(self.shader_program, "global_brightness"), self.global_brightness)
                glUniform1i(glGetUniformLocation(self.shader_program, "deck_a_active"), int(deck_a_active))
                glUniform1i(glGetUniformLocation(self.shader_program, "deck_b_active"), int(deck_b_active))
            except Exception as e:
                logging.error(f"❌ Error setting shader uniforms: {e}")

            # Draw the full-screen quad
            try:
                glBindVertexArray(self.quad_vao)
                glDrawArrays(GL_TRIANGLES, 0, 6)
                glBindVertexArray(0)
            except Exception as e:
                logging.error(f"❌ Error drawing quad: {e}")
            
            # Clean up
            glUseProgram(0)
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, 0)
            glActiveTexture(GL_TEXTURE1)
            glBindTexture(GL_TEXTURE_2D, 0)
            
            # Track performance
            self.frame_count += 1
            current_time = time.time()
            if current_time - self.last_fps_time > 5.0:
                fps = self.frame_count / (current_time - self.last_fps_time)
                if self.frame_count > 60:
                    logging.debug(f"🎬 Mixer FPS: {fps:.1f}")
                self.last_fps_time = current_time
                self.frame_count = 0
            
        except Exception as e:
            logging.error(f"❌ Error in paintGL: {e}")
            import traceback
            traceback.print_exc()
            # Render fallback
            glClearColor(0.1, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def resizeGL(self, w, h):
        """Handle window resize"""
        try:
            pixel_ratio = self.gl_widget.devicePixelRatio()
            current_size = QSize(int(w * pixel_ratio), int(h * pixel_ratio))
            logging.debug(f"📏 MixerWindow resized to {w}x{h} (px ratio {pixel_ratio})")
            
            if not self.gl_initialized:
                return
                
            # Make sure GL context is current
            self.gl_widget.makeCurrent()
            
            # Resize decks
            if self.deck_a:
                self.deck_a.resize(current_size)
            if self.deck_b:
                self.deck_b.resize(current_size)
            
        except Exception as e:
            logging.error(f"❌ Error in resizeGL: {e}")

    # Main slot methods
    @pyqtSlot(int)
    def set_mix_value(self, value):
        """Set crossfader mix value (0-100)"""
        with QMutexLocker(self._mutex):
            self.mix_value = max(0.0, min(1.0, value / 100.0))
            logging.debug(f"🎚️ Mix value set to: {self.mix_value:.2f} ({value}%)")

    @pyqtSlot(str, object)
    def set_deck_visualizer(self, deck_id, visualizer_name):
        """Set visualizer for a specific deck - supports fade transitions"""
        fade_ms = self.deck_fade_times.get(deck_id, 0)
        target_deck = None
        if deck_id == 'A':
            target_deck = self.deck_a
        elif deck_id == 'B':
            target_deck = self.deck_b

        if (
            fade_ms > 0
            and target_deck
            and target_deck.has_active_visualizer()
            and visualizer_name not in (None, "-- No preset selected --")
        ):
            self._fade_and_set_visualizer(deck_id, visualizer_name, fade_ms)
            return

        with QMutexLocker(self._mutex):
            logging.info(f"🎮 Setting deck {deck_id} to visualizer: {visualizer_name}")

            if not self.gl_initialized:
                logging.warning("⚠️ OpenGL not initialized, queuing visualizer change")
                QTimer.singleShot(500, lambda: self.set_deck_visualizer(deck_id, visualizer_name))
                return

            self.gl_widget.makeCurrent()

            if deck_id == 'A' and self.deck_a:
                if visualizer_name is None or visualizer_name == "-- No preset selected --":
                    self.deck_a.clear_visualizer()
                    logging.info("🚫 Deck A cleared - no visualizer")
                else:
                    self.deck_a.set_visualizer(visualizer_name)
                    logging.info(f"✅ Deck A set to: {visualizer_name}")
            elif deck_id == 'B' and self.deck_b:
                if visualizer_name is None or visualizer_name == "-- No preset selected --":
                    self.deck_b.clear_visualizer()
                    logging.info("🚫 Deck B cleared - no visualizer")
                else:
                    self.deck_b.set_visualizer(visualizer_name)
                    logging.info(f"✅ Deck B set to: {visualizer_name}")
            else:
                logging.warning(f"⚠️ Unknown deck ID: {deck_id}")

    def _fade_and_set_visualizer(self, deck_id, visualizer_name, fade_ms):
        """Fade out current visualizer, switch, and fade back in"""
        target_deck = self.deck_a if deck_id == 'A' else self.deck_b
        if not target_deck:
            return

        phase_ms = max(1, fade_ms // 2)
        steps = max(1, int(phase_ms / 16))
        step_time = max(1, int(phase_ms / steps))
        current_opacity = self.deck_a_opacity if deck_id == 'A' else self.deck_b_opacity

        timer = QTimer(self)
        self._fade_timers.append(timer)

        state = {'step': 0, 'phase': 'out'}

        def step():
            if state['phase'] == 'out':
                if state['step'] < steps:
                    new_opacity = current_opacity * (1 - (state['step'] + 1) / steps)
                    self.set_deck_opacity(deck_id, new_opacity)
                    state['step'] += 1
                else:
                    timer.stop()
                    self.set_deck_opacity(deck_id, 0.0)
                    with QMutexLocker(self._mutex):
                        if not self.gl_initialized:
                            return
                        self.gl_widget.makeCurrent()
                        target_deck.set_visualizer(visualizer_name)
                    state['phase'] = 'in'
                    state['step'] = 0
                    timer.start(step_time)
            else:
                if state['step'] < steps:
                    new_opacity = current_opacity * ((state['step'] + 1) / steps)
                    self.set_deck_opacity(deck_id, new_opacity)
                    state['step'] += 1
                else:
                    self.set_deck_opacity(deck_id, current_opacity)
                    timer.stop()
                    timer.deleteLater()
                    if timer in self._fade_timers:
                        self._fade_timers.remove(timer)


        timer.timeout.connect(step)
        timer.start(step_time)

    @pyqtSlot(str, str, object)
    def update_deck_control(self, deck_id, name, value):
        """Update a control parameter for a specific deck"""
        with QMutexLocker(self._mutex):
            logging.debug(f"🎛️ Updating deck {deck_id} control {name} to {value}")
            
            if not self.gl_initialized:
                return
                
            if deck_id == 'A' and self.deck_a:
                self.deck_a.update_control(name, value)
            elif deck_id == 'B' and self.deck_b:
                self.deck_b.update_control(name, value)

    @pyqtSlot(str, str)
    def trigger_deck_action(self, deck_id, action):
        """Trigger a custom action for a specific deck"""
        with QMutexLocker(self._mutex):
            logging.debug(f"🎬 Triggering action {action} on deck {deck_id}")
            if not self.gl_initialized:
                return
            if deck_id == 'A' and self.deck_a:
                self.deck_a.trigger_action(action)
            elif deck_id == 'B' and self.deck_b:
                self.deck_b.trigger_action(action)

    @pyqtSlot(str, float)
    def set_deck_opacity(self, deck_id, opacity):
        """Set opacity for a specific deck (0.0-1.0)"""
        with QMutexLocker(self._mutex):
            opacity = max(0.0, min(1.0, opacity))
            if deck_id == 'A':
                self.deck_a_opacity = opacity
                logging.debug(f"🎚️ Deck A opacity set to: {opacity:.2f}")
            elif deck_id == 'B':
                self.deck_b_opacity = opacity
                logging.debug(f"🎚️ Deck B opacity set to: {opacity:.2f}")

    def set_deck_fade_time(self, deck_id, fade_ms):
        """Configure fade time for deck transitions in milliseconds"""
        with QMutexLocker(self._mutex):
            self.deck_fade_times[deck_id] = max(0, int(fade_ms))
            logging.debug(f"⏱️ Deck {deck_id} fade time set to {fade_ms} ms")

    # Thread-safe public methods
    def safe_set_mix_value(self, value):
        """Thread-safe wrapper for setting mix value"""
        self.signal_set_mix_value.emit(value)

    def safe_set_deck_visualizer(self, deck_id, visualizer_name):
        """Thread-safe wrapper for setting deck visualizer"""
        self.signal_set_deck_visualizer.emit(deck_id, visualizer_name)

    def safe_update_deck_control(self, deck_id, name, value):
        """Thread-safe wrapper for updating deck control"""
        self.signal_update_deck_control.emit(deck_id, name, value)

    def safe_set_deck_opacity(self, deck_id, opacity):
        """Thread-safe wrapper for setting deck opacity"""
        self.signal_set_deck_opacity.emit(deck_id, opacity)

    def safe_trigger_deck_action(self, deck_id, action):
        """Thread-safe wrapper for triggering deck actions"""
        self.signal_trigger_deck_action.emit(deck_id, action)

    def safe_set_global_brightness(self, brightness):
        """Set global brightness (0.0-1.0)"""
        with QMutexLocker(self._mutex):
            self.global_brightness = max(0.0, min(2.0, brightness))  # Allow up to 200% brightness
            logging.debug(f"🔆 Global brightness set to: {self.global_brightness:.2f}")

    # Utility methods
    def get_deck_controls(self, deck_id):
        """Get available controls for the specified deck"""
        with QMutexLocker(self._mutex):
            if not self.deck_a or not self.deck_b:
                return {}
                
            if deck_id == 'A':
                return self.deck_a.get_controls()
            elif deck_id == 'B':
                return self.deck_b.get_controls()
            else:
                return {}

    def get_current_visualizers(self):
        """Get currently loaded visualizers for both decks"""
        with QMutexLocker(self._mutex):
            if not self.deck_a or not self.deck_b:
                return {'A': 'Not Initialized', 'B': 'Not Initialized'}
                
            return {
                'A': self.deck_a.get_current_visualizer_name(),
                'B': self.deck_b.get_current_visualizer_name()
            }

    def get_mix_value(self):
        """Get current mix value (0.0-1.0)"""
        with QMutexLocker(self._mutex):
            return self.mix_value

    def get_mix_value_percent(self):
        """Get current mix value as percentage (0-100)"""
        with QMutexLocker(self._mutex):
            return int(self.mix_value * 100)

    def get_deck_opacity(self, deck_id):
        """Get deck opacity (0.0-1.0)"""
        with QMutexLocker(self._mutex):
            if deck_id == 'A':
                return self.deck_a_opacity
            elif deck_id == 'B':
                return self.deck_b_opacity
            return 1.0

    def get_deck_opacity_percent(self, deck_id):
        """Get deck opacity as percentage (0-100)"""
        return int(self.get_deck_opacity(deck_id) * 100)

    def get_global_brightness(self):
        """Get global brightness (0.0-2.0)"""
        with QMutexLocker(self._mutex):
            return self.global_brightness

    def get_global_brightness_percent(self):
        """Get global brightness as percentage (0-200)"""
        return int(self.get_global_brightness() * 100)

    def get_deck_status(self, deck_id):
        """Get comprehensive deck status"""
        with QMutexLocker(self._mutex):
            if deck_id == 'A' and self.deck_a:
                info = self.deck_a.get_deck_info()
                info.update({'opacity': self.deck_a_opacity})
                return info
            elif deck_id == 'B' and self.deck_b:
                info = self.deck_b.get_deck_info()
                info.update({'opacity': self.deck_b_opacity})
                return info
            return {
                'active': False,
                'visualizer': None,
                'opacity': 1.0,
                'controls_count': 0,
                'frame_count': 0,
                'fps': 0.0,
                'gpu_renderer': None
            }

    def apply_gpu_selection(self, index, backend_type=None):
        """Apply GPU selection to decks"""
        with QMutexLocker(self._mutex):
            logging.info(f"🎮 Applying GPU selection: index={index}, backend={backend_type}")
            
            if self.deck_a:
                self.deck_a.set_gpu_index(index, backend_type)
            if self.deck_b:
                self.deck_b.set_gpu_index(index, backend_type)
                
            # Force refresh
            if self.gl_initialized:
                self.gl_widget.update()

    def cleanup(self):
        """Clean up OpenGL resources"""
        with QMutexLocker(self._mutex):
            if self.gl_initialized:
                try:
                    self.gl_widget.makeCurrent()
                    
                    if self.shader_program:
                        glDeleteProgram(self.shader_program)
                        self.shader_program = None
                        
                    if self.quad_vao:
                        glDeleteVertexArrays(1, [self.quad_vao])
                        self.quad_vao = None
                        
                    if self.quad_vbo:
                        glDeleteBuffers(1, [self.quad_vbo])
                        self.quad_vbo = None
                    
                    # Clean up decks
                    if self.deck_a:
                        self.deck_a.cleanup()
                    if self.deck_b:
                        self.deck_b.cleanup()
                        
                    logging.info("✅ OpenGL resources cleaned up")
                except Exception as e:
                    logging.error(f"❌ Error during cleanup: {e}")

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            self.animation_timer.stop()
            self.cleanup()
            super().closeEvent(event)
        except Exception as e:
            logging.error(f"❌ Error in closeEvent: {e}")
            super().closeEvent(event)

    def keyPressEvent(self, event):
        """Handle key presses for fullscreen exit"""
        if event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self.exit_fullscreen.emit()
        else:
            super().keyPressEvent(event)