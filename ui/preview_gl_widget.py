# ui/preview_gl_widget.py
import logging
import numpy as np
import ctypes
import time
import math
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import QTimer, QMutex, QMutexLocker
from OpenGL.GL import *

class PreviewGLWidget(QOpenGLWidget):
    def __init__(self, deck, parent=None):
        super().__init__(parent)
        self.deck = deck
        self.quad_vao = 0
        self.quad_vbo = 0
        self.shader_program = None
        self.initialized = False
        self.frame_count = 0
        
        # Thread safety
        self._mutex = QMutex()
        
        # Update timer for continuous refresh
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.trigger_update)
        self.update_timer.start(50)  # 20 FPS for previews (less resource intensive)
        
        logging.info(f"🖼️ PreviewGLWidget created for deck {deck.deck_id if deck else 'unknown'}")

    def trigger_update(self):
        """Trigger a repaint"""
        if self.initialized and self.isVisible():
            self.update()

    def initializeGL(self):
        """Initialize OpenGL resources"""
        with QMutexLocker(self._mutex):
            try:
                logging.debug(f"🔧 PreviewGLWidget.initializeGL for deck {self.deck.deck_id if self.deck else 'unknown'}")
                
                # Make sure we have the context
                self.makeCurrent()
                
                # Clear any existing OpenGL errors
                while glGetError() != GL_NO_ERROR:
                    pass
                
                # Set clear color
                glClearColor(0.05, 0.05, 0.1, 1.0)
                
                # Setup OpenGL state
                glDisable(GL_DEPTH_TEST)
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                
                # Load shaders
                if self.load_shaders():
                    if self.setup_quad():
                        self.initialized = True
                        logging.debug(f"✅ PreviewGLWidget initialized for deck {self.deck.deck_id if self.deck else 'unknown'}")
                    else:
                        logging.error("❌ Failed to setup preview quad")
                else:
                    logging.error("❌ Failed to load preview shaders")
                    
            except Exception as e:
                logging.error(f"❌ Error in PreviewGLWidget.initializeGL: {e}")
                import traceback
                traceback.print_exc()

    def load_shaders(self):
        """Load and compile shaders"""
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
            uniform sampler2D deckTexture;
            uniform int hasTexture;
            uniform float time;
            
            void main()
            {
                if (hasTexture > 0) {
                    // Sample the deck's FBO texture directly
                    FragColor = texture(deckTexture, TexCoord);
                    // Ensure full opacity
                    FragColor.a = 1.0;
                } else {
                    // No texture - show loading animation
                    vec2 center = vec2(0.5, 0.5);
                    float dist = distance(TexCoord, center);
                    float pulse = sin(time * 2.0) * 0.5 + 0.5;
                    vec3 color = vec3(0.1, 0.1, 0.2) * (1.0 - dist) * pulse;
                    FragColor = vec4(color, 1.0);
                }
            }
            """

            return self.compile_shader_program(vs_src, fs_src)
            
        except Exception as e:
            logging.error(f"❌ Error loading preview shaders: {e}")
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
                logging.error(f"❌ Preview vertex shader error: {error}")
                return False

            # Compile fragment shader
            fs = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fs, fs_src)
            glCompileShader(fs)
            
            if not glGetShaderiv(fs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(fs).decode()
                logging.error(f"❌ Preview fragment shader error: {error}")
                return False

            # Link program
            self.shader_program = glCreateProgram()
            glAttachShader(self.shader_program, vs)
            glAttachShader(self.shader_program, fs)
            glLinkProgram(self.shader_program)
            
            if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(self.shader_program).decode()
                logging.error(f"❌ Preview shader program link error: {error}")
                return False

            # Clean up shaders
            glDeleteShader(vs)
            glDeleteShader(fs)
            
            logging.debug("✅ Preview shaders compiled successfully")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error compiling preview shaders: {e}")
            return False

    def setup_quad(self):
        """Setup fullscreen quad geometry"""
        try:
            # Quad vertices with texture coordinates
            quad_vertices = np.array([
                # positions   # texCoords
                -1.0,  1.0,  0.0, 1.0,
                -1.0, -1.0,  0.0, 0.0,
                 1.0, -1.0,  1.0, 0.0,

                -1.0,  1.0,  0.0, 1.0,
                 1.0, -1.0,  1.0, 0.0,
                 1.0,  1.0,  1.0, 1.0
            ], dtype=np.float32)

            # Create VAO and VBO
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
            
            logging.debug("✅ Preview quad geometry created")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error setting up preview quad: {e}")
            return False

    def paintGL(self):
        """Render the preview"""
        try:
            # Make sure we have the context
            self.makeCurrent()
            
            # Set viewport for this widget
            glViewport(0, 0, self.width(), self.height())
            
            # Clear with dark background
            glClearColor(0.05, 0.05, 0.1, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            if not self.initialized or not self.shader_program:
                return
            
            # Ensure the deck renders to its FBO first
            texture_id = 0
            if self.deck and self.deck.is_ready():
                # Force deck to render to its FBO
                self.deck.render_to_fbo()
                # Get the texture from the deck's FBO
                texture_id = self.deck.get_texture()
            
            # Use shader program
            glUseProgram(self.shader_program)
            
            # Set uniforms
            has_texture = 1 if texture_id > 0 else 0
            glUniform1i(glGetUniformLocation(self.shader_program, "hasTexture"), has_texture)
            glUniform1f(glGetUniformLocation(self.shader_program, "time"), time.time())
            
            if texture_id > 0:
                # Bind the deck's FBO texture
                glActiveTexture(GL_TEXTURE0)
                glBindTexture(GL_TEXTURE_2D, texture_id)
                glUniform1i(glGetUniformLocation(self.shader_program, "deckTexture"), 0)
                
                # Set texture parameters
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            
            # Draw the quad
            if self.quad_vao:
                glBindVertexArray(self.quad_vao)
                glDrawArrays(GL_TRIANGLES, 0, 6)
                glBindVertexArray(0)
            
            # Clean up
            glUseProgram(0)
            if texture_id > 0:
                glBindTexture(GL_TEXTURE_2D, 0)
            
            # Update frame counter for debugging
            self.frame_count += 1
            if self.frame_count % 100 == 0:  # Every ~5 seconds at 20fps
                if self.deck:
                    current_vis = self.deck.get_current_visualizer_name()
                    logging.debug(f"🖼️ Preview {self.deck.deck_id}: {current_vis}, Frame: {self.frame_count}")
                
        except Exception as e:
            if not hasattr(self, '_last_error_time') or time.time() - self._last_error_time > 5:
                logging.error(f"❌ Error in PreviewGLWidget.paintGL: {e}")
                self._last_error_time = time.time()

    def resizeGL(self, width, height):
        """Handle resize"""
        glViewport(0, 0, width, height)
        logging.debug(f"📐 Preview resized to {width}x{height}")

    def update_preview(self):
        """Update the preview (called from outside)"""
        if self.initialized:
            self.update()

    def set_deck(self, deck):
        """Set a new deck for this preview"""
        with QMutexLocker(self._mutex):
            self.deck = deck
            logging.debug(f"🔄 Preview deck changed to {deck.deck_id if deck else 'None'}")

    def cleanup(self):
        """Clean up OpenGL resources"""
        try:
            with QMutexLocker(self._mutex):
                self.update_timer.stop()
                
                self.makeCurrent()
                
                if self.shader_program:
                    glDeleteProgram(self.shader_program)
                    self.shader_program = None
                    
                if self.quad_vao:
                    glDeleteVertexArrays(1, [self.quad_vao])
                    self.quad_vao = 0
                    
                if self.quad_vbo:
                    glDeleteBuffers(1, [self.quad_vbo])
                    self.quad_vbo = 0
                    
                self.initialized = False
                logging.debug("✅ Preview GL resources cleaned up")
                
        except Exception as e:
            logging.error(f"❌ Error cleaning up preview: {e}")

    def closeEvent(self, event):
        """Handle close event"""
        self.cleanup()
        super().closeEvent(event)