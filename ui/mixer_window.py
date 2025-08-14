# ui/mixer_window.py
import logging
import numpy as np
import ctypes
import time
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSlot, pyqtSignal, QMutex, QMutexLocker
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *

from visuals.deck import Deck

class MixerWindow(QMainWindow):
    # Custom signals for thread-safe communication
    signal_set_mix_value = pyqtSignal(int)
    signal_set_deck_visualizer = pyqtSignal(str, str)
    signal_update_deck_control = pyqtSignal(str, str, object)

    def __init__(self, visualizer_manager):
        super().__init__()
        self.setWindowTitle("Audio Visualizer Pro - Main Output")
        self.setGeometry(100, 100, 800, 600)
        self.visualizer_manager = visualizer_manager

        # Thread safety
        self._mutex = QMutex()
        
        # Initialize variables first
        self.mix_value = 0.5
        self.deck_a = None
        self.deck_b = None
        
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
        
        # Set up timer for continuous animation
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(16)  # ~60 FPS

        logging.info("🖥️ MixerWindow initialized")

    def initializeGL(self):
        """Initialize OpenGL context and resources"""
        with QMutexLocker(self._mutex):
            try:
                logging.info("🎮 MixerWindow.initializeGL called")
                
                # Make context current
                self.gl_widget.makeCurrent()
                
                # Clear any existing GL errors
                while glGetError() != GL_NO_ERROR:
                    pass
                
                # Basic OpenGL setup
                glClearColor(0.0, 0.0, 0.0, 1.0)
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                glDisable(GL_DEPTH_TEST)
                
                # Load shaders and setup geometry
                if not self.load_shaders():
                    logging.error("❌ Failed to load mixer shaders")
                    return
                    
                if not self.setup_quad():
                    logging.error("❌ Failed to setup quad geometry")
                    return
                
                # Create decks with proper IDs
                logging.info("🎨 Creating decks...")
                self.deck_a = Deck(self.visualizer_manager, "A")
                self.deck_b = Deck(self.visualizer_manager, "B")
                
                # Initialize deck FBOs
                current_size = QSize(
                    max(self.gl_widget.width(), 800), 
                    max(self.gl_widget.height(), 600)
                )
                
                self.deck_a.resize(current_size)
                self.deck_b.resize(current_size)
                
                # Setup initial visualizers
                self.setup_initial_visualizers()
                
                self.gl_initialized = True
                logging.info("✅ MixerWindow OpenGL initialized successfully")
                
            except Exception as e:
                logging.error(f"❌ Error in initializeGL: {e}")
                import traceback
                traceback.print_exc()
                self.gl_initialized = False

    def setup_initial_visualizers(self):
        """Setup initial visualizers"""
        try:
            visualizer_names = self.visualizer_manager.get_visualizer_names()
            if not visualizer_names:
                logging.warning("⚠️ No visualizers available")
                return
                
            logging.info(f"🎨 Setting up initial visualizers from: {visualizer_names}")
            
            # Set default visualizers
            deck_a_viz = "Simple Test" if "Simple Test" in visualizer_names else visualizer_names[0]
            self.deck_a.set_visualizer(deck_a_viz)
            
            if len(visualizer_names) > 1:
                deck_b_viz = "Wire Terrain" if "Wire Terrain" in visualizer_names else visualizer_names[1]
                self.deck_b.set_visualizer(deck_b_viz)
            else:
                self.deck_b.set_visualizer(visualizer_names[0])
                
            logging.info(f"✅ Initial visualizers set")
                
        except Exception as e:
            logging.error(f"❌ Error setting up initial visualizers: {e}")

    def load_shaders(self):
        """Load and compile shaders for mixing"""
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
            uniform float mixValue;
            
            void main()
            {
                vec4 color1 = texture(texture1, TexCoord);
                vec4 color2 = texture(texture2, TexCoord);
                
                // Ensure alpha is 1.0
                color1.a = 1.0;
                color2.a = 1.0;
                
                FragColor = mix(color1, color2, mixValue);
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
            logging.debug("✅ Mixer shaders compiled successfully")
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
        """Render the mixed output"""
        try:
            if not self.gl_initialized:
                glClearColor(0.1, 0.1, 0.2, 1.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return
                
            # Make sure we have the current context
            self.gl_widget.makeCurrent()
            
            # First, render both decks to their FBOs
            if self.deck_a:
                self.deck_a.paint()
            if self.deck_b:
                self.deck_b.paint()
            
            # Now composite them in the main framebuffer
            glBindFramebuffer(GL_FRAMEBUFFER, self.gl_widget.defaultFramebufferObject())
            glViewport(0, 0, self.gl_widget.width(), self.gl_widget.height())

            # Clear main framebuffer and reset state that might be changed by visualizers
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_CULL_FACE)
            glDepthMask(GL_FALSE)
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glDepthMask(GL_TRUE)

            if not self.shader_program or not self.quad_vao:
                return
                
            # Use the mixing shader
            glUseProgram(self.shader_program)
            
            # Get textures from decks
            texture_a = self.deck_a.get_texture() if self.deck_a else 0
            texture_b = self.deck_b.get_texture() if self.deck_b else 0
            
            # If we don't have textures, show a fallback
            if texture_a == 0 and texture_b == 0:
                glClearColor(0.1, 0.0, 0.1, 1.0)
                glClear(GL_COLOR_BUFFER_BIT)
                glUseProgram(0)
                return
            
            # Bind textures
            glActiveTexture(GL_TEXTURE0)
            if texture_a > 0:
                glBindTexture(GL_TEXTURE_2D, texture_a)
            else:
                # Create a dummy texture for deck A
                glBindTexture(GL_TEXTURE_2D, 0)
            
            glActiveTexture(GL_TEXTURE1)
            if texture_b > 0:
                glBindTexture(GL_TEXTURE_2D, texture_b)
            else:
                # Create a dummy texture for deck B
                glBindTexture(GL_TEXTURE_2D, 0)
            
            # Set shader uniforms
            glUniform1i(glGetUniformLocation(self.shader_program, "texture1"), 0)
            glUniform1i(glGetUniformLocation(self.shader_program, "texture2"), 1)
            glUniform1f(glGetUniformLocation(self.shader_program, "mixValue"), self.mix_value)

            # Draw the full-screen quad
            glBindVertexArray(self.quad_vao)
            glDrawArrays(GL_TRIANGLES, 0, 6)
            glBindVertexArray(0)
            
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
            glClearColor(0.5, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def resizeGL(self, w, h):
        """Handle window resize"""
        try:
            current_size = QSize(w, h)
            logging.debug(f"📐 MixerWindow resized to {w}x{h}")
            
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
            logging.info(f"🎚️ Mix value set to: {self.mix_value:.2f} ({value}%)")

    @pyqtSlot(str, str)
    def set_deck_visualizer(self, deck_id, visualizer_name):
        """Set visualizer for a specific deck"""
        with QMutexLocker(self._mutex):
            logging.info(f"🎮 Setting deck {deck_id} to visualizer: {visualizer_name}")
            
            if not self.gl_initialized:
                logging.warning("⚠️ OpenGL not initialized")
                return
                
            # Make sure we have OpenGL context
            self.gl_widget.makeCurrent()
            
            if deck_id == 'A' and self.deck_a:
                self.deck_a.set_visualizer(visualizer_name)
                logging.info(f"✅ Deck A set to: {visualizer_name}")
            elif deck_id == 'B' and self.deck_b:
                self.deck_b.set_visualizer(visualizer_name)
                logging.info(f"✅ Deck B set to: {visualizer_name}")
            else:
                logging.warning(f"⚠️ Unknown deck ID: {deck_id}")

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

    def cleanup(self):
        """Clean up OpenGL resources"""
        with QMutexLocker(self._mutex):
            if self.gl_initialized:
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

    def closeEvent(self, event):
        """Handle window close event"""
        self.animation_timer.stop()
        self.cleanup()
        super().closeEvent(event)