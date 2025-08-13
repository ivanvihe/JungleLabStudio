import logging
import numpy as np
import ctypes
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSlot, pyqtSignal
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
        self.initial_setup_done = False
        self.gl_initialized = False
        self.shader_program = None
        self.quad_vao = None
        self.quad_vbo = None
        
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
        try:
            logging.info("🎮 MixerWindow.initializeGL called")
            
            # Basic OpenGL setup
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glDisable(GL_DEPTH_TEST)  # We don't need depth testing for 2D mixing
            
            # Load shaders and setup geometry
            self.load_shaders()
            self.setup_quad()
            
            # NOW create decks with valid OpenGL context
            logging.info("🎨 Creating decks with OpenGL context...")
            self.deck_a = Deck(self.visualizer_manager)
            self.deck_b = Deck(self.visualizer_manager)
            
            # Initialize decks with current size - NOW with valid OpenGL context
            current_size = QSize(max(self.gl_widget.width(), 800), max(self.gl_widget.height(), 600))
            logging.info(f"🔧 Initializing decks with size: {current_size.width()}x{current_size.height()}")
            
            # Make sure GL context is current
            self.gl_widget.makeCurrent()
            
            # Resize decks to create FBOs
            self.deck_a.resize(current_size)
            self.deck_b.resize(current_size)
            
            # Setup initial visualizers now that OpenGL is ready
            if not self.initial_setup_done:
                self.setup_initial_visualizers()
                self.initial_setup_done = True
            
            self.gl_initialized = True
            logging.info("✅ MixerWindow OpenGL initialized successfully")
            
        except Exception as e:
            logging.error(f"❌ Error in initializeGL: {e}")
            self.gl_initialized = False
            raise

    def setup_initial_visualizers(self):
        """Setup initial visualizers now that OpenGL context is available"""
        try:
            visualizer_names = self.visualizer_manager.get_visualizer_names()
            if visualizer_names and self.deck_a and self.deck_b:
                logging.info(f"🎨 Setting up initial visualizers from: {visualizer_names}")
                
                # Make sure we have current GL context
                self.gl_widget.makeCurrent()
                
                # Set default visualizers for both decks
                # Always try to set Deck A to "Simple Test" if available, otherwise use the first visualizer
                if "Simple Test" in visualizer_names:
                    self.deck_a.set_visualizer("Simple Test")
                else:
                    self.deck_a.set_visualizer(visualizer_names[0])

                if len(visualizer_names) > 1:
                    # Try to set Deck B to "Wire Terrain" if available, otherwise use the second visualizer
                    if "Wire Terrain" in visualizer_names:
                        self.deck_b.set_visualizer("Wire Terrain")
                    else:
                        self.deck_b.set_visualizer(visualizer_names[1])
                else:
                    self.deck_b.set_visualizer(visualizer_names[0])
                    
                logging.info("✅ Initial visualizers set up successfully")
            else:
                logging.warning("⚠️ No visualizers available for initial setup or decks not created")
                
        except Exception as e:
            logging.error(f"❌ Error setting up initial visualizers: {e}")

    def animate(self):
        """Called by timer to trigger repaints"""
        try:
            if self.gl_widget and self.gl_initialized and self.deck_a and self.deck_b:
                self.gl_widget.update()
        except Exception as e:
            logging.error(f"❌ Error in animate: {e}")

    def load_shaders(self):
        """Load and compile shaders for mixing"""
        try:
            # Try to load shaders from files first
            vs_src = None
            fs_src = None
            
            try:
                with open("shaders/mix.vert", 'r') as f:
                    vs_src = f.read()
                with open("shaders/mix.frag", 'r') as f:
                    fs_src = f.read()
                logging.debug("📁 Loaded shaders from files")
            except FileNotFoundError:
                logging.warning("⚠️ Shader files not found, using fallback shaders")
                
            # Fallback shaders if files don't exist
            if not vs_src:
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
                
            if not fs_src:
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
                    FragColor = mix(color1, color2, mixValue);
                }
                """

            # Compile vertex shader
            vs = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vs, vs_src)
            glCompileShader(vs)
            
            if not glGetShaderiv(vs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(vs).decode()
                logging.error(f"❌ Vertex shader compilation failed: {error}")
                raise Exception(f"Vertex shader error: {error}")

            # Compile fragment shader
            fs = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fs, fs_src)
            glCompileShader(fs)
            
            if not glGetShaderiv(fs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(fs).decode()
                logging.error(f"❌ Fragment shader compilation failed: {error}")
                raise Exception(f"Fragment shader error: {error}")

            # Link program
            self.shader_program = glCreateProgram()
            glAttachShader(self.shader_program, vs)
            glAttachShader(self.shader_program, fs)
            glLinkProgram(self.shader_program)
            
            if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(self.shader_program).decode()
                logging.error(f"❌ Shader program linking failed: {error}")
                raise Exception(f"Shader program error: {error}")

            # Clean up individual shaders
            glDeleteShader(vs)
            glDeleteShader(fs)
            logging.info("✅ Mixer shaders loaded successfully")
            
        except Exception as e:
            logging.error(f"❌ Failed to load mixer shaders: {e}")
            raise

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
            logging.info("✅ Quad geometry setup complete")
            
        except Exception as e:
            logging.error(f"❌ Error setting up quad geometry: {e}")
            raise

    def paintGL(self):
        """Render the mixed output"""
        try:
            if not self.gl_initialized or not self.shader_program or not self.deck_a or not self.deck_b:
                # Draw a simple color to show the window is working
                glClearColor(0.1, 0.1, 0.2, 1.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return
                
            # Make sure we have the current context
            self.gl_widget.makeCurrent()
            
            # Render both decks to their framebuffers
            try:
                self.deck_a.paint()
                self.deck_b.paint()
            except Exception as e:
                logging.error(f"❌ Error painting decks: {e}")
                # Draw fallback color
                glClearColor(0.2, 0.0, 0.0, 1.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return

            # Now composite them in the main framebuffer
            glBindFramebuffer(GL_FRAMEBUFFER, self.gl_widget.defaultFramebufferObject())
            glViewport(0, 0, self.gl_widget.width(), self.gl_widget.height())
            glClear(GL_COLOR_BUFFER_BIT)

            # Use the mixing shader
            glUseProgram(self.shader_program)
            
            # Get textures from decks
            texture_a = self.deck_a.get_texture()
            texture_b = self.deck_b.get_texture()
            
            logging.debug(f"Mixer paintGL: Deck A texture ID: {texture_a}, Deck B texture ID: {texture_b}")
            
            # Bind texture A
            glActiveTexture(GL_TEXTURE0)
            if texture_a and texture_a > 0:
                glBindTexture(GL_TEXTURE_2D, texture_a)
            else:
                # Bind a default black texture if needed
                glBindTexture(GL_TEXTURE_2D, 0)
            
            # Bind texture B
            glActiveTexture(GL_TEXTURE1)
            if texture_b and texture_b > 0:
                glBindTexture(GL_TEXTURE_2D, texture_b)
            else:
                glBindTexture(GL_TEXTURE_2D, 0)
            
            # Set shader uniforms
            glUniform1i(glGetUniformLocation(self.shader_program, "texture1"), 0)
            glUniform1i(glGetUniformLocation(self.shader_program, "texture2"), 1)
            glUniform1f(glGetUniformLocation(self.shader_program, "mixValue"), self.mix_value)

            # Draw the full-screen quad
            if self.quad_vao:
                glBindVertexArray(self.quad_vao)
                glDrawArrays(GL_TRIANGLES, 0, 6)
                glBindVertexArray(0)
            
            # Clean up
            glUseProgram(0)
            
        except Exception as e:
            logging.error(f"❌ Error in paintGL: {e}")
            # Draw error color
            glClearColor(0.5, 0.0, 0.5, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def resizeGL(self, w, h):
        """Handle window resize"""
        try:
            current_size = QSize(w, h)
            logging.debug(f"🔧 MixerWindow resized to {w}x{h}")
            
            if not self.gl_initialized or not self.deck_a or not self.deck_b:
                return
                
            # Make sure GL context is current
            self.gl_widget.makeCurrent()
            
            # Resize decks
            self.deck_a.resize(current_size)
            self.deck_b.resize(current_size)
            
        except Exception as e:
            logging.error(f"❌ Error in resizeGL: {e}")

    # Main slot methods (called from signals)
    @pyqtSlot(int)
    def set_mix_value(self, value):
        """Set crossfader mix value (0-100)"""
        try:
            self.mix_value = max(0.0, min(1.0, value / 100.0))
            logging.info(f"🎚️ Mix value set to: {self.mix_value} ({value}%)")
            
            if self.gl_initialized:
                self.gl_widget.update()  # Trigger a repaint
                
        except Exception as e:
            logging.error(f"❌ Error setting mix value: {e}")

    @pyqtSlot(str, str)
    def set_deck_visualizer(self, deck_id, visualizer_name):
        """Set visualizer for a specific deck"""
        try:
            logging.info(f"🎮 SETTING deck {deck_id} to visualizer: {visualizer_name}")
            
            if not self.gl_initialized:
                logging.warning("⚠️ OpenGL not initialized, cannot set visualizer")
                return
                
            if not self.deck_a or not self.deck_b:
                logging.warning("⚠️ Decks not initialized, cannot set visualizer")
                return
                
            # Make sure we have OpenGL context
            self.gl_widget.makeCurrent()
            
            if deck_id == 'A':
                self.deck_a.set_visualizer(visualizer_name)
                logging.info(f"✅ Deck A set to: {visualizer_name}")
            elif deck_id == 'B':
                self.deck_b.set_visualizer(visualizer_name)
                logging.info(f"✅ Deck B set to: {visualizer_name}")
            else:
                logging.warning(f"⚠️ Unknown deck ID: {deck_id}")
                return
                
            self.gl_widget.update()  # Trigger a repaint
            
        except Exception as e:
            logging.error(f"❌ Error setting deck visualizer: {e}")

    @pyqtSlot(str, str, object)
    def update_deck_control(self, deck_id, name, value):
        """Update a control parameter for a specific deck"""
        try:
            logging.info(f"🎛️ UPDATING deck {deck_id} control {name} to {value}")
            
            if not self.gl_initialized:
                logging.warning("⚠️ OpenGL not initialized, cannot update control")
                return
                
            if not self.deck_a or not self.deck_b:
                logging.warning("⚠️ Decks not initialized, cannot update control")
                return
                
            if deck_id == 'A':
                self.deck_a.update_control(name, value)
                logging.info(f"✅ Updated A.{name} = {value}")
            elif deck_id == 'B':
                self.deck_b.update_control(name, value)
                logging.info(f"✅ Updated B.{name} = {value}")
            else:
                logging.warning(f"⚠️ Unknown deck ID: {deck_id}")
                return
                
            self.gl_widget.update()  # Trigger a repaint
            
        except Exception as e:
            logging.error(f"❌ Error updating deck control: {e}")

    # Thread-safe public methods (emit signals)
    def safe_set_mix_value(self, value):
        """Thread-safe wrapper for setting mix value"""
        logging.info(f"🔄 safe_set_mix_value called with value: {value}")
        self.signal_set_mix_value.emit(value)

    def safe_set_deck_visualizer(self, deck_id, visualizer_name):
        """Thread-safe wrapper for setting deck visualizer"""
        logging.info(f"🔄 safe_set_deck_visualizer called: deck {deck_id} -> {visualizer_name}")
        self.signal_set_deck_visualizer.emit(deck_id, visualizer_name)

    def safe_update_deck_control(self, deck_id, name, value):
        """Thread-safe wrapper for updating deck control"""
        logging.info(f"🔄 safe_update_deck_control called: {deck_id}.{name} = {value}")
        self.signal_update_deck_control.emit(deck_id, name, value)

    # Utility methods
    def get_deck_controls(self, deck_id):
        """Get available controls for the specified deck"""
        try:
            if not self.deck_a or not self.deck_b:
                logging.warning("⚠️ Decks not initialized, cannot get controls")
                return {}
                
            if deck_id == 'A':
                return self.deck_a.get_controls()
            elif deck_id == 'B':
                return self.deck_b.get_controls()
            else:
                logging.warning(f"⚠️ Unknown deck ID: {deck_id}")
                return {}
                
        except Exception as e:
            logging.error(f"❌ Error getting deck controls: {e}")
            return {}

    def get_current_visualizers(self):
        """Get currently loaded visualizers for both decks"""
        try:
            if not self.deck_a or not self.deck_b:
                return {'A': 'Not Initialized', 'B': 'Not Initialized'}
                
            return {
                'A': self.deck_a.get_current_visualizer_name() if hasattr(self.deck_a, 'get_current_visualizer_name') else 'Unknown',
                'B': self.deck_b.get_current_visualizer_name() if hasattr(self.deck_b, 'get_current_visualizer_name') else 'Unknown'
            }
        except Exception as e:
            logging.error(f"❌ Error getting current visualizers: {e}")
            return {'A': 'Error', 'B': 'Error'}

    def get_mix_value(self):
        """Get current mix value (0.0-1.0)"""
        return self.mix_value

    def get_mix_value_percent(self):
        """Get current mix value as percentage (0-100)"""
        return int(self.mix_value * 100)

    def cleanup(self):
        """Clean up OpenGL resources"""
        try:
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
                    
                logging.info("✅ OpenGL resources cleaned up")
                
        except Exception as e:
            logging.error(f"❌ Error cleaning up OpenGL resources: {e}")

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            self.animation_timer.stop()
            self.cleanup()
            super().closeEvent(event)
        except Exception as e:
            logging.error(f"❌ Error in closeEvent: {e}")
            super().closeEvent(event)